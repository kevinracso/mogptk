import numpy as np
import gpflow

import logging
logging.getLogger('tensorflow').propagate = False

def load(filename):
    # TODO: load training data too?
    m = gpflow.saver.Saver().load(filename)
    return model(None, m)

class model:
    """
    Multioutput Gaussian proccess model. Can be either MOSM, CSM, SM-LMC or CONV.

    This class is used to use a multioutput GP model, train and test data can be added,
    the model can be used to train a predict.

    Example:

        ---TO-DO---

    Atributes:
        name ():
        data (obj, instance of mogptk.data):
        model ():
        Q (int): Number of components of the model.
        parameters ():
    """

    def __init__(self, name, data, Q):
        self.name = name
        self.data = data
        self.model = None
        self.Q = Q
        self.params = []

    def _kernel(self):
        # overridden by specific models
        raise Exception("kernel not specified")
    
    def _transform_data(self, x, y):
        # overridden by specific models
        raise Exception("kernel not specified")

    def _update_params(self, trainables):
        for key, val in trainables.items():
            names = key.split("/")
            if len(names) == 5 and names[1] == 'kern' and names[2] == 'kernels':
                q = int(names[3])
                name = names[4]
                self.params[q][name] = val

    def get_params(self):
        """
        Returns all parameters set for the kernel per component.
        """
        return self.params

    def set_param(self, q, key, val):
        """
        Sets an initial kernel parameter prior to optimizations for component q with key the parameter name.

        Args:
            q (int): Component of kernel.

            key (str): Name of component.

            val (float, ndarray): Value of parameter.
        """
        if q < 0 or len(self.params) <= q:
            raise Exception("qth component %d does not exist" % (q))
        if key not in self.params[q]:
            raise Exception("parameter name '%s' does not exist" % (key))

        self.params[q][key] = val

    def save(self, filename):
        # TODO: needs testing and saving training data?
        gpflow.saver.Saver().save(filename, self.model)

    def build(self, kind='full', disp=True):
        if disp:
            print("Building...")

        x, y = self._transform_data(self.data.X, self.data.Y)

        if kind == 'full':
            self.model = gpflow.models.GPR(x, y, self._kernel())
        elif kind == 'sparse':
            # TODO: test if induction points are set
            self.name += ' (sparse)'
            self.model = gpflow.models.SGPR(x, y, self._kernel())
        elif kind == 'sparse-variational':
            self.name += ' (sparse-variational)'
            self.model = gpflow.models.SVGP(x, y, self._kernel(), gpflow.likelihoods.Gaussian())
        else:
            raise Exception("model type '%s' does not exist" % (kind))

        self.X_pred = {}
        self.Y_mu_pred = {}
        self.Y_var_pred = {}

    def train(self, kind='full', method='L-BFGS-B', maxiter=1000, disp=True, learning_rate=0.001):
        """
        Builds and trains the model using the kernel and its parameters.

        For different optimizers, see scipy.optimize.minimize.
        It can be bounded by a maximum number of iterations, disp will output final optimization information.
        When using the 'Adam' optimizer, a learning_rate can be set.

        Args:
            kind (str): Type of model to use, posible mode are 'full', 'sparse' and 'sparse-variational'.
            method (str): Optimizer to use, if "Adam" is chosen, gpflow.training.Adamoptimizer will be used,
                otherwise the passed scipy optimizer is used. Default to scipy 'L-BFGS-B'.

            maxiter (int): Maximum number of iterations, default to 1000.

            disp (bool): If true it display information on the optimization, only valid to scipy optimizers.
                Default to True.

            learning_rate(float): Learning rate of Adam optimizer. Only valid with Adam, default to 0.001.
        """
        
        if self.model == None:
            self.build(kind, disp)

        if disp:
            print("Optimizing...")

        opt = gpflow.train.ScipyOptimizer(method=method)
        opt.minimize(self.model, anchor=True, disp=disp, maxiter=maxiter)

        self._update_params(self.model.read_trainables())

        if disp:
            print("Done")


    ################################################################################
    # Predictions ##################################################################
    ################################################################################

    def get_predictions(self):
        """
        Returns the input, posterior mean and posterior variance values all channels.

        Returns:
            x_pred, y_mu_pred, y_var_pred: ndarrays with the input, posterior mean and 
                posterior variance of the las prediction done. 
        """
        if self.model == None:
            raise Exception("build (and train) the model before doing predictions")

        if len(self.X_pred) == 0:
            raise Exception("use predict before retrieving the predictions on the model")
        return self.X_pred, self.Y_mu_pred, self.Y_var_pred

    def get_channel_predictions(self, channel):
        """
        Returns the input, posterior mean and posterior variance values for a given channel.

        Args:
            channel (str, int): Channel to set prediction, can be either a string with the name
                of the channel or a integer with the index.

        Returns:
            x_pred, y_mu_pred, y_var_pred: ndarrays with the input, posterior mean and 
                posterior variance of the las prediction done. 
        """
        if self.model == None:
            raise Exception("build (and train) the model before doing predictions")

        if len(self.X_pred) == 0:
            raise Exception("use predict before retrieving the predictions on the model")
        channel = self.data.get_channel_index(channel)

        return self.X_pred[channel], self.Y_mu_pred[channel], self.Y_var_pred[channel]

    def set_prediction_range(self, channel, start=None, end=None, step=None, n=None):
        """
        Sets the prediction range for a certain channel in the interval [start,end].
        with either a stepsize step or a number of points n.

        Args:
            channel (str, int): Channel to set prediction, can be either a string with the name
                of the channel or a integer with the index.

            start (float, optional): Initial value of range, if not passed the first point of training
                data is taken. Default to None.

            end (float, optional): Final value of range, if not passed the last point of training
                data is taken. Default to None.

            step (float, optional): Spacing between values.

            n (int, optional): Number of samples to generate.

            If neither "step" or "n" is passed, default number of points is 100.
        """
        if self.model == None:
            raise Exception("build (and train) the model before doing predictions")

        channel = self.data.get_channel_index(channel)
        if start == None:
            start = self.data.X[channel][0]
        if end == None:
            end = self.data.X[channel][-1]
        if end <= start:
            raise Exception("start must be lower than end")

        if step == None and n != None:
            self.X_pred[channel] = np.linspace(start, end, n)
        else:
            if step == None:
                step = (end-start)/100
            self.X_pred[channel] = np.arange(start, end+step, step)
    
    def set_predictions(self, xs):
        """
        Sets the prediction ranges for all channels.

                Args:

                xs (list, ndarray, dict): Prediction ranges, where the index/key is the channel
                        ID/name and the values are either lists or Numpy arrays.
        """
        if isinstance(xs, list):
            xs = np.array(xs)

        if isinstance(xs, np.ndarray):
            for channel in range(len(xs)):
                self.set_prediction_x(channel, xs[channel])
        elif isinstance(xs, dict):
            for channel, x in xs.items():
                self.set_prediction_x(channel, x)
        else:
            raise Exception("xs expected to be a list, dict or Numpy array")

    def set_prediction_x(self, channel, x):
        """
        Sets the prediction range using a list of Numpy array for a certain channel.

        Args:
            channel (str, int): Channel to set prediction, can be either a string with the name
                of the channel or a integer with the index.
            x (ndarray): Numpy array with input values for channel.
        """
        if self.model == None:
            raise Exception("build (and train) the model before doing predictions")

        channel = self.data.get_channel_index(channel)
        if isinstance(x, list):
            x = np.array(x)
        elif not isinstance(x, np.ndarray):
            raise Exception("x expected to be a list or Numpy array")

        self.X_pred[channel] = x

    def predict(self, x=None):
        """
        Predict with model.

        Will make a prediction using x as input. If no input value is passed, the prediction will 
        be made with atribute self.X_pred that can be setted with other functions.
        It returns the X, Y_mu, Y_var values per channel.

        Args:
            x (dict): Dictionary where keys are channel index and elements numpy arrays with 
                          channel inputs.

        Returns:
            X_pred, Y_mu_pred, Y_var_pred: Prediction input, output and variance of the model.

        """
        if self.model == None:
            raise Exception("build (and train) the model before doing predictions")

        if x is not None:
            self.set_predictions(x)

        x, _ = self._transform_data(self.X_pred)
        mu, var = self.model.predict_f(x)

        n = 0
        for channel in self.X_pred:
            n += self.X_pred[channel].shape[0]
        
        i = 0
        for channel in self.X_pred:
            n = self.X_pred[channel].shape[0]
            if n != 0:
                self.Y_mu_pred[channel] = mu[i:i+n].reshape(1, -1)[0]
                self.Y_var_pred[channel] = var[i:i+n].reshape(1, -1)[0]
                i += n


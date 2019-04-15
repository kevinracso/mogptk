# MultiOutputSpectralMixture
This repository provides a toolbox to perform multi-output GP regression with multi-output spectral mixture kernel (MOSM). This kernel is specified in detail in the following publication: G. Parra, F. Tobar, Spectral Mixture Kernels for Multi-Output Gaussian Processes, Advances in Neural Information Processing Systems, 2017

Proceedings link: http://papers.nips.cc/paper/7245-spectral-mixture-kernels-for-multi-output-gaussian-processes

The kernel learns the cross-channel correlations of the data, so it is particularly well-suited for the task of signal reconstruction in the event of sporadic data loss.

# Main Requirements
-Python 3.6
-GPFlow 1.3
-Tensorflow-gpu 1.12
-scikit-learn
-matplotlib
-seaborn
-numpy
-scipy
-skopt

# Notes on requirements
It seems that the latest tensorflow packages can be found in the anaconda channel, so using the
following command to create a new conda environment yields the easiest results:
	conda create -n TFGPU -c anaconda scipy scikit-learn matplotlib seaborn tensorflow-gpu 
This command creates a new env named TFGPU with tensorflow-gpu 1.12 (as of this writing).
--------------------------------------------------------------------------------------------------
To install GPFlow: 
- Clone the repo https://github.com/GPflow/GPflow
- source the environment TFGPU
- Go to GPflow folder
- run pip install .
--------------------------------------------------------------------------------------------------
To install skopt (which is used for initial parameter search using bayesian optimization):
- pip install scikit-optimize
--------------------------------------------------------------------------------------------------
The above commands should work as long as the pip you're using corresponds to the env you 
created. To make sure this is the case you can use the command 'which pip', and this should
show pip running from a bin folder located at the environment. Otherwise, you'd
be using other pip (which could be from another env or, even worse, from the local machine).

#################################################################################################

Some simple examples are provided in the examples notebook.
To see the model performing over real-world data refer to the smartphone_dataset_example notebook.

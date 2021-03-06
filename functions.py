
import numpy as np
import math

############################
#   ACTIVATION FUNCTIONS   #
############################

def _relu (x):
    '''
        REctified Linear Unit acivation function: relu(x) = max(0,x)
    '''
    return max(0,x)

def _identity (x):
    '''
        identity function: identity(x) = x
    '''
    return x

def _threshold (x):
    '''
        threshold activation function: treshold(x) = 1 if x>0
                                       treshold(x) = 0 if x<=0
    '''
    return 1 if x>0 else 0

def _logistic (x):
    '''
        logistic activation function: logistic(x) = 1 / (1 + exp(-x))
    '''
    return 1 / ( 1 + math.exp(-x) )

def _tanh (x):
    '''
        tanh activation function (returns hyperbolic tangent of the input) = tanh(x)
    '''
    return math.tanh (x)

def _zero_one_tanh (x):
    '''
        tanh activation function which output is from zero to one: _zero_one_tanh(x) = (1 + tanh(x))/2
    '''
    return (1 + math.tanh (x))/2


relu = np.vectorize (_relu, otypes=[float])
identity = np.vectorize (_identity, otypes=[float])
threshold = np.vectorize (_threshold, otypes=[float])
logistic = np.vectorize (_logistic, otypes=[float])
tanh = np.vectorize (_tanh, otypes=[float])
zero_one_tanh = np.vectorize (_zero_one_tanh, otypes=[float])

activation_functions = {
    "relu": relu,
    "identity": identity,
    "threshold": threshold,
    "logistic": logistic,
    "tanh": tanh,
    "zero_one_tanh": zero_one_tanh,
}


########################################
#   ACTIVATION FUNCTIONS DERIVATIVES   #
########################################

def _relu_derivative (x):
    '''
        REctified Linear Unit activation function derivative: relu'(x) = 0 if x<0
                                                              relu'(x) = 1 if x>=0
    '''
    return 0 if x<=0 else 1

def _identity_derivative (x):
    '''
        identity function derivative: identity'(x) = 1
    '''
    return 1

def _threshold_derivative (x):
    '''
        threshold activation function derivative: treshold'(x) = 0
    '''
    return 0

def _logistic_derivative (x):
    '''
        logistic activation function derivative: logistic'(x) = logistic(x) * ( 1 - logistic(x) )
    '''
    return _logistic(x) * ( 1 - _logistic (x) )

def _tanh_derivative (x):
    '''
        tanh activation function derivatives: tanh'(x) = 1 - (tanh(x))**2
    '''
    return 1 - (math.tanh (x))**2

def _zero_one_tanh_derivative (x):
    '''
        zero-one tanh activation function derivatives: tanh'(x) = 1/2 * ( 1 - (tanh(x))**2 )
    '''
    return 1/2 * ( 1 - (math.tanh (x))**2 )

relu_derivative = np.vectorize (_relu_derivative, otypes=[float])
identity_derivative = np.vectorize (_identity_derivative, otypes=[float])
threshold_derivative = np.vectorize (_threshold_derivative, otypes=[float])
logistic_derivative = np.vectorize (_logistic_derivative, otypes=[float])
tanh_derivative = np.vectorize (_tanh_derivative, otypes=[float])
zero_one_tanh_derivative = np.vectorize (_zero_one_tanh_derivative, otypes=[float])

activation_functions_derivatives = {
    "relu": relu_derivative,
    "identity": identity_derivative,
    "threshold": threshold_derivative,
    "logistic": logistic_derivative,
    "tanh": tanh_derivative,
    "zero_one_tanh": zero_one_tanh_derivative
}

######################
#   LOSS FUNCTIONS   #
######################

def _squaredLoss ( true_output, predicted_output ):
    '''
        squared loss: squaredLoss (t, p) = 1/2 * (t - p)^2 
    '''
    return 1/2 * (true_output - predicted_output)**2

def _binaryLogLoss ( true_output, predicted_output ):
    '''
        loss function for binary classification task: binaryLogLoss(t,p) = - (t * log(p) + (1-t) * log(1-p))
        t ∈ {0,1} is the true class.
        p ∈ [0,1] is the predicted probability for class 1.

        This implementation avoids the extreme values of the logatithm function by returning:
         0            if t==p
        -log(1e-6)    if t==1-p instead of -log(0) that would be -∞

    '''
    eps = 1e-6
    if true_output>0.5:
        return -math.log(max(predicted_output,eps))
    else:
        return -math.log(max(1-predicted_output,eps))


squaredLoss = np.vectorize (_squaredLoss, otypes=[float])
binaryLogLoss = np.vectorize (_binaryLogLoss, otypes=[float])

loss_functions = {
    "squared": squaredLoss,
    "log_loss": binaryLogLoss
}

##################################
#   LOSS FUNCTIONS DERIVATIVES   #
##################################

def _squaredLoss_derivative ( true_output, predicted_output ):
    '''
        squared loss derivative wrt predicted output p: squaredLoss' (t, p) = -(t - p)
    '''
    return predicted_output - true_output

def _binaryLogLoss_derivative ( true_output, predicted_output ):
    '''
        derivative of the loss function for binary classification task wrt predicted output p: 
        binaryLogLoss'(t,p) = - (t/p - (1-t)/(1-p))
        
        t ∈ {0,1} is the true class.
        p ∈ [0,1] is the predicted probability for class 1.

        This implementation avoids the extreme values of the inverse function by returning:
         -1             if t==1 and p==1 
          1             if t==0 and p==0 
         -1/1e-6        if t==1 and p==0 instead of -1/0 that would be -∞
          1/1e-6        if t==0 and p==1 instead of  1/0 that would be  ∞

    '''
    eps = 1e-6
    if true_output > 0.5:
        return -1/max(predicted_output, eps)
    else:
        return 1/max(1-predicted_output, eps)

squaredLoss_derivative = np.vectorize ( _squaredLoss_derivative, otypes=[float] )
binaryLogLoss_derivative = np.vectorize ( _binaryLogLoss_derivative, otypes=[float] )

loss_functions_derivatives = {
    "squared": squaredLoss_derivative,
    "log_loss": binaryLogLoss_derivative
}

##########################
#   ACCURACY FUNCTIONS   #
##########################

def _euclidean_loss (true_output, predicted_output):
    '''
        computes the mean euclidean loss given an array of true outputs T and an array of predicted outputs P.
        
        the euclidean loss is defined for one item (true output t and predicted output p) as
        euclideanloss (t,p) = √ sum_i (t_i - p_i)^2
        
        the mean euclidean loss for two arrays of true outputs T and an array of predicted outputs P is just the average of the euclidean loss of the elements:
        euclideanloss (T,P) = 1/n sum_j euclideanloss (T[j], P[j])
    '''
    squares = (true_output - predicted_output) ** 2
    sum_of_squares = np.sum (squares, axis=1)
    distances = np.sqrt (sum_of_squares)
    return np.average (distances)

def _classification_loss (true_output, predicted_output):
    '''
        computes the mean classification error given an array of true outputs T and an array of predicted outputs P.

        the classification loss is defined for one item (true output t and predicted output p) as
        classificationloss (t,p) = 1 if t!=p
                                   0 otherwise

        the mean classification error for two arrays of true outputs T and an array of predicted outputs P is just the average of the classification error of the elements:
        classificationloss (T,P) = 1/n sum_j classificationloss (T[j], P[j])
    '''
    true_output = np.array(true_output)
    return sum (map (lambda x:1 if x else 0, true_output.ravel() != predicted_output.ravel() ) ) / len(true_output)

accuracy_functions = {
    "euclidean": _euclidean_loss,
    "classification": _classification_loss
}

##############################
#   WEIGHT INIT. FUNCTIONS   #
##############################

def _normal_random_weight_init(value, shape, generator=None):
    '''
        returns a random matrix with given shape and which entries are drawn from a normal distribution with given average.
        if no random generator is provided numpy.random is used  
    '''
    if generator is None:
        generator = np.random
    return value * generator.standard_normal (shape)

def _uniform_random_weight_init(value, shape, generator=None):
    '''
        returns a random matrix with given shape and which entries are drawn from an uniform distribution of range (-value; +value).     

        if no random generator is provided numpy.random is used  
    '''
    if generator is None:
        generator = np.random
    return generator.uniform(-value, value, shape)

weights_init_functions = {
    "random_normal": _normal_random_weight_init,
    "random_uniform": _uniform_random_weight_init
}

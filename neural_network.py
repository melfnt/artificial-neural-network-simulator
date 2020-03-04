
import numpy as np
import random

from functions import activation_functions, activation_functions_derivatives, loss_functions, loss_functions_derivatives

class BaseNeuralNetwork:

    def __init__(self, hidden_layer_sizes=(100, ), hidden_activation='relu', output_activation="identity", solver='sgd', alpha=0.0001, batch_size='auto',
                       learning_rate='constant', learning_rate_init=0.001, power_t=0.5, max_iter=200, shuffle=True,
                       random_state=None, tol=0.0001, verbose=False, warm_start=False, momentum=0.9, nesterovs_momentum=True,
                       early_stopping=False, validation_fraction=0.1, beta_1=0.9, beta_2=0.999, epsilon=1e-08, n_iter_no_change=10,
                       max_fun=15000, loss="squared"):

        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.power_t = power_t
        self.max_iter = max_iter
        self.shuffle = shuffle
        self.random_state = random_state
        self.tol = tol
        self.verbose = verbose
        self.warm_start = warm_start
        self.momentum = momentum
        self.nesterovs_momentum = nesterovs_momentum
        self.early_stopping = early_stopping
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        
        self._debug_forward_pass = False
        self._debug_backward_pass = False
        self._debug_epochs = False

        self.b_size = 0

        if solver != "sgd":
            raise ValueError ("Only stochastic gradient descent solver is implemented")

        if hidden_activation not in activation_functions or hidden_activation not in activation_functions_derivatives:
            raise ValueError ("hidden activation function {} not implemented".format(hidden_activation))
        self._hidden_activation = activation_functions[hidden_activation]
        self._hidden_activation_derivative = activation_functions_derivatives[hidden_activation]

        if output_activation not in activation_functions or output_activation not in activation_functions_derivatives:
            raise ValueError ("output activation function {} not implemented".format(output_activation))
        self._output_activation = activation_functions[output_activation]
        self._output_activation_derivative = activation_functions_derivatives[output_activation]

        if loss not in loss_functions or loss not in loss_functions_derivatives:
            raise ValueError ("loss function {} not implemented".format(loss_functions))
        self._loss = loss_functions[loss]
        self._loss_derivative = loss_functions_derivatives[loss]

        if random_state is not None:
            np.random.seed ( random_state )

        # TODO: actual learning rate rule
        self._eta = learning_rate_init

        self._weights = None
        self.delta_olds = None

    def set_weights ( self, weights ):
        for i in range (len(weights)-1):
            assert weights[i].shape[1] == weights[i+1].shape[0]-1, "weight shapes must be compatible. Got {}".format(list(map (lambda x: x.shape, weights)))
        self._weights = weights

    def _generate_random_weights ( self, n_features, n_outputs ):
        self._weights = []
        for n,m in zip ([n_features]+list(self.hidden_layer_sizes), list(self.hidden_layer_sizes)+[n_outputs]):
            W = 0.7 * np.random.randn (n+1,m)
            self._weights.append (W)

    def _forward_pass ( self, X ):
        '''
            feeds the network with a minibatch of samples X (n_samples, n_features)
            returns layer_nets, layer_outputs such that:
                layer_nets[0] is the input X (n_samples, n_features)
                layer_nets[i] for i=1...n_layers are the nets of the hidden layer i (n_samples, dim_layer_i)
                layer_outputs[0] is the input X (n_samples, n_features)
                layer_outputs[i] for i=1...n_layers are the outputs of the hidden layer i (n_samples, dim_layer_i)

                in particular, layer_outputs[-1] is the output predicted by the output units 
        '''
        assert X.shape[1] == self._weights[0].shape[0]-1, "wrong number of features {} for first layer weights shape {}".format(X.shape[1], self._weights[0].shape[0]-1)
        layer_outputs = [X]
        layer_nets = [X]
        
        #hidden layers
        for i in range (len(self._weights)-1):
            inp = layer_outputs[i]
           
            biases = np.ones( (inp.shape[0], 1) )
            inp_and_biases = np.hstack ( (inp, biases) )
            
            net = np.matmul (inp_and_biases, self._weights[i])
            
            layer_nets.append (net)
            layer_outputs.append ( self._hidden_activation (net) )
            if self._debug_forward_pass:
                print ("[DEBUG] layer {}\ninput + bias:\n{}\nweights\n{}\nnet\n{}\noutput\n{}".format(i, inp_and_biases, self._weights[i], net, layer_outputs[-1]))
        
        # output layer
        inp = layer_outputs[-1]
        biases = np.ones( (inp.shape[0], 1) )
        inp_and_biases = np.hstack ( (inp, biases) )
        net = np.matmul (inp_and_biases, self._weights[-1])
        layer_nets.append (net)
        layer_outputs.append (self._output_activation (net))
        
        if self._debug_forward_pass:
            print ("[DEBUG] output layer\ninput + bias:\n{}\nweights\n{}\nnet\n{}\noutput\n{}".format(inp_and_biases, self._weights[-1], net, layer_outputs[-1]))
        
        return layer_nets, layer_outputs

    def _backpropagation ( self, layers_nets, layers_outputs, real_outputs ):

        assert len(layers_outputs) == len(layers_nets), "Backpropagation: number of layers outputs and nets must be the same."
        assert len(layers_outputs) == len(self._weights) + 1, "Backpropagation: number of layers outputs must be number of weights matrices + 1"

        n_samples = len(layers_outputs[0])
        delta_weights = []

        #output layers        
        dE = self._loss_derivative (real_outputs, layers_outputs[-1])
        df = self._output_activation_derivative ( layers_nets[-1] )
        deltas = dE * df

        prev_layer_outputs = layers_outputs[-2]
        biases = np.ones( (prev_layer_outputs.shape[0], 1) )
        out_and_biases = np.hstack ( (prev_layer_outputs, biases) )
        dW = sum ( a[:, np.newaxis]*b for a,b in zip (out_and_biases, deltas) ) / n_samples

        delta_weights.insert (0, dW)

        if self._debug_backward_pass:
            print ("[DEBUG] backpropagation output layer\nerror derivative:\n{}\nactivation derivative\n{}".format(dE, df))
            print ("[DEBUG] deltas for this layer (=dE*df)\n{}".format(deltas))
            print ("[DEBUG] dW\n{}".format(dW))
            print ("\n")
        
        # hidden layers
        for i in range ( len(layers_outputs)-2, 0, -1 ):
            weights = self._weights[i]
            dE = np.array ( list (map(lambda d: np.matmul(weights,d[:,np.newaxis]).flatten(), deltas )) )
            # remove dE/do_b where o_b is the bias output
            dE = dE[:, :-1]
            df = self._hidden_activation_derivative ( layers_nets[i] )
            deltas = dE * df
            prev_layer_outputs = layers_outputs[i-1]
            biases = np.ones( (prev_layer_outputs.shape[0], 1) )
            out_and_biases = np.hstack ((prev_layer_outputs, biases))
            dW = sum ( a[:, np.newaxis]*b for a,b in zip (out_and_biases, deltas) ) / n_samples
            delta_weights.insert (0, dW)

            if self._debug_backward_pass:
                print ("[DEBUG] backpropagation layer {}\nerror derivative:\n{}\nactivation derivative\n{}".format(i, dE, df))
                print ("[DEBUG] deltas for this layer (=dE*df)\n{}".format(deltas))
                print ("[DEBUG] dW\n{}".format(dW))
                print ("\n")


        assert len(delta_weights) == len (self._weights), "Backpropagation: number of delta_weights and weights are not the same"     
        return delta_weights

    def _do_epoch ( self, X, y ):

        if (self.shuffle):
            indexes = list (range(len(X)))
            random.shuffle (indexes)
            X = X[indexes]
            y = y[indexes]

        if self.delta_olds is None:
            self.delta_olds = [np.zeros_like(W) for W in self._weights]

        n_iterations = len(X) // self.b_size + (0 if len(X) % self.b_size == 0 else 1)

        for b in range(n_iterations):

            start = self.b_size * b
            stop = self.b_size * (b + 1)

            layers_nets, layer_outputs = self._forward_pass (X[start:stop])

            delta_weights = self._backpropagation ( layers_nets, layer_outputs, y[start:stop] )
            for W, dW, m in zip (self._weights, delta_weights, self.delta_olds):
                # TODO: use the right learning rate depending on the epochs
                m *= self.momentum
                m += (1 - self.momentum) * dW

                W -= (self._eta * m) + 2 * (self.alpha * (self.b_size/len(X)) * W)
            
    def predict ( self, X ):
        assert self._weights is not None, "call fit() or set_weights() before predict()"
        X = np.array (X)
        _ , layer_outputs = self._forward_pass (X)
        return layer_outputs[-1]
    
    def fit ( self, X, y ):
        X = np.array (X)
        y = np.array (y)
        # if y.shape == (n_samples) convert it to a column vector (n_samples, 1)
        if y.ndim == 1:
            y = y[:, np.newaxis]

        assert len(X) == len(y), "size of X and y must be the same"

        if not self._weights or not self.warm_start:
            self._generate_random_weights (X.shape[1], y.shape[1])

        # TODO: other stopping criterions
        epoch_no = 0

        if (self.batch_size=='auto'):
            self.b_size=min(200, len(X))
        else:
            self.b_size=max(1, min(self.batch_size, len(X)))

        if self._debug_epochs:
            n_iterations = len(X) // self.b_size + (0 if len(X) % self.b_size == 0 else 1)
            print ("[DEBUG] batch size:", self.b_size)
            print ("[DEBUG] n_iterations per epoch:", n_iterations)


        while epoch_no < self.max_iter:
            self._do_epoch ( X, y )
            predicted = self.predict (X)
            loss = self._loss (y, predicted)
            if self._debug_epochs:
                print ("Loss for epoch {}: {}".format(epoch_no, sum(loss)))
            epoch_no += 1

class MLPRegressor (BaseNeuralNetwork):
    def __init__ ( self, hidden_layer_sizes=(100, ), activation='relu', solver='sgd', alpha=0.0001, batch_size='auto', 
                   learning_rate='constant', learning_rate_init=0.001, power_t=0.5, max_iter=200, shuffle=True, random_state=None, 
                   tol=0.0001, verbose=False, warm_start=False, momentum=0.9, nesterovs_momentum=True, early_stopping=False, 
                   validation_fraction=0.1, beta_1=0.9, beta_2=0.999, epsilon=1e-08, n_iter_no_change=10, max_fun=15000 ):
        
        super().__init__ (hidden_layer_sizes=hidden_layer_sizes, hidden_activation=activation, output_activation="identity", 
                       solver=solver, alpha=alpha, batch_size=batch_size, learning_rate=learning_rate, learning_rate_init=learning_rate_init,
                       power_t=power_t, max_iter=max_iter, shuffle=shuffle, random_state=random_state, tol=tol, verbose=verbose, 
                       warm_start=warm_start, momentum=momentum, nesterovs_momentum=nesterovs_momentum, early_stopping=early_stopping, 
                       validation_fraction=validation_fraction, beta_1=beta_1, beta_2=beta_2, epsilon=epsilon, n_iter_no_change=n_iter_no_change,
                       max_fun=max_fun, loss="squared")

class MLPClassifier (BaseNeuralNetwork):
    def __init__ ( self, hidden_layer_sizes=(100, ), activation='relu', solver='sgd', alpha=0.0001, batch_size='auto', learning_rate='constant',
                   learning_rate_init=0.001, power_t=0.5, max_iter=200, shuffle=True, random_state=None, tol=0.0001, verbose=False,
                   warm_start=False, momentum=0.9, nesterovs_momentum=True, early_stopping=False, validation_fraction=0.1, beta_1=0.9,
                   beta_2=0.999, epsilon=1e-08, n_iter_no_change=10, max_fun=15000 ):
        
        super().__init__ (hidden_layer_sizes=hidden_layer_sizes, hidden_activation=activation, output_activation="zero_one_tanh", 
                       solver=solver, alpha=alpha, batch_size=batch_size, learning_rate=learning_rate, learning_rate_init=learning_rate_init,
                       power_t=power_t, max_iter=max_iter, shuffle=shuffle, random_state=random_state, tol=tol, verbose=verbose, 
                       warm_start=warm_start, momentum=momentum, nesterovs_momentum=nesterovs_momentum, early_stopping=early_stopping, 
                       validation_fraction=validation_fraction, beta_1=beta_1, beta_2=beta_2, epsilon=epsilon, n_iter_no_change=n_iter_no_change,
                       max_fun=max_fun, loss="log_loss")
    
    def fit ( self, X, y ):
        y = np.array (y)
        # if y.shape == (n_samples) convert it to a column vector (n_samples, 1)
        if y.ndim == 1:
            y = y[:, np.newaxis]
        assert y.shape[1] == 1, "Multilabel output is not supported for classification"
        for label in y[:, 0]:
            assert label == 0 or label == 1, "labels for classification must be either 0 or 1"
        super().fit(X,y)

    def predict ( self, X ):
        y = super().predict (X)
        ones = y >= 0.5
        zeros = y < 0.5
        y[ones] = 1
        y[zeros] = 0
        return y

    def predict_proba ( self, X ):
        return super().predict (X)
    
    def predict_log_proba ( self, X ):
        return np.log( self.predict_proba(X) )
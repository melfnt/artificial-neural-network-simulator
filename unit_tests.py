
import unittest

import numpy as np
from neural_network import *
from utility import *
import os

class DummyModel:

    def __init__(self):
        self.learning_rate_init = 0.1
        self.momentum = 0.5
        self.alpha = 0.001
        self.n_classes = 0

        self.fit_log = []
        self.predict_log = []
    
    def fit (self, X, y):
        self.fit_log.append (self.get_params())
        y = np.array (y)
        if y.ndim == 1:
            self.n_classes = y.shape[0]
        else:
            self.n_classes = y.shape[1]
        return y

    def predict (self, X):
        self.predict_log.append (self.get_params())
        return  np.zeros ((len(X), self.n_classes))
    
    def get_params (self):
        return {'alpha': self.alpha, "momentum": self.momentum, "learning_rate_init": self.learning_rate_init}

    

class TestNeuralNetwork (unittest.TestCase):

    def test_forward_pass ( self ):
        # a network that XORs its inputs
        n = BaseNeuralNetwork ( hidden_layer_sizes=(2,), hidden_activation="threshold", momentum=0, alpha=0 )
        weights = [
                    np.array ([[ 1,    1  ],
                               [ 1,    1  ],
                               [-1.5, -0.5]]),
                    np.array ([[-1  ],
                               [ 1  ],
                               [-0.5]])
        ]
        n.set_weights (weights)
        X = np.array ([[0,0],
                       [0,1],
                       [1,0],
                       [1,1]])
        y = [[0], [1], [1], [0]]
        predicted = n.predict (X)
        for x, y_pred, y_true in zip (X,predicted, y):
            if y_true[0] == 1:
                self.assertGreater (y_pred[0], 0, "wrong XOR prediction for input {}".format(x))
            else:
                self.assertLess (y_pred[0], 0, "wrong XOR prediction for input {}".format(x))
    
    # TEST backpropagation based on: https://mattmazur.com/2015/03/17/a-step-by-step-backpropagation-example/
    def test_matt_mazur ( self ):
        n = BaseNeuralNetwork ( hidden_layer_sizes=(2,), hidden_activation="logistic", output_activation="logistic", max_iter=1, 
                                warm_start=True, learning_rate_init=0.5, momentum=0, alpha=0 )
        weights = [
                    np.array ([[ .15, .25 ],
                               [ .2 , .3  ],
                               [ .35, .35 ]]),
                    np.array ([[ .4 , .5  ],
                               [ .45, .55 ],
                               [ .6 , .6  ]])
        ]
        n.set_weights (weights)
        X = np.array ([[0.05, 0.1]])
        y = np.array ([[0.01, 0.99]])
        predicted = n.predict (X)
        losses = loss_functions["squared"] (y, predicted)
        for x, p, loss in zip (X,predicted, losses):
            self.assertAlmostEqual (sum(loss), 0.2983711083, 8, "Wrong loss")
        n.fit (X, y)
        expected_weights = [
            np.array ([[ .149780716, .24975114  ],
                       [ .19956143,  .29950229  ],
                       [ .34561432,  .34502287  ]]),
            np.array ([[ .35891648,  .51130127  ],
                       [ .408666186, .561370121 ],
                       [ .53075072,  .61904912  ]])
        ]
        self.assertTrue (np.allclose (n._weights, expected_weights), "Wrong weights after one step of backpropagation")
    
    def test_params (self):
        c = MLPClassifier (hidden_layer_sizes=(10,10), activation="tanh", alpha=1, batch_size=200, max_iter=300)
        r = MLPRegressor (hidden_layer_sizes=(20,20), activation="relu", random_state=1, momentum=2, early_stopping=True)

        classifier_params = c.get_params ()
        regressor_params = r.get_params ()

        self.assertEqual (classifier_params["hidden_layer_sizes"], (10,10), "wrong parameter returned by get_params()")
        self.assertEqual (classifier_params["activation"], "tanh", "wrong parameter returned by get_params()")
        self.assertEqual (classifier_params["alpha"], 1, "wrong parameter returned by get_params()")
        self.assertEqual (classifier_params["batch_size"], 200, "wrong parameter returned by get_params()")
        self.assertEqual (classifier_params["max_iter"], 300, "wrong parameter returned by get_params()")

        self.assertEqual (regressor_params["hidden_layer_sizes"], (20,20), "wrong parameter returned by get_params()")
        self.assertEqual (regressor_params["activation"], "relu", "wrong parameter returned by get_params()")
        self.assertEqual (regressor_params["random_state"], 1, "wrong parameter returned by get_params()")
        self.assertEqual (regressor_params["momentum"], 2, "wrong parameter returned by get_params()")
        self.assertEqual (regressor_params["early_stopping"], True, "wrong parameter returned by get_params()")
        

    # TEST convergence on classification case (Xnor)
    def test_classification(self):
        n = BaseNeuralNetwork (hidden_layer_sizes=(30,), learning_rate_init=0.1, output_activation="zero_one_tanh", loss="log_loss",
                               momentum=0, alpha=0)
        X = [ [0, 0],
              [0, 1],
              [1, 0],
              [1, 1]
        ]
        y = [ [ 1],
              [ 0],
              [ 0],
              [ 1]
        ]
        n.fit (X, y)
        predicted = n.predict (X)
        losses = loss_functions["log_loss"] (y, predicted)
        for x, p, loss in zip (X,predicted, losses):
            self.assertLess ( sum(loss), 0.1, "Wrong predicted Xnor for input: {}".format(x) )
        
    def test_regression_linear_case ( self ):
        # network that learns to compute sum of its inputs and double of the second input
        n = BaseNeuralNetwork (hidden_layer_sizes=(50,), learning_rate_init=0.01, momentum=0, alpha=0)
        X = [ 
                [-0.55609785, -0.44237751, -1.51930792,  0.31342967],
                [ 1.86589251, -0.64794613, -1.40532609,  0.19970042],
                [ 2.07525975,  1.14612304, -1.21620428, -0.2127494 ],
                [-0.9680726 ,  1.81546847, -0.71370392, -0.37450352]
            ]
        y = [
                [-2.20435361, -0.88475503 ],
                [ 0.0123207,  -1.29589226 ],
                [ 1.79242911,  2.29224607 ],
                [-0.24081157,  3.63093693 ]
            ]
        n.fit (X, y)
        predicted = n.predict (X)
        losses = loss_functions["squared"] (y, predicted)
        for x, p, loss in zip (X,predicted, losses):
            # print ("sum(loss)", sum(loss))
            self.assertLess ( sum(loss), 0.1, "wrong (sum,double) prediction for input {}".format(x) )

    def test_external_readable_properties ( self ):
        # network that learns to compute sum of its inputs and double of the second input
        n = BaseNeuralNetwork (hidden_layer_sizes=(50,), learning_rate_init=0.01, momentum=0, alpha=0)
        X = [ 
                [-0.55609785, -0.44237751, -1.51930792,  0.31342967],
                [ 1.86589251, -0.64794613, -1.40532609,  0.19970042],
                [ 2.07525975,  1.14612304, -1.21620428, -0.2127494 ],
                [-0.9680726 ,  1.81546847, -0.71370392, -0.37450352]
            ]
        y = [
                [-2.20435361, -0.88475503 ],
                [ 0.0123207,  -1.29589226 ],
                [ 1.79242911,  2.29224607 ],
                [-0.24081157,  3.63093693 ]
            ]
        n.fit (X, y)
        predicted = n.predict (X)
        losses = loss_functions["squared"] (y, predicted)
        
        self.assertLess (n.n_iter_, 2000, "Neural network should converge in less than 200 epochs")
        self.assertLess (n.loss_, 0.1, "average loss too high")
        self.assertEqual (n.n_layers_, 1, "Network has one layer")
        self.assertEqual (n.n_outputs_, 2, "Network has two outputs")
        

    def test_regression_nonlinear_case ( self ):
        # network that learns to compute a nonlinear function on its inputs
        n = BaseNeuralNetwork (hidden_layer_sizes=(50, 50,), learning_rate_init=0.01, momentum=0.6, alpha=0.00,)
        X = np.random.randn (100, 3)
        y = (X[:,0]**3 + 4 * X[:,1]**2 - X[:,1] + X[:,2]) + 0.02 * np.random.randn ()
        n.fit (X, y)
        predicted = n.predict (X)
        losses = loss_functions["squared"] (y[:, np.newaxis], predicted)
        self.assertLess ( np.average (losses), 0.5, "Loss to high" )

    def test_grid_search ( self ):

        '''
        n = DummyModel ()
        data, labels, testdata, testlabels = ReadData("cup/ML-CUP19-TR.csv", 0.75)
        '''

        data, labels, _, _ = readMonk("monks/monks-1.train")
        n = MLPClassifier ( hidden_layer_sizes=(20,), activation="relu", batch_size = 3, learning_rate_init=0.5, momentum=0.2, alpha=0.04 )
        n.enable_reporting(data, labels, "monks 1", 'classification')
    
        if (len(data) == 0):
            self.skipTest("training data not accessible")

        params=[
        {'alpha': [0.0001, 0.001, 0.01], 'learning_rate': ['constant'], 'learning_rate_init': [0.01, 0.05, 0.1], 'momentum': [0.3, 0.8]},
        {'alpha': [0.0001, 0.001, 0.01], 'learning_rate': ['adaptive'], 'learning_rate_init': [0.02, 0.1, 0.2], 'momentum': [0.3, 0.8]},
        ]

        ResList , minIdx = GridSearchCV(n, params, data, labels, ClassErrFun, 2)

        print ('--- Res: ----')
        print (ResList)
        print ('-------------')
        print ('Best: ')
        print (ResList[minIdx])

        writeGridSearchFiles(n.__class__.__name__, params, ResList, minIdx)
    
        self.assertEqual (len(n.fit_log), 60, "fit was not called 60 times")
        self.assertEqual (len(n.predict_log), 60, "predict was not called 60 times")

    
    def test_regressor ( self ):
        # network that learns to compute a nonlinear function on its inputs
        n = MLPRegressor (hidden_layer_sizes=(50, 50,), learning_rate_init=0.01, momentum=0.9, alpha=0.00,)
        X = np.random.randn (100, 2)
        y1 = X[:,0]**2 - X[:,0] + 2*X[:,1]  + 0.02*np.random.randn (100)
        y2 = X[:,1]**2 + X[:,0] + 3*X[:,1]  + 0.02*np.random.randn (100)
        y = np.stack((y1,y2), axis=-1)
        n.fit (X, y)
        predicted = n.predict (X)
        losses = loss_functions["squared"] (y, predicted)
        self.assertLess ( np.average (losses), 0.5, "Loss to high" )

    def test_classifier ( self ):
        n = MLPClassifier (hidden_layer_sizes=(30,), learning_rate_init=0.1, momentum=0, alpha=0)
        X = [ [0, 0],
              [0, 1],
              [1, 0],
              [1, 1]
        ]
        y = [ [ 0],
              [ 1],
              [ 1],
              [ 0]
        ]
        n.enable_reporting (X,y, "same", "classification")
        n.fit (X, y)
        predicted = n.predict (X)
        for x, t, p in zip (X, y, predicted):
            # print ("predicted XOR({}) = {} - logloss: {}".format(x, p, loss))
            self.assertEqual ( t, p, "Wrong predicted XOR for input: {}".format(x) )
    
    # @unittest.skip("takes too long")
    def test_minibatch (self):
        X = np.random.randn (100, 2)
        y1 = X[:,0]**2 - X[:,0] + 2*X[:,1]  + 0.02*np.random.randn (100)
        y2 = X[:,1]**2 + X[:,0] + 3*X[:,1]  + 0.02*np.random.randn (100)
        y = np.stack((y1,y2), axis=-1)
        
        for batch_size in ['auto', len(X), 50, 5, 1]:

            n = MLPRegressor (hidden_layer_sizes=(50, 50,), learning_rate_init=0.005, momentum=0.9, alpha=0.00, batch_size=batch_size)
            n.fit (X, y)
            predicted = n.predict (X)
            losses = loss_functions["squared"] (y, predicted)
            self.assertLess (np.average (np.sum(losses, axis=1)), 0.5, "Loss too high for minibatch size={}".format(batch_size))
            # print ("average loss (batch_size={}): {}".format(batch_size, np.average (np.sum(losses, axis=1)))) 

    def test_random_state (self):
        X = [ 
                [-0.55609785, -0.44237751, -1.51930792,  0.31342967],
                [ 1.86589251, -0.64794613, -1.40532609,  0.19970042],
                [ 2.07525975,  1.14612304, -1.21620428, -0.2127494 ],
                [-0.9680726 ,  1.81546847, -0.71370392, -0.37450352]
            ]
        y = [
                [-2.20435361, -0.88475503 ],
                [ 0.0123207,  -1.29589226 ],
                [ 1.79242911,  2.29224607 ],
                [-0.24081157,  3.63093693 ]
            ]
        n = BaseNeuralNetwork (hidden_layer_sizes=(50,), learning_rate_init=0.01, momentum=0, alpha=0, random_state=42)
        n.fit (X, y)
        first_predictions = n.predict (X)
        
        n = BaseNeuralNetwork (hidden_layer_sizes=(50,), learning_rate_init=0.01, momentum=0, alpha=0, random_state=42)
        n.fit (X, y)
        second_predictions = n.predict (X)
        
        for p1, p2 in zip (first_predictions, second_predictions):
            self.assertTrue (np.allclose(p1,p2), "network predictions are different with the same random state")
            # print ("p1, p2, allclose", p1, p2, np.allclose(p1,p2))

    def test_reporting (self):
        X = [ 
                [-0.55609785, -0.44237751, -1.51930792,  0.31342967],
                [ 1.86589251, -0.64794613, -1.40532609,  0.19970042],
                [ 2.07525975,  1.14612304, -1.21620428, -0.2127494 ],
                [-0.9680726 ,  1.81546847, -0.71370392, -0.37450352]
            ]
        y = [
                [-2.20435361, -0.88475503 ],
                [ 0.0123207,  -1.29589226 ],
                [ 1.79242911,  2.29224607 ],
                [-0.24081157,  3.63093693 ]
            ]
        X_reporting = [
            [ 1.19206586,  0.04911357,  0.22842882, -0.31796648],
            [-0.7267358 , -1.50846338, -0.7300164 , -1.04309072]
        ]
        y_reporting = [ 
            [ 1.15164177,   .09822714 ],
            [-4.00830630, -3.01692676 ]
        ]
        n = MLPRegressor (hidden_layer_sizes=(50,), learning_rate_init=0.01, momentum=0, alpha=0, random_state=42)
        n.enable_reporting (X_reporting, y_reporting, "sum_and_double", "euclidean", fname="test_reporting.tsv")
        n.fit (X, y)
        self.assertTrue ( os.path.isfile ("reports/test_reporting.tsv"), "report not created")
        
        

#unit tests
if __name__ == "__main__":

    unittest.main ()
        

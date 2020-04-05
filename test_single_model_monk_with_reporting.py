
import sys
from neural_network import *
from functions import _classification_loss
from utility import readMonk
from utility import GridSearchCV
from utility import getRandomParams

def main():

    Xtrain, ytrain, _, _ = readMonk("monks/monks-3.train")
    Xtest, ytest, _, _ = readMonk("monks/monks-3.test")
    
    if len(Xtrain) == 0 or len(Xtest) == 0:
        print ("Error reading data")
        exit()

    # con monk 2 mettere weight_init_value=0.25 (comunque è il default per la classificazione)
    nn = MLPClassifier( max_iter=500, n_iter_no_change=10)

    # funzionanti da Paolo (curva stabile, alpha>0 e n_iter_no_change alto)
    # params={"hidden_layer_sizes": [6], "alpha": 0.003, "activation": "tanh", "learning_rate": "constant", "learning_rate_init": 0.82,  "momentum": 0.6, "n_iter_no_change": 80}
    #params={"hidden_layer_sizes": [6], "alpha": 0.003, "activation": "tanh", "learning_rate": "constant", "learning_rate_init": 0.82,  "momentum": 0.6, "n_iter_no_change": 80}

    '''    
    # monks1
    params={"hidden_layer_sizes": [15], "alpha": 0., "activation": "relu", "learning_rate": "constant", "learning_rate_init": 0.8,  "momentum": 0.8, "n_iter_no_change": 20, "weights_init_value":0.1 }

    # monks2
    params={"hidden_layer_sizes": [15], "alpha": 0., "activation": "relu", "learning_rate": "constant", "learning_rate_init": 0.8,  "momentum": 0.8, "n_iter_no_change": 20, "weights_init_value":0.25 }
    '''
     # monks3
    params={"hidden_layer_sizes": [15], "alpha": 0., "activation": "relu", "learning_rate": "constant", "learning_rate_init": 0.8,  "momentum": 0.8, "n_iter_no_change": 8, "weights_init_value":0.1}
  
    nn.set_params (**params)
    
    # print ("Xtrain.shape", Xtrain.shape)
    # print ("ytrain.shape", ytrain.shape)
    # print ("Xtest.shape", Xtest.shape)
    # print ("ytest.shape", ytest.shape)

    nn.enable_reporting ( Xtest, ytest, "monk-test", "classification" )
    nn.fit (Xtrain, ytrain)

    predicted = nn.predict (Xtest)
    loss = _classification_loss (ytest, predicted)

    print ("avg classification loss on validation:", loss)

main()

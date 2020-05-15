import numpy as np
import csv
import os
import itertools
from itertools import product
from pathlib import Path
import random
from matplotlib import pyplot as plt
from functions import *
import pickle
import pprint
from datetime import datetime
import heapq
import json
import tqdm

#_DISABLE_TQDM = True
_DISABLE_TQDM = False
   
def readMonk(filename, devfraction = 1, shuffle = False):
    '''
    used to read monk datasets performing one-hot encoding
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    data = []
    labels = []
    try:
        with open(Path(dir_path + '/' + filename)) as infile:
            reader = csv.reader(infile, delimiter=" ")
            '''
            1. class: 0, 1 
            2. a1:    1, 2, 3
            3. a2:    1, 2, 3
            4. a3:    1, 2
            5. a4:    1, 2, 3
            6. a5:    1, 2, 3, 4
            7. a6:    1, 2
            8. Id:    (A unique symbol for each instance)
            '''
            for row in reader:
                label = int(row[1])

                rowdata = np.zeros(17)
                rowdata[int(row[2]) - 1] = 1
                rowdata[int(row[3]) + 2] = 1
                rowdata[int(row[4]) + 5] = 1
                rowdata[int(row[5]) + 7] = 1
                rowdata[int(row[6]) + 10] = 1
                rowdata[int(row[7]) + 14] = 1

                data.append(rowdata)
                labels.append(label)

            data = np.array (data)
            labels = np.array (labels)

            if (shuffle):
                indexes = list (range(len(data)))
                random.shuffle(indexes)
                data = data [ indexes ]
                labels = labels [ indexes ]

            if  0 < devfraction < 1:
                n = int(devfraction*len(data))
                return data[:n], labels[:n], data[n:], labels[n:]

            return data, labels, [], []

    except IOError:
        print('File ' + str(Path(dir_path)) + '/' + filename + ' not accessible')
        return [], [], [], []

def ReadData(filename, devfraction):
    '''
    used to read cup dataset
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    try:
        with open(Path(dir_path + '/' + filename)) as infile:
            reader = csv.reader(infile, delimiter=",")
            labels = []
            data = []
            for row in reader:
                if row[0][0] != '#':
                    # Id, 20 data, 2 label
                    labels.append([float(row[21]), float(row[22])])
                    data.append([float(x) for x in row[1:21]])

        n = int(devfraction*len(data))

        return data[:n], labels[:n], data[n:], labels[n:]

    except IOError:
        print('File ' + str(Path(dir_path)) + '/' + filename + ' not accessible')
        return [], [], [], []

def ReadBlindData(filename):
    '''
    used to read blind data of the cup
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    try:
        with open(Path(dir_path + '/' + filename)) as infile:
            reader = csv.reader(infile, delimiter=",")
            ids = []
            data = []
            for row in reader:
                if row[0][0] != '#':
                    # Id, 20 data
                    ids.append(int(row[0]))
                    data.append([float(x) for x in row[1:21]])
        
        return ids, data

    except IOError:
        print('File ' + str(Path(dir_path)) + '/' + filename + ' not accessible')
        return [], [], [], []

def cross_val(model, data, labels, loss_function, folds=5):
    '''
    performs a cross validation on the model with the data, labels and loss function provided as input
    returns average loss on validation, average loss on training, standard deviation, number of folds in which the validation actually succeeded
    '''
    X_tr_folds = np.array_split(data, folds)
    y_tr_folds = np.array_split(labels, folds)
    losses = []
    losses_train = []

    for i in tqdm.tqdm(range(folds), desc="k-fold crossval", disable=_DISABLE_TQDM):
        tr_data, test_data = np.concatenate(X_tr_folds[:i] + X_tr_folds[i+1:]), X_tr_folds[i]
        tr_labels, testlabels = np.concatenate(y_tr_folds[:i] + y_tr_folds[i+1:]), y_tr_folds[i]
        
        model.fit(tr_data, tr_labels)
        result = model.predict(test_data)
        loss = loss_function (testlabels, result)

        result_train = model.predict(tr_data)
        loss_train = loss_function (tr_labels, result_train)

        if loss is np.nan:
            raise ValueError ("loss is nan")

        losses.append ( loss )
        losses_train.append(loss_train)

    if len(losses) != 0:
        return np.mean (losses), np.mean (loss_train), np.std(losses), len(losses)
    else:
        return 0, 0, 0, 0

##########################
# GRID SEARCH FUNCTIONS  #
##########################
def GridSearchCV(model, params, data, labels, loss, folds=5, uniquefile=False, write_best=True):
    '''
    performs a grid search on the parameters provided as input through cross validation 
    '''
    os.makedirs ("grid_reports", exist_ok=True)

    # print ("[DEBUG] testing parameters {}".format(params))

    timestamp = datetime.today().isoformat().replace(':','_')
    openmode = ''
    if (uniquefile):
        filename = "grid_reports/" + model.__class__.__name__
        openmode = 'a'
    else:
        filename = "grid_reports/" + model.__class__.__name__ + "_" + timestamp
        openmode = 'w'

    with open(filename + ".gsv", openmode, buffering=1) as outt:
        attribm = (dir(model))
        grid = GetParGrid(params, attribm)
        resList = []
        for p in tqdm.tqdm(grid, desc="grid search", disable=True):
            for k in p.keys():
                if k in attribm:
                    setattr(model, k, p[k])
            
            try:
                # res = (avg, std, n_successful_folds)
                res=cross_val(model,data,labels,loss,folds)
                resList.append([p, res])
                json.dump(p, outt)
                print (file=outt)
                json.dump(res, outt)
                print (file=outt)
            except Exception as e:
                # print ("ignoring parameters {} because: {}".format(p, e))
                pass

        idx_min = -1
        if len(resList) > 0:
            # print ("[DEBUG] list:", resList, len(resList))
            idx_min = np.argmin([it[1][0] for it in resList])
            # print ("[DEBUG] best idx:", idx_min)
            
        if idx_min>=0 and write_best:
            print("*** Best ***", file=outt)
            json.dump(resList[idx_min][0], outt)
            print (file=outt)
            json.dump(resList[idx_min][1], outt)
            print (file=outt)            

        return resList, idx_min
           
def getRandomParams(params):
    '''
    get random parameters on a set of hyper-parameters provided as list of lists of dictionaries
    '''
    params = [params]
    randparams = []
    for line in params:
        for p in line:
            items = sorted(p.items())
            if items == []:
                return
            else:
                pa = {}
                keys, values = zip(*items)
                for k, vl in zip(keys, values):
                    isnumber = all(type(v) in (int, float) for v in vl)
                    if (isnumber):
                        pa[k] = [np.random.uniform(min(vl),max(vl))]
                    else:
                        pa[k] = [random.choice(vl)]                    
                randparams.append(pa)
    return randparams
  
def GetParGrid(params, attribm):
    '''
    transform parameters from a list of lists of dictionaries to a list of dictionaries
    '''
    res = []
    params = [params]
    for line in params:
        for p in line:

            for key in [key for key in p if not key in attribm]:
                print ("warning: skipped param " + key + " (not found)")
                del p[key] 
        
            items = sorted(p.items())
            if items == []:
                return
            else:
                keys, values = zip(*items)
                for v in product(*values):
                    par = dict(zip(keys, v))
                    res.append(par)
    return res

def readGridSearchFile(filename):
    '''
    read a grid search output file
    '''
    out = []
    params = {}
    perf_tuple = (0,0,0)
    with open(Path(filename)) as infile:
        for lineno, line in enumerate(infile):
            if line.startswith("*"):
                return out
            elif lineno % 2 == 0:
                params = json.loads(line)
            else:
                perf_tuple = json.loads(line)
                out.append ((params, perf_tuple))
    
    return out

def getBestRes(fileprefix, directory, k=1):
    '''
        retrieves the best `k` results from all the gridSearch report files in `directory` whose name starts with `fileprefix`
    '''
    best_so_far = []
    for f in os.listdir(directory):
        if f.startswith(fileprefix) and f.endswith(".gsv"):
            results = readGridSearchFile( directory + "/" + f) 
            best_so_far = heapq.nsmallest (k, results+best_so_far, key=lambda x: x[1])

    return best_so_far

##########################
#     PLOT FUNCTIONS     #
##########################
def CreateLossPlot(filename, training_legend="Train", validation_legend="Validation"):
    '''
    create a plot showing train and validation loss curves from a NN report file provided as input
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    train_loss = []
    valid_loss = []
    
    try:
        with open(Path(filename)) as infile:
            for line in infile:
                if line.startswith('# parameters:'):
                    param_line = line
                else:
                    ln = line.split('\t')
                    if (ln[0].isdigit()):
                        train_loss.append(float(ln[1]))
                        valid_loss.append(float(ln[2]))
        
        epoch_count = range(1, len(train_loss) + 1)
        plt.plot(epoch_count, train_loss, 'b.-')
        
        plt.plot(epoch_count, valid_loss, 'r--')
        plt.legend([training_legend, validation_legend], fontsize= 'x-large')
        
        plt.ylim(bottom=-0.02,top=0.72)
        plt.xlabel('Epoch', fontsize= 'x-large')
        plt.ylabel('Loss', fontsize= 'x-large')
        plt.xticks(fontsize= 'x-large')
        plt.yticks(fontsize= 'x-large')
        plt.savefig(filename + '_loss.png', bbox_inches='tight')
        # DEBUG
        plt.clf()

    except IOError:
        print('File ' + str(Path(dir_path)) + '/' + filename + ' not accessible')
        return True, [], [], [], []

def CreateAccuracyPlot(filename, training_legend="Train", validation_legend="Test"):
    '''
    create a plot showing train and validation accuracy curves from a NN report file provided as input
    '''
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    train_acc = []
    valid_acc = []
    
    try:
        with open(Path(filename)) as infile:
            for line in infile:
                if not line.startswith('# parameters:'):               
                    ln = line.split('\t')
                    if (ln[0].isdigit()):
                        valid_acc.append(1 - float(ln[3]))
                        train_acc.append(1 - float(ln[4]))
        
        epoch_count = range(1, len(train_acc) + 1)
        plt.plot(epoch_count, train_acc, 'g.-')
        
        plt.plot(epoch_count, valid_acc, 'k--')
        plt.legend([training_legend, validation_legend], fontsize= 'x-large')
        
        plt.ylim(bottom=0.47, top=1.02)
        plt.xlabel('Epoch', fontsize= 'x-large')
        plt.ylabel('Accuracy', fontsize= 'x-large')
        plt.xticks(fontsize= 'x-large')
        plt.yticks(fontsize= 'x-large')
        plt.savefig(filename + '_acc.png', bbox_inches='tight')
        
        # DEBUG
        plt.clf()

    except IOError:
        print('File ' + str(Path(dir_path)) + '/' + filename + ' not accessible')
        return True, [], [], [], []

def save_table(filename, data, col_labels):
    _ , axs =plt.subplots()
    axs.axis('off')
    axs.axis('tight')
    table = axs.table(cellText=data,colLabels= col_labels, cellLoc = 'center', loc='center')
    cellDict = table.get_celld()
    for i in range(0,len(col_labels)):
        cellDict[(0,i)].set_height(.1)
    
    table.auto_set_font_size(False)
    table.auto_set_column_width(col=list(range(len(col_labels))))
    #table.set_fontsize(10)
    
    plt.savefig(filename)
    plt.clf()

def save_grid_table(filename):
    results = readGridSearchFile(filename)
    data = np.empty((len(results), 8), dtype='<U21')
    collabel=("$\\bf{batch}$\n$\\bf{size}$", "$\\bf{activation}$", "$\\bf{learning}$", "$\\bf{eta}$", "$\\bf{lambda}$", "$\\bf{alpha}$",  "$\\bf{MEE(TR)}$", "$\\bf{MEE(VL)}$")
    for i, (params, perf) in enumerate(results):
        data[i] = np.array([ params['batch_size'], params['activation'], params['learning_rate'], round(params['learning_rate_init'], 4), round(params['alpha'], 4), round(params['momentum'], 4), round(perf[1], 4), round(perf[0], 4)])

    save_table("grid.png", data, collabel)

    

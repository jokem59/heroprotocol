#!usr/bin/python

import pandas as pd
import numpy as np
import time
from sklearn import linear_model
from sklearn.metrics import accuracy_score

start_time = time.time()

data = np.genfromtxt('mmrData.csv', delimiter=',')

print "Time to load dataset"
print("--- %s seconds ---\n" % (time.time() - start_time))

print "Length of dataset:", len(data), "\n"
train_set = int(0.8 * len(data))
test_set = len(data) - train_set

# split train/test - 80/20
features_train = data[:train_set, 6:]
features_test = data[train_set:len(data), 6:]

labels_train = data[:train_set, 1]
labels_test = data[train_set:len(data), 1]

print 'features_train example:', features_train[0]
print 'features_train length:', len(features_train), "features_train ndim:", features_train.ndim
print 'features_test length:', len(features_test), "features_test ndim:", features_test.ndim
print 'labels_train length:', len(labels_train), "labels_train ndim:", labels_train.ndim
print 'labels_test length:', len(labels_test), "labels_test ndim:", labels_test.ndim, '\n'


# X array (features) - 2D Array 8 x (Num Obs)
# [Std Team MMR, Mean Team MMR, Max Team MMR, Min Team MMR, Diff Std MMR, Diff Mean MMR, Diff Max MMR, Diff Min MMR]
# y array (labels) - 1D array len(X Array)
# [obs1, obs2, ... , obsn]

clf = linear_model.SGDClassifier(loss='squared_hinge')
clf.fit(features_train, labels_train)

pred = clf.predict(features_test)

acc = accuracy_score(pred, labels_test)
print "Accuracy: ", acc, '\n'

print "Time until completion"
print("--- %s seconds ---" % (time.time() - start_time))

# logs current current algorithm parameters, accuracy, time to load dataset, time to complete
log = str(clf.get_params()) + ' ' + str(acc)
filename = 'sgdClassifier' + str(len(features_train) + len(features_test)) + '.txt'
with open(filename, 'a') as f:
    f.write(log)

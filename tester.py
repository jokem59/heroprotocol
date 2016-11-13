#!/usr/bin/python

import formatter as fmt
import os
import pandas as pd

directories = [x[0] for x in os.walk('../testData/')]
del directories[0]
directories

for path in directories:
    path += '/'
    print "Checking", path, "for consistency..."
    dictInitData, replayId = fmt.generateInitialData(path)
    dfSummary = fmt.generateSummary(path, dictInitData, replayId)
    dfTruth = pd.read_csv(path + 'truth.csv', index_col = 0)
    a = len(dfSummary.columns)
    b = len(dfTruth.columns)
    if a != b:
        print path, 'Does NOT have equal columns - examine data.'
    else:
        print path, "passed test!\n"
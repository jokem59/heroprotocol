# TODO: modify parameter inputs in main to follow naming convention of multiple files

import json
import ast
import hashlib
import pandas as pd


def createJsonTrackerGameEvents(parserOutput, jsonFileName, replayId):
    '''
    :param parserOutput: raw hero protocol outputs --trackerevents, --gameevents
    :param jsonFileName: name of output JSON file
    :param replayId: unique replayId generated from getReplayId()
    :return: JSON formatted file of inputs
    '''
    with open(parserOutput, 'r') as f:
        lines = f.readlines()

    temp_string = ''
    for i in range(len(lines)):
        line = lines[i]
        if i == 0:
            temp_string += "{'" + parserOutput + "': [" + line.rstrip()
            continue
        try:
            if lines[i + 1][0] == '{':
                line = line.rstrip()
                temp_string += line + ','
                continue
        except:
            pass
        temp_string += line.rstrip()

    temp_string += "]}"
    dictEvents = ast.literal_eval(temp_string)
    dictEvents['replayId'] = replayId

    with open(jsonFileName, 'w') as f:
        json.dump(dictEvents, f)

def createJsonInitData(dictInitData, jsonFileName, replayId):
    '''
    :param dictInitData: <dictionary> of raw heroprotocol --initdata, generated from createDictInitData()
    :param jsonFileName: name of output JSON file
    :param replayId: unique replayId generated from getReplayId()
    :return: JSON formatted file of input
    '''
    # Removes cahche handles; no value in data analysis and certain characters cause UTF-8 encoding
    # error when converting to JSON
    dictInitData['m_syncLobbyState']['m_gameDescription']['m_cacheHandles'] = []
    dictInitData['m_syncLobbyState']['replayId'] = replayId

    with open(jsonFileName, 'w') as f:
        json.dump(dictInitData, f)

def createDictInitData(initData):
    '''
    :param initData: raw data output of heroprotocol --initdata
    :return: python <dictionary> of --initdata for replayId information and JSON conversion
    '''
    with open(initData, 'r') as f:
        lines = f.readlines()
    with open(initData, 'w') as f:
        dict_start = False
        for line in lines:
            if line[0] == '{' or dict_start:
                dict_start = True
                f.write(line)
            continue
    with open(initData, 'r') as f:
        dictInitData = ast.literal_eval(f.read())

    return dictInitData


def createJsonAEDH(output, jsonFileName, replayId):
    '''
    :param output: raw data output of heroptocol --header, --details, --attributeevents
    :param jsonFileName: name of output JSON file
    :param replayId: unique replayId generated from getReplayId()
    :return:
    '''
    with open(output, 'r') as f:
        dictOutput = ast.literal_eval(f.read())
    try:
        if dictOutput['m_cacheHandles']:
            dictOutput['m_cacheHandles'] = []
    except:
        pass

    dictOutput['replayId'] = replayId

    with open(jsonFileName, 'w') as f:
        json.dump(dictOutput, f)

def getReplayId(dictInitData):
    '''
    :param dictInitData: <dictionary> object from output of createDictInitData()
    :return: unique replayId
    '''
    randomValue = dictInitData['m_syncLobbyState']['m_gameDescription']['m_randomValue']
    playerNames = ''
    for i in dictInitData['m_syncLobbyState']['m_userInitialData']:
        playerNames += i['m_name']

    replayId = hashlib.md5(str(randomValue) + playerNames).hexdigest()

    return replayId

# temp
def createDfAEDH(output, replayId):
    '''
    :param output: raw data output of heroptocol --header, --details, --attributeevents
    :param jsonFileName: name of output JSON file
    :param replayId: unique replayId generated from getReplayId()
    :return:
    '''
    with open(output, 'r') as f:
        dictOutput = ast.literal_eval(f.read())
    try:
        if dictOutput['m_cacheHandles']:
            dictOutput['m_cacheHandles'] = []
    except:
        pass

    dictOutput['replayId'] = replayId

    df = pd.DataFrame(dictOutput)

    return df

if __name__ == '__main__':

    dictInitData = createDictInitData('init_data')
    replayId = getReplayId(dictInitData)

    df = createDfAEDH('header.txt', replayId)
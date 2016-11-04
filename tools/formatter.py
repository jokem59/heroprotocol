import ast
import hashlib
import collections
import pandas as pd
import numpy as np
import re


def createDictTGE(parserOutput):
    '''
    :param parserOutput: raw heroprotocol outputs --trackerevents, --gameevents
    :return: <dictionary> of raw heroprotocol outputs
    '''
    with open(parserOutput, 'r') as f:
        lines = f.readlines()

    temp_string = ''
    for i in range(len(lines)):
        line = lines[i]
        if i == 0:
            temp_string += "[" + line.rstrip()
            continue
        try:
            if lines[i + 1][0] == '{':
                line = line.rstrip()
                temp_string += line + ','
                continue
        except:
            pass
        temp_string += line.rstrip()

    temp_string += "]"
    dictEvents = ast.literal_eval(temp_string)
    for i in dictEvents:
        i['replayId'] = replayId

    return dictEvents


def prepDictTE(dictTE):
    '''
    Preps data and returns 4 <dict>s read for dataframe conversion, reference schema diagram
    dictTE, m_intData, m_stringData, m_fixedData
    Each dict/table record all tracker events and populate fields with np.nan if no values for that _gameloop
    were present
    '''
    # initialize keys of parent table
    parentKeys = []
    parentTE = {}
    for d in dictTE:
        for k in d.keys():
            if k not in parentKeys:
                parentKeys.append(k)
    for k in parentKeys:
        parentTE[k] = []

    # populate parent table
    listLength = 0
    for d in dictTE:
        listLength += 1
        for i in d:
            parentTE[i].append(d[i])
        for e in parentTE:
            if len(parentTE[e]) < listLength:
                parentTE[e].append(np.nan)

    # clean parentTE
    cleanParentTE = ['m_instanceList', 'm_items', 'm_count', 'm_killerUnitTagIndex', 'm_killerUnitTagRecycle',
                     'm_slotId', 'm_upgradeTypeName', 'm_upkeepPlayerId', 'm_type']
    for i in cleanParentTE:
        parentTE.pop(i, None)

    # clean the values of parentTE['m_intData', 'm_stringData', 'm_fixedData']
    # keep same order as listOfDicts and subKeys below
    parentClean = ['m_intData', 'm_stringData', 'm_fixedData']
    for i in parentClean:
        cleanTESubDict(parentTE[i])

    # initialize m_intData, m_stringData, m_fixedData keys
    intDataKeys = initializeTESubKeys(parentTE['m_intData'])
    stringDataKeys = initializeTESubKeys(parentTE['m_stringData'])
    fixedDataKeys = initializeTESubKeys(parentTE['m_fixedData'])

    # initialize sub tables
    m_intData, m_stringData, m_fixedData = {}, {}, {}
    listOfDicts = [m_intData, m_stringData, m_fixedData]
    # order of subkeys should match listOfDicts <dict> above
    subKeys = [intDataKeys, stringDataKeys, fixedDataKeys]

    # initialize keys in <dict> m_int, m_string, m_fixedData
    for i in range(len(listOfDicts)):
        for key in subKeys[i]:
            listOfDicts[i][key] = []
        listOfDicts[i]['replayId'] = []
        listOfDicts[i]['_gameloop'] = []
        listOfDicts[i]['_bits'] = []
        listOfDicts[i]['_eventid'] = []

    # populate values for m_intData, m_stringData, m_fixedData
    for i in range(len(listOfDicts)):
        populateTESubDicts(parentTE, listOfDicts[i], parentClean[i])

    # remove 'GameTime', 'PreviousGameTime', 'Time' from m_fixedData
    fixedDataClean = ['GameTime', 'PreviousGameTime', 'Time']
    for i in fixedDataClean:
        m_fixedData.pop(i, None)

    # edit m_stringData "Hero" key to remove 'Hero' prefix from values
    temp = []
    for i in m_stringData['Hero']:
        if isinstance(i, str):
            temp.append(i.replace('Hero', ''))
        else:
            temp.append(i)
    m_stringData['Hero'] = temp

    # standardize PlayerID to m_userId reporting in m_intData, before{range(1,11)}, after{range(0,10)}
    m_intData['m_userId'] = m_intData.pop('PlayerID')
    m_intData['m_userId'][:] = [x - 1 for x in m_intData['m_userId']]

    # remove m_playerId, m_intData, m_stringData, m_fixedData from parentTE
    parentTE.pop('m_playerId', None)
    parentTE.pop('m_intData', None)
    parentTE.pop('m_stringData', None)
    parentTE.pop('m_fixedData', None)

    return parentTE, m_intData, m_stringData, m_fixedData


def cleanTESubDict(subDict):
    '''
    helper function to clean parentTE['m_intData', 'm_stringData', 'm_fixedData']
    '''
    for i in subDict:
        if isinstance(i, list):
            # i is a list of dictionaries associated with a tracker event
            temp = []
            for d in i:
                # record value of 'm_key' and 'm_value'
                key = d['m_key']
                value = d['m_value']
                # add to new temp list as a dict
                temp.append({key: value})
            # after iterating through all d in current list, clear list
            i[:] = []
            # set current list equal to temp list
            for d in temp:
                i.append(d)


def populateTESubDicts(parentTE, subDict, dictName):
    '''
    Helper function to prepDictTE
    Param: subDict <dict>, dictionary to populate
    Param: dictName <string>, string corresponding to <dict> name
    '''
    for i in range(len(parentTE[dictName])):
        # entry is a list of <dict>s
        # e.g. entry = [{'PlayerID': 8}, {'KillingPlayer': 1}, {'KillingPlayer': 2}]
        entry = parentTE[dictName][i]
        if isinstance(entry, list):
            isDuplicates, duplicateKeys = isDuplicateKeys(entry)
            if not isDuplicates:
                # populate all pertinent keys with one element
                populateFromEntry(parentTE, subDict, entry, i)
            # case where there are multiple instances of 'KillerPlayer' associated with one 'PlayerID'
            else:
                dupeIndex = range(1, len(entry))
                for num in dupeIndex:
                    newEntry = []
                    newEntry.append(entry[0])
                    newEntry.append(entry[num])  # this value needs to be range(1, len(entry))
                    populateFromEntry(parentTE, subDict, newEntry, i)


def initializeTESubKeys(subDict):
    '''
    helper function, takes sub-dict from TG and creates a comprehensive list of keys
    '''
    listOfKeys = []
    for i in subDict:
        if isinstance(i, list):
            for d in i:
                for k in d.keys():
                    if k not in listOfKeys:
                        listOfKeys.append(k)

    return listOfKeys


def isDuplicateKeys(entry):
    # @param: <list> of <dict>s
    # @return: isDuplicates - True if there are multiple copies of same key:
    # e.g. entry = [{'PlayerID': 8}, {'KillingPlayer': 1}, {'KillingPlayer': 2}]
    # @return: duplicateKeys - <list> of duplicate keys, one per duplicate key
    # checks to see if duplicate keys exists; e.g. multiple copies of 'KillingPlayer' associated with one 'PlayerID'
    # if this is not addressed, the len(m_intData['KillingPlayer']) doesn't match the lengths of the other keys and
    # a DataFrame cannot be constructed.
    keys = []
    for d in entry:
        for k in d:
            keys.append(k)

    duplicateKeys = []
    isDuplicates = False
    for key in keys:
        total = keys.count(key)
        if total > 1:
            duplicateKeys.append(key)
            isDuplicates = True

    return isDuplicates, duplicateKeys


def populateFromEntry(parentTE, subDict, entry, i):
    subDict['replayId'].append(parentTE['replayId'][i])
    subDict['_gameloop'].append(parentTE['_gameloop'][i])
    subDict['_bits'].append(parentTE['_bits'][i])
    subDict['_eventid'].append(parentTE['_eventid'][i])
    for d in entry:
        for k in d:
            subDict[k].append(d[k])
    # then popluate non present keys with np.nan
    for k in subDict:
        if len(subDict[k]) != len(subDict['replayId']):
            subDict[k].append(np.nan)


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

    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_cacheHandles', None)
    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_mapFileName', None)
    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_slotDescriptions', None)

    return dictInitData


def createDictAEDH(output):
    '''
    :param output: raw data output of heroptocol --header, --details, --attributeevents
    :return: <dictionary> of data outputs
    '''
    with open(output, 'r') as f:
        dictOutput = ast.literal_eval(f.read())
    try:
        if dictOutput['m_cacheHandles']:
            dictOutput['m_cacheHandles'] = ['']

    except:
        pass

    dictOutput['replayId'] = replayId

    return dictOutput


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


def renameKeys(data):
    for i in data:
        match = re.search('^m_', i)
        if match:
            new_key = i[2:len(i)]
            dictDetails[new_key] = dictDetails.pop(i)
        match = re.search('^_', i)
        if match:
            new_key = i[2:len(i)]
            dictDetails[new_key] = dictDetails.pop(i)


def prepForDf(dictionary):
    '''
    Preps <dictionary> for to proper pandas DataFrame format with values as lists.  Does NOT break out
    embedded dictionaries.  Use function flattenDict() for that.

    ONLY WORKS ON OUTPUTS THAT GENERATE ONE <dictionary>
    NEED TO TEST and DEVELOP ON OUTPUTS THAT PROVIDE <list> of <dictionary>s
    '''
    for i in dictionary:
        # USE CASE 1: convert one <int> or <str> into a list for pandas DataFrame processing
        # (no <floats> in outputs)
        # print type(i), i, type(dictionary[i]), dictionary[i]
        if isinstance(dictionary[i], bool) or isinstance(dictionary[i], int) or isinstance(dictionary[i], str):
            dictionary[i] = [dictionary[i]]
            continue
        # USE CASE 2: convert one <list> with one <dictionary> w/ multiple elements to proper DataFrame format
        if isinstance(dictionary[i], list) and len(dictionary[i]) == 1 and isinstance(dictionary[i][0], dict):
            dictionary[i] = dictionary[i][0]
            continue
        # USE CASE 3: convert one <list> with multiple <dictionary>s to proper DataFrame format
        if isinstance(dictionary[i], list) and len(dictionary[i]) > 1 and isinstance(dictionary[i][0], dict):
            for d in dictionary[i]:
                prepForDf(d)
            continue
        # USE CASE 4: convert one <list> with multiple entries to a list with one tuple entry
        # Ignores lists with dictionaries in them to prevent wrapping a dictionary with a tuple layer
        if isinstance(dictionary[i], list) and len(dictionary[i]) > 0 and not isinstance(dictionary[i][0], dict):
            dictionary[i] = [tuple(dictionary[i])]
            continue
        # USE CASE 5: convert empty <dictionary> to a <list> with an empty <dictionary> inside
        if isinstance(dictionary[i], dict) and len(dictionary[i]) == 0:
            dictionary[i] = [{}]
            continue
        # USE CASE 6: convert <dictionary> with length = 1 to use parent key
        if isinstance(dictionary[i], dict) and len(dictionary[i]) == 1:
            dictionary[i] = dictionary[i].values()
            continue
        # USE CASE 7: convert <dictionary> with length > 1 as a separate dictionary w/ replayId
        if isinstance(dictionary[i], dict) and len(dictionary[i]) > 1:
            prepForDf(dictionary[i])
        # USE CASE 8: populate empty field with np.nan
        if len(dictionary[i]) == 0 or dictionary[i] is None:
            dictionary[i] = np.nan

    return dictionary


def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = str(parent_key) + sep + str(k) if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def prepDictInitData(dictInitData):
    '''
    Splits <dict> of InitData into the following tables: m_gameDescription, m_userInitialData, m_slots
    Reference the schema diagram for key breakout
    Return: Three dictionaries ready for conversion to DataFrames
    '''
    m_gameDescription, m_userInitialData, m_lobbyState = {}, {}, {}
    listOfDicts = [m_gameDescription, m_userInitialData, m_lobbyState]
    # contents of dictInitData['m_syncLobbyState']['m_userInitialData'] is a <list> of <dict>s
    listOfKeys = ['m_gameDescription', 'm_userInitialData', 'm_lobbyState']

    parent_key = 'm_syncLobbyState'
    for i in range(len(listOfDicts)):
        sub_key = listOfKeys[i]
        cur_dict = listOfDicts[i]
        if sub_key != 'm_userInitialData':
            cur_dict['replayId'] = replayId
            for key in dictInitData[parent_key][sub_key]:
                cur_dict[key] = dictInitData[parent_key][sub_key][key]
        else:
            # initialize keys in m_userInitialData
            for k in dictInitData[parent_key][sub_key][0]:
                cur_dict[k] = []
            cur_dict['m_userId'] = []
            cur_dict['replayId'] = []
            slotId = 0
            # Populate dictionary with a list, each <list> entry is one <dict> entry
            for d in dictInitData[parent_key][sub_key]:
                for entry in d:
                    cur_dict[entry].append(d[entry])
                cur_dict['m_userId'].append(slotId)
                cur_dict['replayId'].append(replayId)
                slotId += 1

    m_lobbyState = flatten(m_lobbyState)

    # remove parent keys from m_lobbyState and return m_slots as flat <dict> with <list> of each entry
    m_slots = {}
    # each <dict> has same elements
    # initialize keys in m_slots
    for k in m_lobbyState['m_slots'][0]:
        m_slots[k] = []
    m_slots['replayId'] = []
    # populate <dict>
    for d in m_lobbyState['m_slots']:
        for entry in d:
            if entry == 'm_colorPref':
                m_slots[entry].append(d[entry]['m_color'])
            else:
                m_slots[entry].append(d[entry])
        m_slots['replayId'].append(replayId)

    # clean m_slots
    m_slots['m_userId'] = m_slots.pop('m_workingSetSlotId', None)
    clean_m_slots = ['m_aiBuild', 'm_artifacts', 'm_licenses', 'm_logoIndex', 'm_racePref', 'm_rewards',
                     'm_tandemLeaderUserId', 'm_control', 'm_difficulty']
    for k in clean_m_slots:
        m_slots.pop(k, None)

    # clean m_userInitialData
    clean_m_initData = ['m_customInterface', 'm_examine', 'm_hero', 'm_mount', 'm_randomSeed',
                        'm_skin', 'm_teamPreference', 'm_racePreference', 'm_testAuto', 'm_testMap',
                        'm_testType', 'm_toonHandle', 'm_clanLogo', 'm_combinedRaceLevels']
    for k in clean_m_initData:
        m_userInitialData.pop(k, None)

    m_gameDescription = flatten(m_gameDescription)
    m_gameDescription = prepForDf(m_gameDescription)

    # clean m_gameDescription
    clean_m_gameDescription = ['m_defaultDifficulty', 'm_gameCacheName', 'm_gameOptions_m_advancedSharedControl',
                               'm_gameOptions_m_amm', 'm_gameOptions_m_ammId', 'm_gameOptions_clientDebugFlags',
                               'm_gameOptions_m_randomRaces', 'm_gameOptions_m_teamsTogether',
                               'm_gameOptions_m_userDifficulty', 'm_mapAuthorName', 'm_mapFileSyncChecksum',
                               'm_maxRaces', 'm_modFileSyncChecksum', 'm_gameOptions_m_clientDebugFlags',
                               'm_hasExtensionMod', 'm_maxColors', 'm_maxControls']
    for k in clean_m_gameDescription:
        m_gameDescription.pop(k, None)

    m_slots = flatten(m_slots)

    return m_gameDescription, m_userInitialData, m_slots


def prepDictHeader(dictHeader):
    '''
    Return: <dict> header ready for DataFrame conversion
    '''

    # clean header
    clean_header = ['m_ngdpRootKey', 'm_signature']
    for k in clean_header:
        dictHeader.pop(k, None)

    # flatten header
    dictHeader = flatten(dictHeader)

    # prep for df
    dictHeader = prepForDf(dictHeader)

    return dictHeader


def prepDictDetails(dictDetails):
    '''
    Converts dictDetails into dict ready for DataFrame conversion
    '''
    m_playerList = {}
    # each <dict> has same elements
    # initialize keys in m_slots
    for k in dictDetails['m_playerList'][0]:
        m_playerList[k] = []
    m_playerList['replayId'] = []
    # populate <dict>
    for d in dictDetails['m_playerList']:
        for entry in d:
            m_playerList[entry].append(d[entry])
        m_playerList['replayId'].append(replayId)

    # clean m_playerList
    clean_m_playerList = ['m_race', 'm_color', 'm_toon']
    for k in clean_m_playerList:
        m_playerList.pop(k, None)

    return m_playerList


def testTEData(parentTE, m_intData, m_stringData, m_fixedData):
    '''
    @param: each <dict> of the --trackerevents output
    @return: print statements if proper formatting exists, otherwise, a <list> of key lengths of incorrect <dict>
    '''
    check = [parentTE, m_intData, m_stringData, m_fixedData]
    names = ['parentTE', 'm_intData', 'm_stringData', 'm_fixedData']

    index = 0
    for d in check:
        count = 0
        for k in d:
            errors = False
            if count == 0:
                prevLength = len(d[k])
            else:
                if len(d[k]) != prevLength:
                    errors = True
                    print 'ERROR: <dict>', names[index], 'keys have differing lengths!'
                    for k in d:
                        print '{0:<25} {1:>5}'.format(k, len(d[k]))
                    break
                else:
                    prevLength = len(d[k])
            count += 1
        if errors is False:
            print 'SUCCESS: <dict>', names[index], 'is ready for DataFrame conversion!'
        index += 1


dictInitData = createDictInitData('../replayData/init_data.txt')
replayId = getReplayId(dictInitData)

if __name__ == '__main__':
    dictTE = createDictTGE('../replayData/tracker_events.txt')
    # dictGE = createDictTGE('../replayData/game_events.txt')
    dictHeader = prepDictHeader(createDictAEDH('../replayData/header.txt'))
    dictDetails = prepDictDetails(createDictAEDH('../replayData/details.txt'))
    m_gameDescription, m_userInitialData, m_slots = prepDictInitData(dictInitData)
    parentTE, m_intData, m_stringData, m_fixedData = prepDictTE(dictTE)

    dfTE = pd.DataFrame(dictTE)
    # dfGE = pd.DataFrame(dictGE)
    dfHeader = pd.DataFrame(dictHeader)
    dfDetails = pd.DataFrame(dictDetails)
    df_m_gameDescription = pd.DataFrame(m_gameDescription)
    df_m_userInitialData = pd.DataFrame(m_userInitialData)
    df_m_slots = pd.DataFrame(m_slots)
    dfParentTE = pd.DataFrame(parentTE)
    df_m_intData = pd.DataFrame(m_intData)
    df_m_stringData = pd.DataFrame(m_stringData)
    df_m_fixedData = pd.DataFrame(m_fixedData)
#!/usr/bin/python

import ast
import hashlib
import collections
import pandas as pd
import numpy as np
import re


def createDictTGE(input, replayId):
    '''
    Converts raw heroprotocol outputs --trackerevents, --gameevents to a <dict>.
    @param <file> input: raw heroprotocol outputs --trackerevents, --gameevents
    @return: <dictionary> of raw heroprotocol outputs
    '''
    with open(input, 'r') as f:
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


def prepDictTE(listTE, replayId):
    '''
    Flattens tracker events <dict> and returns 4 sub-<dict> ready for Pandas <DataFrame> conversion.  Blank values
    are populated with np.nan.
    @param <list> listTE: <list> of <dict> of --trackerevents, the output of createDictTGE
    @return: <list> dictTE, <dict> m_intData, <dict> m_stringData, <dict> m_fixedData
    '''
    # initialize keys of parent table
    parentKeys = []
    parentTE = {}
    for d in listTE:
        for k in d.keys():
            if k not in parentKeys:
                parentKeys.append(k)
        if 'm_instanceList' in d:
            summary = d
    for k in parentKeys:
        parentTE[k] = []

    # populate parent table
    listLength = 0
    for d in listTE:
        listLength += 1
        for i in d:
            parentTE[i].append(d[i])
        for e in parentTE:
            if len(parentTE[e]) < listLength:
                parentTE[e].append(np.nan)

    parentTE['replayId'] = [replayId] * len(listTE)

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
        if isinstance(i, str) or isinstance(i, unicode):
            temp.append(i.replace('Hero', ''))
        else:
            temp.append(i)
    m_stringData['Hero'] = temp

    # standardize PlayerID to m_userId reporting in m_intData, before{range(1,11)}, after{range(0,10)}
    m_intData['m_userId'] = m_intData.pop('PlayerID')
    m_intData['m_userId'][:] = [x - 1 for x in m_intData['m_userId']]
    # adjust m_intData['KillingPlayer'] from range(1,11) to range(0,10) for consistency on userId
    m_intData['KillingPlayer'] = [x - 1 for x in m_intData['KillingPlayer']]
    # adjust m_intData['TeamLevel'] from range(1,3) to range(0,2)
    m_intData['Team'] = [x - 1 for x in m_intData['Team']]

    # remove m_playerId, m_intData, m_stringData, m_fixedData from parentTE
    parentTE.pop('m_playerId', None)
    parentTE.pop('m_intData', None)
    parentTE.pop('m_stringData', None)
    parentTE.pop('m_fixedData', None)

    return parentTE, m_intData, m_stringData, m_fixedData, summary


def cleanTESubDict(subDict):
    '''
    prepDictTE() helper function to format parentTE['m_intData', 'm_stringData', 'm_fixedData'].
    @param <dict> subDict: sub <dict> to the parent tracker events <dict>
    '''
    for i in subDict:
        takeAction = True
        if isinstance(i, list):
            # i is a list of dictionaries associated with a tracker event
            temp = []
            for d in i:
                # record value of 'm_key' and 'm_value'
                try:
                    key = d['m_key']
                    value = d['m_value']
                    # add to new temp list as a dict
                    temp.append({key: value})
                except:
                    takeAction = False
                    continue
            # after iterating through all d in current list, clear list
            if takeAction:
                i[:] = []
                # set current list equal to temp list
                for d in temp:
                    i.append(d)


def populateTESubDicts(parentTE, subDict, dictName):
    '''
    prepDictTE() helper function to populate the sub <dict>.
    @param <dict> parentTE: parent <dict> of tracker events
    @param: <dict> subDict: <dict> to populate
    @param: <str> dictName: <str> corresponding to <dict> name
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
    prepDictTE() helper function that takes subDict from tracker events and creates a comprehensive list of keys.
    @param <dict> subDict: <dict> to collect list of keys from
    @return: <list> of all keys found in that subDict
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
    '''
    Checks if duplicate keys exist; e.g. multiple copies of 'KillingPlayer' associated with one 'PlayerID', and
    creates a new entry to tie each 'KillingPlayer' to 'PlayerID'.  Necessary to ensure all keys in <dict> have
    <list> values of equal length.
    @param <list> entry: a <list> of <dict>
    @return <bool> isDuplicates: True or False
    @return <list> duplicateKeys: <list> of all duplicate keys
    '''
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
    '''
    prepTESubDicts() helper function that works with isDuplicateKeys() to create separate entries for each duplicate
    key.
    @param <dict> parentTE: the parent <dict>
    @param <dict> subDict: sub of the parent
    @param <list> entry: <list> of <dict> of all entries of the duplicate keys associated with one 'PlayerID'
    @param <int> i: index to keep track of position in entry
    '''
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


def createDictInitData(initData, type="text"):
    '''
    Converts raw heroprotocol outputs --initdata to a <dict>.
    @param <file> initData: raw data output of heroprotocol --initdata
    @return: python <dict> of --initdata for replayId information and JSON conversion
    '''
    if type == "text":
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

    else:
        initData['m_syncLobbyState']['m_gameDescription'].pop('m_cacheHandles', None)
        initData['m_syncLobbyState']['m_gameDescription'].pop('m_mapFileName', None)
        initData['m_syncLobbyState']['m_gameDescription'].pop('m_slotDescriptions', None)

        return initData

    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_cacheHandles', None)
    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_mapFileName', None)
    dictInitData['m_syncLobbyState']['m_gameDescription'].pop('m_slotDescriptions', None)

    return dictInitData


def createDictAEDH(input, replayId, type="text"):
    '''
    Converts raw heroprotocol outputs --header, --details, --attributeevents to a <dict>.
    @param <file> input: raw data output of heroprotocol --header, --details, --attributeevents
    @return: python <dict> of --header, --details, --attributeevents
    '''
    if type == 'text':
        with open(input, 'r') as f:
            dictInput = ast.literal_eval(f.read())
        try:
            if dictInput['m_cacheHandles']:
                dictInput['m_cacheHandles'] = ['']
        except:
            pass
    else:
        input['replayId'] = replayId
        return input

    dictInput['replayId'] = replayId

    return dictInput


def getReplayId(dictInitData):
    '''
    Generates a unique ReplayId based on 'm_randomValue' and player names.
    @param <dict> dictInitData: <dict> from output of createDictInitData()
    @return <int>: unique replayId
    '''
    randomValue = dictInitData['m_syncLobbyState']['m_gameDescription']['m_randomValue']
    playerNames = ''

    for i in dictInitData['m_syncLobbyState']['m_userInitialData']:
        playerNames += i['m_name']

    replayId = hashlib.md5(str(randomValue) + playerNames).hexdigest()

    return replayId


def renameKeys(data):
    '''
    Currently unused, consider using in the future.
    '''
    for i in data:
        match = re.search('^m_', i)
        if match:
            new_key = i[2:len(i)]
            dictDetails[new_key] = dictDetails.pop(i)
        match = re.search('^_', i)
        if match:
            new_key = i[2:len(i)]
            dictDetails[new_key] = dictDetails.pop


def prepForDf(dictionary):
    '''
    Preps <dict> to proper Pandas <DataFrame> format with values as lists.  Does NOT break out embedded dictionaries.
    Use function flatten() for that.
    @param <dict> dictionary: <dict> that requires formatting
    @return <dict> dictionary: formatted <dict>
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
        if dictionary[i] is np.nan:
            dictionary[i] = n
            continue
        if len(dictionary[i]) == 0:
            dictionary[i] = np.nan

    return dictionary


def flatten(d, parent_key='', sep='_'):
    '''
    Flattens embedded <dict> into parent <dict> by combining key names using '_' separator.
    @param <dict> d: <dict> to be flattened
    @param <str> parent_key: optional addition to new combined key
    @param <str> sep: <str> to combine key names
    @return: the flattened <dict>
    '''
    items = []
    for k, v in d.items():
        new_key = str(parent_key) + sep + str(k) if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def prepDictInitData(dictInitData, replayId):
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
                               'm_gameOptions_clientDebugFlags', 'm_defaultAIBuild', 'm_gameOptions_m_battleNet',
                               'm_gameOptions_m_competitive', 'm_gameOptions_m_cooperative', 'm_gameOptions_m_fog',
                               'm_gameOptions_m_lockTeams', 'm_gameOptions_m_noVictoryOrDefeat',
                               'm_gameOptions_m_practice', 'm_gameType', 'm_isCoopMode', 'm_isPremadeFFA',
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


def prepDictDetails(dictDetails, replayId):
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

    # rename 'm_workingSetSlotId' to 'm_userId' for consistency
    m_playerList['m_userId'] = m_playerList.pop('m_workingSetSlotId')
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


def prepSummary(summary, m_gameDescription, dfHeader, dictDetails, dfDetails, df_m_slots, df_m_stringData, replayId):
    '''
    Creates <DataFrame> containing summary information from game
    @param <dict> summary: the <dict> in dictTE containing 'm_instanceList'
    @return: <DataFrame> of summary information
    '''
    gameTypeMap = {0: 'Custom',
                   50001: 'Quick Match',
                   50021: 'AI Coop',
                   50051: 'Unranked Draft',
                   50061: 'Hero League',
                   50071: 'Team League'}
    # references init_data 'm_ammId' to determine GameType in conjunction with the map defined above
    if isinstance(m_gameDescription['m_gameOptions_m_ammId'], float):
        gameTypeId = 0
    else:
        gameTypeId = m_gameDescription['m_gameOptions_m_ammId'][0]

    gameType = gameTypeMap[gameTypeId]

    # use summary['m_instnaceList'][0]['m_values'][2] because sometimes zero index has no values
    gameTime = summary['m_instanceList'][0]['m_values'][2][0]['m_time']
    dictSummary = {'ReplayId': [replayId] * 10,
                   'GameTime': [gameTime] * 10,
                   'GameType': [gameType] * 10,
                   'Map': [dictDetails['m_title']] * 10,
                   'DataBuildNum': [dfHeader['m_dataBuildNum'][0]] * 10,
                   'Win_Loss': ['Win' if x == 1 else 'Loss' for x in dfDetails['m_result']],
                   'UserId': [x for x in dfDetails['m_userId']],
                   'PlayerName': [x for x in dfDetails['m_name']],
                   'Hero': [x for x in dfDetails['m_hero']],
                   'Mount': [x for x in df_m_slots.loc[df_m_slots['m_userId'] < 10]['m_mount']],
                   'Skin': [x for x in df_m_slots.loc[df_m_slots['m_userId'] < 10]['m_skin']],
                   'Silenced': [x for x in df_m_slots.loc[df_m_slots['m_userId'] < 10]['m_hasSilencePenalty']]}

    for i in range(1, 8):
        key = 'Tier ' + str(i) + ' Choice'
        if key in df_m_stringData:
            dictSummary[key] = [x for x in df_m_stringData.loc[df_m_stringData['Tier 1 Choice'] > 0][key]]
        else:
            dictSummary[key] = ['', '', '', '', '', '', '', '', '', '']

    for d in summary['m_instanceList']:
        tempKey = d['m_name']
        tempVal = []
        for i in d['m_values']:
            if len(i) != 0:
                tempVal.append(i[0]['m_value'])
        dictSummary[tempKey] = tempVal

    dfSummary = pd.DataFrame(dictSummary)
    return dfSummary


def generateInitialData(path):
    '''
    Generates the initial data required to build <DataFrames>
    @param <string> path: destination of raw output *.txt files
    @return <dict> dictInitData: used to initialized the remainder of <dict> and <DataFrame>
    @return <str> replayId: unique identifier
    '''
    dictInitData = createDictInitData(path + 'init_data.txt')
    replayId = getReplayId(dictInitData)

    return dictInitData, replayId


def generateSummary(path, dictInitData, replayId):
    '''
    Generates all <DataFrame> for data mining.
    @param <string> path: destination of raw output *.txt files
    @retrun <DataFrame> dfSummary: summary data
    '''
    dictTE = createDictTGE(path + 'tracker_events.txt', replayId)
    # dictGE = createDictTGE(path + 'game_events.txt', replayId)
    dictHeader = prepDictHeader(createDictAEDH(path + 'header.txt', replayId))
    dictDetails = createDictAEDH(path + 'details.txt', replayId)
    prepDictDetails = prepDictDetails(dictDetails, replayId)
    m_gameDescription, m_userInitialData, m_slots = prepDictInitData(dictInitData, replayId)
    parentTE, m_intData, m_stringData, m_fixedData, summary = prepDictTE(dictTE, replayId)

    dfTE = pd.DataFrame(dictTE)
    # dfGE = pd.DataFrame(dictGE)
    dfHeader = pd.DataFrame(dictHeader)
    dfDetails = pd.DataFrame(prepDictDetails)
    df_m_gameDescription = pd.DataFrame(m_gameDescription)
    df_m_userInitialData = pd.DataFrame(m_userInitialData)
    df_m_slots = pd.DataFrame(m_slots)
    dfParentTE = pd.DataFrame(parentTE)
    df_m_intData = pd.DataFrame(m_intData)
    df_m_stringData = pd.DataFrame(m_stringData)
    df_m_fixedData = pd.DataFrame(m_fixedData)
    dfSummary = prepSummary(summary, m_gameDescription, dfHeader, dfDetails, df_m_slots, df_m_stringData, replayId)

    return dfSummary


def gameData(dfSummary):
    '''
    Generates <DataFrame> for Map level data
    @param <DataFrame> dfSummary: returned value of prepSummary()
    @return <DataFrame>: a subset of dfSummary containing 'ReplayId', 'DataBuildNum', 'GameTime'
                        , 'GameType', 'Map' with one row per game
    '''
    replayId = dfSummary['ReplayId'][0]
    dataBuildNum = dfSummary['DataBuildNum'][0]
    gameTime = dfSummary['GameTime'][0]
    gameType = dfSummary['GameType'][0]
    mapName = dfSummary['Map'][0]
    d = {'ReplayId': replayId, 'DataBuildNum': dataBuildNum, 'GameTime': gameTime,
         'GameType': gameType, 'Map': mapName}
    return pd.DataFrame(data=d, index=[0])


def playerData(dfSummary):
    '''
    Generates <DataFrame> for player data.
    @param <DataFrame> dfSummary: returned value of prepSummary()
    @return <DataFrame>: a subset of dfSummary with 10 rows per game
    '''
    df = dfSummary[['ReplayId', 'PlayerName', 'Hero', 'UserId', 'Takedowns', 'SoloKill', 'Assists', 'Deaths',
                    'HighestKillStreak', 'HeroDamage', 'SiegeDamage', 'StructureDamage', 'MinionDamage',
                    'CreepDamage', 'SummonDamage', 'TimeCCdEnemyHeroes', 'Healing', 'SelfHealing',
                    'DamageTaken', 'ExperienceContribution', 'TownKills', 'TimeSpentDead', 'MercCampCaptures',
                    'WatchTowerCaptures', 'MetaExperience', 'Win_Loss', 'Tier 1 Choice',
                    'Tier 2 Choice', 'Tier 3 Choice', 'Tier 4 Choice',
                    'Tier 5 Choice', 'Tier 6 Choice', 'Tier 7 Choice']]
    return df


def replayExists(currentFile, replayId):
    '''
    Checks if replayId exists in current file.
    @param currentFile: Pyton csv object
    @param <str> replayId: replayId
    @return <bool>: True/False
    '''
    dfReplayId = pd.read_csv(currentFile, usecols=['ReplayId'])

    if replayId in list(dfReplayId['ReplayId']):
        return True
    else:
        return False


def isMismatch(dict1, dict2):
    '''
    Used to support the unittest script tester.py.  Required to compared <dict> with <list> that include np.nan.
    np.nan == np.nan > False
    @param dict1 <dict>: loaded from JSON
    @param dict2 <dict>: generated from function
    @return <bool>: False if two <dict> are identical
    '''
    mismatch = False

    for k in dict1:
        for i in range(0, len(dict1[k])):
            if isinstance(dict1[k][i], float):
                if np.isnan(dict1[k][i]) and np.isnan(dict2[k][i]):
                    continue
                else:
                    print "\ndict 1:", dict1[k][i], "dict 2:", dict2[k][i]
                    mismatch = True
                    break
            if dict1[k][i] == dict2[k][i]:
                continue
            else:
                print "\ndict 1:", dict1[k][i], "dict 2:", dict2[k][i]
                mismatch = True
                break

    return mismatch


if __name__ == '__main__':
    dictInitData = createDictInitData('testData/init_data.txt')
    replayId = getReplayId(dictInitData)

    path = "testData/"

    dictTE = createDictTGE(path + 'tracker_events.txt', replayId)
    # dictGE = createDictTGE(path + 'game_events.txt', replayId)
    dictHeader = prepDictHeader(createDictAEDH(path + 'header.txt', replayId))
    dictDetails = createDictAEDH(path + 'details.txt', replayId)
    prepDictDetails = prepDictDetails(dictDetails, replayId)
    m_gameDescription, m_userInitialData, m_slots = prepDictInitData(dictInitData, replayId)
    parentTE, m_intData, m_stringData, m_fixedData, summary = prepDictTE(dictTE, replayId)

    dfTE = pd.DataFrame(dictTE)
    # dfGE = pd.DataFrame(dictGE)
    dfHeader = pd.DataFrame(dictHeader)
    dfDetails = pd.DataFrame(prepDictDetails)
    df_m_gameDescription = pd.DataFrame(m_gameDescription)
    df_m_userInitialData = pd.DataFrame(m_userInitialData)
    df_m_slots = pd.DataFrame(m_slots)
    dfParentTE = pd.DataFrame(parentTE)
    df_m_intData = pd.DataFrame(m_intData)
    df_m_stringData = pd.DataFrame(m_stringData)
    df_m_fixedData = pd.DataFrame(m_fixedData)
    dfSummary = prepSummary(summary, m_gameDescription, dfHeader, dictDetails, dfDetails, df_m_slots
                            , df_m_stringData, replayId)
    dfGameData = gameData(dfSummary)
    dfPlayerData = playerData(dfSummary)
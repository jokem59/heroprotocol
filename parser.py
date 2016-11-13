#!/usr/bin/env python

import sys
import formatter as fmt
import pandas as pd
import pprint
import json

from mpyq import mpyq
import protocol29406

class EventLogger:
    def __init__(self):
        self._event_stats = {}

    def log(self, output, event):
        # update stats
        if '_event' in event and '_bits' in event:
            stat = self._event_stats.get(event['_event'], [0, 0])
            stat[0] += 1  # count of events
            stat[1] += event['_bits']  # count of bits
            self._event_stats[event['_event']] = stat
        # write structure
        if args['json']:
            s = json.dumps(event, encoding="ISO-8859-1");
            print(s);
        else:
            pprint.pprint(event, stream=output)

    def log_stats(self, output):
        for name, stat in sorted(self._event_stats.iteritems(), key=lambda x: x[1][1]):
            print >> output, '"%s", %d, %d,' % (name, stat[0], stat[1] / 8)


if __name__ == '__main__':
    # TODO: Check to ensure that every file in the directory is a *.StormReplay file before looping through
    # TODO: loop through each *.StormReplay file in specified directory
    # replace argument with *.StormReplay
    archive = mpyq.MPQArchive('replays/HL HOTS Logs Shared Replay.StormReplay')

    logger = EventLogger()

    # Read the protocol header, this can be read with any protocol
    contents = archive.header['user_data_header']['content']
    # headers is a <dict>
    header = protocol29406.decode_replay_header(contents)

    # The header's baseBuild determines which protocol to use
    baseBuild = header['m_version']['m_baseBuild']
    try:
        protocol = __import__('protocol%s' % (baseBuild,))
    except:
        print >> sys.stderr, 'Unsupported base build: %d' % baseBuild
        sys.exit(1)

    # Create pertinent <dict>/<DataFrames>

    # initialize initdata
    contents = archive.read_file('replay.initData')
    initdata = protocol.decode_replay_initdata(contents) # this is a <dict>
    dictInitData = fmt.createDictInitData(initdata, type="dict")
    replayId = fmt.getReplayId(dictInitData)

    m_gameDescription, m_userInitialData, m_slots = fmt.prepDictInitData(dictInitData, replayId)

    # initialize header
    formattedHeader = fmt.prepDictHeader(header)
    dfHeader = pd.DataFrame(formattedHeader)

    # initialize details
    contents = archive.read_file('replay.details')
    details = protocol.decode_replay_details(contents)
    dictDetails = fmt.createDictAEDH(details, replayId, type="dict")
    dictDetails = fmt.prepDictDetails(dictDetails, replayId)

    # Print tracker events
    if hasattr(protocol, 'decode_replay_tracker_events'):
        contents = archive.read_file('replay.tracker.events')
        listTE = []
        for event in protocol.decode_replay_tracker_events(contents):
            listTE.append(event)

        parentTE, m_intData, m_stringData, m_fixedData, summary = fmt.prepDictTE(listTE, replayId)

    # prep summary data
    dfTE = pd.DataFrame(parentTE)
    # dfGE = pd.DataFrame(dictGE)
    dfDetails = pd.DataFrame(dictDetails)
    df_m_gameDescription = pd.DataFrame(m_gameDescription)
    df_m_userInitialData = pd.DataFrame(m_userInitialData)
    df_m_slots = pd.DataFrame(m_slots)
    dfParentTE = pd.DataFrame(parentTE)
    df_m_intData = pd.DataFrame(m_intData)
    df_m_stringData = pd.DataFrame(m_stringData)
    df_m_fixedData = pd.DataFrame(m_fixedData)
    dfSummary = fmt.prepSummary(summary, m_gameDescription, dfHeader, dfDetails, df_m_slots, df_m_stringData, replayId)
    dfSummary.to_csv('test.csv')



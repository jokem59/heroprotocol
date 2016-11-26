#!/usr/bin/python

import formatter as fmt
import json
import unittest
import pandas as pd

class TestFormatter(unittest.TestCase):
    '''
    Tests functions up to their conversion to DataFrames.  The <dict> is the foundation of the data outputted
    and is the only aspects that require testing.  The DataFrames are modified based on what information is desired.
    '''
    def setUp(self):
        with open('testData/dictInitData.txt', 'r') as f:
            self.dictInitData = json.load(f)

        self.replayId = fmt.getReplayId(self.dictInitData)

        with open('testData/dictHeader.txt', 'r') as f:
            self.dictHeader = json.load(f)

        with open('testData/dictDetails.txt', 'r') as f:
            self.dictDetails = json.load(f)

        with open('testData/prepDictDetails.txt', 'r') as f:
            self.prepDictDetails = json.load(f)

        with open('testData/m_gameDescription.txt', 'r') as f:
            self.m_gameDescription = json.load(f)

        with open('testData/m_userInitialData.txt', 'r') as f:
            self.m_userInitialData = json.load(f)

        with open('testData/m_slots.txt', 'r') as f:
            self.m_slots = json.load(f)

        with open('testData/dictTE.txt', 'r') as f:
            self.dictTE = json.load(f)

        with open('testData/parentTE.txt', 'r') as f:
            self.parentTE = json.load(f)

        with open('testData/m_intData.txt', 'r') as f:
            self.m_intData = json.load(f)

        with open('testData/m_stringData.txt', 'r') as f:
            self.m_stringData = json.load(f)

        with open('testData/m_fixedData.txt', 'r') as f:
            self.m_fixedData = json.load(f)

        with open('testData/summary.txt', 'r') as f:
            self.summary = json.load(f)

    def test_createDictInitData(self):
        t_dict = fmt.createDictInitData('testData/init_data.txt')
        self.assertEqual(t_dict, self.dictInitData)

    def test_getReplayId(self):
        self.assertEqual(fmt.getReplayId(self.dictInitData), self.replayId)

    def test_prepDictHeader(self):
        self.assertEqual(fmt.prepDictHeader(fmt.createDictAEDH('testData/header.txt', self.replayId)), self.dictHeader)

    def test_createDictAEDH(self):
        self.assertEqual(fmt.createDictAEDH('testData/details.txt', self.replayId), self.dictDetails)

    def test_prepDictDetails(self):
        self.assertEqual(fmt.prepDictDetails(self.dictDetails, self.replayId), self.prepDictDetails)

    def test_prepDictInitData(self):
        self.assertEqual(fmt.prepDictInitData(self.dictInitData, self.replayId),
                         (self.m_gameDescription, self.m_userInitialData, self.m_slots))

    # comparing the last element which is the summary game data
    def test_createDictTGE(self):
        self.assertEquals(fmt.createDictTGE('testData/tracker_events.txt', self.replayId)[-1], self.dictTE[-1])

    def test_prepDictTE(self):
        test_parentTE, test_m_intData, test_m_stringData, test_m_fixedData, test_summary \
            = fmt.prepDictTE(self.dictTE, self.replayId)
        self.assertFalse(fmt.isMismatch(test_parentTE, self.parentTE))
        self.assertFalse(fmt.isMismatch(test_m_intData, self.m_intData))
        self.assertFalse(fmt.isMismatch(test_m_stringData, self.m_stringData))
        self.assertFalse(fmt.isMismatch(test_m_fixedData, self.m_fixedData))
        self.assertEqual(test_summary, self.summary)

if __name__ == '__main__':
    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFormatter)
    unittest.TextTestRunner(verbosity=2).run(suite)
dictDetails -> prepDictDetails()
--preps 1 sub dictionary m_playerList for df conversion

dictHeader -> prepDictHeader()
--preps 1 parent dictionary for df conversion

dictInitData -> prepDictInitData()
--preps 3 dictionaries (sub 3x), m_gameDescription, m_userInitialData, m_slots for df conversion

dictTE -> prepDictTE()
Ex: parentTE, m_intData, m_stringData, m_fixedData = prepDictTE(dictTE)
--preps 4 dictionaries (parent, sub 3x), parentTE, m_intData, m_stringData, m_fixedData with a set of all keys, values are list of each event
NOTE: Above may not conform to overall architecture defined below

dictGE -> 

Create separate tables:
1. dictDetails, dictHeader, dictInitData, dictAE
2. dictTE, dictGE

Architecture - one flat dictionary -> DataFrame per output product with replayId as primary key!

Flat Dictionary structured with all keys and a list of all elments, must always have a value so all lists are same length.
These values must match datatype of that field.
dict = {'a': [1, 2, 3, 4, 5,..., n],
	'b': ['joe', 'jamie', 'mog', 'aj', 'hunter',...,n'],
	'replayId': [3, 3, 3, 3, 3,...,n]}


Test Scripts:
Go from raw heroprotocol output to flattened dictionaries
- check that each events dictionaries contain the same number of events
- check that each event in above dictionaries contain 'replayId' and '_gameloop' 
- check to ensure there are no embedded data structures (lists, dicts, tuples)

test that TE subDicts have keys of same length of DF conversion
for k in m_intData:
    print k, len(m_intData[k])

TODO:
- How to tell from data if QM, HL, TL, UD

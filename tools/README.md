# Hero Protocol Tools

These tools extend the functionality of the Blizzard released heroprotocol reference Python Library.  Currently, tools will extract summary data found from —initdata ‘m_instanceList’ and compile them into a CSV file.  This will loop through all replays in ../replays/ and archive parsed *.StormReplay files in the ../replays/archive/ directory.  Each replay is assigned a unique ID using an MD5 hash utilizing the —initiate ‘m_randomValue’ and the string of all the player names in the game.

# How To Use

# License

Open sourced under the MIT license.

# Acknowledgements

Thanks to Blizzard for the free-use of heroprotocol and the consistent updates with new game patches.

Thanks to Ben Barret of [HOTSLogs](http://www.hotslogs.com) for valuable feedback and insight into the replay data. 
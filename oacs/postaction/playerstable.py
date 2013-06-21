#!/usr/bin/env python
# encoding: utf-8

## @package playerstable
#
# This contains the PlayersTable class which manage the HDF players' table from a players' table log file, and also provide extended informations about the current player (if cheater)

from oacs.postaction.basepostaction import BasePostAction
from oacs.inputparser.csvparser import CsvParser
import pandas as pd

## PlayersTable
#
# Manage the HDF players' table from a players' table log file, and also provide extended informations about the current player (if cheater)
class PlayersTable(BasePostAction):

    ## @var config
    # A reference to a ConfigParser object, already loaded

    ## @var parent
    # A reference to the parent object (Runner)

    ## Maximum string size to store inside the HDF table (will cap ANY field, including player name but also numbers, so choose this number large enough!)
    maxstringsize = 80

    ## Constructor
    # @param config An instance of the ConfigParser class
    def __init__(self, config=None, parent=None, *args, **kwargs):
        self.inputparser = CsvParser(config=config, parent=self)
        return BasePostAction.__init__(self, config, parent, *args, **kwargs)

    ## Manage the local playerstable database and add extended informations about the player (that are substitutable) if detected as a cheater
    # @param Cheater Is the player a cheater?
    # @param Playerinfo A dict containing the info of the last detected cheater
    # @return An updated dict of vars (mainly the Playerinfo, now containing extended informations)
    def action(self, Cheater=False, Playerinfo=None, *args, **kwargs):

        # Update our local playerstable database with the latest entries from the playerstable log generated by the game
        self._updatePlayersTable()

        # If the player is a cheater, we fetch extended infos from the playerstable database
        if Cheater:
            Playerinfo.update(self._updatePlayerinfo(Playerinfo))

        return {'Playerinfo': Playerinfo} # return an updated dict of vars (mainly the Playerinfo, now containing extended informations)

    def _updatePlayerinfo(self, Playerinfo=None):
        if Playerinfo is None: return # if Playerinfo is empty, we cannot match the playerid thus we don't have to do anything and just return

        # Open the HDF store
        ptdb = pd.HDFStore('playerstabledb.h5')

        # Fetch the record associated with the current player's playerid
        X = ptdb.select('playerstable', 'playerid=%s' % str(int(Playerinfo['playerid']))) # convert first to an int because sometimes pandas funnily add a .0 at the end to show that it is dtype float

        # if no player with this id can be found, we won't modify Playerinfo
        if not X.empty:
            # Select the last result (normally, the ids should be unique, but in case of conflict, the latest choice is the most reasonable since we just detected the cheating attempt)
            X = X.iloc[-1]
            # Update the Playerinfo with those extended informations
            Playerinfo.update(X.to_dict())

        # Close the HDF store
        ptdb.close()

        # Return the updated Playerinfo (if a record was found in the playerstable)
        return Playerinfo

    def _updatePlayersTable(self):
        # Setup the files we need
        ptfile = self.config.get('playerstable', None) # Playerstable source log file
        ptdb = self.config.get('playerstabledb', 'playerstabledb.h5') # Target playerstable database in HDF

        # No source file? we quit
        if ptfile is None: return None


        # Opening the files

        # Opening the source file
        gendata = self.inputparser.read(ptfile, row_header=0)

        if gendata is None: return None # quit if empty or no new line to read

        # Opening the target database
        store = pd.HDFStore(ptdb)

        # For each new entry in the source file
        for dictofvars in gendata:
            # Read the entry (should be stored in a dict's key X) - as a Series
            X = dictofvars['X']
            # Convert to a one-row DataFrame because Pandas cannot yet store Series in HDF stores... And must also convert to dtype string! Int are not allowed!
            X = pd.DataFrame(X).transpose()
            # WORKAROUND: since pandas 0.11 stable, astype("string") will cast a truncated representation string from a long number, thus we have to cast it correctly manually
            #X.applymap(lambda x: "%.0f" % x if not isinstance(x, basestring) else x)
            # Ensure that playername, which is set by the player, cannot break this code because it's too long (if longer than maxstringsize, the entry won't be stored at all!)
            if 'playername' in X.keys():
                X['playername'] = self._cap(X['playername'], self.maxstringsize)
            # Save into the database (will automatically create the database with the correct setup settings if the db file does not yet exist)
            store.append('playerstable', X.astype("string"), data_columns=['playerid'], min_itemsize = self.maxstringsize, chunksize=1, expectedrows=1) # data_columns=True force all columns to be searchable (else you can't query playerid=someid, but just columns=playerid!). Here we only set playerid, because else the searchable data_columns are size limited, and if overflow then crash! And we certainly don't want that. So we have to skip playernames.

        # Close the HDF store
        store.close()

        # Everything went alright!
        return True

    ## Cap a string to a maximum length
    def _cap(self, string, length):
        return string if len(string) <= length else string[0:length]

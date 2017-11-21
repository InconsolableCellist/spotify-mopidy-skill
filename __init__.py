import sys
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message
from os.path import dirname, abspath, basename
from pprint import pprint, pformat

sys.path.append(abspath(dirname(__file__)))
Mopidy = __import__('mopidy').Mopidy

__author__ = 'InconsolableCellist'

LOGGER = getLogger(__name__)

class SpotifyMopidySkill(MycroftSkill): 
    def __init__(self): 
        super(SpotifyMopidySkill, self).__init__(name="SpotifyMopidySkill")

    def initialize(self):
        LOGGER.info("initializing Spotify Mopidy skill")
        self.mopidy = Mopidy()

#        play_intent = IntentBuilder("PlayIntent"). \
#                require("PlayKeyword"). \
#                optionally("ArtistKeyword"). \
#                optionally("SongKeyword"). \
#                optionally("AlbumKeyword"). \
#                optionally("Artist"). \
#                build()

        play_intent = IntentBuilder("PlayIntent"). \
                require("PlayKeyword"). \
                require("Artist"). \
                build()
        self.register_intent(play_intent, self.handle_play_intent2)

    def stop(self):
        pass


    def handle_play_intent2(self, message):
        keyword = None
        artist = None
        album = None
        result = {}
        LOGGER.info("message.data is {}".format(pformat(message.data)))

        if 'SongKeyword' in message.data:
            LOGGER.info("Song keyword found! {}".format(message.data['SongKeyword']))
            self.handle_song(message)
        elif 'AlbumKeyword' in message.data:
            LOGGER.info("Album keyword found! {}".format(message.data['AlbumKeyword']))
            self.handle_album(message)
        else:
            LOGGER.info("Don't know if this is an album or an artist.")
            self.handle_keyword(message)

    def get_artist(self, message):
        artist = ""
        if 'ArtistKeyword' in message.data:
            LOGGER.info("Artist keyword found! {}".format(message.data['ArtistKeyword']))
            artist = message.data['ArtistKeyword']
        if 'Artist' in message.data:
            LOGGER.info("Artist found! {}".format(message.data['Artist']))
            artist = message.data['Artist']
        return artist

    def handle_song(self, message):
        LOGGER.info("\tHandling what we know to be a song")
        artist = self.get_artist(message)
        if artist != "":
            LOGGER.info("\tartist is {}".format(artist))

    def handle_album(self, message):
        LOGGER.info("\tHandling what we know to be a album")
        artist = self.get_artist(message)
        if artist != "":
            LOGGER.info("\tartist is {}".format(artist))

    def handle_keyword(self, message):
        LOGGER.info("\tHandling something we don't know to be a song or album.")
        artist = self.get_artist(message)
        if artist != "":
            LOGGER.info("\tartist is {}".format(artist))

        

    def handle_play_intent(self, message):
        keyword = None
        artist = None
        album = None
        result = {}

        LOGGER.info("message.data is {}".format(pformat(message.data)))
        if 'Keyword' in message.data: 
            keyword = message.data['Keyword']
            LOGGER.info("keyword found! {}".format(keyword))
        if 'Artist' in message.data: 
            artist = message.data['Artist']
            LOGGER.info("artist found! {}".format(artist))
        # DEBUG: uncomment
        if keyword and artist: 
            LOGGER.info("searching spotify with keyword {} and artist {}.".format(keyword, artist))
            result = self.mopdiy.search_any(keyword, artist_hint=artist)
        elif keyword:
            LOGGER.info("searching spotify with keyword {}.".format(keyword))
            result = self.mopidy.search_any(keyword)
        else:
            LOGGER.info("wasn't able to obtain even a keyword to search spotify with!")

        #result = self.mopidy.search_any("mask off", isKeywordTrack=True, isKeywordAlbum=False, artist_hint="future")
        pprint(result)
        if 'uri' in result:
            if result['name'] and result['artist_name']:
                LOGGER.info("playing {} by {}. URI: {}".format(result['name'], result['artist_name'], result['uri']))
            self.play(result['uri'])
        else:
            LOGGER.info("Didn't get any results, or the result was missing the URI! {}".format(pformat(result)))

    def play(self, tracks):
        self.mopidy.clear_list()
        self.mopidy.add_list(tracks)
        self.mopidy.play()

def create_skill(): 
    return SpotifyMopidySkill()


import sys
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message
from os.path import dirname, abspath, basename
from pprint import pprint, pformat
import re
import time

# based off the skill "mopidy_skill" by forslund: https://github.com/forslund/mopidy_skill

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

        play_intent = IntentBuilder("PlayIntent"). \
                require("PlayKeyword"). \
                require("Keyword"). \
                optionally("SongKeyword"). \
                optionally("AlbumKeyword"). \
                build()
        self.register_intent(play_intent, self.handle_play_intent)

        what_is_playing_intent = IntentBuilder("WhatIsPlayingIntent"). \
                require("WhatSong"). \
                build()
        self.register_intent(what_is_playing_intent, self.handle_what_is_playing_intent)

        pause_intent = IntentBuilder("PauseIntent"). \
                require("PauseKeyword"). \
                build()
        self.register_intent(pause_intent, self.handle_pause_intent)

        resume_intent = IntentBuilder("ResumeIntent"). \
                require("ResumeKeyword"). \
                build()
        self.register_intent(resume_intent, self.handle_resume_intent)

    def stop(self):
        if self.mopidy:
                self.mopidy.clear_list()
                self.mopidy.stop()

    def handle_play_intent(self, message):
        keyword = None
        artist = None
        album = None
        result = {}
        LOGGER.info("Handling play intent. message.data is {}".format(pformat(message.data)))

        if 'SongKeyword' in message.data:
            LOGGER.info("Song keyword found! {}".format(message.data['SongKeyword']))
            self.handle_song(message)
        elif 'AlbumKeyword' in message.data:
            LOGGER.info("Album keyword found! {}".format(message.data['AlbumKeyword']))
            self.handle_album(message)
        else:
            LOGGER.info("Don't know if this is an album or an artist.")
            self.handle_keyword(message)

    # breaks up the keywords into artist and keyword, if possible. Otherwise just keyword
    def break_artist(self, message):
        result = {}
        if not 'Keyword' in message.data:
            LOGGER.error("received malformed message input to the break_artist parser")
            return result

        m = re.match(r'^(.+) by (?:the (group|artist|composer|musician|band|rapper|orchestra))?(.*)$', message.data['Keyword'], re.M|re.I)
        if m: 
            LOGGER.info("\tI think the keyword/track is {} and the artist is {}".format(m.group(1), m.group(3)))
            result['keyword'] = m.group(1)
            result['artist'] = m.group(3)
        else: 
            result['keyword'] = message.data['Keyword']
            LOGGER.info("\tthis messsage doesn't appear to have any artist information")
        return result

    def handle_song(self, message):
        LOGGER.info("\tHandling what we know to be a song")
        keywords = self.break_artist(message)
        if 'artist' in keywords:
            self.handle_results(self.mopidy.search_any(keywords['keyword'], isKeywordTrack=True, artist_hint=keywords['artist']))
        else: 
            self.handle_results(self.mopidy.search_any(keywords['keyword'], isKeywordTrack=True))


    def handle_album(self, message):
        LOGGER.info("\tHandling what we know to be a album")
        keywords = self.break_artist(message)
        if 'artist' in keywords:
            self.handle_results(self.mopidy.search_any(keywords['keyword'], isKeywordAlbum=True, artist_hint=keywords['artist']), isAlbum=True, isTrack=False)
        else: 
            self.handle_results(self.mopidy.search_any(keywords['keyword'], isKeywordAlbum=True), isAlbum=True, isTrack=False)

    def handle_keyword(self, message):
        LOGGER.info("\tHandling something we don't know to be a song or album.")
        keywords = self.break_artist(message)
        if 'artist' in keywords:
            self.handle_results(self.mopidy.search_any(keywords['keyword'], artist_hint=keywords['artist']))
        else: 
            self.handle_results(self.mopidy.search_any(keywords['keyword']))

    # takes search results from self.mopidy search functions and plays what's necessary
    def handle_results(self, result, isAlbum=False, isTrack=True):
        pprint("result is {}".format(result))
        if 'uri' in result: 
            self.stop()
            if isAlbum:
                self.speak_dialog("playing_album", {'album' : result['name'], 'artist' : result['artist_name']})
            else:
                self.speak_dialog("playing_track", {'track' : result['name'], 'artist' : result['artist_name']})
#            LOGGER.info("playing {} by {}. URI: {}".format(result['name'], result['artist_name'], result['uri']).encode('utf-8'))

            self.stop()
            time.sleep(3)
            self.play(result['uri'])
        else:
            self.speak_dialog("no_results")
            LOGGER.info("Didn't get any results, or the result was missing the URI! {}".format(pformat(result)))

    def handle_what_is_playing_intent(self, message):
        LOGGER.info("We've been asked to find out what's currently playing")
        result = self.mopidy.get_current_track().json()['result']
        if result: 
            track_name = result['album']['name']
            artist_name = result['album']['artists'][0]['name']
            self.speak_dialog("whats_playing", {'song' : track_name, 'artist' : artist_name})
            LOGGER.info("We're currently playing {} by {}".format(track_name, artist_name))
        else: 
            self.speak_dialog("nothing_playing")
            LOGGER.info("Nothing is currently playing")

    def handle_pause_intent(self, message):
        LOGGER.info("Pausing")
        self.mopidy.pause()

    def handle_resume_intent(self, message):
        LOGGER.info("Unpausing")
        self.mopidy.resume()

    def play(self, tracks):
        self.mopidy.clear_list()
        self.mopidy.add_list(tracks)
        self.mopidy.play()

def create_skill(): 
    return SpotifyMopidySkill()


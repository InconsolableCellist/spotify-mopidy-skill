#!/usr/bin/python

import requests
from copy import copy
import json
from pprint import pprint
import pickle
from random import *
from mycroft.util.log import getLogger

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

MOPIDY_API = '/mopidy/rpc'

_base_dict = {'jsonrpc' : '2.0', 'id' : 1, 'params': {}}
url = 'http://localhost:6680' + MOPIDY_API

LOGGER = getLogger(__name__)

class Mopidy(object):
    def __init__(self):
        self.url = url
        self.is_playing = False
        self.volume = None
        self.volume_low = 3
        self.volume_high = 100

    def clear_list(self, force=False):
        if self.is_playing or force:
            d = copy(_base_dict)
            d['method'] = 'core.tracklist.clear'
            r = requests.post(self.url, data=json.dumps(d))
            return r

    def add_list(self, uri):
        d = copy(_base_dict)
        d['method'] = 'core.tracklist.add'
        if type(uri) == str or type(uri) == unicode:
            d['params'] = {'uri' : uri}
        elif type(uri) == list:
            d['params'] = {'uris' : uri}
        else:
            return None

        r = requests.post(self.url, data=json.dumps(d))
        return r

    def play(self): 
        self.is_playing = True
        self.restore_volume()
        d = copy(_base_dict)
        d['method'] = 'core.playback.play'
        r = requests.post(self.url, data=json.dumps(d))

    def stop(self):
        if self.is_playing:
            d = copy(_base_dict)
            d['method'] = 'core.playback.stop'
            r = requests.post(self.url, data=json.dumps(d))
            self.is_playing = False

    def get_current_track(self):
        d = copy(_base_dict)
        d['method'] = 'core.playback.get_current_track'
        r = requests.post(self.url, data=json.dumps(d))
        return r

    def restore_volume(self):
        self.set_volume(self.volume_high)

    def set_volume(self, percent):
        if self.is_playing:
            d = copy(_base_dict)
            d['method'] = 'core.mixer.set_volume'
            d['params'] = {'volume': percent}
            r = requests.post(self.url, data=json.dumps(d))


    # searches Spotify for keyword
    # if it's suspected that the keyword is just a single track, set isKeyWordTrack
    # similarly, if it's suspected that it's an album, set isKeywordAlbum
    # you may also set keyword to None for the broadest possible search on an artist_hint
    #   in this case you should also make sure isKeywordTrack and isKeywordAlbum are False, as you
    #   aren't actually supplying any Keyword at all
    # if you have artist information, supply it as an artist_hint
    # set returnRandomOrder to False if you wish to receive the first item that Spotify happens to return. Set it to True if you wish to pick a random result from the list
    # returns a JSON object of the form:
    # { name : <str>, artist_name : <str>, uri : <str> } 
    # returns an empty JSON object if no results 
    def search_any(self, keyword, isKeywordTrack=False, isKeywordAlbum=False, artist_hint=None, returnRandomOrder=False):
        d = copy(_base_dict)
        params = {}
        d['method'] = 'core.library.search'

        if isKeywordTrack and keyword: 
            LOGGER.debug("we're told keyword {} is apparently a track".format(keyword))
            params['track_name'] = keyword
        elif isKeywordAlbum and keyword: 
            LOGGER.debug("we're told keyword {} is apparently an album".format(keyword))
            params['album'] = keyword
        else:
            if keyword: 
                LOGGER.debug("we haven't been told whether keyword {} is an album or track".format(keyword))
                params['any'] = keyword

        if artist_hint is not None:
            LOGGER.debug("we're told the artist is {}".format(artist_hint))
            params['artist'] = artist_hint

        d['params'] = params

        LOGGER.debug("our query to mopidy is {}".format(d))
        r = requests.post(url, data=json.dumps(d))

        result = {}
        queryresults = r.json()["result"]
        LOGGER.debug(queryresults)
        for item in queryresults: 
            if 'albums' in item and (isKeywordAlbum or returnRandomOrder):
                albumIndex = 0
                if returnRandomOrder:
                    albumIndex = randint(0, len(item['albums']))
                    LOGGER.debug("Album index is {}".format(albumIndex))
                target = item['albums'][albumIndex]
                LOGGER.debug("length is {}".format(len(item['albums'])))
                if target['artists']:
                    result['artist_name'] = target['artists'][0]['name']
                if target['name']:
                    result['name'] = target['name']
                if target['uri']:
                    result['uri'] = target['uri']
            elif 'tracks' in item:
                target = item['tracks'][0]
                if target['artists']:
                    result['artist_name'] = target['artists'][0]['name']
                if target['name']:
                    result['name'] = target['name']
                if target['uri']:
                    result['uri'] = target['uri']

        return result

    def pause(self):                                                            
        LOGGER.debug("sending pause to mopidy")
        r = {}
        if self.is_playing:                                                     
            d = copy(_base_dict)                                                
            d['method'] = 'core.playback.pause'                                 
            r = requests.post(self.url, data=json.dumps(d))                     
        return r
                                                                                
    def resume(self):                                                           
        LOGGER.debug("sending resume to mopidy")
        r = {}
        if self.is_playing:                                                     
            d = copy(_base_dict)                                                
            d['method'] = 'core.playback.resume'                                
            r = requests.post(self.url, data=json.dumps(d))
        return r



#mopidy = Mopidy()
#result = mopidy.get_current_track().json()['result']
#if result: 
#        LOGGER.debug("currently playing {} by {}".format(result['album']['name'], \
#                result['album']['artists'][0]['name']))
#else:
#        LOGGER.debug("Nothing")

#mopidy = Mopidy()
#result = mopidy.search_any(None, artist_hint="mozart", isKeywordAlbum=False, returnRandomOrder=True)
#LOGGER.debug(result)

#mopidy = Mopidy()
#result = mopidy.pause()
#LOGGER.debug(result)

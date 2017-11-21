#!/usr/bin/python

import requests
from copy import copy
import json
from pprint import pprint
import pickle

MOPIDY_API = '/mopidy/rpc'

_base_dict = {'jsonrpc' : '2.0', 'id' : 1, 'params': {}}
url = 'http://localhost:6680' + MOPIDY_API

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
    # if you have artist information, supply it as an artist_hint
    # returns a JSON object of the form:
    # { name : <str>, artist_name : <str>, uri : <str> } 
    # returns an empty JSON object if no results 
    def search_any(self, keyword, isKeywordTrack=False, isKeywordAlbum=False, artist_hint=None):
        d = copy(_base_dict)
        params = {}
        d['method'] = 'core.library.search'

        if isKeywordTrack: 
            pprint("we're told keyword {} is apparently a track".format(keyword))
            params['track_name'] = keyword
        elif isKeywordAlbum: 
            pprint("we're told keyword {} is apparently an album".format(keyword))
            params['album'] = keyword
        else:
            pprint("we haven't been told whether keyword {} is an album or track".format(keyword))
            params['any'] = keyword

        if artist_hint is not None:
            pprint("we're told the artist is {}".format(artist_hint))
            params['artist'] = artist_hint

        d['params'] = params

        pprint("our query to mopdiy is {}".format(d))
        r = requests.post(url, data=json.dumps(d))

        result = {}
        queryresults = r.json()["result"]
        pprint(queryresults)
        for item in queryresults: 
            if 'albums' in item and isKeywordAlbum:
                target = item['albums'][0]
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


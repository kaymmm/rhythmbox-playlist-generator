#!/usr/bin/env python

"""
Copyright (c) 2022 Keith Miyake
Copyright (c) 2009 Wolfgang Steitz

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

"""

# Rhythmbox Playlist Generator
# v0.2.0
# 2022-02-05

import datetime
import inspect
from lxml import etree
import logging
import os
import random
import sys
from urllib.parse import unquote
import yaml

# Default paths, change them in the config file
filename = inspect.getframeinfo(inspect.currentframe()).filename
SCRIPT_DIR = os.path.dirname(os.path.abspath(filename))
RHYTHMBOX_DB = os.path.expanduser('~/.local/share/rhythmbox/rhythmdb.xml')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'rbplgen.yaml')
MUSIC_DIR = 'file://' + os.path.expanduser('~/Music/')
PLAYLIST_DIR = os.path.expanduser('~/Playlists/')

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class PLGen():
    config = None
    db_root = None
    songs = None

    def __init__(self,
                 config_file=CONFIG_FILE,
                 db_file=RHYTHMBOX_DB,
                 music_dir=MUSIC_DIR,
                 playlist_dir=PLAYLIST_DIR):
        if self.config is None:
            self.load_config(config_file)
        if os.path.isfile(self.config['rhythmdb']):
            db = etree.parse(self.config['rhythmdb'])
            self.db_root = db.getroot()

    def load_config(self, config_file):
        try:
            if os.path.isfile(config_file):
                with open(config_file, 'r') as f:
                    logging.debug('Configuration file opened: ' + config_file)
                    self.config = yaml.load(f, Loader=yaml.SafeLoader)
            else:
                logging.error('The configuration file does not exist at ' + config_file)
        except Exception as err:
            logging.error('There was an error loading the configuration file: {0}'.format(err))
            sys.exit('Fatal error. Exiting.')
        if not self.config:
            logging.error('Configuration not parsed correctly')
            logging.error('  make sure you have a "rbplgen.yaml" file configured.')
            sys.exit('Fatal error. Exiting.')
        else:
            logging.debug('Configuration file parsed.')
            if not 'playlists' in self.config:
                logging.error('No playlists defined in the configuration file.')
                sys.exit('Fatal error. Exiting.')
            if 'rhythmdb' in self.config:
                self.config['rhythmdb'] = os.path.expanduser(self.config['rhythmdb'])
            else:
                self.config['rhythmdb'] = RHYTHMBOX_DB
            if 'music_dir' in self.config:
                self.config['music_dir'] = 'file://' + os.path.expanduser(self.config['music_dir'])
            else:
                self.config['music_dir'] = MUSIC_DIR
            if 'playlist_dir' in self.config:
                self.config['playlist_dir'] = os.path.expanduser(self.config['playlist_dir'])
            else:
                self.config['playlist_dir'] = PLAYLIST_DIR
        logging.debug('Configuration:')
        logging.debug(self.config)

    def get_songs(self, xpath_query='//entry[@type="song"]'):
        songs = []
        for song in self.db_root.xpath('//entry[@type="song"]'):
            artist = song.find('artist')
            if artist is not None:
                artist = artist.text
            title = song.find('title')
            if title is not None:
                title = title.text
            duration = song.find('duration')
            if duration is not None:
                duration = int(duration.text)
            location = song.find('location').text
            file_size = int(song.find('file-size').text)
            genre = song.find('genre')
            if genre is not None:
                genre = genre.text
            rating = song.find('rating')
            if rating is not None:
                rating = float(rating.text)
            last_played = song.find('last-played')
            if last_played is not None:
                last_played = int(last_played.text)
            else:
                last_played = 0
            songs.append({
                'artist': artist,
                'title': title,
                'duration': duration,
                'genre': genre,
                'rating': rating,
                'location': location,
                'file_size': file_size,
                'last_played': last_played
                })
        return songs

    def get_playlist_query(self, playlist):
        if playlist is None:
            return []
        query = '//entry[@type="song"]'
        if 'genres' in playlist:
            logging.debug('Genres: ')
            logging.debug(playlist['genres'])
            genre_count = 0
            query += '/grenre['
            for g in playlist['genres']:
                operator = '='
                if g[0] == '!':
                    genre = g[1:-1]
                    operator = '!='
                else:
                    genre = g
                genre = genre.lower()
                if genre_count > 0:
                    query += ' or '
                # TODO: use variables for genre, need to figure out how to pass all variables to xpath
                query += 'contains(lower(text())' + operator + genre + ')'
                genre_count += 1
            query += ']/..'

        if 'rating_min' in playlist:
            logging.debug('Rating min: ' + str(playlist['rating_min']))
            query += '/rating[text()>=' + str(playlist['rating_min']) + ']/..'

        if 'rating_max' in playlist:
            logging.debug('Rating max: ' + str(playlist['rating_max']))
            query += '/rating[text()<=' + str(playlist['rating_max']) + ']/..'

        if 'rating' in playlist:
            logging.debug('Rating: ' + str(playlist['rating']))
            query += '/rating[text()=' + str(playlist['rating']) + ']/..'

        if 'weeks_since_played' in playlist:
            played_before = datetime.datetime.now() - \
                datetime.timedelta(weeks=int(playlist['weeks_since_played']))
            played_before = str(played_before.timestamp())
            query += '/last-played[text()<=' + played_before + ']/..'
        return query

    def get_song_matches(self, songlist, playlist):
        if playlist is None:
            return []

        if 'genres' in playlist:
            logging.debug('Genres: ')
            logging.debug(playlist['genres'])
            songlist = list(filter(
                lambda song:
                    self.strListInStr(playlist['genres'], song['genre']),
                songlist
            ))

        if 'rating_min' in playlist:
            songlist = list(filter(
                lambda song:
                    song['rating'] is not None and
                    song['rating'] >= playlist['rating_min'],
                songlist
            ))

        if 'rating_max' in playlist:
            songlist = list(filter(
                lambda song:
                    song['rating'] is not None and
                    song['rating'] <= playlist['rating_max'],
                songlist
            ))

        if 'rating' in playlist:
            songlist = list(filter(
                lambda song:
                    song['rating'] is not None and
                    song['rating'] == playlist['rating'],
                songlist
            ))

        if 'weeks_since_played' in playlist:
            played_before = datetime.datetime.now() - \
                datetime.timedelta(weeks=int(playlist['weeks_since_played']))
            played_before = int(played_before.timestamp())
            songlist = list(filter(
                lambda song:
                    song['last_played'] < played_before,
                songlist
            ))

        return songlist

    def create_playlist(self, songlist, playlist):
        logging.debug('Playlist Info: ')
        logging.debug(playlist)
        random.shuffle(songlist)
        file_size_sum = 0.0
        song_count = 0
        try:
            f = open(self.config['playlist_dir'] + playlist['filename'], 'w')
            logging.debug('Opened ' + playlist['filename'])
            print("#EXTM3U", file=f)

            for song in songlist:
                print("#EXTINF:" + str(song['duration'])
                    + "," + song['artist'] + " - " + song['title'], file=f)
                print(unquote(song['location'].replace(self.config['music_dir'], '/music/')), file=f)
                song_count += 1
                file_size_sum += song['file_size']
                if 'size' in playlist:
                    if file_size_sum >= (playlist['size'] * 1000000):
                        break
                if 'count' in playlist:
                    if song_count >= playlist['count']:
                        break
            f.close()
        except Exception as err:
            logging.error('There was an error creating ' + playlist['filename'] + ': {0}'.format(err))

        logging.info('Added ' + str(song_count) + ' songs to ' +
            playlist['filename'])

    def generate_playlists(self):
        random.seed()
        for pl in self.config['playlists']:
            # copying the whole songlist and filtering takes longer and more memory
            # self.songs = self.get_songs()
            # songlist = self.get_song_matches(self.songs, pl)
            # using xpath with a bunch of patterns seems to work faster with less memory
            song_query = self.get_playlist_query(pl)
            songlist = self.get_songs(song_query)
            self.create_playlist(songlist, pl)

    def strListInStr(self, compList, testStr):
        # Function to determine whether or not any of the strings in a given list
        # are contained within another string
        # if an item in compList begins with an `!` character, the function returns
        # false if testStr contains that string, even if it contains other items
        # in compList
        # if all of the items in compList begin with a `!` then return true if none
        # of the items in compList are found in testStr
        #  compList: list of strings to look for
        #  testStr: string to search within
        retVal = True
        retSet = False
        allBangs = True
        for s in compList:
            if s.startswith('!'):
                s = s[1:]
                bang = False
            else:
                bang = True
                allBangs = False
            if testStr and s.lower() in testStr.lower():
                retVal = bang is True and retVal
                retSet = True
        return retVal and (retSet or allBangs)

if __name__ == '__main__':
    plgen = PLGen()
    plgen.generate_playlists()

# :set ts=8 et sw=4 sts=4

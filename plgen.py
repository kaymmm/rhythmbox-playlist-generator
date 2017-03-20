#!/usr/bin/env python

"""
Copyright (c) 2017 Keith Miyake
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

from lxml import etree
from os.path import expanduser
from urllib.parse import unquote
import datetime
import random

# Change the following paths as appropriate for your system
user_home = expanduser('~')
db_file = user_home + '/.local/share/rhythmbox/rhythmdb.xml'
path_repl = 'file://' + user_home + '/Music/'
path_playlists = user_home + '/Playlists/'
playlist_names = ['sync.m3u',
                  'rnb.m3u',
                  'jazz.m3u'
                  ]


genre_filters = ["rock",
                 "alternative",
                 "house",
                 "pop",
                 "metal",
                 "electr",
                 "dance",
                 "grunge",
                 ]

# TODO: fix this
played_before = datetime.datetime.now() - datetime.timedelta(weeks=3)
played_before = str(int(played_before.timestamp()))

xpath_date_filter = " and (not(last-played) "\
        + "or ./last-played[.<" + played_before + "])"

xpath_and_cmd = ""
for filter in genre_filters:
    xpath_and_cmd += ' and ./genre[not(contains(text(),"' + filter + '"))]'

or_filters = [(),
              ("./genre[contains(text(),'r&b')]",
               "./genre[contains(text(),'soul')]",
               "./genre[contains(text(),'funk')]"
               ),
              ("./genre[contains(text(),'jazz')]",
               )]

size_limits = (2000000000, 1500000000, 1500000000)

# db_cmd_base = "SELECT Name, Title, Duration, Uri, FileSize "\
#     + "FROM CoreTracks "\
#     + "LEFT JOIN CoreArtists "\
#     + "ON CoreTracks.ArtistID=CoreArtists.ArtistID "\
#     + "WHERE TrackID in ("\
#     + "SELECT TrackID FROM CoreTracks WHERE "

xpath_base = '//entry[@type="song"' + xpath_date_filter

tree = etree.parse(db_file)
root = tree.getroot()

for j, playlist in enumerate(playlist_names):
    xpath_or_cmd = ""
    first_filter = True
    for filter in or_filters[j]:
        if first_filter:
            first_filter = False
            xpath_or_cmd = " and (" + filter
        else:
            xpath_or_cmd += " or " + filter
    if xpath_or_cmd:
        xpath_or_cmd += ") "
    # db_sub_cmd = xpath_and_cmd + date_filter + xpath_or_cmd
    xpath_cmd = xpath_base + xpath_or_cmd + "]"

    file_size_sum = 0.0
    f = open(path_playlists + playlist_names[j], 'w')
    print("#EXTM3U", file=f)

    full_list = []
    for song in root.xpath(xpath_cmd):
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
        full_list.append({
            'artist': artist,
            'title': title,
            'duration': duration,
            'location': location,
            'file_size': file_size
            })

    random.shuffle(full_list)
    for song in full_list:
        print("#EXTINF:" + str(song['duration'])
              + "," + song['artist'] + " - " + song['title'], file=f)
        print(unquote(song['location'].replace(path_repl, '')), file=f)
        file_size_sum += file_size
        if file_size_sum > size_limits[j]:
            break

    f.close()

# :set ts=8 et sw=4 sts=4

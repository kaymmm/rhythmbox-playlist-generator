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

# setup the playlists here:
playlists = [
        {
            'filename': 'sync.m3u',
            'size': 2000000000,
            'rating_min': 3,
            'genres': (
                "!rock",
                "!punk",
                "!alternative",
                "!house",
                "!pop",
                "!metal",
                "!electr",
                "!dance",
                "!grunge",
            )
        },
        {
            'filename': 'rnb.m3u',
            'size': 1500000000,
            'rating_min': 3,
            'genres': (
                "r&b",
                "funk",
                "soul",
                "!rock",
                "!punk",
                "!alternative",
                "!house",
                "!pop",
                "!metal",
                "!electr",
                "!dance",
                "!grunge",
            )
        },
        {
            'filename': 'jazz.m3u',
            'size': 1500000000,
            'genres': (
                "jazz",
                "!rock",
                "!punk",
                "!alternative",
                "!house",
                "!pop",
                "!metal",
                "!electr",
                "!dance",
                "!grunge",
            )
        }
]  # /playlists


# Date filter: only select songs that haven't been played
# within the last [3] weeks.
played_before = datetime.datetime.now() - datetime.timedelta(weeks=3)
played_before = str(int(played_before.timestamp()))

xpath_filter = '//entry[@type="song"'
xpath_filter += " and (not(last-played) "\
        + "or ./last-played[.<" + played_before + "])]"

# get the rhythmbox database (xml file)
tree = etree.parse(db_file)
root = tree.getroot()
full_list = []

# Copy filtered songs into full_list dictionary
for song in root.xpath(xpath_filter):
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
    full_list.append({
        'artist': artist,
        'title': title,
        'duration': duration,
        'genre': genre,
        'rating': rating,
        'location': location,
        'file_size': file_size
        })


# Function to determine whether or not any of the strings in a given list
# are contained within another string
# if an item in compList begins with an `!` character, the function returns
# false if testStr contains that string, even if it contains other items
# in compList
# if all of the items in compList begin with a `!` then return true if none
# of the items in compList are found in testStr
#  compList: list of strings to look for
#  testStr: string to search within
def strListInStr(compList, testStr):
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
        if s.lower() in testStr.lower():
            retVal = bang is True and retVal
            retSet = True
    return retVal and (retSet or allBangs)


# Loop through each of the playlists
for playlist in playlists:

    # Filter genres
    filtered_list = list(filter(
        lambda song: strListInStr(playlist['genres'], song['genre']),
        full_list
    ))

    # Filter ratings
    if 'rating_min' in playlist:
        filtered_list = list(filter(
            lambda song:
                song['rating'] is not None and
                song['rating'] >= playlist['rating_min'],
            filtered_list
        ))

    # Shuffle all the songs so that we select "random" tracks
    random.shuffle(filtered_list)

    file_size_sum = 0.0
    f = open(path_playlists + playlist['filename'], 'w')
    print("#EXTM3U", file=f)

    for song in filtered_list:
        print("#EXTINF:" + str(song['duration'])
              + "," + song['artist'] + " - " + song['title'], file=f)
        print(unquote(song['location'].replace(path_repl, '')), file=f)
        file_size_sum += file_size
        if file_size_sum > playlist['size']:
            break

    f.close()

# :set ts=8 et sw=4 sts=4

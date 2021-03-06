#!/usr/bin/env python

"""
Copyright (c) 2020 Keith Miyake
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
            'filename': 'mix.m3u',
            'size': 1600,     # Total size (in Mbytes) of songs to include
            'count': 350,     # Number of songs to include
                              # NOTE: The script will stop after first of
                              # 'size' or 'count' is reached
            'rating_min': 3,  # Songs must have minimum of X star rating
            'last_play': 6,   # Only songs not played in previous X weeks
            'genres': (       # Include songs matching these genres
                "!alternat",      # NOTE: items starting with "!" are excluded
                "!blues",
                "!burmese",
                "!dance",
                "!electr",
                "!grunge",
                "!house",
                "!instrument",
                "!jazz",
                "!metal",
                "!ondo",
                "!obon",
                "!pop",
                "!punk",
                "!rock",
                "!spoken",
                "!trip",
                "!wave",
                "!world"
            )
        },
        {
            'filename': 'rnb.m3u',
            'size': 1700,
            'rating_min': 3,
            'last_play': 4,
            'genres': (
                "r&b",
                "funk",
                "soul"
            )
        },
        {
            'filename': 'hiphop.m3u',
            'size': 1700,
            'rating_min': 3,
            'last_play': 4,
            'genres': (
                "hip-hop",
                "!instrument"
            )
        },
        {
            'filename': 'jazz.m3u',
            'size': 1000,
            'genres': (
                "jazz",
                "!nu",
                "!latin",
                "!acid",
                "!electr",
                "!hip"
            )
        }
]  # /playlists


xpath_filter = '//entry[@type="song"]'
# xpath_filter += " and (not(last-played) "\
#         + "or ./last-played[.<" + played_before + "])]"

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
    last_played = song.find('last-played')
    if last_played is not None:
        last_played = int(last_played.text)
    else:
        last_played = 0
    full_list.append({
        'artist': artist,
        'title': title,
        'duration': duration,
        'genre': genre,
        'rating': rating,
        'location': location,
        'file_size': file_size,
        'last_played': last_played
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
random.seed()
for playlist in playlists:

    # Filter genres
    filtered_list = list(filter(
        lambda song: strListInStr(playlist['genres'], song['genre']), full_list
    ))

    # Filter ratings
    if 'rating_min' in playlist:
        filtered_list = list(filter(
            lambda song:
                song['rating'] is not None and
                song['rating'] >= playlist['rating_min'],
            filtered_list
        ))

    # Date filter: only select songs that haven't been played
    # within the last x weeks.
    if 'last_play' in playlist:
        played_before = datetime.datetime.now() - \
            datetime.timedelta(weeks=int(playlist['last_play']))
        played_before = int(played_before.timestamp())
        filtered_list = list(filter(
            lambda song:
                song['last_played'] < played_before,
            filtered_list
            ))

    # Shuffle all the songs so that we select "random" tracks
    random.shuffle(filtered_list)

    file_size_sum = 0.0
    counter = 0
    f = open(path_playlists + playlist['filename'], 'w')
    print("#EXTM3U", file=f)

    for song in filtered_list:
        print("#EXTINF:" + str(song['duration'])
              + "," + song['artist'] + " - " + song['title'], file=f)
        print(unquote(song['location'].replace(path_repl, '')), file=f)
        counter += 1
        file_size_sum += song['file_size']
        if 'size' in playlist:
            if file_size_sum >= (playlist['size'] * 1000000):
                break
        if 'count' in playlist:
            if counter >= playlist['count']:
                break

    print("Added " + str(counter) + " songs to " +
          playlist['filename'])

    f.close()

# :set ts=8 et sw=4 sts=4

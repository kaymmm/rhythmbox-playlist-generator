# Rhythmbox Playlist Generator

A simple script to generate static smartish playlists from the rhythmbox database. Useful for automatic syncing of music to a phone with my android_sync script based on rsync!

Configure the playlists within the script itself, including the playlist names, playlist directory, smart playlist filters.

Currently uses a fixed set of genre filters that are applied to all of the playlists.

Relies on somewhat complex XPath filters to generate the playlists.

## TO-DO
 * Create a better system for nested OR filters that are ANDed to the playlist:
    * a AND b AND (c OR d) AND (e OR f)
    * consider storing all of the filters within a single list, if element is a list, then `or` them, else simply `and` with the rest of the elements
 * Use a JSON/YAML file to store playlist configurations
    * playlist: smart1
    * limit: 200
    * filters: ...


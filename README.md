# Rhythmbox Playlist Generator

A simple script to generate static smartish playlists from the rhythmbox database. Useful for automatic syncing of music to a phone or from Rhythmbox to Navidrome or similar.

Create and edit a `rbplgen.yaml` file (can use `sample_rbplgen.yaml` as a template) containing configuration options and the list of playlists

Relies on somewhat complex XPath filters to generate the playlists.

## TO-DO

- [ ]Create a better system for nested OR filters that are ANDed to the playlist:
  - [ ] a AND b AND (c OR d) AND (e OR f)
  - [ ] consider storing all of the filters within a single list, if element is a list, then `or` them, else simply `and` with the rest of the elements
- [X] Use a ~~JSON~~/YAML file to store playlist configurations
- [X] Use fancier Xpath queries and don't copy the whole library to a dict

## Version History

v1.0.0: Overhauled the filtering system and added config files (breaking changes)

v0.1.1: Dependency updates

v0.1.0: Initial script

# Rotten Bites

[![Build Status](https://travis-ci.org/philipbl/rotten_bites.svg?branch=master)](https://travis-ci.org/philipbl/rotten_bites) [![Coverage Status](https://coveralls.io/repos/github/philipbl/rotten_bites/badge.svg?branch=master)](https://coveralls.io/github/philipbl/rotten_bites?branch=master)

A small utility for checking for [bit rot][bit_rot]. This project is heavily influenced by [chkbit][chkbit] and [bitrot][bitrot]. Both projects had things I liked about them and other things that I didn't. I took what I liked and made something myself.

The focus of Rotten Bites is scalability and speed. To achieve this, small files (`.bit_check`) are placed in every directory. I know, no one wants a ["bunch of turdy files sprinkled all over your hard drive"][atp], but in my opinion it is the best way to allow for flexibility (folders can be moved around without any problem because all paths are relative to that directory) and scalability (having one central database with all files stored does not scale well).

There are two components to Rotten Bites: the CLI and library. I designed Rotten Bites to be callback based so it makes it easy to extend. See the CLI (`rotten_bites/__main__.py`) and rot_check.py, for examples.

## Install

```
pip install rotten_bites
```

## Usage

```
Usage: rotten_bites [OPTIONS] DIRECTORY

  Given a directory, rotten bites calculates the sha1 hash of every file and
  stores it in .bit_check files. Once stored, subsequent checks will see if
  the hash has changed, detecting bit rot.

  Status codes:

      'E'     error, sha1 mismatch

      'a'     add to index

      'u'     update sha1

      ' '     not modified (shown only with verbose)

      '?'     could not read file (permission denied or file no longer
              exists)

Options:
  --delete                Delete all .bit_check files.
  -n, --dry-run           Run without making any changes. No .bit_check files
                          are created or updated
  --ignore-list FILENAME  List of files and folders to ignore. Similar syntax
                          to .gitignore files. "-" can be used to read from
                          stdin.
  -q, --quiet             Turn off all output except for hash errors.
  -v, --verbose           Display all files that are scanned, even if they
                          haven't changed
  --verify                Verify hashes without updating.
  --help                  Show this message and exit.
```


[bit_rot]: https://en.wikipedia.org/wiki/Data_degradation
[chkbit]: https://github.com/laktak/chkbit
[bitrot]: https://github.com/ambv/bitrot/
[atp]: http://atp.fm/episodes/176

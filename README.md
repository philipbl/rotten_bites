# Rotten Bites

A small utility for checking for bit rot. This project is influnced by [`chkbit`][chkbit] and [`bitrot`][bitrot]. Both projects had things I liked about them and other things that I didn't. I took what I liked and made something myself.

The focus of Rotten Bites is scalability and speed. To achieve this, small files (`.bit_check`) are placed in every directory. I know, no one wants a "bunch of turdy files sprinkled all over your hard drive", but it is the best way to allow for flexibility (folders can be moved around without any problem because all paths are relative to that directory) and scalability (having one central database with all paths does not scale well).

## Install

```
pip install rotten_bites
```

## Usage

```
Usage: __main__.py [OPTIONS] DIRECTORY

  Given a directory, it calculates the sha1 hash of every file and stores
  it. Once stored, subsequent checks will see if the hash has changed,
  detecting bit rot.

  Status codes:

      'E'     error, sha1 mismatch

      'a'     add to index

      'u'     update sha1

      ' '     not modified (with verbose)

      '?'     could not read file (permission denied or file no longer
      exists)

Options:
  --delete                Delete all .bit_check files.
  -n, --dry-run           Run without making any changes.
  --ignore-list FILENAME  List of files and folders to ignore. Similar syntax
                          to .gitignore files. "-" can be used to read from
                          stdin.
  -q, --quiet             Turn off all output except for hash errors.
  -v, --verbose           Display all files that are scanned, even if they
                          haven't changed
  --verify                Verify hashes without updating.
  --help                  Show this message and exit.
```

## Example


[chkbit]: https://github.com/laktak/chkbit
[bitrot]: https://github.com/ambv/bitrot/

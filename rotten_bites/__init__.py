"""Utility for detecting if bit rot in files."""
import errno
import hashlib
import os
import os.path
from enum import Enum

try:
    import json
    from json.decoder import JSONDecodeError  # 3.5
except ImportError:  # pragma: no cover
    JSONDecodeError = ValueError  # 3.4

import pathspec

DEFAULT_CHUNK_SIZE = 16384
CHECK_FILE = ".bit_check"


class Result(Enum):
    """Describes how a file has changed."""

    nothing = 0
    updated = 1
    added = 2
    error = 3


class File():
    """
    Represents everything that I care about in a file.

    The only things I care about are the name, path, when the file was modified
    and the hash value of the file.
    """

    def __init__(self, name, path, mtime, hash_value=None):
        """
        Create a file object.

        If a hash value is not provided, it calculates the hash itself.
        """
        self.name = name
        self.path = path
        self.mtime = mtime
        self.hash = hash_value or self.rehash()

    @staticmethod
    def from_json(path, obj):
        """Convert json object to File objects."""
        return {k: File(k, path, v[0], v[1]) for k, v in obj.items()}

    def rehash(self, chunk_size=DEFAULT_CHUNK_SIZE):
        """Calculate the hash of this file."""
        path = os.path.join(self.path, self.name)
        digest = hashlib.sha1()

        with open(path, 'rb') as file:
            data = file.read(chunk_size)
            while data:
                digest.update(data)
                data = file.read(chunk_size)
        return digest.hexdigest()

    def to_json(self):
        """Convert File object to json."""
        return [self.mtime, self.hash]

    def __repr__(self):  # pragma: no cover
        """String representation of File."""
        return "<File name:{}, path:{}, mtime:{}, hash:{}".format(
            self.name, self.path, self.mtime, self.hash)


def walk_dir(directory, ignore=None, follow_links=False):
    """
    My version of os.walk.

    It takes care of ignoring files that should be ignored and produces a
    generator.
    """
    for path, _, files in os.walk(directory, followlinks=follow_links):

        if ignore is not None:
            files = ignore.match_files(
                (os.path.join(path, f) for f in files))
            files = (os.path.basename(f) for f in files)
            files = sorted(files)

        yield path, files


def get_stat(follow_links=False):
    """Return appropriate stat function."""
    func = os.lstat if follow_links else os.stat
    return func


def walk_files(directory, files, follow_links=False):
    """Walk through each file, stat-ing them."""
    stat = get_stat(follow_links)

    for file in files:
        try:
            stat_data = stat(os.path.join(directory, file))
        except OSError as exception:
            # For some reason we couldn't stat the file. I will look at why
            # later.
            yield file, None, exception
            continue

        yield file, stat_data, None


def read_bitcheck(path):
    """Read file that contains file hash information."""
    try:
        with open(os.path.join(path, CHECK_FILE)) as file:
            return json.load(
                file, object_hook=lambda obj: File.from_json(path, obj))
    except (FileNotFoundError, JSONDecodeError):
        return {}


def save_bitcheck(path, data):
    """Save file that contains file hash information."""
    with open(os.path.join(path, CHECK_FILE), 'w') as file:
        json.dump(data, file, sort_keys=True, default=lambda x: x.to_json())


def compare_files(old_file, new_file):
    """
    Determine how a two files have changed.

    If there is no old version of a file, then the file was added.
    If the hash of the old and new files match, then nothing has happened.
    If the hash of the old and new files does not match, but the modified time
    has changed, then the file has been updated.
    If the hash of the old and new files does not match and the modified time
    has not changed, then there is an error.
    """
    if old_file is None:
        # Don't have a hash for this file, so it is new
        return Result.added

    if old_file.hash != new_file.hash:
        if old_file.mtime == new_file.mtime:
            return Result.error
        else:
            return Result.updated

    return Result.nothing


def convert_ignore_list(lst):
    """Convert an ignore list to an accept list."""
    def create_ignore_list():
        """Generator for creating ignore list."""
        yield '*'  # Accept everything
        yield '!*{}'.format(CHECK_FILE)  # Ignore my files

        for line in lst:
            if line[0] == '!':
                yield line[1:]
            else:
                yield '!{}'.format(line)

    return pathspec.PathSpec.from_lines('gitignore', create_ignore_list())


# pylint: disable=too-many-arguments
def handle_error(error, path, file, old_file, file_error_cb, missing_cb):
    """Deal with file error."""
    # Check what kind of error it is
    if error.errno == errno.EACCES:
        # We don't have access to the file
        file_error_cb(path, file, error)
    elif error.errno == errno.ENOENT:
        # The file was deleted
        if old_file is not None:
            missing_cb(old_file)
    else:
        # Don't know what else to do with it
        raise error


# pylint: disable=too-many-arguments,too-many-locals
def run(directory, added_cb=lambda x: x, updated_cb=lambda x: x,
        nothing_cb=lambda x: x, file_error_cb=lambda p, f, e: p,
        hash_error_cb=lambda old, new: old, missing_cb=lambda x: x,
        ignore=None, just_verify=False, dry_run=False):
    """Run rotten bits, checking for bit errors."""
    ignore = convert_ignore_list(ignore or [])

    for path, files in walk_dir(directory, ignore):
        data = read_bitcheck(path)

        for file, stat, error in walk_files(path, files):
            old_file = data.get(file)

            # Check if any errors occurred while walking the file
            if error:
                handle_error(error, path, file, old_file, file_error_cb,
                             missing_cb)
                continue

            try:
                new_file = File(file, path, stat.st_mtime)
            except FileNotFoundError:
                # The file was deleted between when the file list was created
                # and now
                if old_file is not None:
                    # We only care about this if the old file existed
                    missing_cb(old_file)
                continue

            result = compare_files(old_file, new_file)

            if result == Result.updated and not just_verify:
                old_file.mtime = new_file.mtime
                old_file.hash = new_file.hash
                updated_cb(old_file)

            elif result == Result.added and not just_verify:
                data[file] = new_file
                added_cb(new_file)

            elif result == Result.nothing:
                nothing_cb(old_file)

            elif result == Result.error:
                hash_error_cb(old_file, new_file)

        for missing in set(data.keys()) - set(files):
            missing_cb(data.pop(missing))

        if not dry_run:
            save_bitcheck(path, data)


def delete_check_files(directory):
    """Delete all metafiles for Rotten Bites."""
    for path, files in walk_dir(directory):
        if CHECK_FILE in files:
            os.remove(os.path.join(path, CHECK_FILE))

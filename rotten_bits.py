import errno
import hashlib
import json
import os
import os.path
from enum import Enum

DEFAULT_CHUNK_SIZE = 16384
CHECK_FILE = ".bit_check"


class Result(Enum):
    nothing = 0
    updated = 1
    added = 2
    error = 3


class File():
    def __init__(self, name, path, mtime, hash=None):
        self.name = name
        self.path = path
        self.mtime = int(mtime)
        self.hash = hash or self.rehash()

    @staticmethod
    def from_JSON(path, obj):
        return {k: File(k, path, v[0], v[1]) for k, v in obj.items()}

    def rehash(self):
        return hash_func(os.path.join(self.path, self.name))

    def to_JSON(self):
        return [self.mtime, self.hash]

    def __repr__(self):
        return "<File name:{}, path:{}, mtime:{}, hash:{}".format(
            self.name, self.path, self.mtime, self.hash)


def hash_func(path, chunk_size=DEFAULT_CHUNK_SIZE):
    digest = hashlib.sha1()
    with open(path, 'rb') as f:
        d = f.read(chunk_size)
        while d:
            digest.update(d)
            d = f.read(chunk_size)
    return digest.hexdigest()


def walk_dir(directory, ignore=None, follow_links=False):
    for path, _, files in os.walk(directory, followlinks=follow_links):
        yield path, files


def walk_files(directory, files, follow_links=False):
    stat = os.lstat if follow_links else os.stat

    for f in files:
        file_path = os.path.join(directory, f)

        try:
            st = stat(file_path)
        except OSError as e:
            if e.errno in [errno.EACCES, errno.ENOENT]:
                # Either we don't have access to the file or it doesn't exist
                # anymore
                yield f, None, e
            else:
                raise

        yield f, st, None


def read_bitcheck(path):
    try:
        with open(os.path.join(path, CHECK_FILE)) as f:
            return json.load(f, object_hook=lambda obj: File.from_JSON(path, obj))
    except FileNotFoundError:
        return {}


def save_bitcheck(path, data):
    with open(os.path.join(path, CHECK_FILE), 'w') as f:
        json.dump(data, f, default=lambda x: x.to_JSON())


def compare_files(old_file, new_file):
    if old_file is None:
        # Don't have a hash for this file, so it is new
        return Result.added

    if old_file.hash != new_file.hash:
        if old_file.mtime == new_file.mtime:
            return Result.error
        else:
            return Result.updated

    else:
        return Result.nothing


def run(directory, added_cb=lambda x: x, updated_cb=lambda x: x,
        nothing_cb=lambda x: x, file_error_cb=lambda x: x,
        hash_error_cb=lambda x: x, deleted_cb=lambda x: x, ignore=None,
        just_verify=False):

    ignore = ignore or set()
    ignore.add(CHECK_FILE)

    for path, files in walk_dir(directory):
        data = read_bitcheck(path)

        for file, stat, error in walk_files(path, files):
            if file in ignore:
                continue

            if error:
                file_error_cb(path, file, error)
                continue

            new_file = File(file, path, stat.st_mtime)
            old_file = data.get(file)
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

        for removed in (set(data.keys()) - set(files)):
            removed_cb(data.pop(removed))

        # TODO: What happens if you scan a file and then later ignore it?
        # It should be removed from the list!

        save_bitcheck(path, data)


def delete_check_files(directory):
    for path, files in walk_dir(directory):
        if CHECK_FILE in files:
            os.remove(os.path.join(path, CHECK_FILE))

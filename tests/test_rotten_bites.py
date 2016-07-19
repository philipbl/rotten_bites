import errno
import os
import shutil
import unittest
import unittest.mock

import pathspec
from pyfakefs import fake_filesystem_unittest

import rotten_bites

# Test for unicode in file names


class TestRottenBites(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

        self.file_1_hash = 'dc27719b974abe67f9c744549cfbffd09b7dc1ee'

    def tearDown(self):
        pass

    def test_File(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")

        name = "file_1.txt"
        path = ""
        mtime = 1000
        file = rotten_bites.File(name, path, mtime)

        self.assertEqual(file.name, name)
        self.assertEqual(file.path, path)
        self.assertEqual(file.mtime, mtime)
        self.assertEqual(file.hash, self.file_1_hash)

        self.assertEqual(file.to_json(), [mtime, self.file_1_hash])

    def test_File_from_json(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")

        name = "file_1.txt"
        path = ""
        mtime = 1000

        data = {name: [mtime, self.file_1_hash]}
        data = rotten_bites.File.from_json(path, data)

        self.assertTrue(name in data)
        file = data[name]

        self.assertEqual(file.name, name)
        self.assertEqual(file.path, path)
        self.assertEqual(file.mtime, mtime)
        self.assertEqual(file.hash, self.file_1_hash)

    def test_hash_func(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")

        result = rotten_bites.hash_func('file_1.txt')
        self.assertEqual(result, self.file_1_hash)

    def test_walk_dir(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/1/i/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('a/1/i/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('a/1/ii/file_4.txt', contents="file_4\n")

        gen = rotten_bites.walk_dir('.')

        path, files = next(gen)
        self.assertEqual(path, '.')
        self.assertEqual(files, ['file_1.txt'])

        path, files = next(gen)
        self.assertEqual(path, 'a')
        self.assertEqual(files, [])

        path, files = next(gen)
        self.assertEqual(path, 'a/1')
        self.assertEqual(files, [])

        path, files = next(gen)
        self.assertEqual(path, 'a/1/i')
        self.assertEqual(files, ['file_2.txt', 'file_3.txt'])

        path, files = next(gen)
        self.assertEqual(path, 'a/1/ii')
        self.assertEqual(files, ['file_4.txt'])

    def test_walk_dir_deleted_dir(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('b/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('b/file_4.txt', contents="file_4\n")
        self.fs.CreateFile('c/file_5.txt', contents="file_4\n")

        gen = rotten_bites.walk_dir('.')

        path, files = next(gen)
        self.assertEqual(path, '.')
        self.assertEqual(files, ['file_1.txt'])

        path, files = next(gen)
        self.assertEqual(path, 'a')
        self.assertEqual(files, ['file_2.txt'])

        # folder was deleted
        shutil.rmtree('b')

        path, files = next(gen)
        self.assertEqual(path, 'c')
        self.assertEqual(files, ['file_5.txt'])

    def test_walk_dir_deleted_file(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('a/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('a/file_4.txt', contents="file_4\n")
        self.fs.CreateFile('a/file_5.txt', contents="file_4\n")

        gen = rotten_bites.walk_dir('.')

        path, files = next(gen)
        self.assertEqual(path, '.')
        self.assertEqual(files, ['file_1.txt'])

        os.remove('a/file_4.txt')

        path, files = next(gen)
        self.assertEqual(path, 'a')
        self.assertEqual(files, ['file_2.txt', 'file_3.txt', 'file_5.txt'])

    def test_walk_dir_ignore(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('a/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('a/file_4.txt', contents="file_4\n")
        self.fs.CreateFile('a/file_5.txt', contents="file_4\n")

        ignore = pathspec.PathSpec.from_lines(
            'gitignore', ['*', '!*.bit_check', '!file_4.txt'])
        gen = rotten_bites.walk_dir('.', ignore=ignore)

        path, files = next(gen)
        self.assertEqual(path, '.')
        self.assertEqual(files, ['file_1.txt'])

        path, files = next(gen)
        self.assertEqual(path, 'a')
        self.assertEqual(files, ['file_2.txt', 'file_3.txt', 'file_5.txt'])

    def test_walk_files(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('file_2.txt', contents="file_2\n")

        files = ['file_1.txt', 'file_2.txt']
        gen = rotten_bites.walk_files('.', files)

        file, st, error = next(gen)
        self.assertEqual(file, files[0])
        self.assertNotEqual(st.st_mtime, None)
        self.assertEqual(error, None)

        file, st, error = next(gen)
        self.assertEqual(file, files[1])
        self.assertNotEqual(st.st_mtime, None)
        self.assertEqual(error, None)

    def test_walk_files_no_files(self):
        files = ['file_1.txt', 'file_2.txt']
        gen = rotten_bites.walk_files('.', files)

        file, st, error = next(gen)
        self.assertEqual(file, files[0])
        self.assertEqual(st, None)
        self.assertNotEqual(error, None)

    def test_walk_files_deleted_file(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('file_2.txt', contents="file_2\n")

        files = ['file_1.txt', 'file_2.txt']
        gen = rotten_bites.walk_files('.', files)

        file, st, error = next(gen)
        self.assertEqual(file, files[0])
        self.assertNotEqual(st.st_mtime, None)
        self.assertEqual(error, None)

        os.remove('file_2.txt')

        file, st, error = next(gen)
        self.assertEqual(file, files[1])
        self.assertEqual(st, None)
        self.assertNotEqual(error, None)

    def test_read_bitcheck(self):
        self.fs.CreateFile('.bit_check',
                           contents='{"file_1.txt": [1234, "abcd"]}\n')

        result = rotten_bites.read_bitcheck('.')

        self.assertTrue('file_1.txt' in result)
        self.assertEqual(len(result), 1)

        file = result['file_1.txt']
        self.assertEqual(file.name, 'file_1.txt')
        self.assertEqual(file.path, '.')
        self.assertEqual(file.hash, 'abcd')
        self.assertEqual(file.mtime, 1234)

    def test_read_bitcheck_no_file(self):
        result = rotten_bites.read_bitcheck('.')
        self.assertEqual(result, {})

    def test_read_bitcheck_bad_json(self):
        self.fs.CreateFile('.bit_check', contents='not json\n')

        result = rotten_bites.read_bitcheck('.')
        self.assertEqual(result, {})

    def test_save_bitcheck(self):
        file_1 = rotten_bites.File("file_1.txt", ".", 1234, hash_value="abc")
        rotten_bites.save_bitcheck('.', {"file_1.txt": file_1})
        self.assertTrue(os.path.exists('.bit_check'))

    def test_compare_files(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")

        file_1 = rotten_bites.File("file_1.txt", ".", 1234)
        file_2 = rotten_bites.File("file_1.txt", ".", 1234)

        # New file
        result = rotten_bites.compare_files(None, file_1)
        self.assertEqual(result, rotten_bites.Result.added)

        # Nothing changed
        result = rotten_bites.compare_files(file_1, file_2)
        self.assertEqual(result, rotten_bites.Result.nothing)

        # Error (hash changed, but time didn't)
        file_2.hash = 'different_hash'
        result = rotten_bites.compare_files(file_1, file_2)
        self.assertEqual(result, rotten_bites.Result.error)

        # Updated (time and hash changed)
        file_2.mtime = 5678
        file_2.hash = 'different_hash'
        result = rotten_bites.compare_files(file_1, file_2)
        self.assertEqual(result, rotten_bites.Result.updated)

    def test_convert_ignore_list(self):
        ignore_list = [
            "file1",
            "file2",
            "!file3"
        ]

        new_ignore_list = rotten_bites.convert_ignore_list(ignore_list)
        self.assertEqual(list(new_ignore_list),
                         ["*", "!*.bit_check", "!file1", "!file2", "file3"])

    def test_run(self):
        """
        Run without any callbacks passed in.

        This makes sure that the signatures of the default call
        backs are correct.
        """
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/1/i/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('a/1/i/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('a/1/ii/file_4.txt', contents="file_4\n")

        # Should only have added files
        rotten_bites.run('.')

        # Should only have nothing files
        rotten_bites.run('.')

        # Update one of the files and add another file
        self.fs.CreateFile('a/2/file_5.txt', contents="file_4\n")

        # Should only have one added and the rest nothing
        rotten_bites.run('.')

        # Update file
        with open('file_1.txt', 'w') as f:
            f.write("updated\n")

        # Should only have one updated
        rotten_bites.run('.')

        # Bit rot
        st = os.stat('file_1.txt')
        mtime_ns = st.st_mtime
        atime_ns = st.st_atime
        with open('file_1.txt', 'w') as f:
            f.write("bit rot\n")
        os.utime('file_1.txt', (atime_ns, mtime_ns))

        # Should only have one error
        rotten_bites.run('.')

        # Delete file
        os.remove('file_1.txt')

        # Should only have one deleted
        rotten_bites.run('.')

    def test_run_with_cb(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('a/1/i/file_2.txt', contents="file_2\n")
        self.fs.CreateFile('a/1/i/file_3.txt', contents="file_3\n")
        self.fs.CreateFile('a/1/ii/file_4.txt', contents="file_4\n")

        added = []
        updated = []
        nothing = []
        file_error = []
        hash_error = []
        missing = []

        params = {
            'added_cb': lambda x: added.append(x),
            'updated_cb': lambda x: updated.append(x),
            'nothing_cb': lambda x: nothing.append(x),
            'file_error_cb': lambda x: file_error.append(x),
            'hash_error_cb': lambda old, new: hash_error.append(new),
            'missing_cb': lambda x: missing.append(x),
            'ignore': None,
            'just_verify': False,
            'dry_run': False
        }

        rotten_bites.run('.', **params)

        self.assertEqual(len(added), 4)
        self.assertEqual([f.name for f in added],
                         ['file_1.txt', 'file_2.txt', 'file_3.txt', 'file_4.txt'])
        self.assertEqual(len(updated), 0)
        self.assertEqual(len(nothing), 0)
        self.assertEqual(len(file_error), 0)
        self.assertEqual(len(hash_error), 0)
        self.assertEqual(len(missing), 0)

        added = []
        rotten_bites.run('.', **params)

        self.assertEqual(len(added), 0)
        self.assertEqual(len(updated), 0)
        self.assertEqual(len(nothing), 4)
        self.assertEqual([f.name for f in nothing],
                         ['file_1.txt', 'file_2.txt', 'file_3.txt', 'file_4.txt'])
        self.assertEqual(len(file_error), 0)
        self.assertEqual(len(hash_error), 0)
        self.assertEqual(len(missing), 0)

        # Update one of the files and add another file
        self.fs.CreateFile('a/2/file_5.txt', contents="file_4\n")

        with open('file_1.txt', 'w') as f:
            f.write("More test\n")

        nothing = []
        rotten_bites.run('.', **params)

        self.assertEqual(len(added), 1)
        self.assertEqual([f.name for f in added],
                         ['file_5.txt'])
        self.assertEqual(len(updated), 1)
        self.assertEqual([f.name for f in updated],
                         ['file_1.txt'])
        self.assertEqual(len(nothing), 3)
        self.assertEqual([f.name for f in nothing],
                         ['file_2.txt', 'file_3.txt', 'file_4.txt'])
        self.assertEqual(len(file_error), 0)
        self.assertEqual(len(hash_error), 0)
        self.assertEqual(len(missing), 0)

        # Delete a file
        os.remove('a/2/file_5.txt')

        # Cause bit rot
        st = os.stat('file_1.txt')
        mtime_ns = st.st_mtime
        atime_ns = st.st_atime
        with open('file_1.txt', 'w') as f:
            f.write("bit rot\n")
        os.utime('file_1.txt', (atime_ns, mtime_ns))

        added = []
        updated = []
        nothing = []
        rotten_bites.run('.', **params)

        self.assertEqual(len(added), 0)
        self.assertEqual(len(updated), 0)
        self.assertEqual(len(nothing), 3)
        self.assertEqual([f.name for f in nothing],
                         ['file_2.txt', 'file_3.txt', 'file_4.txt'])
        self.assertEqual(len(file_error), 0)
        self.assertEqual(len(hash_error), 1)
        self.assertEqual([f.name for f in hash_error],
                         ['file_1.txt'])
        self.assertEqual(len(missing), 1)
        self.assertEqual([f.name for f in missing],
                         ['file_5.txt'])

    def test_run_with_delete(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('file_2.txt', contents="file_2\n")
        self.fs.CreateFile('file_3.txt', contents="file_3\n")

        error_list = []
        first = True

        def error_cb(path, file, error):
            # print(path, file, error)
            error_list.append((path, file, error))

        def added_cb(file):
            nonlocal first

            if first:
                os.remove('file_2.txt')
            first = False

        rotten_bites.run('.', added_cb=added_cb, file_error_cb=error_cb)

        self.assertEqual(len(error_list), 1)
        self.assertEqual(error_list[0][1], 'file_2.txt')

    def test_run_with_exception(self):
        self.fs.CreateFile('file_1.txt', contents="file_1\n")

        def mock_stat(path):
            raise OSError(100, "Error")

        with unittest.mock.patch('rotten_bites.get_stat',
                                 return_value=mock_stat):
            with self.assertRaises(OSError):
                rotten_bites.run('.')

    def test_delete_check_files(self):
        # Delete with no check file
        rotten_bites.delete_check_files('.')  # Nothing should happen

        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.fs.CreateFile('.bit_check', contents="stuff\n")

        rotten_bites.delete_check_files('.')
        self.assertFalse(os.path.exists('.bit_check'))

        self.fs.CreateFile('.bit_check', contents="stuff\n")
        self.fs.CreateFile('a/.bit_check', contents="stuff\n")
        self.fs.CreateFile('a/b/.bit_check', contents="stuff\n")
        self.fs.CreateFile('a/b/c/.bit_check', contents="stuff\n")
        self.fs.CreateFile('a/b/c/.bit_checker', contents="stuff\n")
        self.fs.CreateFile('a/b/c/bit_check', contents="stuff\n")

        rotten_bites.delete_check_files('.')
        for path, _, files in os.walk('.'):
            self.assertFalse('.bit_check' in files)

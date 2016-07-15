import unittest
from pyfakefs import fake_filesystem_unittest

import rotten_bites

# Test for unicode in file names

class TestRottenBites(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()

        self.fs.CreateFile('file_1.txt', contents="file_1\n")
        self.file_1_hash = 'dc27719b974abe67f9c744549cfbffd09b7dc1ee'


    def tearDown(self):
        pass


    def test_File(self):
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
        result = rotten_bites.hash_func('file_1.txt')
        self.assertEqual(result, self.file_1_hash)

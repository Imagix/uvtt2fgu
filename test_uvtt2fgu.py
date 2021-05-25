#!/usr/bin/env python3

from pathlib import Path
import unittest
import uvtt2fgu


class TestComposeFilePaths(unittest.TestCase):
    def test_fileonly(self) -> None:
        '''Test with a filename, and no output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('filename.dd2vtt'), None)
        self.assertEqual(uvttpath, Path('filename.dd2vtt'))
        self.assertEqual(pngpath, Path('filename.png'))
        self.assertEqual(jpgpath, Path('filename.jpg'))
        self.assertEqual(xmlpath, Path('filename.xml'))

    def test_filewithpath(self) -> None:
        '''Test with a filename with a relative path, and no output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('abc/filename.dd2vtt'), None)
        self.assertEqual(uvttpath, Path('abc/filename.dd2vtt'))
        self.assertEqual(pngpath, Path('filename.png'))
        self.assertEqual(jpgpath, Path('filename.jpg'))
        self.assertEqual(xmlpath, Path('filename.xml'))

    def test_filewithoutputpath(self) -> None:
        '''Test with a filename, and an output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('filename.dd2vtt'), Path('xyz'))
        self.assertEqual(uvttpath, Path('filename.dd2vtt'))
        self.assertEqual(pngpath, Path('xyz/filename.png'))
        self.assertEqual(jpgpath, Path('xyz/filename.jpg'))
        self.assertEqual(xmlpath, Path('xyz/filename.xml'))

    def test_filewithpathwithoutputpath(self) -> None:
        '''Test with a filename with a relative path, and an output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('abc/filename.dd2vtt'), Path('xyz'))
        self.assertEqual(uvttpath, Path('abc/filename.dd2vtt'))
        self.assertEqual(pngpath, Path('xyz/filename.png'))
        self.assertEqual(jpgpath, Path('xyz/filename.jpg'))
        self.assertEqual(xmlpath, Path('xyz/filename.xml'))


if __name__ == '__main__':
    unittest.main()

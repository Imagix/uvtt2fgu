#!/usr/bin/env python3

import argparse
from pathlib import Path
import unittest
import uvtt2fgu


class TestComposeFilePaths(unittest.TestCase):
    def setUp(self) -> None:
        uvtt2fgu.loadConfigData(None)
        uvtt2fgu.__dict__['configData'].xmlpath = '.'
        uvtt2fgu.configData.pngpath = '.'
        uvtt2fgu.configData.jpgpath = '.'
        return super().setUp()

    def test_fileonly(self) -> None:
        '''Test with a filename, and no output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('filename.dd2vtt'))
        self.assertEqual(uvttpath, Path('filename.dd2vtt'))
        self.assertEqual(pngpath, Path('filename.png'))
        self.assertEqual(jpgpath, Path('filename.jpg'))
        self.assertEqual(xmlpath, Path('filename.xml'))

    def test_filewithpath(self) -> None:
        '''Test with a filename with a relative path, and no output directory specified'''
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('abc/filename.dd2vtt'))
        self.assertEqual(uvttpath, Path('abc/filename.dd2vtt'))
        self.assertEqual(pngpath, Path('filename.png'))
        self.assertEqual(jpgpath, Path('filename.jpg'))
        self.assertEqual(xmlpath, Path('filename.xml'))

    def test_filewithoutputpath(self) -> None:
        '''Test with a filename, and an output directory specified'''
        uvtt2fgu.configData.xmlpath = 'd1x'
        uvtt2fgu.configData.jpgpath = 'd2x'
        uvtt2fgu.configData.pngpath = 'd3x'
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('filename.dd2vtt'))
        self.assertEqual(uvttpath, Path('filename.dd2vtt'))
        self.assertEqual(pngpath, Path('d3x/filename.png'))
        self.assertEqual(jpgpath, Path('d2x/filename.jpg'))
        self.assertEqual(xmlpath, Path('d1x/filename.xml'))

    def test_filewithpathwithoutputpath(self) -> None:
        '''Test with a filename with a relative path, and an output directory specified'''
        uvtt2fgu.configData.xmlpath = 'd1x'
        uvtt2fgu.configData.jpgpath = 'd2x'
        uvtt2fgu.configData.pngpath = 'd3x'
        (uvttpath, pngpath, jpgpath, xmlpath) = uvtt2fgu.composeFilePaths(
            Path('abc/filename.dd2vtt'))
        self.assertEqual(uvttpath, Path('abc/filename.dd2vtt'))
        self.assertEqual(pngpath, Path('d3x/filename.png'))
        self.assertEqual(jpgpath, Path('d2x/filename.jpg'))
        self.assertEqual(xmlpath, Path('d1x/filename.xml'))

class TestPortalAdjust(unittest.TestCase):
    def test_percent(self) -> None:
        '''Test the custom argument parser'''
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', nargs=1, action=uvtt2fgu.PortalAdjust)
        args = parser.parse_args('--foo 25%'.split())
        self.assertEqual(args.foo, '25%')

    def test_pixels(self) -> None:
        '''Test the custom argument parser'''
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', nargs=1, action=uvtt2fgu.PortalAdjust)
        args = parser.parse_args('--foo 99px'.split())
        self.assertEqual(args.foo, '99px')

    def test_other(self) -> None:
        '''Test the custom argument parser'''
        parser = argparse.ArgumentParser()
        parser.add_argument('--foo', nargs=1, action=uvtt2fgu.PortalAdjust)
        with self.assertRaises(argparse.ArgumentTypeError):
            args = parser.parse_args('--foo 99'.split())

if __name__ == '__main__':
    unittest.main()

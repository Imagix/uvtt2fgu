#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import Optional,Tuple

class UVTTFile(object):
    filepath = None

    def __init__(self, filepath: Path, *args, **kwargs):
        self.filepath = filepath

def processFile(filepaths: Tuple[Path, Path, Path, Path]) -> None:
    '''Process an individual Universal VTT file'''
    (uvttpath, pngpath, jpgpath, xmlpath) = filepaths

    print('Processing {}'.format(uvttpath))
    print('  Writing {}'.format(pngpath))
    print('  Writing {}'.format(jpgpath))
    print('  Writing {}'.format(xmlpath))
    uvttfile = UVTTFile(uvttpath)


def composeFilePaths(filepath: Path, outputpath: Optional[Path]) -> Tuple[Path, Path, Path, Path]:
    '''Take the input filepath and output the full set of input and output paths

    The returned tuple is the input uvtt file, the output png path, the output
    jpg path, and the output xml path.  
    '''
    vttpath = filepath

    if not outputpath:
        outputpath = Path('.')
    
    pngpath = Path.joinpath(outputpath, filepath.with_suffix('.png').name)
    jpgpath = Path.joinpath(outputpath, filepath.with_suffix('.jpg').name)
    xmlpath = Path.joinpath(outputpath, filepath.with_suffix('.xml').name)

    return (vttpath, pngpath, jpgpath, xmlpath)

def init_argparse() -> argparse.ArgumentParser:
    '''Set up the command-line argument parser'''
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] [FILES]',
        description='Convert Dungeondraft .dd2vtt files to .jpg/.png/.xml for Fantasy Grounds Unity (FGU)'
    )
    parser.add_argument(
        '-o', '--output', help='Path to the output directory'
    )
    parser.add_argument(
        '--version', action='version', version=f'{parser.prog} version 1.0.0'
    )
    parser.add_argument('files', nargs='*',
                        help='Files to convert to .png + .xml for FGU')
    return parser


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()

    for filename in args.files:
        outputpath = args.output if args.output else '.'
        filepaths = composeFilePaths(Path(filename), Path(outputpath))
        processFile(filepaths)


if __name__ == '__main__':
    main()

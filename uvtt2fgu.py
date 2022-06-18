#!/usr/bin/env python3

import argparse
import base64
import configparser
import errno
from io import BytesIO
import json
import logging
from math import sin, cos
from os import getenv, remove
from pathlib import Path
import platform
import sys
from typing import Optional, Tuple
from PIL import Image
import xml.etree.ElementTree as ET
from xml.dom import minidom

class ConfigFileData(object):
    def __init__(self, configFile: str) -> None:
        if not configFile:
            configFile = self.configFilePath() / 'uvtt2fgu.conf'

        logging.info('Reading configuration from {}'.format(configFile))
        config = configparser.ConfigParser()

        config.read(configFile)

        self.xmlpath = None
        self.jpgpath = None
        self.writejpg = True
        self.jpgQuality = 90
        self.jpgOptimize = True
        self.jpgSubsampling = 2
        self.pngpath = None
        self.writepng = True
        self.forceOverwrite = None
        self.remove = None
        self.alllocaldd2vttfiles = False
        self.objectsAreTerrain = True

        for section in config.sections():
            self.xmlpath = config[section].get('xmlpath')
            self.jpgpath = config[section].get('jpgpath')
            self.jpgQuality = config[section].get('jpgquality')
            self.jpgOptimize = config[section].get('jpgoptimize')
            self.jpgSubsampling = config[section].get('jpgsubsampling')
            self.writejpg = config[section].getboolean('writejpg', True)
            self.pngpath = config[section].get('pngpath')
            self.writepng = config[section].getboolean('writepng', True)
            self.forceOverwrite = config[section].getboolean('force')
            self.remove = config[section].getboolean('remove')
            self.alllocaldd2vttfiles = config[section].getboolean('alllocaldd2vttfiles')
            self.objectsAreTerrain = config[section].getboolean('objectsareterrain')

    def configFilePath(self) -> Path:
        myPlatform = platform.system()

        if myPlatform == 'Windows':
            platformPath = Path(getenv('APPDATA')) / 'uvtt2fgu'
        elif myPlatform == 'Darwin':
            platformPath = Path(getenv('HOME')) / 'Library' / 'Preferences' / 'uvtt2fgu'
        elif myPlatform == 'Linux':
            xdgConfigHome = getenv('XDG_CONFIG_HOME')

            if xdgConfigHome:
                platformPath = Path(xdgConfigHome)
            else:
                platformPath = Path(getenv('HOME')) / '.config'

        return platformPath

configData = None

def composeId(id: int) -> ET.Element:
    '''Converts an int to an XML element 'id' with the value'''
    elem = ET.Element('id')
    elem.text = str(id)
    return elem


class Point(object):
    def __init__(self, x: float, y: float):
        # FGU only wants 1 decimal point
        self.x = round(x, 1)
        self.y = round(y, 1)

def translatePortalAdjustment(gridsize: int, adjustment: str) -> float:
    '''Converts from the adjustment value to the actual pixel count

    Either ##% of the grid size, or a ##px literal pixels
    '''
    if adjustment[-1] == '%':
        val = max(gridsize * float(adjustment[:-1]) / 100, 1) / 2
    elif adjustment[-2:] == 'px':
        val = float(adjustment[:-2]) / 2
    else:
        raise ValueError('Invalid input: {}'.format(adjustment))

    return val


def convertLineToRect(line, width, length, angle):
    '''Essentially turns a line into a fat line'''
    widthModifyX = width * sin(angle)
    widthModifyY = width * cos(angle)
    lengthModifyX = abs(length * cos(angle))
    lengthModifyY = abs(length * sin(angle))

    if (line[0].x > line[1].x):
        line[0].x += lengthModifyX
        line[1].x -= lengthModifyX
    else:
        line[0].x -= lengthModifyX
        line[1].x += lengthModifyX

    if (line[0].y > line[1].y):
        line[0].y += lengthModifyY
        line[1].y -= lengthModifyY
    else:
        line[0].y -= lengthModifyY
        line[1].y += lengthModifyY

    points = []

    points.append(Point(line[0].x - widthModifyX, line[0].y - widthModifyY))
    points.append(Point(line[1].x - widthModifyX, line[1].y - widthModifyY))
    points.append(Point(line[1].x + widthModifyX, line[1].y + widthModifyY))
    points.append(Point(line[0].x + widthModifyX, line[0].y + widthModifyY))

    return points


class UVTTFile(object):
    class Occluder(object):
        '''Represents a generic Occluder'''
        def __init__(self):
            self.points = []

        def xmlElemStart(self, id) -> ET.Element:
            '''Create the initial XML element for an occluder'''
            elem = ET.Element('occluder')
            elem.append(composeId(id))
            return elem

        def addPoint(self, coord: Point):
            '''Add a point to this occluder'''
            self.points.append(coord)

    class WallOccluder(Occluder):
        '''Represents a Wall Occluder'''
        def xmlElem(self, id) -> ET.Element:
            '''Build up the XML representation of a wall'''
            elem = self.xmlElemStart(id)

            logging.debug('  Occluder(Wall) {} {} points'.format(id, len(self.points)))
            pointsElem = ET.Element('points')
            pt = []
            for point in self.points:
                pt.append(str(point.x))
                pt.append(str(point.y))
            pointsElem.text = ','.join(pt)
            elem.append(pointsElem)

            return elem

    class ObjectOccluder(Occluder):
        '''Represents an Object Occluder'''
        def __init__(self, objectsAreTerrain):
            super().__init__()
            self.objectsAreTerrain = objectsAreTerrain

        def xmlElem(self, id) -> ET.Element:
            '''Build up the XML representation of a wall'''
            elem = self.xmlElemStart(id)

            logging.debug('  Occluder(Object) {} {} points'.format(id, len(self.points)))
            pointsElem = ET.Element('points')
            pt = []
            for point in self.points:
                pt.append(str(point.x))
                pt.append(str(point.y))
            pointsElem.text = ','.join(pt)
            elem.append(pointsElem)

            if self.objectsAreTerrain:
                elem.append(ET.Element('terrain'))
                elem.append(ET.Element('hidden'))
                elem.append(ET.Element('single_sided'))
                elem.append(ET.Element('allow_move'))
                elem.append(ET.Element('closed'))
                elem.append(ET.Element('counterclockwise'))
                elem.append(ET.Element('toggleable'))

            return elem

    class PortalOccluder(Occluder):
        '''Represents a Portal occluder, could be a door or window'''
        def __init__(self, rotation, widthAdj, lengthAdj):
            super().__init__()
            self.rotation = rotation
            self.widthAdj = widthAdj
            self.lengthAdj = lengthAdj

        def addLine(self, point1, point2):
            '''Add a line to this portal'''
            self.points.extend(convertLineToRect(
                (point1, point2), self.widthAdj, self.lengthAdj, self.rotation))

        def xmlPoints(self, elem, id) -> None:
            '''Add the points data to the XML representation'''
            logging.debug('  Occluder(Portal) {} {} points'.format(id, len(self.points)))
            pointsElem = ET.Element('points')
            pt = []
            for point in self.points:
                pt.append(str(point.x))
                pt.append(str(point.y))
            pointsElem.text = ','.join(pt)
            elem.append(pointsElem)

            toggleAble = ET.Element('toggleable')
            elem.append(toggleAble)

            closeElem = ET.Element('closed')
            elem.append(closeElem)

    class DoorOccluder(PortalOccluder):
        '''Represents a Door occluder'''
        def xmlElem(self, id) -> ET.Element:
            '''Build up the XML representation of a door'''
            elem = self.xmlElemStart(id)

            self.xmlPoints(elem, id)

            singleSided = ET.Element('single_sided')
            elem.append(singleSided)

            counterclockwise = ET.Element('counterclockwise')
            elem.append(counterclockwise)

            return elem

    class WindowOccluder(PortalOccluder):
        '''Represents a Window occluder'''
        def xmlElem(self, id) -> ET.Element:
            '''Build up the XML representation of a window'''
            elem = self.xmlElemStart(id)

            self.xmlPoints(elem, id)

            allowvision = ET.Element('allow_vision')
            elem.append(allowvision)

            return elem

    def __init__(self, filepath: Path, portalWidthAdjustment: str, portalLengthAdjustment: str, *args, **kwargs):
        self.filepath = filepath
        with self.filepath.open(mode='r') as f:
            self.data = json.load(f)

        mapsize = self.data['resolution']['map_size']
        self.originX = self.data['resolution']['map_origin']['x']
        self.originY = self.data['resolution']['map_origin']['y']
        logging.debug('  Origin: {},{}'.format(self.originX, self.originY))
        self.resolution = (mapsize['x'], mapsize['y'])
        self.gridsize = self.data['resolution']['pixels_per_grid']
        self.image = base64.decodebytes(self.data['image'].encode('utf-8'))
        self.portalLengthAdjustmentPixels = translatePortalAdjustment(
            self.gridsize, portalLengthAdjustment)
        logging.debug('  Adding {} pixels to portal length'.format(
            self.portalLengthAdjustmentPixels))
        self.portalWidthAdjustmentPixels = translatePortalAdjustment(
            self.gridsize, portalWidthAdjustment)
        logging.debug('  Adding {} pixels to portal width'.format(
            self.portalWidthAdjustmentPixels))

    def translateCoord(self, coord, dimension) -> float:
        '''Translate from a grid coordinate to a pixel coordinate'''
        return round(coord * self.gridsize + (dimension * self.gridsize) // 2, 1)

    def translateX(self, x_coord) -> float:
        '''Translate from an X grid coordinate to an X pixel coordinate'''
        return self.translateCoord(x_coord - self.originX, -self.resolution[0])

    def translateY(self, y_coord) -> float:
        '''Translate from a Y grid coordinate to a Y pixel coordinate'''
        return self.translateCoord(-(y_coord - self.originY), self.resolution[1])

    def translatePoint(self, coord) -> Point:
        '''Translate an x, y element from the uvtt data to a Point'''
        return Point(self.translateX(coord['x']), self.translateY(coord['y']))

    def composeGrid(self) -> ET.Element:
        '''Build up the XML representation of the map's grid size'''
        elem = ET.Element('gridsize')
        elem.text = '{},{}'.format(self.gridsize, self.gridsize)
        return elem

    def composeWall(self, los) -> Occluder:
        '''Build up an Occluder representation of a wall'''
        wall = self.WallOccluder()

        for coord in los:
            wall.addPoint(self.translatePoint(coord))

        return wall

    def composeObject(self, los) -> Occluder:
        '''Build up an Occluder representation of an object'''
        object = self.ObjectOccluder(configData.objectsAreTerrain)

        for coord in los:
            object.addPoint(self.translatePoint(coord))

        return object

    def composePortal(self, portal) -> Occluder:
        '''Build up an Occluder representation of one portal
        
        Dungeondraft appears to represent windows as essentially an open door
        '''
        if portal['closed'] == False:
            portalElem = self.WindowOccluder(
                portal['rotation'], self.portalWidthAdjustmentPixels, self.portalLengthAdjustmentPixels)
        else:
            portalElem = self.DoorOccluder(
                portal['rotation'], self.portalWidthAdjustmentPixels, self.portalLengthAdjustmentPixels)

        it = iter(portal['bounds'])
        for point1, point2 in zip(it, it):
            portalElem.addLine(self.translatePoint(point1),
                               self.translatePoint(point2))

        return portalElem

    def composeOccluders(self) -> ET.Element:
        '''Build up the XML representation of the line of sight elements'''
        occluders = []

        # First the line-of-sight elements, AKA walls
        logging.debug('  {} los elements'.format(
            len(self.data['line_of_sight'])))
        for los in self.data['line_of_sight']:
            occluders.append(self.composeWall(los))

        objectsLoS = self.data.get('objects_line_of_sight', [])

        logging.debug('  {} object los elements'.format(len(objectsLoS)))
        for los in objectsLoS:
            occluders.append(self.composeObject(los))

        # Next the portal elements, which may be doors or windows
        logging.debug('  {} portal elements'.format(len(self.data['portals'])))
        for portal in self.data['portals']:
            occluders.append(self.composePortal(portal))

        elem = ET.Element('occluders')

        for id, occluder in enumerate(occluders):
            elem.append(occluder.xmlElem(id))

        return elem

    def composeLights(self) -> ET.Element:
        '''Build up the XML representation of the lights'''
        logging.debug('  {} lights'.format(len(self.data['lights'])))

        elem = ET.Element('lights')

        for id, light in enumerate(self.data['lights']):
            lightElem = ET.Element('light')

            lightElem.append(composeId(id))

            position = ET.Element('position')
            position.text = '{},{}'.format(
                self.translateX(light['position']['x']), self.translateY(light['position']['y']))
            lightElem.append(position)

            color = ET.Element('color')
            color.text = '#{}'.format(light['color'])
            lightElem.append(color)

            range = ET.Element('range')
            range.text = '{},0.75,{},0.5'.format(
                light['range'], light['range'] * 2)
            lightElem.append(range)

            on = ET.Element('on')
            lightElem.append(on)

            elem.append(lightElem)

        return elem

    def composeXml(self) -> ET.Element:
        '''Build up the FGU XML representation of the Universal VTT file'''
        root = ET.Element(
            'root', attrib={'version': '4.1', 'dataversion': '20210302'})
        root.append(self.composeGrid())
        root.append(self.composeOccluders())
        root.append(self.composeLights())
        return root

    def writePng(self, filepath: Path) -> None:
        '''Write the image out as a .png file'''
        with filepath.open(mode='wb') as f:
            f.write(self.image)

    def writeJpg(self, filepath: Path) -> None:
        '''Write the image out as a .jpg file'''
        imagebytes = BytesIO(self.image)
        pngimage = Image.open(imagebytes)
        jpgimage = pngimage.convert('RGB')
        jpgimage.save(
            filepath, 
            quality=configData.jpgQuality, 
            subsampling=configData.jpgSubsampling, 
            optimize=configData.jpgOptimize)

    def writeXml(self, filepath: Path) -> None:
        '''Write out the FGU .xml file for line-of-sight and lighting'''
        xmlTree = self.composeXml()
        xmlStr = minidom.parseString(
            ET.tostring(xmlTree)).toprettyxml(indent="  ")
        with filepath.open('w') as f:
            f.write(xmlStr)


def processFile(filepaths: Tuple[Path, Path, Path, Path], portalWidthAdjustment: str, portalLengthAdjustment: str) -> None:
    '''Process an individual Universal VTT file'''
    (uvttpath, pngpath, jpgpath, xmlpath) = filepaths

    logging.info('Processing {}'.format(uvttpath))
    uvttfile = UVTTFile(uvttpath, portalWidthAdjustment,
                        portalLengthAdjustment)

    logging.debug('  Map dimensions: {} grid elements'.format(
        uvttfile.resolution))
    logging.debug('  Grid Size: {} pixels'.format(uvttfile.gridsize))

    if configData.writepng:
        logging.info('  Writing {}'.format(pngpath))
        uvttfile.writePng(pngpath)

    if configData.writejpg:
        logging.info('  Writing {}'.format(jpgpath))
        uvttfile.writeJpg(jpgpath)

    logging.info('  Writing {}'.format(xmlpath))
    uvttfile.writeXml(xmlpath)

    if configData.remove:
        remove(uvttpath)


def composeFilePaths(filepath: Path) -> Tuple[Path, Path, Path, Path]:
    '''Take the input filepath and output the full set of input and output paths

    The returned tuple is the input uvtt file, the output png path, the output
    jpg path, and the output xml path.
    '''
    vttpath = filepath

    pngpath = Path.joinpath(Path(configData.pngpath), filepath.with_suffix('.png').name)
    jpgpath = Path.joinpath(Path(configData.jpgpath), filepath.with_suffix('.jpg').name)
    xmlpath = Path.joinpath(Path(configData.xmlpath), filepath.with_suffix('.xml').name)

    return (vttpath, pngpath, jpgpath, xmlpath)


class PortalAdjust(argparse.Action):
    '''Parse the command-line arguments to verify that it is either a percentage, or a pixel count'''

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs != 1:
            raise ValueError("nargs must be 1")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if values[-1] == '%':
            pass
        elif values[-2:] == 'px':
            pass
        else:
            raise argparse.ArgumentTypeError('value must be 1-100% or ##px')

        setattr(namespace, self.dest, values)


def init_argparse() -> argparse.ArgumentParser:
    '''Set up the command-line argument parser'''
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] [FILES]',
        description='Convert Dungeondraft .dd2vtt files to .jpg/.png/.xml for Fantasy Grounds Unity (FGU)'
    )
    parser.add_argument(
        '-c', '--config', help='Configuration file'
    )
    parser.add_argument(
        '-f', '--force', help='Force overwrite destination files', action='store_true'
    )
    parser.add_argument(
        '-l', '--log', dest='logLevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level'
    )
    parser.add_argument(
        '-o', '--output', help='Path to the output directory'
    )
    parser.add_argument(
        '--portalwidth', help='Width of portals', default='25%'
    )
    parser.add_argument(
        '--portallength', help='Additional length to add to portals', default="0px"
    )
    parser.add_argument(
        '-r', '--remove', help='Remove the input dd2vtt file after conversion'
    )
    parser.add_argument(
        '-v', '--version', action='version', version=f'{parser.prog} version 1.4.0'
    )
    parser.add_argument('files', nargs='*',
                        help='Files to convert to .png + .xml for FGU')
    return parser

def loadConfigData(configFile: str) -> None:
    global configData
    configData = ConfigFileData(configFile)

def main() -> int:
    parser = init_argparse()
    args = parser.parse_args()
    exitcode = 0

    logging.basicConfig(format='%(message)s')

    if args.logLevel:
        logging.getLogger().setLevel(getattr(logging, args.logLevel))

    loadConfigData(args.config)

    # Merge the config file with the command-line arguments
    if args.output:
        configData.xmlpath = args.output
        configData.pngpath = args.output
        configData.jpgpath = args.output
    if not configData.xmlpath:
        configData.xmlpath = '.'
    if not configData.pngpath:
        configData.pngpath = '.'
    if not configData.jpgpath:
        configData.jpgpath = '.'
    if args.force:
        configData.forceOverwrite = args.force
    if not configData.forceOverwrite:
        configData.forceOverwrite = False
    if args.remove:
        configData.remove = args.remove
    if not configData.remove:
        configData.remove = False

    # Verify that the destination directories exist (if we are writing that
    # file)
    if not Path(configData.xmlpath).exists():
        logging.error('{}: No such file or directory'.format(configData.xmlpath))
        return errno.ENOENT
    if not Path(configData.pngpath).exists() and configData.writepng:
        logging.error('{}: No such file or directory'.format(configData.pngpath))
        return errno.ENOENT
    if not Path(configData.jpgpath).exists() and configData.writejpg:
        logging.error('{}: No such file or directory'.format(configData.jpgpath))
        return errno.ENOENT

    if not args.files:
        if not configData.alllocaldd2vttfiles:
            logging.warning('No files specified')
            return errno.EINVAL
        else:
            cwd = Path('.')
            args.files = list(cwd.glob('*.dd2vtt'))

    for filename in args.files:
        filepaths = composeFilePaths(Path(filename))

        # Verify that the source file exists, and the destination path exists
        if not filepaths[0].exists():
            logging.error(
                '{}: No such file or directory, skipping'.format(filepaths[0]))
            exitcode = errno.ENOENT
            continue

        if not configData.forceOverwrite:
            for filepath in filepaths[1:]:
                if filepath.exists():
                    logging.error(
                        '{}: file already exists, skipping'.format(filepath))
                    exitcode = errno.EEXIST
                    continue

            if exitcode:
                return exitcode

        processFile(filepaths, args.portalwidth, args.portallength)

    return exitcode


if __name__ == '__main__':
    sys.exit(main())

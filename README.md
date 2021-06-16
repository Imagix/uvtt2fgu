# uvtt2fgu
Utility to extract Fantasy Grounds Unity Line-of-sight and lighting files from a Univeral VTT file exported from Dungeondraft

This program works with Fantasy Grounds Unity v4.1 or higher as that is the version where dynamic lighting effects were added.
This was last used with Dungeondraft v1.0.2.1 Beta.

## Requirements

uvtt2fgu.py requires a python3 installation with PIP.

## Usage
1. Create your map in Dungeondraft
2. Export the map in Universal VTT format
    - You do not have to use the default "Best Quality" Grid Preset.  You could use the "Roll20" setting as this will make the image files smaller.
      Remember that your players will need to download these images via FGU.  The .jpg is also smaller than the .png.  The pixel count is encoded
      in the exported file and will be correctly set up in FGU when imported.
    - You should turn off Lighting as you want FGU to draw the lighting effects and not have the underlying image with the lighting
    - You should turn off the Grid as well.  The grid size will be correctly set up in FGU so you should only need to turn it on within FGU.
    - These are both "should"s and not "must"s.  If you want your image to have the lighting drawn on it and/or the grid, it won't break anything.
3. Run the script as `uvtt2fgu.py sampleMap.dd2vtt`.  This will emit `sampleMap.png`, `sampleMap.jpg`, and `sampleMap.xml` into your current directory
4. Copy the `sampleMap.xml` file into your campaign's `images` directory
5. Import the .png or .jpg in FGU

## Configuration File
The configuration file is a standard .INI format file.  All of the configuration lives in a "[default]" section.  This file is found In various places:
| Platform | Location |
|----------|----------|
| Windows | %APPDATA%\uvtt2fgu\uvtt2fgu.conf |
| Mac OS | $HOME/Library/Preferences/uvtt2fgu/uvtt2fgu.conf |
| Linux | $XDG_CONFIG_HOME/uvtt2fgu.conf<br>$HOME/.config/uvtt2fgu.conf |

 The file named in the `-c` command-line parameter overrides this search.  For Linux, it uses the XDG_CONFIG_HOME version if that environment variable is set, otherwise use the $HOME version.

Example configuration file:
```
[default]
xmlpath=/home/joesmith/.smiteworks/fgdata/campaigns/TestLight/images
writepng=False
jpgpath=out
force=True
```
This file will cause the program to write the xml file directly out to joesmith's FGU TestLight campaign's images folder.  It will write the jpg to the "out" subdirectory of where the script is run. It will overwrite the xml and jpg files if they exist.  It will not write out the png file.

### Configuration file parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| alllocaldd2vttfiles | If no files are specified, look for all .dd2vtt files in the current directory and convert them | False |
| force     | Force overwrite destination files | False |
| jpgpath   | Path where the .jpg file will be written | Current working directory |
| pngpath   | Path where the .png file will be written | Current working directory |
| remove    | Remove the source file after conversion | False |
| writejpg  | Write the .jpg file | True |
| writepng  | Write the .png file | True |
| xmlpath   | Path where the .xml file will be written | Current working directory |

## Command-line
```
usage: uvtt2fgu.py [OPTIONS] [FILES]

Convert Dungeondraft .dd2vtt files to .jpg/.png/.xml for Fantasy Grounds Unity
(FGU)

positional arguments:
  files                 Files to convert to .png + .xml for FGU

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file
  -f, --force           Force overwrite destination files
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  -o OUTPUT, --output OUTPUT
                        Path to the output directory
  --portalwidth PORTALWIDTH
                        Width of portals
  --portallength PORTALLENGTH
                        Additional length to add to portals
  -r REMOVE, --remove REMOVE
                        Remove the input dd2vtt file after conversion
  -v, --version         show program's version number and exit
```

Parameters specified on the command-line will supersede parameters specified in the configuration file.

By default, the program will not overwrite destination files.  You can use `-f` to force it to overwrite.

By default, the files are all written into your current directory.  You can use `-o /otherdir` to have the files written into `/otherdir`.

`--portalwidth` sets how wide the FGU portals will be.  This is specified either as a percentage of a grid width, or as a specific number of pixels.  Either `--portalwidth 36%` or `--portalwidth 40px`.  The default is 25%.

`--portallength` sets how much extra length for the portals.  This is specified just like `--portalwidth`.  The default is 0px.

## Acknowledgements

[<img src="assets/dungeondraft_icon.png" width=32 height=32/>](https://dungeondraft.net/) [Dungeondraft](https://dungeondraft.net/) is a map drawing tool.  Dungeondraft is produced by Megasploot.

[Fantasy Grounds Unity](https://www.fantasygrounds.com) is a Virtual TableTop program for playing many different table-top Role Playing Games (TTRPG), virtually.  FGU is produced by SmiteWorks USA LLC.

uvtt2vtt.py is not endorsed by either of these companies, it is a community-effort to make these two programs interoperable.
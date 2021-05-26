# uvtt2fgu
Utility to extract Fantasy Grounds Unity Line-of-sight and lighting files from a Univeral VTT file exported from Dungeondraft

This program works with Fantasy Grounds Unity v4.1 or higher as that is the version where dynamic lighting effects were added.
This was last used with Dungeondraft v1.0.1.3.

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
   
## Command-line
```
usage: uvtt2fgu.py [OPTIONS] [FILES]

Convert Dungeondraft .dd2vtt files to .jpg/.png/.xml for Fantasy Grounds Unity (FGU)

positional arguments:
  files                 Files to convert to .png + .xml for FGU

optional arguments:
  -h, --help            show this help message and exit
  -f, --force           Force overwrite destination files
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  -o OUTPUT, --output OUTPUT
                        Path to the output directory
  --portalwidth PORTALWIDTH
                        Width of portals
  --portallength PORTALLENGTH
                        Additional length to add to portals
  -v, --version         show program's version number and exit
```

By default, the program will not overwrite destination files.  You can use `-f` to force it to overwrite.

By default, the files are all written into your current directory.  You can use `-o /otherdir` to have the files written into `/otherdir`.

`--portalwidth` sets how wide the FGU portals will be.  This is specified either as a percentage of a grid width, or as a specific number of pixels.  Either `--portalwidth 36%` or `--portalwidth 40px`.  The default is 25%.

`--portallength` sets how much extra length for the portals.  This is specified just like `--portalwidth`.  The default is 0px.

## Acknowledgements

[Dungeondraft](https://dungeondraft.net/) is a map drawing tool.  Dungeondraft is produced by Megasploot.

[Fantasy Grounds Unity](https://www.fantasygrounds.com) is a Virtual TableTop program for playing many different table-top Role Playing Games (TTRPG), virtually.  FGU is produced by SmiteWorks USA LLC.

uvtt2vtt.py is not endorsed by either of these companies, it is a community-effort to make these two programs interoperable.
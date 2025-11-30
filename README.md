# SVI Disktools
These are a few primitive [Python](https://www.python.org/) scripts to manage DSK disk images, based on information from https://www.samdal.com/svdiskformat.htm .

## SVI-getbootloader
This tool extracts the bootloader at the start of a disk image:
```
c:\>python svi-getbootloader.py -h
usage: SVI-GetBootSector [-h] [--output OUTPUT] diskimage

Extract the bootloader from an SVI-3x8 disk image.

positional arguments:
  diskimage        DSK file containing the disk image.

options:
  -h, --help       show this help message and exit
  --output OUTPUT  Override the filename for the extracted bootloader

Please let me know if you find an undetected bootloader.
```
This detects one disk basic and two CP/M bootloaders I found.

## SVI-imd2dsk
Convert a disk image in ImageDisk format to a disk image in .dsk format:
```
C:\>svi-imd2dsk.py -h
usage: svi-imd2dsk [-h] imdfile dskfile

Convert ImageDisk (.IMD) files into raw images (.DSK)

positional arguments:
  imdfile     Source disk image in IMD format
  dskfile     Target disk image in DSK format

options:
  -h, --help  show this help message and exit
```

## SVI-cas2dsk
Copy all files from a cassete tape in .cas format to a disk image in .dsk format
```
C:\>svi-cas2dsk.py -h
usage: svi-cas2dsk [-h] [--bootloader [BOOTLOADER]] casfile [dskfile]

Convert an SVI cassette (.cas) file into a disk image (.DSK)

positional arguments:
  casfile               Source cassete file in CAS format
  dskfile               Target disk image in DSK format

options:
  -h, --help            show this help message and exit
  --bootloader [BOOTLOADER]
                        Optionally override the bootloader to use.
```
By default it will look for "loader-diskbasic.bin" in the current directory to write into the disk image. You can change the path with the `--bootloader` option. If no bootloader is found the disk will not be bootable, and you have to boot from a different diskbasic disk before you can use it!
> [!IMPORTANT]  
> This will NOT fix any loader to load data from disk instead of cassette! In the simplest case you can just change the path in `bload` commands to include the disk device,
> in assembly loaders you will have to reverse-engineer and reimplement it!

The converter is based on information from https://wiki.kasettilamerit.fi/wiki/index.php/Spectravideo . There doesn't seem to be an easy way to detect the end of each file, so it does some guesses. 

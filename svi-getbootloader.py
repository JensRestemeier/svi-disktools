import hashlib
import argparse
import os.path

bootSectorHashes = {
    '4534b4cd068b6dcc121243d5d5d7e141a0f146d71e2f03214810ad0a87681444': ("boot-diskbasic.bin", 18*128+17*256*2), 
    'f87f1847d44509ebfc16f568d0bbfb89ccc1a0a47d05de994419c1d25c6b73ca': ("boot-cpm-v1.bin", 0xB00), 
    '6ea82aecce872ac9ddbf0275d40ab65949bdda0ee3499ebf9792a4a97eb667e4': ("boot-cpm-v2.bin", 0xB00)
}

def extractBootloader(dskPath : str, loaderPath = None):
    if not os.path.exists(dskPath):
        print (f"File {dskPath} not found!")
        return

    with open(dskPath, "rb") as f:
        data = f.read()
    
    bootsector = data[0:128]
    hash = hashlib.sha256(bootsector).hexdigest()
    try:
        name,size = bootSectorHashes[hash]
        bootloader = data[0:size]
        if loaderPath == None or len(loaderPath) == 0:
            loaderPath = name
        print (f"writing {loaderPath}...")
        with open(loaderPath, "wb") as f:
            f.write(bootloader)
    except KeyError:
        print (f"unnown/missing boot sector [{hash}]")

def main():
    parser = argparse.ArgumentParser(
        prog='SVI-GetBootSector',
        description='Extract the bootloader from an SVI-3x8 disk image.',
        epilog='Please let me know if you find an undetected bootloader.')
    parser.add_argument('diskimage', help="DSK file containing the disk image.")           
    parser.add_argument('--output', type=str, help="Override the filename for the extracted bootloader")

    args = parser.parse_args()
    if len(args.diskimage) > 0:
        extractBootloader(args.diskimage, args.output)

if __name__ == "__main__":
    main()

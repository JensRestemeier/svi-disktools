import hashlib
import argparse
import os.path
import glob

bootSectorHashes = {
    '4534b4cd068b6dcc121243d5d5d7e141a0f146d71e2f03214810ad0a87681444': ("boot-diskbasic.bin", 18*128+17*256*2), 
    'f87f1847d44509ebfc16f568d0bbfb89ccc1a0a47d05de994419c1d25c6b73ca': ("boot-cpm-v1.bin", 0xB00), 
    '6ea82aecce872ac9ddbf0275d40ab65949bdda0ee3499ebf9792a4a97eb667e4': ("boot-cpm-v2.bin", 0xB00)
}

bootLoaderHashes = {
    'a8f37ac67cf7d3e2b2107b70648e469091dce9ad499f54849d46f36abf1258a1': "loader-diskbasic.bin", 
    '70291824fe67fc2f75721c78b35798af09fbde1fa80c45a87f9783b9c1e51982': "loader-cpm-v1.bin", 
    'e62e43f46cf6f8566bf5d60701231af74037496f582ae3089727886b7b664cae': "loader-cpm-v2.bin", 
    'd4d32e6aa3e32c32a3a4cabfeffa36ccd95d174be1a7b5084d1baf1f4ce3c947': "loader-cpm-v3.bin"
}

def extractBootloader(dskPath : str, loaderPath = None):
    if not os.path.exists(dskPath):
        print (f"File {dskPath} not found!")
        return

    with open(dskPath, "rb") as f:
        data = f.read()
    
    bootsector = data[0:128]
    bootHash = hashlib.sha256(bootsector).hexdigest()
    try:
        name,size = bootSectorHashes[bootHash]
        bootloader = data[0:size]

        loaderHash = hashlib.sha256(bootloader).hexdigest()
        try:
            loaderName = bootLoaderHashes[loaderHash]
        except KeyError:
            print (f"unnown/missing boot loader [{loaderHash}]")
        if loaderPath == None or len(loaderPath) == 0:
            loaderPath = loaderName

        print (f"writing {loaderPath}...")
        with open(loaderPath, "wb") as f:
            f.write(bootloader)
    except KeyError:
        print (f"unnown/missing boot sector [{bootHash}]")

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

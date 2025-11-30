import argparse
import os.path
import struct

def skipSync(data : bytes, pos : int):
    while pos < len(data) and data[pos] == 0x55:
        pos += 1
    if pos < len(data) and data[pos] == 0x7F:
        pos += 1
    return pos

def skipStop(data : bytes, pos : int):
    while pos < len(data) and data[pos] == 0x00:
        pos += 1
    return pos

def isHeader(data : bytes, pos : int):
    if pos < len(data):
        filetype = data[pos]
        if filetype not in [0xD3, 0xD0, 0xEA]:
            return False
        for i in range(10):
            if data[pos] == filetype:
                pos += 1
            else:
                return False
        return True

def isEndOfData(data : bytes, pos : int):
    if pos >= len(data):
        return True
    elif data[pos] != 0x00 and data[pos] != 0x55:
        return False
    pos = skipStop(data, pos)

    # check if we have a sync
    if pos >= len(data):
        return True
    elif data[pos] != 0x55:
        return False
    pos = skipSync(data, pos)

    # check if we have a header
    if pos < len(data) and not isHeader(data, pos):
        return False

    return True

def isEndOfSequential(data : bytes, pos : int):
    # is Sync?
    if pos >= len(data):
        return True
    elif data[pos] != 0x55:
        return False
    while pos < len(data) and data[pos] == 0x55:
        pos += 1

    # does sync end with 7F?
    if pos >= len(data):
        return True
    elif data[pos] == 0x7F:
        pos += 1
    else:
        return False
    
    if pos >= len(data):
        return True
    elif not isHeader(data, pos):
        return False

    return True

def allocTrack(fat : bytearray):
    for i in range(len(fat)):
        if fat[i] == 0xFF:
            fat[i] = 0xC0 # mark as allocated
            return i
    return 0xFF

def getTrackOfs(track : int):
    if track == 0:
        return 0
    else:
        return 18 * 128 + (track-1) * 17 * 256

def isBinary(filedata):
    base,end,start = struct.unpack_from("<HHH", filedata, 0)
    if base < 0x8000 and base > 0xF000:
        return False
    if end < base:
        return False
    if start < base or start > end:
        return False
    return True

def convertCasToDsk(casPath : str, dskPath : str, bootloaderPath : str):
    # load the tape file:
    if not os.path.exists(casPath):
        print (f"File {casPath} not found!")
        return

    print (f"reading {casPath}")
    with open(casPath, "rb") as f:
        data = f.read()

    if dskPath == None:
        dskPath = os.path.splitext(casPath)[0] + ".dsk"

    if bootloaderPath == None:
        bootloaderPath = "boot-diskbasic.bin"

    # split tape into files
    files = []
    pos = 0
    while pos < len(data):
        pos = skipSync(data, pos)

        # get header
        if pos < len(data):
            filetype = data[pos]
            while data[pos] == filetype:
                pos += 1
            name,attribute = struct.unpack_from("<6sB", data, pos)
            pos += 7
            pos = skipStop(data, pos)

            if filetype == 0xEA:
                # sequential file:
                filedata = bytearray()
                while pos < len(data) and not isEndOfSequential(data, pos):
                    pos = skipSync(data, pos)
                    filedata += data[pos:pos+256]
                    pos += 256
                    pos = skipStop(data, pos)
            else:
                pos = skipSync(data, pos)

                # detect the size of the file
                dataStart = pos
                while pos < len(data) and not isEndOfData(data, pos):
                    pos += 1
                filedata = data[dataStart:pos]
                pos = skipStop(data, pos)

            files.append((name, filetype, attribute, filedata))

    # create disk image
    dsk = bytearray([0xE5] * (18 * 128 + 17 * 256 * 39))

    # install boot loader
    if os.path.exists(bootloaderPath):
        print (f"installing bootloader \"{bootloaderPath}\"")
        with open(bootloaderPath, "rb") as f:
            boot = f.read()
        dsk[0:len(boot)] = boot
    else:
        print (f"Bootloader \"{bootloaderPath}\" not found!")

    # create initial FAT
    fat = bytearray([0xFF] * 256)
    for track in [0,1,2,20]:
        fat[track] = 254

    # create empty filesystem
    count = 0
    fs = bytearray([0xFF] * 256 * 13)
    for name, filetype, attribute, filedata in files:
        track = allocTrack(fat)
        fsType = 0 # binary
        if filetype == 0xEA and attribute == 0xFF:
            fsType = 0x81 # ascii basic program
        elif filetype == 0xD3:
            if attribute == 0xFF:
                fsType = 0x80 # tokenised basic progream
            elif attribute in [0,1,2]:
                fsType = 0xA0 # screen file
        elif isBinary(filedata):
            fsType = 0x41
        struct.pack_into("<6s3sBB", fs, count * 16, name, "   ".encode("ascii"), fsType, track)
        pos = 0
        while pos < len(filedata):
            if len(filedata) - pos > (17 * 256):
                trackOfs = getTrackOfs(track)
                dsk[trackOfs:trackOfs+(17*256)] = filedata[pos:pos+(17*256)]
                nextTrack = allocTrack(fat)
                fat[track] = nextTrack
                track = nextTrack
                pos += 17 * 256
            else:
                trackOfs = getTrackOfs(track)
                size = len(filedata) - pos
                dsk[trackOfs:trackOfs+size] = filedata[pos:pos+size]
                pad = 256 - (size % 256)
                if pad < 256:
                    if filetype == 0xEA:
                        dsk[trackOfs+size:trackOfs+size+pad] = [0x1A] * (pad)
                    else:
                        dsk[trackOfs+size:trackOfs+size+pad] = [0] * pad
                fat[track] = 0xC0 + (size + 255) // 256
                pos += size
        count += 1

    # store filesystem
    fsTrack = getTrackOfs(20)
    dsk[fsTrack:fsTrack+len(fs)] = fs

    # store disk allocation table
    dsk[fsTrack + 13 * 256:fsTrack + 13 * 256 + 256] = [0] * 256
    
    # store three copies of the FAT
    for i in range(3):
        fatPtr = fsTrack + 14 * 256 + i * 256
        dsk[fatPtr:fatPtr + 256] = fat

    print (f"writing {dskPath}")
    with open(dskPath, "wb") as f:
        f.write(dsk)

def main():
    parser = argparse.ArgumentParser(prog='svi-cas2dsk', description='Convert an SVI cassette (.cas) file into a disk image (.DSK)')
    parser.add_argument('casfile', help="Source cassete file in CAS format")
    parser.add_argument('dskfile', help="Target disk image in DSK format", nargs='?', default=None)
    parser.add_argument('--bootloader', type=str, help="Optionally override the bootloader to use.", nargs='?', default=None)

    args = parser.parse_args()
    convertCasToDsk(args.casfile, args.dskfile, args.bootloader)

if __name__ == "__main__":
    main()

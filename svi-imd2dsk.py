import struct
import argparse

def convert(src:str, dst:str):
    with open(src, "rb") as f:
        img = f.read()

    # skip ascii header
    ofs = 0
    while ofs < len(img) and img[ofs] != 0x1A:
        ofs += 1
    ofs += 1

    # export data
    dsk = bytearray([0] * (18 * 128 + 39 * 17 * 256))
    while ofs < len(img):
        mode,cylinder,head,sector_count,sector_size = struct.unpack_from("<BBBBB", img, ofs)
        ofs += 5
        sector_numbering_map = img[ofs:ofs+sector_count]
        ofs += sector_count
        size = 128 << sector_size
        # print (mode,cylinder,head,sector_count,sector_size, size)
        # print (" ".join(["%2.2x" % x for x in sector_numbering_map]))
        if head == 0:
            track_ofs = 18 * 128 + 17 * 256 * (cylinder - 1) if cylinder > 0 else 0
        else:
            if len(dsk) < 18 * 128 + 17 * 256 * 39 + 40 * 17 * 256:
                dsk += bytearray([0] * 40 * 17 * 256)
            track_ofs = 18 * 128 + 17 * 256 * 39 + cylinder * 17 * 256
        for i in range(sector_count):
            sector_ofs = track_ofs + size * (sector_numbering_map[i]-1)
            record = img[ofs]
            ofs += 1
            if record == 1:
                dsk[sector_ofs:sector_ofs+size] = img[ofs:ofs+size]
                ofs += size
            elif record == 2:
                val = img[ofs]
                dsk[sector_ofs:sector_ofs+size] = [val for i in range(size)]
                ofs += 1
            elif record == 3:
                dsk[sector_ofs:sector_ofs+size] = img[ofs:ofs+size]
                ofs += size
            elif record == 4:
                val = img[ofs]
                dsk[sector_ofs:sector_ofs+size] = [val for i in range(size)]
                ofs += 1
            elif record == 5:
                val = img[ofs]
                dsk[sector_ofs:sector_ofs+size] = [val for i in range(size)]
                ofs += 1

    with open(dst, "wb") as f:
        f.write(dsk)

def main():
    parser = argparse.ArgumentParser(prog='svi-imd2dsk', description='Convert ImageDisk (.IMD) files into raw images (.DSK)')
    parser.add_argument('imdfile', help="Source disk image in IMD format")
    parser.add_argument('dskfile', help="Target disk image in DSK format")

    args = parser.parse_args()
    convert(args.imdfile, args.dskfile)

if __name__ == "__main__":
    main()

from jl_usbproto import JLUSBProto
from jl_stuff import *
import argparse

ap = argparse.ArgumentParser(description='JieLi chip flasher')
ap.add_argument('--device', help='path to device (e.g. /dev/sg2 or \\\\.\\E:)', required=True)
ap.add_argument('files', metavar='address file', help='files to write', nargs='+')
args = ap.parse_args()

with JLUSBProto(args.device) as dev:
    print(args.files)

    print('Online device       --> %(type)d / %(id)x' % dev.online_device())
    print('Chip key            --> %04x' % dev.chip_key())
    print('Flash page max size --> %d' % dev.flash_page_max_size())

    for addr, file in zip(args.files[::2], args.files[1::2]):
        with open(file, 'rb') as f:
            addr = int(addr, 0)

            while True:
                data = f.read(0x1000)
                if data == b'': break

                print('%x' % addr)
                dev.flash_erase_sector(addr)
                dev.flash_program(addr, data)
                addr += len(data)

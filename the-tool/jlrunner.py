from jl_usbproto import JLUSBProto
from jl_stuff import *
import argparse

ap = argparse.ArgumentParser(description='Load and run the code binary')
ap.add_argument('--device',   help='Path to device (e.g. /dev/sg2 or \\\\.\\E:)', required=True)
ap.add_argument('address',    help='Address where the payload will be loaded')
ap.add_argument('file',       help='The payload that will be loaded')
ap.add_argument('--argument', help='Payload argument, default=%(default)s', default='0x4777')
ap.add_argument('--raw',      help="Load the file as-is", action='store_true')
args = ap.parse_args()

with JLUSBProto(args.device) as dev:
    addr = int(args.address, 0)
    arg  = int(args.argument, 0)

    with open(args.file, 'rb') as f:
        dev.mem_write(addr, f.read(), raw=args.raw)

    dev.mem_run(addr, arg)

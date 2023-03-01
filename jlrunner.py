from jl_stuff import *
from jl_uboot import JL_UBOOT
import argparse

ap = argparse.ArgumentParser(description='Load code into memory and execute it')

ap.add_argument('--device',
                help='Path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:)',
                required=True)

ap.add_argument('--arg', default='0x4777',
                help="Numerical argument that's passed to the code (default: %(default)s)")

ap.add_argument('--encrypt', action='store_true',
                help="Encrypt the data as it goes into the chip, usually used for chips that"
                     "have encrypted loaders and so they decrypt it as it goes in. "
                     "This will be replaced with --raw parameter that will pass the data as-is instead.")

ap.add_argument('--block-size', default='512', metavar='SIZE',
                help="Size of the block that is used when transferring data to the chip. (default = %(default)s)"
                     " Please keep in mind that the encrypted loaders usually use a block size of 512 bytes. ")

ap.add_argument('address',
                help="Address where the file will be loaded and executed from")

ap.add_argument('file',
                help="File that will be loaded and executed")

args = ap.parse_args()

with JL_UBOOT(args.device) as dev:
    with open(args.file, 'rb') as f:
        addr = int(args.address, 0)

        while True:
            block = f.read(int(args.block_size, 0))
            if block == b'': break

            if args.encrypt:
                block = jl_crypt_mengli(block)

            dev.mem_write(addr, block)
            addr += len(block)

        dev.mem_jump(int(args.address, 0), int(args.arg, 0))

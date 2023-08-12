from jl_stuff import *
from jl_uboot import JL_MSCDevice, JL_UBOOT
import argparse

ap = argparse.ArgumentParser(description='Load code into memory and execute it')

def anyint(s):
    return int(s, 0)

ap.add_argument('--device',
                help='Path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:)')

ap.add_argument('--arg', type=anyint, default=0x4777,
                help="Numerical argument that's passed to the code (default: 0x%(default)04x)")

ap.add_argument('--encrypt', action='store_true',
                help="Encrypt the data as it goes into the chip, usually used for chips that"
                     "have encrypted loaders and so they decrypt it as it goes in. "
                     "This will be replaced with --raw parameter that will pass the data as-is instead.")

ap.add_argument('--block-size', default='512', metavar='SIZE',
                help="Size of the block that is used when transferring data to the chip. (default = %(default)s)"
                     " Please keep in mind that the encrypted loaders usually use a block size of 512 bytes. ")

ap.add_argument('address', type=anyint,
                help="Address where the file will be loaded and executed from")

ap.add_argument('file',
                help="File that will be loaded and executed")

args = ap.parse_args()

if args.device is not None:
    device = args.device

else:
    from jldevfind import choose_jl_device

    device = choose_jl_device()
    if device is None:
        exit(1)

with JL_MSCDevice(device) as dev:
    # TODO, determine whether we are in UBOOT1.00 or Loader/UBOOT2.00 modes
    uboot = JL_UBOOT(dev)

    with open(args.file, 'rb') as f:
        addr = args.address

        while True:
            block = f.read(int(args.block_size, 0))
            if block == b'': break

            if args.encrypt:
                block = jl_crypt_mengli(block)

            uboot.mem_write(addr, block)
            addr += len(block)

        uboot.mem_jump(args.address, args.arg)

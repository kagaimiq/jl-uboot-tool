from jltech.uboot import JL_MSCDevice, JL_UBOOT
from jltech.cipher import jl_crc_cipher, cipher_bytes
import argparse, struct

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
                     " Please keep in mind that encrypted loaders usually use a block size of 512 bytes. ")

ap.add_argument('--mitraddr', type=anyint,
                help='Address of the "MiZUTraX" thing to dump after execution')

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
    uboot = JL_UBOOT(dev.dev)

    def mem_read(addr, size):
        data = uboot.mem_read(addr, size)
        if args.encrypt: data = cipher_bytes(jl_crc_cipher, data)
        return data

    def mem_write(addr, data):
        if args.encrypt: data = cipher_bytes(jl_crc_cipher, data)
        uboot.mem_write(addr, data)

    #----------------------------------------------------

    with open(args.file, 'rb') as f:
        addr = args.address

        while True:
            block = f.read(int(args.block_size, 0))
            if block == b'': break

            mem_write(addr, block)
            addr += len(block)

    #----------------------------------------------------

    try:
        uboot.mem_jump(args.address, args.arg)
    except Exception as e:
        print('Something failed during execution, is your code running too long or locking up the USB code, or what?')
        print('Message:', e)
        exit(1)

    #----------------------------------------------------

    def mitrparse(addr):
        magic, buffaddr, buffsize, nbytes = struct.unpack('<8sIII', mem_read(addr, 8+12))

        if magic != b'MiZUTraX':
            print("!!! There isn't any MizuTrax out there!")
            return

        print('////////// MiZU TraX LogTrace thingy //////////')

        print('Data spans %x-%x (%d bytes long), total data written: %d bytes' % (buffaddr, buffaddr + buffsize - 1, buffsize, nbytes))

        data = mem_read(buffaddr, min(buffsize, nbytes))

        if nbytes > buffsize:
            splitpos = nbytes % buffsize
            data = data[splitpos:] + data[:splitpos]
            print('## %d bytes left the scene' % (nbytes - buffsize))

        print('============= The Data =============')
        print(data.decode('utf-8', errors='ignore'))
        print('====================================')

    if args.mitraddr:
        mitrparse(args.mitraddr)


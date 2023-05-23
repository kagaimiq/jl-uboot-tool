from jl_stuff import *
from jl_uboot import JL_UBOOT, SCSIException
import argparse, cmd, time
import pathlib, yaml

ap = argparse.ArgumentParser(description='JieLi tech test X1000000',
                             epilog='JieLi technology gives us opportunity to make our fantasy go!')

ap.add_argument('--device',
                help='Specify a path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:), ' +
                     'if not specified, then it tries to search for devices.')

ap.add_argument('--loader',
                help='Custom loader binary load address and file',
                metavar=('ADDR','FILE'), nargs=2)

ap.add_argument('--loader-arg',
                help="Loader's numerical argument (overrides the default)",
                metavar='ARG')

ap.add_argument('--force-loader',
                help="Explicitly run the loader, even when it's not needed",
                action='store_true')

args = ap.parse_args()

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

scriptroot = pathlib.Path(__file__).parent

JL_chips        = yaml.load(open(scriptroot/'loaderblobs'/'chips.yaml'),        Loader=yaml.SafeLoader)
JL_usb_loaders  = yaml.load(open(scriptroot/'loaderblobs'/'usb-loaders.yaml'),  Loader=yaml.SafeLoader)
JL_uart_loaders = yaml.load(open(scriptroot/'loaderblobs'/'uart-loaders.yaml'), Loader=yaml.SafeLoader)

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

def makebar(ratio, length):
    bratio = int(ratio * length)

    bar = ''

    if bratio > 0:
        bar += '=' * (bratio - 1)
        bar += '>'

    bar += ' ' * (length - bratio)

    return bar

def largedigits(number, count=-1):
    chars = (
        ('  _____ ',' |   / |',' |  /  |',' |_/___|'),
        ('    _   ','   /|   ','    |   ','  __|__ '),
        ('  _____ ',' |     |','  _____|',' |______'),
        ('  _____ ','    ___|','       |',' ______|'),
        ('        ',' |    | ',' |____|_','      | '),
        ('  ______',' |_____ ','       |',' ______|'),
        ('  ______',' |_____ ',' |     |',' |_____|'),
        ('  _____ ',' |     |','       |','       |'),
        ('  _____ ',' |_____|',' |     |',' |_____|'),
        ('  _____ ',' |     |',' |_____|',' ______|'),
        ('  _____ ',' |_____|',' |     |',' |     |'),
        ('  ______',' |_____/',' |     |',' |_____|'),
        ('  _____ ',' |     |',' |      ',' |______'),
        ('  _____ ',' |     |',' |     |',' |____/ '),
        ('  ______',' |_____ ',' |      ',' |______'),
        ('  ______',' |_____ ',' |      ',' |      '),
    )

    for iln in range(4):
        ln = ''

        for i in range(count):
            ln = chars[(number >> (i * 4)) & 0xf][iln] + ln

        print(ln)

    print()



class DasShell(cmd.Cmd):
    intro = \
    """
  .--------------------------------------------------.
  |     _____________                                |
  |    /___  __  ___/                                |
  |       / / / /     _______                        |
  |  __  / / / /        | |    | | |_   _   _  |_    |
  | / /_/ / / /____   |_| |__  |_| |_| |_| |_| |_    |
  | \____/ /______/                                  |
  |                                                  |
  | JieLi tech console. Type 'help' or '?' for help. |
  '--------------------------------------------------'
    """
    prompt = '=>JL: '

    def __init__(self, dev):
        super(DasShell, self).__init__()
        self.dev = dev

    def emptyline(self):
        pass

    def do_exit(self, args):
        """Get out of the shell"""
        return True

    #------#------#------#------#------#------#------#------#------#------#

    def do_chipkey(self, args):
        """Read the chip key from the chip
        chipkey
        """

        try:
            key = dev.chip_key()
        except SCSIException:
            print("Failed to get the chip key")
            return

        print('Your chip key is...')

        largedigits(key, 4)

        if key == 0xffff:
            print("All clean!")
        elif key == 0x0000:
            print("All burnt out! W-What? Yes! Maybe something went wrong?!")
        else:
            print("There's something programmed there!")

    def do_onlinedev(self, args):
        """Get the device type and info we're working with
        onlinedev
        """

        try:
            info = dev.online_device()
        except SCSIException:
            print("Failed to get the online device info")
            return

        devtypes = {
            0x00: 'None',
            0x01: 'SDRAM',
            0x02: 'SD card',
            0x03: 'SPI NOR flash (on SPI0)',
            0x04: 'SPI NAND flash (on SPI0)',
            0x05: 'OTP',
            0x10: 'SD card (2)',
            0x11: 'SD card (3)',
            0x12: 'SD card (4)',
            0x13: 'Something 0x13',
            0x14: 'Something 0x14',
            0x15: 'Something 0x15',
            0x16: 'SPI NOR flash (on SPI1)',
            0x17: 'SPI NOR flash (on SPI1)',
        }

        print('Device type:\n  0x%02x [%s]' % (info['type'], devtypes.get(info['type'])))
        print("\nDevice ID:")
        largedigits(info['id'], 8)

    #------#------#------#------#------#------#------#------#------#------#

    def do_read(self, args):
        """Read flash to file.
        read <address> <length> <file>
        """
#        <length> can be 0 to dump whole flash (size aligned to the address used)
#        """

        args = args.split(maxsplit=2)

        if len(args) < 3:
            print("Not enough arguments!")
            self.do_help('read')
            return

        try:
            address = int(args[0], 0)
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        try:
            length = int(args[1], 0)
        except ValueError:
            print("<length> [%s] is not a number!" % args[1])
            return

        try:
            fil = open(args[2], 'wb')
        except Exception as e:
            print("Can't open file [%s] - %s" % (args[2], e))
            return

        with fil:
            maxlen = self.dev.flash_max_page_size()

            print()

            dlength = 0

            while length > 0:
                n = min(maxlen, length)

                #print("\rReading %x-%x..." % (address, address + length - 1), end='', flush=True)

                t = time.time()
                data = self.dev.flash_read(address, n)
                t = time.time() - t

                fil.write(data)

                length -= n
                dlength += n

                ratio = dlength / (dlength + length)
                print("\rReading %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
                print(" %.2f KB/s" % (len(data) / 1000 / t), end='', flush=True)

                address += n

            print("")

    #-------------------------------------

    def do_write(self, args):
        """Write file to flash.
        write <address> <file>
        """

        args = args.split(maxsplit=1)

        if len(args) < 2:
            print("Not enough arguments!")
            self.do_help('write')
            return

        try:
            address = int(args[0], 0)
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        try:
            fil = open(args[1], 'rb')
        except Exception as e:
            print("Can't open file [%s] - %s" % (args[1], e))
            return

        with fil:
            fil.seek(0, 2)
            length = fil.tell()
            fil.seek(0)

            maxlen = self.dev.flash_max_page_size()

            print()

            xaddress = address
            xlength = length
            dlength = 0

            while length > 0:
                if length >= 0x10000 and (address & 0xffff) == 0:
                    block = 0x10000
                else:
                    block = 0x1000

                n = min(length, block - (address % block))

                #print("\rErasing %x-%x..." % (address, address + length - 1), end='', flush=True)

                t = time.time()
                if block > 0x1000: self.dev.flash_erase_block(address)
                else:              self.dev.flash_erase_sector(address)
                t = time.time() - t

                length -= n
                dlength += n

                ratio = dlength / (dlength + length)
                print("\rErasing %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
                print(" %.2f KB/s" % (block / 1000 / t), end='', flush=True)

                address += n

            print()

            address = xaddress
            length = xlength
            dlength = 0

            while length > 0:
                block = fil.read(maxlen)
                if block == b'': break
                n = len(block)

                #print("\rWriting %x-%x..." % (address, address + length - 1), end='', flush=True)

                t = time.time()
                self.dev.flash_write(address, block)
                t = time.time() - t

                length -= n
                dlength += n

                ratio = dlength / (dlength + length)
                print("\rWriting %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
                print(" %.2f KB/s" % (len(block) / 1000 / t), end='', flush=True)

                address += n

            print("")

    #-------------------------------------

    def do_erase(self, args):
        """Erase flash.
        erase <address> <length>
        """
#        erase [<address> [<length>]]
#
#        If <address> and <length> is not specified,
#         then the whole flash will be erased.
#
#        If only the <address> is specified, then everything starting from
#         that address will be erased. (the same works when <length> specified as 0)
#        """

        args = args.split(maxsplit=2)

        if len(args) < 2:
            print("Not enough arguments!")
            self.do_help('erase')
            return

        try:
            address = int(args[0], 0)
        except IndexError:
            address = 0
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        try:
            length = int(args[1], 0)
        except IndexError:
            length = 0
        except ValueError:
            print("<length> [%s] is not a number!" % args[1])
            return

        print()

        dlength = 0

        while length > 0:
            if length >= 0x10000 and (address & 0xffff) == 0:
                block = 0x10000
            else:
                block = 0x1000

            n = min(length, block - (address % block))

            #print("\rErasing %x-%x..." % (address, address + length - 1), end='', flush=True)

            t = time.time()
            if block > 0x1000: self.dev.flash_erase_block(address)
            else:              self.dev.flash_erase_sector(address)
            t = time.time() - t

            length -= n
            dlength += n

            ratio = dlength / (dlength + length)
            print("\rErasing %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
            print(" %.2f KB/s" % (block / 1000 / t), end='', flush=True)

            address += n

        print("")

    #-------------------------------------

    def do_dump(self, args):
        """Dump flash to console.
        dump <address> [<length>]

        If <length> is not specified, then it will default to 256 bytes.
        """

        args = args.split(maxsplit=2)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('dump')
            return

        try:
            address = int(args[0], 0)
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        try:
            length = int(args[1], 0)
        except IndexError:
            length = 256
        except ValueError:
            print("<length> [%s] is not a number!" % args[1])
            return

        maxlen = self.dev.flash_max_page_size()

        while length > 0:
            n = min(length, maxlen)

            hexdump(self.dev.flash_read(address, n), address=address)

            address += n
            length -= n

    #------#------#------#------#------#------#------#------#------#------#

    def do_reset(self, args):
        """Reset the chip.
        reset [<code>]

        If <code> is not specified, then it will default to 1.
        """

        args = args.split(maxsplit=2)

        try:
            code = int(args[0], 0)
        except IndexError:
            code = 1
        except ValueError:
            print("<code> [%s] is not a number!" % args[0])
            return

        try:
            self.dev.reset(code)
        except SCSIException:
            print("dies...")
            return True

    #------#------#------#------#------#------#------#------#------#------#

    def do_vmdump(self, args):
        """Dumps the VM.
        vmdump <address>

        <address> is the address of the VM in the flash,
            can be identified as the 4k block that's starting with
            "55 AA AA 55", "AE A5 5A EA" or "51 5A A5 15".
        """

        """
        v1:
            AE A5 5A EA <= Sign         [DV12]
            51 5A A5 15 <= Another Sign [DV16]

            CcccccccLlllllllNnnnnnnn10101101

            Cccccccc     = CRC16 of data (lower 8 bits)
            Llllllll     = Data length
            Nnnnnnnn     = ID

        v2:
            55 AA AA 55 <= Valid
            88 44 11 22 <= Defrag started
            AA 55 11 22 <= Defrag almost completed

            CcccccccNnnnnnnnLlllllllllll1101

            Cccccccc     = CRC16 of data (lower 8 bits)
            Nnnnnnnn     = ID
            Llllllllllll = Data length

        v3:
            55 AA AA 55 <= Valid
            88 44 11 22 <= Defrag started
            AA 55 11 22 <= Defrag almost completed

            LlllllllllllNnnnnnnnnnnnCccccccc

            Llllllllllll = Data length
            Nnnnnnnnnnnn = ID
            Cccccccc     = CRC16 of data (lower 8 bits)
        """

        args = args.split(maxsplit=2)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('vmdump')
            return

        try:
            address = int(args[0], 0)
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        #--------------------------------------------

        if self.dev.flash_read(address, 4) not in (b'\x55\xaa\xaa\x55', b'\xae\xa5\x5a\xea', b'\x51\x5a\xa5\x15'):
            print("There isn't any valid VM at %x" % address)
            return

        caddr = address + 4


        def dec_v1(addr):
            hdr = int.from_bytes(self.dev.flash_read(addr, 4), 'little')

            if hdr == 0xffffffff:
                return None

            if (hdr & 0xff) != 0xAD:
                return None

            ecrc = (hdr >> 24) & 0xff
            elen = (hdr >> 16) & 0xff
            eid  = (hdr >> 8)  & 0xff

            edat = self.dev.flash_read(addr + 4, elen)

            if (jl_crc16(edat) & 0xff) != ecrc:
                return None

            return {'len': elen + 4, 'id': eid, 'data': edat}

        def dec_v2(addr):
            hdr = int.from_bytes(self.dev.flash_read(addr, 4), 'little')

            if hdr == 0xffffffff:
                return None

            if (hdr & 0xf) != 0xD:
                return None

            ecrc = (hdr >> 24) & 0xff
            eid  = (hdr >> 16) & 0xff
            elen = (hdr >> 4)  & 0xfff

            edat = self.dev.flash_read(addr + 4, elen)

            if (jl_crc16(edat) & 0xff) != ecrc:
                return None

            return {'len': elen + 4, 'id': eid, 'data': edat}

        def dec_v3(addr):
            hdr = int.from_bytes(self.dev.flash_read(addr, 4), 'little')

            if hdr == 0xffffffff:
                return None

            ecrc = (hdr >> 0)  & 0xff
            eid  = (hdr >> 8)  & 0xfff
            elen = (hdr >> 20) & 0xfff

            edat = self.dev.flash_read(addr + 4, elen)

            if (jl_crc16(edat) & 0xff) != ecrc:
                return None

            return {'len': elen + 4, 'id': eid, 'data': edat}

        fmt = -1

        while True:
            if fmt < 0:
                if dec_v1(caddr) is not None:
                    fmt = 0
                    continue

                if dec_v2(caddr) is not None:
                    fmt = 1
                    continue

                if dec_v3(caddr) is not None:
                    fmt = 2
                    continue

                break

            else:
                ent = ([dec_v1, dec_v2, dec_v3][fmt])(caddr)
                if ent is None:
                    fmt = -1
                    continue

            print('[%4d]:' % ent['id'], ent['data'].hex(':'))

            caddr += ent['len']

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

if args.device is not None:
    device = args.device

else:
    from jldevfind import choose_jl_device

    device = choose_jl_device()
    if device is None:
        exit(1)

with JL_UBOOT(device) as dev:
    vendor, product, prodrev = dev.inquiry()

    chipname = vendor.lower()
    if chipname not in JL_chips:
        print("Oh well, chip %s is either not supported or is invalid." % chipname)
        exit(2)

    family = JL_chips[chipname]
    print('Chip: %s (%s)' % (chipname, ', '.join(family['name'])))

    runtheloader = False

    if args.force_loader:
        print("Loader will be explicitly loaded as specified on the command line")
        runtheloader = True

    elif product == 'UBOOT1.00':
        print("UBOOT1.00 device, loader will be loaded")
        runtheloader = True

    if runtheloader:
        if args.loader is not None:
            print("Using custom loader specified on the command line")
            addr = int(args.loader[0], 0)
            path = args.loader[1]

            if not os.path.exists(path):
                print("File '%s' does not exist..." % path)
                exit(3)

            loader = {"file": path, "address": addr}

        else:
            print("Using builtin loader collection")

            if chipname not in JL_usb_loaders:
                print("No USB loader is available.")
                exit(3)

            loader = JL_usb_loaders[chipname]

        ###########

        with open(scriptroot/loader['file'], 'rb') as f:
            addr = loader['address']

            while True:
                block = f.read(loader.get('blocksize', 512))
                if block == b'': break

                dev.mem_write(addr, block)

                addr += len(block)

        if args.loader_arg is not None:
            loader['argument'] = int(args.loader_arg, 0)

        if 'argument' not in loader:
            loader['argument'] = 0

        print("Running loader at %(address)08x, with argument %(argument)04x..." % loader)

        dev.mem_jump(loader['address'], loader['argument'])

        print("Loader uploaded successfully")

    #-------------------------

    ds = DasShell(dev)

    print("----------------:------------------------")

    try:
        print("Online device   : id=%(id)x type=%(type)d" % dev.online_device())
    except SCSIException:
        print("Failed to get online device info.. TODO")

    try:
        print("Chip key        : %04x" % dev.chip_key())
    except SCSIException:
        print("Failed to get chip key.. TODO")

    try:
        print("Flash page size : %d" % dev.flash_max_page_size())
    except SCSIException:
        print("Failed to get flash page size.. TODO")

    print("----------------:------------------------")

    ds.onecmd('onlinedev')
    ds.onecmd('chipkey')

    ds.cmdloop()

from jl_stuff import *
from jl_uboot import JL_UBOOT, JL_Loader, SCSIException
import argparse, cmd, time
import pathlib, yaml

ap = argparse.ArgumentParser(description='JieLi UBOOT tool',
                             epilog='TaiyouKouhaTsuden System ver.125 by TsutsuMin')

def anyint(s):
    return int(s, 0)

ap.add_argument('--device',
                help='Specify a path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:), ' +
                     'if not specified, then it tries to search for devices.')

ap.add_argument('--loader-arg', type=anyint, metavar='ARG',
                help="Loader's numerical argument (overrides the default)")

ap.add_argument('--custom-loaders', metavar='FILE',
                help='Path to the custom loader spec YAML file. ' +
                     'If something goes wrong when loading it, then the builtin loader spec is used.')

ap.add_argument('--force-loader', action='store_true',
                help="Run the loader even when it's not needed")

args = ap.parse_args()

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

scriptroot = pathlib.Path(__file__).parent

JL_chips        = yaml.load(open(scriptroot/'loaderblobs'/'chips.yaml'),        Loader=yaml.SafeLoader)
JL_usb_loaders  = yaml.load(open(scriptroot/'loaderblobs'/'usb-loaders.yaml'),  Loader=yaml.SafeLoader)
JL_uart_loaders = yaml.load(open(scriptroot/'loaderblobs'/'uart-loaders.yaml'), Loader=yaml.SafeLoader)

print('** %d chips, %d USB loaders, %d UART loaders **' % (len(JL_chips), len(JL_usb_loaders), len(JL_uart_loaders)))

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

dev_type_strs = {
    0x00: 'None',
    0x01: 'SDRAM',
    0x02: 'SD card',
    0x03: 'SPI NOR flash on SPI0',
    0x04: 'SPI NAND flash on SPI0',
    0x05: 'OTP',
    0x10: 'SD card 2',
    0x11: 'SD card 3',
    0x12: 'SD card 4',
    0x13: 'Something 0x13',
    0x14: 'Something 0x14',
    0x15: 'Something 0x15',
    0x16: 'SPI NOR flash on SPI1',
    0x17: 'SPI NOR flash on SPI1',
}



def makebar(ratio, length):
    bratio = int(ratio * length)

    bar = ''

    if bratio > 0:
        bar += '=' * (bratio - 1)
        bar += '>'

    bar += ' ' * (length - bratio)

    return bar

def print_largeletters(string):
    string = string.upper()

    chars = {
        '0': ('  _____ ', ' |   / |', ' |  /  |', ' |_/___|'),
        '1': ('    _   ', '   /|   ', '    |   ', '  __|__ '),
        '2': ('  _____ ', ' |     |', '  _____|', ' |______'),
        '3': ('  _____ ', '    ___|', '       |', ' ______|'),
        '4': ('        ', ' |    | ', ' |____|_', '      | '),
        '5': ('  ______', ' |_____ ', '       |', ' ______|'),
        '6': ('  ______', ' |_____ ', ' |     |', ' |_____|'),
        '7': ('  _____ ', ' |     |', '       |', '       |'),
        '8': ('  _____ ', ' |_____|', ' |     |', ' |_____|'),
        '9': ('  _____ ', ' |     |', ' |_____|', ' ______|'),
        'A': ('  _____ ', ' |_____|', ' |     |', ' |     |'),
        'B': ('  ______', ' |_____/', ' |     |', ' |_____|'),
        'C': ('  _____ ', ' |     |', ' |      ', ' |______'),
        'D': ('  _____ ', ' |     |', ' |     |', ' |____/ '),
        'E': ('  ______', ' |_____ ', ' |      ', ' |______'),
        'F': ('  ______', ' |_____ ', ' |      ', ' |      '),
        'G': ('  _____ ', ' |      ', ' |  ___ ', ' |_____|'),
        'H': ('        ', ' |_____|', ' |     |', ' |     |'),
        'I': (' _______', '    |   ', '    |   ', ' ___|___'),
        'J': ('    ___ ', '       |', '       |', ' |_____|'),
        'K': ('        ', ' |___/  ', ' |   \  ', ' |     \\'),
        'L': ('        ', ' |      ', ' |      ', ' |_____|'),
        'M': (' ______ ', ' |  |  |', ' |     |', ' |     |'),
        'N': ('        ', ' |\    |', ' |  \  |', ' |    \|'),
        'O': ('  _____ ', ' |     |', ' |     |', ' |_____|'),
        'P': ('  ______', ' |_____/', ' |      ', ' |      '),
        'Q': ('  _____ ', ' |     |', ' |   \ |', ' |____\|'),
        'R': ('  ______', ' |_____/', ' |     |', ' |     |'),
        'S': (' _______', ' \_____ ', '       |', ' ______|'),
        'T': (' _______', '    |   ', '    |   ', '    |   '),
        'U': ('        ', ' |     |', ' |     |', ' |_____|'),
        'V': ('        ', ' |     |', '  \   / ', '   \_/  '),
        'W': ('        ', ' |     |', ' |  |  |', ' |__|__|'),
        'X': ('        ', ' \     /', '  >---< ', ' /     \\'),
        'Y': ('        ', ' |     |', ' |_____|', ' ______|'),
        'Z': (' _______', '    ___/', '   /    ', ' _/_____'),
    }

    height = 0

    for c in string:
        char = chars.get(c, [])
        height = max(height, len(char))

    for line in range(height):
        ln = ''

        for c in string:
            char = chars.get(c, [])

            if line >= len(char): continue
            ln += char[line]

        print(ln)

    print()



class DasShell(cmd.Cmd):
    intro = \
    """
  =========================================================
  .-------------------.
  |     _____________ | .------------------------------.
  |    /___  __  ___/ | |       JieLi UBOOT Tool
  |       / / / /     | |        - Das Shell -
  |  __  / / / /      | `------------------------------.
  | / /_/ / / /____   |    -*- JieLi tech console -*-  |
  | \____/ /______/   |   Type 'help' or '?' for help. |
  |                   | `------------------------------'
  `-------------------'
  =========================================================
    """
    prompt = '=>JL: '

    def __init__(self, dev):
        super(DasShell, self).__init__()
        self.dev = dev


        self.bufsize = self.dev.usb_buffer_size()



    def emptyline(self):
        pass

    def do_exit(self, args):
        """Get out of the shell"""
        print("Bye!")
        return True

    #------#------#------#------#------#------#------#------#------#------#

    def do_chipkey(self, args):
        """Read the chip key from the chip
        chipkey
        """

        try:
            key = self.dev.chip_key()
        except SCSIException:
            print("Failed to get the chip key")
            return

        print('Your chip key is...')

        print_largeletters('%04X' % key)

        if key == 0xffff:
            print("All bits are nice and clean! You're good to go!")
        elif key == 0x0000:
            print("All bits of your chipkey seems to be burnt out!")
            print("Maybe something gone wrong? Or this is what it should be?")
        else:
            nbits = bin(key).count('1')
            print("There are %d bits intact!" % nbits)

    def do_burnchipkey(self, args):
        """ Burn the chipkey into the chip
        burnchipkey <key>
        """

        args = args.split(maxsplit=1)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('burnchipkey')
            return

        try:
            newkey = int(args[0], 0) & 0xffff
        except ValueError:
            print("<key> [%s] is not a number!" % args[0])
            return

        try:
            key = self.dev.chip_key()
        except SCSIException:
            print("Failed to get the chip key")
            return

        print('Your current chip key:')
        print_largeletters('%04X' % key)

        print("Chip key you're going to burn:")
        print_largeletters('%04X' % newkey)

        realkey = newkey & key

        #
        # Print the messages..
        #
        if key == 0x0000:
            if newkey == 0xffff:
                print("Nice try. Do you think you can ever do that?")
            elif newkey == 0x0000:
                print("You chipkey is already burned to death.")
                return
            else:
                print("Well, your chipkey has been burned to death. You think you can do something?")

        elif key == 0xffff:
            if newkey == 0xffff:
                print("Your chipkey is already nice and clean! Cheers!")
                return

            elif newkey == 0x0000:
                print("Hey! Look at these pretty FF's! Do you ever want to burn them all to death?")

            else:
                print("Well, seems like you want to write the chipkey into a blank chip.. Yes?")

        else:
            if newkey == 0xffff:
                print("Hmmm... You really think you can clear the chipkey?")

            elif newkey == 0x0000:
                print("Oh, so you want to burn the remaining bits to death? Do you?")

            elif key == newkey:
                print("The chip already has this key burned in!")
                return

            else:
                if realkey == newkey:
                    print("Well, this key could be burned into the chip. Do you want to proceed?")

                else:
                    print("Well, there is a key burned into this chip which won't let this key being burned correctly.")

                    print("Here's what you get instead:")
                    print_largeletters('%04X' % realkey)

                    #print("\nHere are the bits of your current key:")
                    #print(' '.join(['1' if key & (0x8000 >> b) else '0' for b in range(16)]))

                    #print("\nAnd the bits of the key you're going to write:")
                    #print(' '.join(['1' if newkey & (0x8000 >> b) else '0' for b in range(16)]))

                    #print("\nBut since you can't unburn a bit, you're going to get this instead:")
                    #print(' '.join(['1' if realkey & (0x8000 >> b) else '0' for b in range(16)]))

                    print("\nDo you still want to proceed?")

        answer = input('Say "yes i do" to proceed: ')
        if answer.strip().lower() != 'yes i do':
            print("You didn't answer correctly. Aborting")
            return

        try:
            result = self.dev.write_chipkey(newkey)
        except SCSIException:
            print("Failed to burn chipkey!")
            return

        print("Result:")
        print_largeletters('%04x' % result)

    def do_onlinedev(self, args):
        """Get the device type and info we're working with
        onlinedev
        """

        try:
            info = self.dev.online_device()
        except SCSIException:
            print("Failed to get the online device info")
            return

        print('Device type:\n  0x%02x [%s]' % (info['type'], dev_type_strs.get(info['type'])))
        print("\nDevice ID:")
        print_largeletters('%08X' %  info['id'])

    def do_execcmd(self, args):
        """Execute an arbitrary loader command
        execcmd <opcode> [<arg bytes>]
        """

        args = args.split(maxsplit=1)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('execcmd')
            return

        try:
            opcode = int(args[0], 0) & 0xffff
        except ValueError:
            print("<opcode> [%s] is not a number!" % args[0])
            return

        try:
            data = bytes.fromhex(args[1])
        except IndexError:
            data = b''
        except ValueError:
            print('Wrong hex string "%s"!' % args[1])
            return

        try:
            resp = self.dev.cmd_exec(opcode, data, ignore_wrong_resp=True)
            print('Response: %04x / [%s]' % (resp[0], resp[1].hex(' ')))
        except Exception as e:
            print("Command execution failed: ", e)

    #------#------#------#------#------#------#------#------#------#------#

    def flash_erase(self, address, length):
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

    def flash_write_file(self, address, length, fil):
        buffsz = self.dev.usb_buffer_size()

        dlength = 0

        while length > 0:
            block = fil.read(buffsz)
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

        print()

    def flash_read_file(self, address, fil):
        buffsz = self.dev.usb_buffer_size()

        dlength = 0

        while length > 0:
            n = min(buffsz, length)

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

        print()

    #-------------------------------------

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
            print()
            self.flash_read_file(address, fil)

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

            print()

            self.flash_erase(address, length)
            self.flash_write_file(address, length, fil)

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

        self.flash_erase(address, length)

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

        buffsz = self.dev.usb_buffer_size()

        while length > 0:
            n = min(length, buffsz)

            hexdump(self.dev.flash_read(address, n), address=address)

            address += n
            length -= n

    #------#------#------#------#------#------#------#------#------#------#

    def do_reset(self, args):
        """Reset the chip. (or Run App)
        reset [<arg>]

        If <arg> is not specified, then it will default to 1.
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
            self.dev.run_app(code)
        except Exception as e:
            print("<!> Exiting..", e)
            return True

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
    print('Chip: %s (%s)' % (chipname.upper(), ', '.join(family['name'])))

    #print_largeletters(chipname)

    runtheloader = False

    if args.force_loader:
        print("Will run the loader regardless of whether it is needed or not.")
        runtheloader = True

    elif product == 'UBOOT1.00':
        print("This is the UBOOT1.00 device, so we'll run the loader.")
        runtheloader = True

    if runtheloader:
        gotcustom = False

        #
        # Is there any custom loader spec passed?
        #
        if args.custom_loaders is not None:
            try:
                loaderspec = yaml.load(open(args.custom_loaders), Loader=yaml.SafeLoader)
                loaderroot = pathlib.Path(args.custom_loaders).parent

                gotcustom = True
            except Exception as e:
                print("Something went wrong while loading the custom loader spec file:", e)

        #
        # We did load the custom loader spec, so check if it has that chip.
        #
        if gotcustom:
            if chipname not in loaderspec:
                print("There is no USB loader for %s in the provided loader spec. Proceeding with builtin" % chipname)
                gotcustom = False

        #
        # Use the builtin loader spec if we can't use a custom loader spec.
        #
        if not gotcustom:
            loaderspec = JL_usb_loaders
            loaderroot = scriptroot

        #
        # Is there a loader for our chip?
        #
        if chipname not in loaderspec:
            print("Sorry, but there is no USB loader available for %s." % chipname)
            exit(3)

        loader = loaderspec[chipname]

        with open(loaderroot/loader['file'], 'rb') as f:
            blocksz = loader.get('blocksize', 512)

            #
            # Write
            #
            addr = loader['address']
            while True:
                block = f.read(blocksz)
                if block == b'': break

                dev.mem_write(addr, block)

                addr += len(block)

            f.seek(0)

            #
            # Verify
            #
            addr = loader['address']
            while True:
                block = f.read(blocksz)
                if block == b'': break

                rblock = dev.mem_read(addr, len(block))
                if block != rblock:
                    print('Mismatch at %08x!' % addr)
                    break

                addr += len(block)

        if 'argument' not in loader:
            print('This loader does not seem to have a default argument.')
            loader['argument'] = (0<<12) | (4<<4) | (1<<0) # spi mode=0, div=4, mem=1 (spi nor)

        if args.loader_arg is not None:
            print('Overriding the default loader argument (%04x) with %04x' % (loader['argument'], args.loader_arg))
            loader['argument'] = args.loader_arg

        if 'entry' not in loader:
            loader['entry'] = loader['address']

        print("Running loader (loaded to 0x%(address)04x) on 0x%(entry)04x, with argument 0x%(argument)04x..." % loader)

        try:
            dev.mem_jump(loader['entry'], loader['argument'])
            print("Loader runs successfully.")
        except SCSIException:
            print("Failed to run loader.")

    #
    # Let's try to gather some info beforehand
    #

    loader = JL_Loader(dev)

    print("----------------:------------------------")

    try:
        odev = loader.online_device()
        print("Online device   : id=0x%06x type=%d (%s)"
                    % (odev['id'], odev['type'], dev_type_strs.get(odev['type'], 'unknown')))
    except SCSIException:
        pass #print("(!) Failed to get online device info")

    try:
        print("Chip key        : 0x%04x" % loader.chip_key())
    except SCSIException:
        pass #print("(!) Failed to get chip key")

    try:
        print("USB buffer size : %d" % loader.usb_buffer_size())
    except SCSIException:
        pass #print("(!) Failed to get USB buffer size")

    try:
        print("Status          : 0x%02x" % loader.read_status())
    except SCSIException:
        pass #print("(!) Failed to read status")

    try:
        print("Device ID       : 0x%06x" % loader.read_id())
    except SCSIException:
        pass #print("(!) Failed to read device ID")

    #try:
    #    print("Loader version  : %s" % loader.version())
    #except SCSIException:
    #    pass #print("(!) Failed to get loader version")

    #try:
    #    print("MaskROM ID      : 0x%08x" % loader.maskrom_id())
    #except SCSIException:
    #    pass #print("(!) Failed to get MaskROM ID")

    print("----------------:------------------------")

    #
    # Let's enter the shell!
    #
    ds = DasShell(loader)

    #ds.onecmd('onlinedev')
    ds.onecmd('chipkey')

    ds.cmdloop()

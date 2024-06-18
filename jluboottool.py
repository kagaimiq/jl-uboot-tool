from scsiio.common import SCSIException
from jltech.uboot import JL_MSCDevice, JL_UBOOT, JL_LoaderV2, JL_LoaderV1
from jltech.cipher import cipher_bytes, jl_crc_cipher, jl_rxgp_cipher
from jltech.utils import *
import argparse, cmd, time
import pathlib, yaml

ap = argparse.ArgumentParser(description='JieLi UBOOT tool - the swiss army knife for JieLi technology',
                             epilog="// it's not that great, actually.")

ap.add_argument('--device',
                help='Specify a path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:), ' +
                     'if not specified, then it tries to search for devices.')

ap.add_argument('--loader-arg', type=anyint, metavar='ARG',
                help="Loader's argument (overrides the default).\n" +
                     "Hint: usually, the argument is parsed by the loader as follows:\n" +
                     "  bit0-3: Target memory (1 = SPI flash, 7 = OTP),\n" +
                     "  bit4-11: Clock divider (0 = default, >0 = 1/n) - base is usually 48 MHz,\n" +
                     "  bit12-13: SPI mode (0 = half-duplex (2-wire) SPI, 1 = duplex (3-wire) SPI, 2 = DSPI, 3 = QSPI)")

ap.add_argument('--custom-loaders', metavar='FILE',
                help='Path to the custom loader spec YAML file. ' +
                     'If something goes wrong when loading it, then the builtin loader spec is used.')

args = ap.parse_args()

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

scriptroot = pathlib.Path(__file__).parent
dataroot   = scriptroot/'data'

JL_chips        = yaml.load(open(dataroot/'chips.yaml'),        Loader=yaml.SafeLoader)
JL_usb_loaders  = yaml.load(open(dataroot/'usb-loaders.yaml'),  Loader=yaml.SafeLoader)
JL_uart_loaders = yaml.load(open(dataroot/'uart-loaders.yaml'), Loader=yaml.SafeLoader)

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

# XXX: this is specific to V2 loaders.
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

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

class DasShell(cmd.Cmd):
    intro = \
    """
  .------------------------------------------------------.
  |     _____________   .------------------------------. |
  |    /___  __  ___/   |       JieLi UBOOT Tool         |
  |       / / / /       |        - Das Shell -           |
  |  __  / / / /        `------------------------------. |
  | / /_/ / / /____        -*- JieLi tech console -*-  | |
  | `____/ /______/       Type 'help' or '?' for help. | |
  |                     `------------------------------' |
  `------------------------------------------------------'
    """
    prompt = '=>JL: '

    def __init__(self, dev):
        super(DasShell, self).__init__()
        self.dev = dev

        try:
            self.buffsize = self.dev.usb_buffer_size()
        except:
            self.buffsize = 512

    def emptyline(self):
        pass

    def do_exit(self, args):
        """Get out of the shell"""
        print("Bye!")
        return True

    #------#------#------#------#------#------#------#------#------#------#

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

        print(f'Current chipkey: >>> 0x{key:04X} <<<')
        print(f'New chipkey:     >>> 0x{newkey:04X} <<<')

        realkey = newkey & key

        #
        # Print the messages..
        #
        if key == 0x0000:
            if newkey == 0xffff:
                print("You think you can restore this back to normal?")
            elif newkey == 0x0000:
                print("Well, everything is burnt down already. So there's nothing to do.")
                return
            else:
                print("Your chipkey seems to be fully burnt out, you think you can do something about it?")

        elif key == 0xffff:
            if newkey == 0xffff:
                print("Your chipkey is already nice and clean! Cheers!")
                return

            elif newkey == 0x0000:
                print("Well, you want to burn all bits down?")

            else:
                print("You are about to burn the chipkey into a chip. Do you want to proceed?")

        else:
            if newkey == 0xffff:
                print("Hmmm... You really think you can clear the chipkey?")

            elif newkey == 0x0000:
                print("Oh, so you want to burn out all of the remaining bits too, right?")

            elif key == newkey:
                print("This chipkey is already burnt into the chip.")
                return

            else:
                if realkey == newkey:
                    print("This key can be successfully written. Do you want to proceed?")

                else:
                    print("Well, the chip already has a key burnt into it, and your provided key couldn't be written properly.")
                    print(f"Here's what you might get instead: >>> 0x{realkey:04X} <<<")
                    print('Do you still want to proceed?')

        # silly approach to confirming a possibly-"dangerous" task.
        answer = input('Say "yes i do" to proceed: ')
        if answer.strip().lower() != 'yes i do':
            print("You didn't answer correctly. Aborting")
            return

        try:
            result = self.dev.write_chipkey(newkey)
        except SCSIException:
            print("Failed to burn chipkey!")
            return

        print(f'Command result: [{result:08X}]')

        curkey = self.dev.chip_key()
        print(f'Current chipkey: >>> 0x{curkey:04X} <<<')

        if curkey == key:
            print('Seems like nothing have happened.')
        elif curkey == realkey and realkey != newkey:
            print('As it have been predicted.')
        elif curkey == newkey:
            print('Done!')
        else:
            print('Something did change...')

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
            print(" %.2f KB/s" % ((block / 1000 / t) if t > 0 else 0), end='', flush=True)

            address += n

        print()

    def flash_write_file(self, address, length, fil):
        dlength = 0

        while length > 0:
            block = fil.read(self.buffsize)
            if block == b'': break
            n = len(block)

            t = time.time()
            self.dev.flash_write(address, block)
            t = time.time() - t

            length -= n
            dlength += n

            ratio = dlength / (dlength + length)
            print("\rWriting %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
            print(" %.2f KB/s" % ((len(block) / 1000 / t) if t > 0 else 0), end='', flush=True)

            address += n

        print()

    def flash_read_file(self, address, length, fil):
        dlength = 0

        while length > 0:
            n = min(self.buffsize, length)

            t = time.time()
            data = self.dev.flash_read(address, n)
            t = time.time() - t

            fil.write(data)

            length -= n
            dlength += n

            ratio = dlength / (dlength + length)
            print("\rReading %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
            print(" %.2f KB/s" % ((len(data) / 1000 / t) if t > 0 else 0), end='', flush=True)

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
            self.flash_read_file(address, length, fil)

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

    def do_erasechip(self, args):
        """Erase whole flash.
        erasechip

        Warning: may not always work!
        """

        self.dev.flash_erase_chip()

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

        while length > 0:
            n = min(length, self.buffsize)

            hexdump(self.dev.flash_read(address, n), base=address)

            address += n
            length -= n

    #------#------#------#------#------#------#------#------#------#------#

    def do_memread(self, args):
        """Read memory to file.
        memread <address> <length> <file>
        """

        args = args.split(maxsplit=2)

        if len(args) < 3:
            print("Not enough arguments!")
            self.do_help('memread')
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
            dlength = 0

            while length > 0:
                n = min(256, length) # FIXME: the BR25 loader doesn't like reading more than 256+15 bytes!

                t = time.time()
                data = self.dev.mem_read(address, n)
                t = time.time() - t

                fil.write(data)

                length -= n
                dlength += n

                ratio = dlength / (dlength + length)
                print("\rReading %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
                print(" %.2f KB/s" % ((len(data) / 1000 / t) if t > 0 else 0), end='', flush=True)

                address += n

            print()

    #-------------------------------------

    def do_memwrite(self, args):
        """Write file to memory.
        memwrite <address> <file>
        """

        args = args.split(maxsplit=1)

        if len(args) < 2:
            print("Not enough arguments!")
            self.do_help('memwrite')
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

            dlength = 0

            while length > 0:
                block = fil.read(256) # FIXME: same deal
                if block == b'': break
                n = len(block)

                t = time.time()
                self.dev.mem_write(address, block)
                t = time.time() - t

                length -= n
                dlength += n

                ratio = dlength / (dlength + length)
                print("\rWriting %08x [%s] %3d%%" % (address, makebar(ratio, 40), ratio * 100), end='')
                print(" %.2f kB/s" % ((len(block) / 1000 / t) if t > 0 else 0), end='', flush=True)

                address += n

            print()

    #-------------------------------------

    def do_memdump(self, args):
        """Dump memory to console.
        memdump <address> [<length>]

        If <length> is not specified, then it will default to 256 bytes.
        """

        args = args.split(maxsplit=2)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('memdump')
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

        while length > 0:
            n = min(length, 256) # FIXME: same deal

            hexdump(self.dev.mem_read(address, n), base=address)

            address += n
            length -= n

    #-------------------------------------

    def memjump(self, args):
        """Execute code at a given address
        memjump <addr> [<arg>]
        
        [<arg>] specifies an 16-bit integer which is passed to the
        code in its loader parameters structure, if any is supported by the chip or its loader.
        If it is not specified, it defaults to 0
        """

        args = args.split(maxsplit=2)

        if len(args) < 1:
            print("Not enough arguments!")
            self.do_help('memjump')
            return

        try:
            address = int(args[0], 0)
        except ValueError:
            print("<address> [%s] is not a number!" % args[0])
            return

        try:
            arg = int(args[1], 0)
        except IndexError:
            arg = 0
        except ValueError:
            print("<arg> [%s] is not a number!" % args[1])
            return

        try:
            self.dev.mem_jump(address, arg)
        except SCSIException as e:
            print('Something failed while executing code.')
            print(e)

    #------#------#------#------#------#------#------#------#------#------#

    def do_reset(self, args):
        """Reset the chip. (or "Run App")
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

with JL_MSCDevice(device) as dev:
    vendor, product, prodrev = dev.inquiry()

    chipname = vendor.lower()
    if chipname not in JL_chips:
        print("Chip '%s' is not supported, or it is invalid." % chipname)
        exit(2)

    print()

    chipspec = JL_chips[chipname]
    print('Chip: %s (%s series)' % (chipname.upper(), ', '.join(chipspec['name'])))

    #
    # Load the loader.
    #   TODO: MUST be moved out somewhere, in order to reuse this in other tools as well.
    #
    uboot = JL_UBOOT(dev.dev)

    runtheloader = False

    if product == 'UBOOT1.00':
        print("This is a UBOOT1.00 device, running the loader.")
        runtheloader = True

    if runtheloader:
        custom_loaderspecs = None

        #
        # Is there any custom loader spec passed?
        #
        if args.custom_loaders is not None:
            print("Trying to use custom loader specs from [%s]..." % args.custom_loaders)

            try:
                custom_loaderspecs = yaml.load(open(args.custom_loaders), Loader=yaml.SafeLoader)
            except Exception as e:
                print("Something went wrong while loading the custom loader spec file:", e)

        #
        # Is there a chip and its USB loader spec in the custom loader spec?
        #
        if custom_loaderspecs is not None:
            if chipname not in custom_loaderspecs:
                print("The custom loader spec does not contain definition for chip %s" % chipname)
                custom_loaderspecs = None

            elif 'usb' not in custom_loaderspecs[chipname]:
                print("There is no USB loader in the custom loader spec for chip %s" % chipname)
                custom_loaderspecs = None

            else:
                loaderspec = custom_loaderspecs[chipname]['usb']
                loaderroot = pathlib.Path(args.custom_loaders).parent

        #
        # If we didn't load the custom loader specs, then try to use the builtin one..
        #
        if custom_loaderspecs is None:
            if chipname not in JL_usb_loaders:
                print("There is no USB loader for chip %s" % chipname)
                exit(3)

            loaderspec = JL_usb_loaders[chipname]
            loaderroot = dataroot

        #
        # Upload the loader!
        #
        with open(loaderroot/loaderspec['file'], 'rb') as f:
            blocksz = loaderspec.get('blocksize', 512)

            ldrcrypt = loaderspec.get('encryption')

            menglicrypt = False

            # does this chip's UBOOT1.00 accept data in mengli encrypted form?
            if 'uboot1.00' in chipspec:
                if 'quirks' in chipspec['uboot1.00']:
                    menglicrypt = chipspec['uboot1.00']['quirks'].get('memory-rw-mengli-crypt') == True

            # shall we ever perform the mengli de/encryption?
            menglicrypt = (not menglicrypt and ldrcrypt == 'MengLi') or (menglicrypt and ldrcrypt != 'MengLi')

            #
            # Write
            #
            addr = loaderspec['address']
            while True:
                block = f.read(blocksz)
                if block == b'': break

                if ldrcrypt == 'RxGp':
                    # just pass it into the dedicated memory write command
                    uboot.mem_write_rxgp(addr, block)

                else:
                    if menglicrypt:
                        block = cipher_bytes(jl_crc_cipher, block)

                    uboot.mem_write(addr, block)

                addr += len(block)

            f.seek(0)

            #
            # Verify
            #
            addr = loaderspec['address']
            while True:
                block = f.read(blocksz)
                if block == b'': break

                if ldrcrypt == 'RxGp':
                    # Decrypt this block in order to check it with an ordinary memory read command
                    block = cipher_bytes(jl_rxgp_cipher, block)

                elif menglicrypt:
                    # if it is mengli encrypted or the mem_read returns it this way, then de/encrypt it.
                    block = cipher_bytes(jl_crc_cipher, block)

                rblock = uboot.mem_read(addr, len(block))
                if block != rblock:
                    print('Mismatch at %08x!' % addr)
                    break

                addr += len(block)

        if 'argument' not in loaderspec:
            loaderspec['argument'] = (0<<12) | (4<<4) | (1<<0) # spi mode=0, div=4, mem=1 (spi nor)

        if args.loader_arg is not None:
            print('Overriding the default loader argument (%04x) with %04x' % (loaderspec['argument'], args.loader_arg))
            loaderspec['argument'] = args.loader_arg

        if 'entry' not in loaderspec:
            loaderspec['entry'] = loaderspec['address']

        print("Running loader (loaded to 0x%(address)04x) on 0x%(entry)04x, with argument 0x%(argument)04x..." % loaderspec)

        try:
            uboot.mem_jump(loaderspec['entry'], loaderspec['argument'])
            print("Loader ran successfully.")
        except SCSIException:
            print("!! Failed to run the loader !!")
            exit(3)

    loader = JL_LoaderV2(dev.dev)

    #
    # Print some quick info summary
    #

    print()
    print('================ Quick info ==================')
    print('  ** %s (%s series) **' % (chipname.upper(), '/'.join(chipspec['name'])))  # redundant?
    if isinstance(loader, JL_LoaderV2):
        print('  Loader protocol: V2')

        try:
            print('  >> Chip key: 0x%04X <<' % loader.chip_key())
        except SCSIException:
            pass

        try:
            print('  - USB buffer size: %d bytes' % loader.usb_buffer_size())
        except SCSIException:
            pass

        try:
            ondev = loader.online_device()
            print('  - Online device:')
            print('     ID: 0x%06x' % ondev['id'])
            print('     Type: 0x%02x (%s)' % (ondev['type'], dev_type_strs.get(ondev['type'], 'unknown')))
        except SCSIException:
            pass

        try:
            print('  - Another Device ID: 0x%08x' % loader.read_id())
        except SCSIException:
            pass

        #try:
        #    print('  - Status: 0x%02x' % loader.read_status())
        #except SCSIException:
        #    pass

        #try:
        #    print('  - MaskROM ID: 0x%08x' % loader.maskrom_id())
        #except SCSIException:
        #    pass

    elif isinstance(loader, JL_LoaderV1):
        print('  Loader protocol: V1')

        try:
            print('  - Device ID: 0x%08x' % loader.read_id())
        except SCSIException:
            pass

        try:
            print('  - Device type: 0x%02x' % loader.online_device())
        except SCSIException:
            pass

    elif isinstance(loader, JL_UBOOT):
        print('  Loader protocol: V2 MaskROM')

    print('==============================================')


    #
    # Let's enter the shell!
    #
    ds = DasShell(loader)

    ds.cmdloop()

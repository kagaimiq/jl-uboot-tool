from scsiio.common import SCSIException
from jltech.uboot import JL_MSCDevice, JL_UBOOT, JL_LoaderV2, JL_LoaderV1
from jltech.cipher import cipher_bytes, jl_crc_cipher, jl_rxgp_cipher
from jltech.utils import *

from scsiio import SCSIDev

from tqdm import tqdm
from pathlib import Path

import argparse
import cmd
import yaml

###############################################################################

ap = argparse.ArgumentParser(description='JieLi UBOOT tool - a tool to interact with the USB bootloader in JieLi chips.')

ap.add_argument('--device', help='Path to a JieLi "UBOOT/DEVICE/UDISK" disk device, e.g. "/dev/sg2" or "\\\\.\\E:"')

ap.add_argument('--chip', help='Narrow down the search/match to a specific chip family e.g. "BR17" or series name e.g. "ac690n"')

ap.add_argument('--arg-target', type=int, metavar='VAL', default=1, choices=range(16),
                help='Target memory type [0:SDRAM, 1/4: SPI NOR, 2/5: SPI NAND, 7: OTP]; default is %(default)d')

ap.add_argument('--arg-clkdiv', type=int, metavar='VAL', default=0, choices=range(256),
                help='Clock divider [0: default, 1..255 = div 1..255]; default is %(default)d')

ap.add_argument('--arg-spimode', type=int, metavar='VAL', default=0, choices=range(4),
                help='SPI mode [0: "3-wire" half-duplex, 1: "4-wire" full-duplex, 2: DSPI, 3: QSPI]; default is %(default)d')

ap.add_argument('--loader-arg', type=anyint, metavar='ARG',
                help="Loader's argument (overrides one set with the '--arg-xxx' arguments above)."
                     " '--arg-target' defines bits 0-3, '--arg-clkdiv' defines bits 4-11 and '--arg-spimode' defines bits 12-13.")

ap.add_argument('cmds', nargs='*',
                help='Commands to run (as if they were typed into an interactive shell).'
                     ' The shell itself is not going to be executed if the commands were specified there.'
                     ' Finally a solution for using it in automated build enviroments! (sort of)')

args = ap.parse_args()

###############################################################################

scriptroot = Path(__file__).parent
dataroot   = scriptroot/'data'

JL_chips        = yaml.load(open(dataroot/'chips.yaml'),        Loader=yaml.SafeLoader)
JL_usb_loaders  = yaml.load(open(dataroot/'usb-loaders.yaml'),  Loader=yaml.SafeLoader)
JL_uart_loaders = yaml.load(open(dataroot/'uart-loaders.yaml'), Loader=yaml.SafeLoader)


def get_chip_name(name):
    # try searching by the family name
    fname = name.lower()
    if fname in JL_chips:
        return fname

    # now try to search by the series name
    for fname in JL_chips:
        if name.upper() in JL_chips[fname]['name']:
            # there it is
            return fname


###############################################################################

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
            self.flash_io_max = self.dev.usb_buffer_size()
        except:
            self.flash_io_max = 512

        # FIXME: new loaders (br23+) use a very small buffer (just 256 bytes long) for *all* I/O,
        #  and the memory operations will happily overwrite past this buffer, while the flash I/O won't.
        self.mem_io_max = 256


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
        # align the address and length to the small eraseblock boundary
        saddr = address & ~0xFFF
        eaddr = (address + length + 0xFFF) & ~0xFFF

        tq = tqdm(desc='Erasing', total=(eaddr-saddr), unit='B', unit_scale=True, unit_divisor=1024)

        try:
            address = saddr
            while address < eaddr:
                if (address & 0xFFFF) == 0 and (eaddr-address) >= 0x10000:
                    # erase a large block (64k)
                    blocksize = 0x10000
                    self.dev.flash_erase_block(address)
                else:
                    # erase a small block (4k)
                    blocksize = 0x1000
                    self.dev.flash_erase_sector(address)

                address += blocksize
                tq.update(blocksize)

        finally:
            tq.close()

    def flash_write_file(self, address, length, fil):
        tq = tqdm(desc='Writing', total=length, unit='B', unit_scale=True, unit_divisor=1024)

        try:
            while length > 0:
                data = fil.read(min(length, self.flash_io_max))
                if data == b'': break

                self.dev.flash_write(address, data)

                length -= len(data)
                address += len(data)
                tq.update(len(data))

        finally:
            tq.close()

    def flash_read_file(self, address, length, fil):
        tq = tqdm(desc='Reading', total=length, unit='B', unit_scale=True, unit_divisor=1024)

        try:
            while length > 0:
                data = self.dev.flash_read(address, min(length, self.flash_io_max))
                fil.write(data)

                length -= len(data)
                address += len(data)
                tq.update(len(data))

        finally:
            tq.close()

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
            n = min(length, self.flash_io_max)

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
            while length > 0:
                n = min(length, self.mem_io_max)

                data = self.dev.mem_read(address, n)

                fil.write(data)

                length -= n
                address += n

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

            while length > 0:
                block = fil.read(self.mem_io_max)
                if block == b'': break
                n = len(block)

                self.dev.mem_write(address, block)

                length -= n
                address += n

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
            n = min(length, self.mem_io_max)

            hexdump(self.dev.mem_read(address, n), base=address)

            address += n
            length -= n

    #-------------------------------------

    def do_memjump(self, args):
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
        """Reset the chip.
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

###############################################################################

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
    0x17: 'SPI NAND flash on SPI1',
}


if args.device is not None:
    # use the provided device path
    devpath = args.device

else:
    # find and ask about the device to use
    from jldevfind import choose_jl_device

    if args.chip is not None:
        filter = get_chip_name(args.chip)
        if filter is None:
            print(f'Unknown chip "{args.chip}"')
            exit(1)
    else:
        filter = None

    devpath = choose_jl_device(venfilter=filter)
    if devpath is None:
        exit(1)



with JL_MSCDevice(devpath) as dev:
    vendor, product, prodrev = dev.inquiry()

    chipname = vendor.lower()
    if chipname not in JL_chips:
        print(f'"{chipname}" is not supported or it is not a JieLi chip.')
        exit(2)

    print()

    chipspec = JL_chips[chipname]
    print(f'Chip: {chipname.upper()} - {"/".join(chipspec["name"])} series')

    #---------------------------

    loader = JL_UBOOT(dev.dev)

    runtheloader = False

    if product == 'UBOOT1.00':
        runtheloader = True

    if runtheloader:
        if chipname not in JL_usb_loaders:
            print(f'No loader available for "{chipname}".')
            exit(3)

        spec = JL_usb_loaders[chipname]

        menglicrypt = False

        with open(dataroot / spec['file'], 'rb') as f:
            block_size = spec.get('blocksize', 512)
            cipher = spec.get('encryption', 'none')

            # does this chip's UBOOT1.00 accept data in mengli encrypted form?
            if 'uboot1.00' in chipspec:
                if 'quirks' in chipspec['uboot1.00']:
                    menglicrypt = chipspec['uboot1.00']['quirks'].get('memory-rw-mengli-crypt') == True

            # shall we ever perform the mengli de/encryption?
            menglicrypt = (not menglicrypt and cipher == 'MengLi') or (menglicrypt and cipher != 'MengLi')

            # upload the loader
            address = spec['address']

            while True:
                block = f.read(block_size)
                if block == b'': break

                if cipher == 'RxGp':
                    # just pass it into the dedicated memory write command
                    loader.mem_write_rxgp(address, block)

                else:
                    if menglicrypt:
                        # scramble with crc_cipher
                        block = cipher_bytes(jl_crc_cipher, block)

                    loader.mem_write(address, block)

                address += len(block)


        if args.loader_arg is not None:
            spec['argument'] = args.loader_arg
        else:
            spec['argument'] = (args.arg_spimode << 12) | (args.arg_clkdiv << 4) | args.arg_target

        print(f'Running loader with argument 0x{spec["argument"]:04X}.')

        try:
            loader.mem_jump(spec['address'], spec['argument'])
            print('The Loader has been successfully installed.')
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

    try:
        print('  >> Chip key: 0x%04X <<' % loader.chip_key())
    except Exception:
        print('  ** failed to get the chip key **')

    try:
        ondev = loader.online_device()
        print('  - Online device:')
        print('     ID: 0x%06x' % ondev['id'])
        print('     Type: 0x%02x (%s)' % (ondev['type'], dev_type_strs.get(ondev['type'], 'unknown')))
    except Exception:
        print('  ** failed to get the online device info **')

    print('==============================================')

    #
    # Let's enter the shell!
    #
    ds = DasShell(loader)

    if len(args.cmds) > 0:
        # just execute commands in order
        for cmd in args.cmds:
            if ds.onecmd(cmd):
                print('**** interrupted ****')
                break
    else:
        # enter the shell
        ds.cmdloop()

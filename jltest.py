from jl_stuff import *
from jl_uboot import JL_UBOOT, SCSIException
import argparse, cmd, time

ap = argparse.ArgumentParser(description='JieLi tech test X999999',
                             epilog='Taiyoukouhatsudensystem ver1.25 by tsutsumin!')

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

families = {
    "AC4100": {
        "name": ["AC410N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/ac4100loader.bin",
                "address": 0x0009000
            }
        }
    },

    "BT15": {
        "name": ["AC460N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/bt15loader.bin",
                "address": 0x0002000 # ?? maybe?
            }
        }
    },

    "BC51": {
        "name": ["AC461N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/bc51loader.bin",
                "address": 0x0002000 # ?? maybe?
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "DV12": {
        "name": ["AC520N"],
    },

    "DV15": {
        "name": ["AC521N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/dv15loader.enc",
                "address": 0x0f02000,
                "encrypted": True
            }
        }
    },

    "DV16": {
        "name": ["AC540N", "AC560N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/dv16loader.bin",
                "address": 0x3f02000
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "SH54": {
        "name": ["AD14N", "AD104N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/sh54loader.bin",
                "address": 0x0000b00,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/sh54loader.uart",
                "address": 0x0000b00,
                "encrypted": True
            }
        }
    },

    "SH55": {
        "name": ["AD15N", "AD105N"],
        "cryptoweirdo": True,

        "loader": {
            "uart": {
                "file": "loaderblobs/uart/sh55loader.uart",
                "address": 0x0000000,
                "encrypted": True
            }
        }
    },

    "UC03": {
        "name": ["AD16N"],
        "cryptoweirdo": True,

        "loader": {
            #"usb": { # ... in some special format
            #    "file": "loaderblobs/usb/uc03loader.bin",
            #    "address": 0x0101600,
            #    "encrypted": True
            #},
            "uart": {
                "file": "loaderblobs/uart/uc03loader.uart",
                "address": 0x0101600,
                "encrypted": True
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "BD19": {
        "name": ["AC632N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/bd19loader.bin",
                "address": 0x0002000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/bd19loader.uart",
                "address": 0x0002000,
                "encrypted": True
            }
        }
    },

    "BD29": {
        "name": ["AC630N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/bd29loader.bin",
                "address": 0x0002000,
                "encrypted": True
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "BR17": {
        "name": ["AC690N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br17loader.bin",
                "address": 0x0002000,
                "argument": 0x11
            }
        }
    },

    "BR20": {
        "name": ["AC691N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br20loader.bin",
                "address": 0x0002000,
                "argument": 0x0
            }
        }
    },

    "BR21": {
        "name": ["AC692N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br21loader.bin",
                "address": 0x0002000,
                "argument": 0x1    # 0x1 = flash, 0x7 = OTP
            }
        }
    },

    "BR22": {
        "name": ["AC693N"],
    },

    "BR23": {
        "name": ["AC635N", "AC695N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br23loader.bin",
                "address": 0x0012000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/br23loader.uart",
                "address": 0x0012000,
                "encrypted": True
            }
        }
    },

    "BR25": {
        "name": ["AC636N", "AC696N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br25loader.bin",
                "address": 0x0012000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/br25loader.uart",
                "address": 0x0012000,
                "encrypted": True
            }
        }
    },

    "BR28": {
        "name": ["AC701N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br28loader.bin",
                "address": 0x0120000,
                "encrypted": True
            }
        }
    },

    "BR30": {
        "name": ["AC697N", "AD697N", "AC897N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br30loader.bin",
                "address": 0x0002000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/br30loader.uart",
                "address": 0x0002000,
                "encrypted": True
            }
        }
    },

    "BR34": {
        "name": ["AC638N", "AD698N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/br34loader.bin",
                "address": 0x0020000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/uart/br34loader.uart",
                "address": 0x0020000,
                "encrypted": True
            }
        }
    },

    "BR36": {
        "name": ["AC700N"],
        "cryptoweirdo": True,
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "WL80": {
        "name": ["AC790N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/wl80loader.bin",
                "address": 0x1C02000 # ?? ... somewhere in 0x1C0XXXX
            }
        }
    },

    "WL82": {
        "name": ["AC791N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/usb/wl82loader.bin",
                "address": 0x1C02000, # ?? ... somewhere in 0x1C0XXXX
                "encrypted": True
            }
        }
    },
}

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######


def makebar(ratio, length):
    bratio = int(ratio * length)

    bar = ''

    if bratio > 0:
        bar += '=' * (bratio - 1)
        bar += '>'

    bar += ' ' * (length - bratio)

    return bar


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

            print("\rErasing %x-%x..." % (address, address + length - 1), end='', flush=True)

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
    from jldevfind import FindJLDevs

    devs = FindJLDevs()

    if len(devs) == 0:
        print('No devices found')
        exit(1)

    elif len(devs) == 1:
        print('Found some device: %s' % devs[0]['name'])
        device = devs[0]['path']

    else:
        print('Found %d devices, please choose the one you want to use right now, or quit (q)' % len(devs))

        for i, dev in enumerate(devs):
            print('%3d: %s' % (i, dev['name']))

        print()

        while True:
            inp = input('[0..%d|q]: ' % (len(devs) - 1)).strip()

            if inp == '': continue

            if inp.lower().startswith('q'):
                exit()

            try:
                num = int(inp)
            except ValueError:
                print('Please enter a number!')
                continue

            try:
                device = devs[num]['path']
                break
            except IndexError:
                print('Please enter a number in range 0..%d!' % (len(devs) - 1))

with JL_UBOOT(device) as dev:
    vendor, product, prodrev = dev.inquiry()

    chipname = vendor
    if chipname not in families:
        print("Oh well, chip %s is either not supported or is invalid." % chipname)
        exit(2)

    family = families[chipname]
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

            if 'loader' not in family:
                print("No loaders available.")
                exit(3)

            if 'usb' not in family['loader']:
                print("No USB loader is available.")
                exit(3)

            loader = family['loader']['usb']

        ###########

        with open(loader['file'], 'rb') as f:
            addr = loader['address']

            encrypted = loader.get('encrypted', False)
            weirdo = family.get('cryptoweirdo', False)

            while True:
                block = f.read(loader.get('blocksize', 512))
                if block == b'': break

                if (not encrypted and weirdo) or (encrypted and not weirdo):
                    block = jl_crypt_mengli(block)

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

    print("----------------:------------------------")
    print("Online device   : id=%(id)x type=%(type)d" % dev.online_device())
    print("Chip key        : %04x" % dev.chip_key())
    print("Flash page size : %d" % dev.flash_max_page_size())
    print("----------------:------------------------")

    DasShell(dev).cmdloop()

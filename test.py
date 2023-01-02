from scsiio import SCSIDev
from scsiio.common import SCSIException
from jlstuff import *
import argparse, os, time, cmd

ap = argparse.ArgumentParser(description='JieLi tech test X999999',
                             epilog='Taiyoukouhatsudensystem ver1.25 by tsutsumin!')

ap.add_argument('--device',
                help='Path to the JieLi disk (e.g. /dev/sg2 or \\\\.\\E:)',
                required=True)

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
                "file": "loaderblobs/ac4100loader.bin",
                "address": 0x9000
            }
        }
    },

    "BT15": {
        "name": ["AC460N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/bt15loader.bin",
                "address": 0x2000 # ?? maybe?
            }
        }
    },

    "BC51": {
        "name": ["AC461N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/bc51loader.bin",
                "address": 0x2000 # ?? maybe?
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "DV12": {
        "name": ["AC520N"],
    },

    "DV15": {
        "name": ["AC5?1N"],
    },

    "DV16": {
        "name": ["AC54xx", "AC56xx"],

        "loader": {
            "usb": {
                "file": "loaderblobs/dv16loader.bin",
                "address": 0x3f02000
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "BD19": {
        "name": ["AC632N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/bd19loader.bin",
                "address": 0x2000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/bd19loader.uart",
                "address": 0x2000,
                "encrypted": True
            }
        }
    },

    "BD29": {
        "name": ["AC630N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/bd29loader.bin",
                "address": 0x2000,
                "encrypted": True
            }
        }
    },

    # -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- #

    "BR17": {
        "name": ["AC690N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/br17loader.bin",
                "address": 0x2000,
                "argument": 0x11
            }
        }
    },

    "BR20": {
        "name": ["AC691N"],
    },

    "BR21": {
        "name": ["AC692N"],

        "loader": {
            "usb": {
                "file": "loaderblobs/br21loader.bin",
                "address": 0x2000,
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
                "file": "loaderblobs/br23loader.bin",
                "address": 0x12000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/br23loader.uart",
                "address": 0x12000,
                "encrypted": True
            }
        }
    },

    "BR25": {
        "name": ["AC636N", "AC696N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/br25loader.bin",
                "address": 0x12000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/br25loader.uart",
                "address": 0x12000,
                "encrypted": True
            }
        }
    },

    "BR28": {
        "name": ["AC701N"],
        "cryptoweirdo": True,
    },

    "BR30": {
        "name": ["AC697N", "AD697N", "AC897N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/br30loader.bin",
                "address": 0x2000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/br30loader.uart",
                "address": 0x2000,
                "encrypted": True
            }
        }
    },

    "BR34": {
        "name": ["AC638N", "AD698N"],
        "cryptoweirdo": True,

        "loader": {
            "usb": {
                "file": "loaderblobs/br34loader.bin",
                "address": 0x20000,
                "encrypted": True
            },
            "uart": {
                "file": "loaderblobs/br34loader.uart",
                "address": 0x20000,
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
        "cryptoweirdo": True,
    },

    "WL82": {
        "name": ["AC791N"],
        "cryptoweirdo": True,
    },
}

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

class JL_UBOOT:
    def __init__(self, path):
        self.path = path
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, trace):
        self.close()

    #-------------------------------------------#

    def open(self):
        print("Waiting for [%s]" % self.path, end='', flush=True)

        while True:
            # try to open the device *right now*, if we fail for whatever reason,
            # we try again (should probably only ignore the 'file not found' and 'permission denied' stuff)
            try:
                self.dev = SCSIDev(self.path)
            except:
                print('.', end='', flush=True)
                time.sleep(.5)
                continue

            print(" try!", end='', flush=True)

            # try to get inquiry data
            try:
                vendor, product, prodrev = self.inquiry()
            except SCSIException:
                print(" fail!", end='', flush=True)
                self.dev.close()
                time.sleep(.5)
                continue

            # if it's an UBOOT device then we'll proceed
            if product.startswith('UBOOT'):
                print(" ok (%s %s %s)" % (vendor, product, prodrev))
                break

            # otherwise try to enter this mode...
            # product.startswith(('UDISK','DEVICE'))
            else:
                try:
                    self.reset() # any command will suffice
                except SCSIException:
                    pass

            self.dev.close()
            time.sleep(.5)

    def close(self):
        self.dev.close()

    #-------------------------------------------#

    def inquiry(self):
        data = bytearray(36)
        self.dev.execute(b'\x12' + b'\x00\x00' + len(data).to_bytes(2, 'big')
                                               + b'\x00', None, data)

        return (
            str(data[8:16], 'ascii').strip(),
            str(data[16:32], 'ascii').strip(),
            str(data[32:36], 'ascii').strip()
        )

    def exec_cmd(self, cmd):
        resp = bytearray(16)
        self.dev.execute(cmd, None, resp)
        assert(resp[:2] == cmd[:2])
        #print(memoryview(resp).hex('.'))
        return bytes(resp[2:])

    def exec_cmd_datain(self, cmd, len):
        data = bytearray(len)
        self.dev.execute(cmd, None, data)
        return bytes(data)

    def exec_cmd_dataout(self, cmd, data):
        self.dev.execute(cmd, data, None)

    #-------------------------------------------#

    # FB-00 : Erase flash block (64k)
    def flash_erase_block(self, addr):
        resp = self.exec_cmd(b'\xfb\x00' + addr.to_bytes(4, 'big'))

    # FB-01 : Erase flash sector (4k)
    def flash_erase_sector(self, addr):
        resp = self.exec_cmd(b'\xfb\x01' + addr.to_bytes(4, 'big'))

    # FB-02 : Erase flash chip (though seems to be not always implemented)
    def flash_erase_chip(self):
        resp = self.exec_cmd(b'\xfb\x02' + b'\x00\x00\x00\x00')

    # FB-04 : Write (program) flash
    def flash_write(self, addr, data):
        self.exec_cmd_dataout(b'\xfb\x04' + addr.to_bytes(4, 'big') +
                                       len(data).to_bytes(2, 'big'), data)

    # FD-05 : Read flash
    def flash_read(self, addr, len):
        return self.exec_cmd_datain(b'\xfd\x05' + addr.to_bytes(4, 'big') +
                                                   len.to_bytes(2, 'big'), len)

    # FB-06 : Memory write
    def mem_write(self, addr, data):
        self.exec_cmd_dataout(b'\xfb\x06' + addr.to_bytes(4, 'big') +
                                       len(data).to_bytes(2, 'big') + b'\x00' +
                                  jl_crc16(data).to_bytes(2, 'little'), data)

    # FD-07 : Memory read
    def mem_read(self, addr, len):
        return self.exec_cmd_datain(b'\xfd\x07' + addr.to_bytes(4, 'big') +
                                                   len.to_bytes(2, 'big'), len)

    # FB-08 : Memory jump
    def mem_jump(self, addr, arg):
        self.exec_cmd(b'\xfb\x08' + addr.to_bytes(4, 'big') +
                                     arg.to_bytes(2, 'big'))

    # FC-09 : Get chip key
    def chip_key(self, arg=0xac6900):
        resp = self.exec_cmd(b'\xfc\x09' + arg.to_bytes(4, 'big'))
        return int.from_bytes(jl_cryptcrc(resp[4:6][::-1]), 'little')

    # FC-0A : Get online device
    def online_device(self):
        resp = self.exec_cmd(b'\xfc\x0a' + b'\x00\x00\x00\x00')
        return {'type': resp[0], 'id': int.from_bytes(resp[2:6], 'little')}

    # FC-0C : Reset
    def reset(self, arg=1):
        self.exec_cmd(b'\xfc\x0c' + arg.to_bytes(4, 'big'))

    # FC-13 : Get flash CRC16
    def flash_crc16(self, addr, len):
        resp = self.exec_cmd(b'\xfc\x13' + addr.to_bytes(4, 'big') +
                                            len.to_bytes(2, 'big'))
        return int.from_bytes(resp[:2], 'big')

    # FC-14 : Get max flash page size
    def flash_max_page_size(self):
        resp = self.exec_cmd(b'\xfc\x14' + b'\x00\x00\x00\x00')
        return int.from_bytes(resp[:4], 'big')

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

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

    def do_exit(self, args):
        """Get out of the shell"""
        return True

    def emptyline(self):
        pass

    #------#------#------#------#------#------#------#------#------#------#

    def do_open(self, args):
        """Open device.
        open <path>
        """

        print("already opened")

    def do_close(self, args):
        """Close device.
        close
        """

        print("already closed")

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

            while length > 0:
                n = min(maxlen, length)

                print("\rReading %x-%x..." % (address, address + length - 1), end='', flush=True)
                fil.write(self.dev.flash_read(address, n))

                address += n
                length -= n

            print("done!")

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

            while length > 0:
                if length >= 0x10000 and (address & 0xffff) == 0:
                    block = 0x10000
                else:
                    block = 0x1000

                n = min(length, block - (address % block))

                print("\rErasing %x-%x..." % (address, address + length - 1), end='', flush=True)

                if block > 0x1000: self.dev.flash_erase_block(address)
                else:              self.dev.flash_erase_sector(address)

                address += n
                length -= n

            print()

            address = xaddress
            length = xlength

            while length > 0:
                block = fil.read(maxlen)
                if block == b'': break
                n = len(block)

                print("\rWriting %x-%x..." % (address, address + length - 1), end='', flush=True)
                self.dev.flash_write(address, block)

                address += n
                length -= n

            print("done!")

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

        while length > 0:
            if length >= 0x10000 and (address & 0xffff) == 0:
                block = 0x10000
            else:
                block = 0x1000

            n = min(length, block - (address % block))

            print("\rErasing %x-%x..." % (address, address + length - 1), end='', flush=True)

            if block > 0x1000: self.dev.flash_erase_block(address)
            else:              self.dev.flash_erase_sector(address)

            address += n
            length -= n

        print("done!")

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
        """Reset chip.
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
        except:
            print("dies...")
            return True

###### ###### ###### ###### ###### ###### ###### ###### ###### ###### ######

with JL_UBOOT(args.device) as dev:
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
                    block = jl_cryptcrc(block)

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

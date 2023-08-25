from scsiio import SCSIDev
from scsiio.common import SCSIException
from jl_stuff import *
import os, time

class JL_MSCDevice:
    """ Class for handling of the JieLi Mass Storage devices """

    def __init__(self, path):
        self.path = path
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kvargs):
        self.close()

    #-------------------------------------------#

    def open(self):
        print("Waiting for [%s]" % self.path, end='', flush=True)

        # TODO: proper handling for non-UBOOT devices!

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
                break

            # otherwise try to enter this mode...
            # product.startswith(('UDISK','DEVICE'))
            else:
                ldr = JL_LoaderV2(self.dev)

                try:
                    ldr.online_device() # any command will suffice

                    # if it didn't fail, then assume we did get it.
                    #  (in case the fw handles the protocol!)
                    #  - Temporary fix! -
                    break
                except SCSIException:
                    pass

            self.dev.close()
            time.sleep(.5)

        print(" ok (%s %s %s)" % (vendor, product, prodrev))

    def close(self):
        self.dev.close()

    #-------------------------------------------#

    def inquiry(self):
        """ Send an Inquiry request and return manufacturer, product and revision strings """

        data = bytearray(36)
        self.dev.execute(b'\x12' + b'\x00\x00' + len(data).to_bytes(2, 'big')
                                               + b'\x00', None, data)

        return (
            str(data[8:16], 'ascii').strip(),
            str(data[16:32], 'ascii').strip(),
            str(data[32:36], 'ascii').strip()
        )

###############################################################################################################

class JL_MSCProtocolBase:
    """
    Common stuff for the USB Mass Storage Class-based protocols
    """

    def __init__(self, dev):
        self.dev = dev

    def cmd_prepare_cdb(self, cmd, args):
        """ Prepare command's CDB """
        cdb = cmd.to_bytes(2, 'big') + args

        # if the cdb length is less than 16, then we'll just fill with 0xff's
        if len(cdb) < 16:
            cdb += b'\xff' * (16 - len(cdb))

        #print('!! CDB PREPARE !!', '[%04x]' % cmd, '+', '{'+args.hex('.')+'}', '=', '{'+cdb.hex('.')+'}')

        return cdb

    def cmd_exec(self, cmd, args, check_response=True):
        """ Execute command - no data (response is received instead) """
        resp = bytearray(16)
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), None, resp)

        rcmd = int.from_bytes(resp[:2], 'big')
        resp = bytes(resp[2:])

        #print('!! RESPONSE !!', '[%04x]' % rcmd, '+', '{'+resp.hex('.')+'}')

        if check_response:
            # Check if the command in response matched the sent one
            assert(cmd == rcmd)
            return resp
        else:
            # Return raw-ish response
            return (rcmd, resp)

    def cmd_exec_datain(self, cmd, args, dlen):
        """ Execute command - data in (receive from device) """
        data = bytearray(dlen)
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), None, data)
        return bytes(data)

    def cmd_exec_dataout(self, cmd, args, data):
        """ Execute command - data out (send to device) """
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), data, None)



class JL_LoaderV1(JL_MSCProtocolBase):
    """
    First gen loader protocol implementation, used in e.g. AC4100
    or even going back to the USB IDE for AC209N...
    """

    #
    # Commands
    #
    CMD_ERASE_FLASH_BLOCK           = 0xFB00
    CMD_WRITE_FLASH                 = 0xFB01
    CMD_ERASE_FLASH_CHIP            = 0xFB02
    CMD_ERASE_FLASH_SECTOR          = 0xFB03
    CMD_WRITE_MEMORY                = 0xFB04
    CMD_STH_FB05                    = 0xFB05
    CMD_STH_FB06                    = 0xFB06
    CMD_WRITE_WTW                   = 0xFB07
    CMD_READ_WTW                    = 0xFB08
    CMD_JUMP_TO_MEMORY              = 0xFB09

    CMD_FLASH_ID                    = 0xFC00
    CMD_STH_FC01                    = 0xFC01
    CMD_RESET                       = 0xFC02
    CMD_STH_FC03                    = 0xFC03
    CMD_STH_FC04                    = 0xFC04
    CMD_STH_FC05                    = 0xFC05
    CMD_STH_FC06                    = 0xFC06
    CMD_STH_FC07                    = 0xFC07
    CMD_STH_FC08                    = 0xFC08
    CMD_STH_FC09                    = 0xFC09
    CMD_GET_CHIPKEYISH              = 0xFC0A
    CMD_GET_ONLINE_DEVICE           = 0xFC0B
    CMD_SELECT_FLASH                = 0xFC0C

    CMD_READ_FLASH                  = 0xFD01

    #
    # Device types (as returned by the GET_ONLINE_DEVICE command)
    #
    DEVTYPE_NONE                    = 0x00
    DEVTYPE_SPI_FLASH               = 0x01
    DEVTYPE_SD_CARD                 = 0x02

    #-------------------------------------------#

    def flash_erase_block(self, addr):
        """ Erase flash block (64k) """
        self.cmd_exec(JL_LoaderV1.CMD_ERASE_FLASH_BLOCK,
                            addr.to_bytes(4, 'big'))

    def flash_write(self, addr, data):
        """ Write flash """
        self.cmd_exec_dataout(JL_LoaderV1.CMD_WRITE_FLASH,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def flash_erase_chip(self):
        """ Erase flash chip """
        resp = self.cmd_exec(JL_LoaderV1.CMD_ERASE_FLASH_CHIP, b'')

    def flash_erase_sector(self, addr):
        """ Erase flash sector (4k) """
        self.cmd_exec(JL_LoaderV1.CMD_ERASE_FLASH_SECTOR,
                            addr.to_bytes(4, 'big'))

    def mem_write(self, addr, data):
        """ Write memory """
        self.cmd_exec_dataout(JL_LoaderV1.CMD_WRITE_MEMORY,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big'), data)

    def mem_jump(self, addr, arg):
        """ Jump to memory """
        self.cmd_exec(JL_LoaderV1.CMD_JUMP_TO_MEMORY,
                    addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))

    def read_id(self):
        """ Read device ID """
        resp = self.cmd_exec(JL_LoaderV1.CMD_FLASH_ID, b'')
        return int.from_bytes(resp[:3], 'big')

    def online_device(self):
        """ Get online device (unlike V2 protocol it only returns the device type) """
        resp = self.cmd_exec(JL_LoaderV1.CMD_GET_ONLINE_DEVICE, b'')
        return resp[0]

    def flash_select(self, sel):
        """ Select SPI flash, sel is one of:
        0 = SPI_FLASH_CODE,
        1 = SPI_FLASH_DATA
        """
        self.cmd_exec(JL_LoaderV1.CMD_SELECT_FLASH, bytes([sel]))

    def flash_read(self, addr, size):
        """ Read flash """
        return self.cmd_exec_datain(JL_LoaderV1.CMD_READ_FLASH,
                addr.to_bytes(4, 'big') + size.to_bytes(2, 'big'), size)


class JL_UBOOT(JL_MSCProtocolBase):
    """
    UBOOT1.00 class implementation for all (or most?) UBOOT1.00 variants.
    """

    #
    # Commands
    #
    CMD_WRITE_MEMORY                = 0xFB06
    CMD_READ_MEMORY                 = 0xFD07
    CMD_JUMP_TO_MEMORY              = 0xFB08
    CMD_WRITE_MEMORY_RXGP           = 0xFB31

    #-------------------------------------------#

    def mem_write(self, addr, data):
        """ Write memory """
        self.cmd_exec_dataout(JL_UBOOT.CMD_WRITE_MEMORY,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def mem_read(self, addr, len):
        """ Read memory """
        return self.cmd_exec_datain(JL_UBOOT.CMD_READ_MEMORY,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_jump(self, addr, arg):
        """ Jump to memory (with argument) """
        self.cmd_exec(JL_UBOOT.CMD_JUMP_TO_MEMORY,
                    addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))

    def mem_write_rxgp(self, addr, data):
        """ Write memory (RxGp-encrypted payload, probably DVxx or DV15 specific) """
        self.cmd_exec_dataout(JL_UBOOT.CMD_WRITE_MEMORY_RXGP,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

class JL_LoaderV2(JL_MSCProtocolBase):
    """
    Loader class implementation for most loaders.
    """

    #
    # Commands
    #
    CMD_ERASE_FLASH_BLOCK           = 0xFB00
    CMD_ERASE_FLASH_SECTOR          = 0xFB01
    CMD_ERASE_FLASH_CHIP            = 0xFB02
    CMD_READ_STATUS                 = 0xFC03
    CMD_WRITE_FLASH                 = 0xFB04
    CMD_READ_FLASH                  = 0xFD05
    CMD_WRITE_MEMORY                = 0xFB06
    CMD_READ_MEMORY                 = 0xFD07
    CMD_JUMP_TO_MEMORY              = 0xFB08
    CMD_READ_KEY                    = 0xFC09
    CMD_GET_ONLINE_DEVICE           = 0xFC0A
    CMD_READ_ID                     = 0xFC0B
    CMD_RUN_APP                     = 0xFC0C
    CMD_SET_FLASH_CMD               = 0xFC0D
    CMD_FLASH_CRC16                 = 0xFC0E
    CMD_WRITE_KEY                   = 0xFC12
    CMD_FLASH_CRC16_RAW             = 0xFC13
    CMD_GET_USB_BUFF_SIZE           = 0xFC14
    CMD_GET_LOADER_VER              = 0xFC15
    CMD_GET_MASKROM_ID              = 0xFC16

    #-------------------------------------------#

    def flash_erase_block(self, addr):
        """ Erase flash block """
        resp = self.cmd_exec(JL_LoaderV2.CMD_ERASE_FLASH_BLOCK,
                            addr.to_bytes(4, 'big'))
        return resp[0]

    def flash_erase_sector(self, addr):
        """ Erase flash sector """
        self.cmd_exec(JL_LoaderV2.CMD_ERASE_FLASH_SECTOR,
                            addr.to_bytes(4, 'big'))

    def flash_erase_chip(self):
        """ Erase flash chip """
        self.cmd_exec(JL_LoaderV2.CMD_ERASE_FLASH_CHIP, b'')

    def read_status(self):
        """ Read status """
        resp = self.cmd_exec(JL_LoaderV2.CMD_READ_STATUS, b'')
        return resp[0]

    def flash_write(self, addr, data):
        """ Write flash """
        # Note: the CRC16 for data was only required for loaders prior to BR17 one (or something like that)
        self.cmd_exec_dataout(JL_LoaderV2.CMD_WRITE_FLASH,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def flash_read(self, addr, len):
        """ Read flash """
        return self.cmd_exec_datain(JL_LoaderV2.CMD_READ_FLASH,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_write(self, addr, data):
        """ Write memory """
        self.cmd_exec_dataout(JL_LoaderV2.CMD_WRITE_MEMORY,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def mem_read(self, addr, len):
        """ Read memory """
        return self.cmd_exec_datain(JL_LoaderV2.CMD_READ_MEMORY,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_jump(self, addr, arg=0):
        """ Jump to memory """
        self.cmd_exec(JL_LoaderV2.CMD_JUMP_TO_MEMORY,
                    addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))

    def chip_key(self, arg=0xac6900):
        """ Read (chip)key """
        resp = self.cmd_exec(JL_LoaderV2.CMD_READ_KEY, arg.to_bytes(4, 'big'))
        return int.from_bytes(jl_crypt_mengli(resp[4:6][::-1]), 'little')

    def online_device(self):
        """ Get online device """
        resp = self.cmd_exec(JL_LoaderV2.CMD_GET_ONLINE_DEVICE, b'')
        return {'type': resp[0], 'id': int.from_bytes(resp[2:6], 'little')}

    def read_id(self):
        """ Read ID """
        resp = self.cmd_exec(JL_LoaderV2.CMD_READ_ID, b'')
        return int.from_bytes(resp[0:3], 'big')

    def run_app(self, arg=1):
        """ Run app (or reset) """
        self.cmd_exec(JL_LoaderV2.CMD_RUN_APP, arg.to_bytes(4, 'big'))

    def set_flash_cmds(self, cmds):
        """ Set flash commands, cmds in order:
            [0] = Chip erase command               (e.g. 0xC7)
            [1] = Block erase command              (e.g. 0xD8)
            [2] = Sector erase command             (e.g. 0x20)
            [3] = Read command                     (e.g. 0x03)
            [4] = Program command                  (e.g. 0x02)
            [5] = Read status register command     (e.g. 0x05)
            [6] = Write enable command             (e.g. 0x06)
            [7] = Write status register command    (e.g. 0x01)
        """

        self.cmd_exec_datain(JL_LoaderV2.CMD_SET_FLASH_CMD,
            b'\x00\x00\x00\x00' + len(cmds).to_bytes(2, 'big'), bytes(cmds))

    def flash_crc16(self, addr, len):
        """ Calculate flash CRC16 (special) """
        resp = self.cmd_exec(JL_LoaderV2.CMD_FLASH_CRC16,
                        addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'))
        return int.from_bytes(resp[:2], 'big')

    def write_chipkey(self, key):
        """ Write (chip)key """
        resp = self.cmd_exec(JL_LoaderV2.CMD_WRITE_KEY,
                                                key.to_bytes(4, 'big'))
        return int.from_bytes(resp[:4], 'big')

    def flash_crc16_raw(self, addr, len):
        """ Calculate flash CRC16 (raw) """
        resp = self.cmd_exec(JL_LoaderV2.CMD_FLASH_CRC16_RAW,
                        addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'))
        return int.from_bytes(resp[:2], 'big')

    def usb_buffer_size(self):
        """ Get USB buffer size (aka get max flash page size) """
        resp = self.cmd_exec(JL_LoaderV2.CMD_GET_USB_BUFF_SIZE, b'')
        return int.from_bytes(resp[:4], 'big')

    def version(self):
        """ Get loader version """
        # Sometimes the cmd in response is wrong... FIXME
        rcmd, resp = self.cmd_exec(JL_LoaderV2.CMD_GET_LOADER_VER, b'', check_response=False)
        return str(resp[1:5][::-1], 'ascii')

    def maskrom_id(self):
        """ Get MaskROM ID """
        resp = self.cmd_exec(JL_LoaderV2.CMD_GET_MASKROM_ID, b'')
        return int.from_bytes(resp[:4], 'big')


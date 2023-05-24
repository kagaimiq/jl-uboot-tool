from scsiio import SCSIDev
from scsiio.common import SCSIException
from jl_stuff import *
import os, time



class JL_Loader:
    """
    Loader class implementation for most loaders.
    (excluding AC4100 loader, which has different command set)
    """

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
    CMD_GET_ONLINE_DEV              = 0xFC0A
    CMD_READ_ID                     = 0xFC0B
    CMD_RUN_APP                     = 0xFC0C
    CMD_SET_FLASH_CMD               = 0xFC0D
    CMD_FLASH_CRC16                 = 0xFC0E
    CMD_WRITE_KEY                   = 0xFC12
    CMD_FLASH_CRC16_RAW             = 0xFC13
    CMD_GET_USB_BUFF_SIZE           = 0xFC14
    CMD_GET_LOADER_VER              = 0xFC15
    CMD_GET_MASKROM_ID              = 0xFC16

    def __init__(self, dev):
        self.dev = dev

    #-------------------------------------------#

    def flash_erase_block(self, addr):
        """ Erase flash block (64k) """
        resp = self.dev.cmd_exec(JL_Loader.CMD_ERASE_FLASH_BLOCK,
                            addr.to_bytes(4, 'big'))

    def flash_erase_sector(self, addr):
        """ Erase flash sector (4k) """
        resp = self.dev.cmd_exec(JL_Loader.CMD_ERASE_FLASH_SECTOR,
                            addr.to_bytes(4, 'big'))

    def flash_erase_chip(self):
        """ Erase flash chip """
        resp = self.dev.cmd_exec(JL_Loader.CMD_ERASE_FLASH_CHIP, b'')

    def read_status(self):
        """ Read status """
        resp = self.dev.cmd_exec(JL_Loader.CMD_READ_STATUS, b'')
        return resp[0]

    def flash_write(self, addr, data):
        """ Write flash """
        self.dev.cmd_exec_dataout(JL_Loader.CMD_WRITE_FLASH,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big'), data)

    def flash_read(self, addr, len):
        """ Read flash """
        return self.dev.cmd_exec_datain(JL_Loader.CMD_READ_FLASH,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_write(self, addr, data):
        """ Write memory """
        self.dev.cmd_exec_dataout(JL_Loader.CMD_WRITE_MEMORY,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def mem_read(self, addr, len):
        """ Read memory """
        return self.dev.cmd_exec_datain(JL_Loader.CMD_READ_MEMORY,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_jump(self, addr, arg):
        """ Jump to memory """
        self.dev.cmd_exec(JL_Loader.CMD_JUMP_TO_MEMORY,
                    addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))

    def chip_key(self, arg=0xac6900):
        """ Read (chip)key """
        resp = self.dev.cmd_exec(JL_Loader.CMD_READ_KEY, arg.to_bytes(4, 'big'))
        return int.from_bytes(jl_crypt_mengli(resp[4:6][::-1]), 'little')

    def online_device(self):
        """ Get online device """
        resp = self.dev.cmd_exec(JL_Loader.CMD_GET_ONLINE_DEV, b'')
        return {'type': resp[0], 'id': int.from_bytes(resp[2:6], 'little')}

    def read_id(self):
        """ Read ID """
        resp = self.dev.cmd_exec(JL_Loader.CMD_READ_ID, b'')
        return int.from_bytes(resp[0:3], 'big')

    def run_app(self, arg=1):
        """ Run app (or reset) """
        self.dev.cmd_exec(JL_Loader.CMD_RUN_APP, arg.to_bytes(4, 'big'))

    def set_flash_cmds(self, cmds):
        """ Set flash commands
        cmds:
            [0] = Chip erase command               (e.g. 0xC7)
            [1] = Block erase command              (e.g. 0xD8)
            [2] = Sector erase command             (e.g. 0x20)
            [3] = Read command                     (e.g. 0x03)
            [4] = Program command                  (e.g. 0x02)
            [5] = Read status register command     (e.g. 0x05)
            [6] = Write enable command             (e.g. 0x06)
            [7] = Write status register command    (e.g. 0x01)
        """

        self.dev.cmd_exec_datain(JL_Loader.CMD_SET_FLASH_CMD,
            b'\x00\x00\x00\x00' + len(cmds).to_bytes(2, 'big'), bytes(cmds))

    def flash_crc16(self, addr, len):
        """ Calculate flash CRC16 (special) """
        resp = self.dev.cmd_exec(JL_Loader.CMD_FLASH_CRC16,
                        addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'))
        return int.from_bytes(resp[:2], 'big')

    def write_chipkey(self, key):
        """ Write (chip)key """
        resp = self.dev.cmd_exec(JL_Loader.CMD_WRITE_KEY,
                                                key.to_bytes(4, 'big'))
        return int.from_bytes(resp[:4], 'big')

    def flash_crc16_raw(self, addr, len):
        """ Calculate flash CRC16 (raw) """
        resp = self.dev.cmd_exec(JL_Loader.CMD_FLASH_CRC16_RAW,
                        addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'))
        return int.from_bytes(resp[:2], 'big')

    def usb_buffer_size(self):
        """ Get USB buffer size (aka get max flash page size) """
        resp = self.dev.cmd_exec(JL_Loader.CMD_GET_USB_BUFF_SIZE, b'')
        return int.from_bytes(resp[:4], 'big')

    def version(self):
        """ Get loader version """
        # Sometimes the cmd in response is wrong... FIXME
        rcmd, resp = self.dev.cmd_exec(JL_Loader.CMD_GET_LOADER_VER, b'', ignore_wrong_resp=True)
        return str(resp[1:5][::-1], 'ascii')

    def maskrom_id(self):
        """ Get MaskROM ID """
        resp = self.dev.cmd_exec(JL_Loader.CMD_GET_MASKROM_ID, b'')
        return int.from_bytes(resp[:4], 'big')



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

    def cmd_prepare_cdb(self, cmd, args):
        cdb = cmd.to_bytes(2, 'big') + args

        # if the cdb length is less than 16, then we'll just fill with 0xff's
        if len(cdb) < 16:
            cdb += b'\xff' * (16 - len(cdb))

        #print('!! CDB PREPARE !!', '[%04x]' % cmd, '+', '{'+args.hex('.')+'}', '=', '{'+cdb.hex('.')+'}')

        return cdb

    def cmd_exec(self, cmd, args, ignore_wrong_resp=False):
        resp = bytearray(16)
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), None, resp)

        rcmd = int.from_bytes(resp[:2], 'big')
        resp = bytes(resp[2:])

        #print('!! RESPONSE !!', '[%04x]' % rcmd, '+', '{'+resp.hex('.')+'}')

        if ignore_wrong_resp:
            return (rcmd, resp)
        else:
            assert(cmd == rcmd)
            return resp

    def cmd_exec_datain(self, cmd, args, dlen):
        data = bytearray(dlen)
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), None, data)
        return bytes(data)

    def cmd_exec_dataout(self, cmd, args, data):
        self.dev.execute(self.cmd_prepare_cdb(cmd, args), data, None)

    #-------------------------------------------#

    #
    # TODO, get rid of these
    #

    def mem_write(self, addr, data):
        self.cmd_exec_dataout(JL_Loader.CMD_WRITE_MEMORY,
                addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big')
                    + b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def mem_read(self, addr, len):
        return self.cmd_exec_datain(JL_Loader.CMD_READ_MEMORY,
                addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def mem_jump(self, addr, arg):
        self.cmd_exec(JL_Loader.CMD_JUMP_TO_MEMORY,
                    addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))


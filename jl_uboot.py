from scsiio import SCSIDev
from scsiio.common import SCSIException
from jl_stuff import *
import os, time

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
        return int.from_bytes(jl_crypt_mengli(resp[4:6][::-1]), 'little')

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

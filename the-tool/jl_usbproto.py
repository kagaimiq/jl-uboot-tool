from konascsi import SCSI
from jl_stuff import *

class JLUSBProto:
    def __init__(self, device):
        self.scsi = SCSI(device)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.scsi.close()

    #------------------------------------------

    def exec_cmd(self, cdb):
        resp = bytearray(16)
        self.scsi.execute(cdb, None, resp)
        assert(resp[:2] == cdb[:2])
        #print(memoryview(resp).hex('.', -2))
        return bytes(resp)

    def exec_cmd_dataout(self, cdb, data):
        self.scsi.execute(cdb, data, None)

    def exec_cmd_datain(self, cdb, len):
        data = bytearray(len)
        self.scsi.execute(cdb, None, data)
        return bytes(data)

    #-------------------

    def mem_write(self, addr, data, raw=False, chunksize=512):
        while len(data) > 0:
            chunk = data[:chunksize]

            if not raw:
                chunk = jl_cryptcrc(chunk)

            self.exec_cmd_dataout(b'\xfb\x06' + addr.to_bytes(4, 'big') + len(chunk).to_bytes(2, 'big')
                                              + b'\x00' + jl_crc16(chunk).to_bytes(2, 'little'), chunk)

            addr += len(chunk)
            data = data[len(chunk):]

    def mem_read(self, addr, length, raw=False, chunksize=512):
        data = b''

        while length > 0:
            clen = min(length, chunksize)

            chunk = self.exec_cmd_datain(b'\xfd\x07' + addr.to_bytes(4, 'big') + clen.to_bytes(2, 'big'), clen)

            if not raw:
                chunk = jl_cryptcrc(chunk)

            data += chunk
            addr += len(chunk)
            length -= len(chunk)

        return data

    def mem_run(self, addr, arg=0x4777):
        self.exec_cmd(b'\xfb\x08' + addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'))

    #-------------------

    def flash_erase_block(self, addr):
        self.exec_cmd(b'\xfb\x00' + addr.to_bytes(4, 'big'))

    def flash_erase_sector(self, addr):
        self.exec_cmd(b'\xfb\x01' + addr.to_bytes(4, 'big'))

    def flash_erase_chip(self):
        self.exec_cmd(b'\xfb\x02' + b'\x00\x00\x00\x00')

    def flash_program(self, addr, data):
        self.exec_cmd_dataout(b'\xfb\x04' + addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big'), data)

    def flash_read(self, addr, len):
        return self.exec_cmd_datain(b'\xfd\x05' + addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def flash_crc16(self, addr, len):
        res = self.exec_cmd(b'\xfc\x13' + addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'))
        return int.from_bytes(res[2:4], 'big')

    def flash_page_max_size(self):
        res = self.exec_cmd(b'\xfc\x14' + b'\x00\x00\x00\x00')
        return int.from_bytes(res[2:6], 'big')

    #-------------------

    def chip_key(self, wtw=0xac6900):
        res = self.exec_cmd(b'\xfc\x09' + wtw.to_bytes(4, 'big'))
        return int.from_bytes(jl_cryptcrc(res[6:8][::-1]), 'little')

    def online_device(self):
        res = self.exec_cmd(b'\xfc\x0a' + b'\x00\x00\x00\x00')
        return {'type': res[2], 'id': int.from_bytes(res[4:8], 'little')}

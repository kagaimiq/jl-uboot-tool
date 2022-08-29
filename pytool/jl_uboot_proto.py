import os, fcntl, ctypes, time
import crcmod
import sys

## See <linux>/include/scsi/sg.h ##
class sg_io_hdr(ctypes.Structure):
    _fields_ = [
        ("interface_id",    ctypes.c_int),
        ("dxfer_direction", ctypes.c_int),
        ("cmd_len",         ctypes.c_ubyte),
        ("mx_sb_len",       ctypes.c_ubyte),
        ("iovec_count",     ctypes.c_short),
        ("dxfer_len",       ctypes.c_uint),
        ("dxferp",          ctypes.POINTER(ctypes.c_ubyte)),
        ("cmdp",            ctypes.POINTER(ctypes.c_ubyte)),
        ("sbp",             ctypes.POINTER(ctypes.c_ubyte)),
        ("timeout",         ctypes.c_uint),
        ("flags",           ctypes.c_uint),
        ("pack_id",         ctypes.c_int),
        ("usr_ptr",         ctypes.c_voidp),
        ("status",          ctypes.c_ubyte),
        ("masked_status",   ctypes.c_ubyte),
        ("msg_status",      ctypes.c_ubyte),
        ("sb_len_wr",       ctypes.c_ubyte),
        ("host_status",     ctypes.c_ushort),
        ("driver_status",   ctypes.c_ushort),
        ("resid",           ctypes.c_int),
        ("duration",        ctypes.c_uint),
        ("info",            ctypes.c_uint)
    ]

class SCSI():
    SG_INTERFACE_ID_ORIG = ord('S')
    SG_DXFER_NONE     = -1
    SG_DXFER_TO_DEV   = -2
    SG_DXFER_FROM_DEV = -3
    SG_IO = 0x2285

    def __init__(self, path):
        self.fd = None
        self.open(path)

    def __enter__(self):
        return self

    def __exit__(self, etype, evalue, etrace):
        self.close()

    def open(self, path):
        self.fd = os.open(path, os.O_RDWR)

    def close(self):
        if self.fd is None: return
        os.close(self.fd)
        self.fd = None

    def xfer_fromdev(self, cdb, datalen):
        sgio = sg_io_hdr()

        sgio.interface_id = SCSI.SG_INTERFACE_ID_ORIG
        sgio.cmd_len = len(cdb)
        sgio.cmdp    = ctypes.cast(ctypes.create_string_buffer(cdb), ctypes.POINTER(ctypes.c_ubyte))
        sgio.dxfer_direction = SCSI.SG_DXFER_FROM_DEV
        sgio.dxfer_len       = datalen
        sgio.dxferp          = ctypes.cast(ctypes.create_string_buffer(datalen), ctypes.POINTER(ctypes.c_ubyte))
        sgio.timeout         = 1000

        fcntl.ioctl(self.fd, SCSI.SG_IO, sgio)

        return bytes([sgio.dxferp[i] for i in range(datalen)])

    def xfer_todev(self, cdb, data):
        sgio = sg_io_hdr()

        sgio.interface_id = SCSI.SG_INTERFACE_ID_ORIG
        sgio.cmd_len = len(cdb)
        sgio.cmdp    = ctypes.cast(ctypes.create_string_buffer(cdb), ctypes.POINTER(ctypes.c_ubyte))
        sgio.dxfer_direction = SCSI.SG_DXFER_TO_DEV
        sgio.dxfer_len       = len(data)
        sgio.dxferp          = ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_ubyte))
        sgio.timeout         = 1000

        fcntl.ioctl(self.fd, SCSI.SG_IO, sgio)

################################################################################

jl_crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

def jl_crypt(data, key=0xffff):
    data = bytearray(data)

    for i in range(len(data)):
        data[i] ^= key & 0xff
        key = ((key << 1) ^ (0x1021 if (key >> 15) else 0)) & 0xffff

    return bytes(data)

def jl_cryptcrc(data, key=0xffffffff):
    crc = key & 0xffff
    crc = jl_crc16(bytes([key >> 16 & 0xff, key >> 24 & 0xff]), crc)

    magic = b'\xc3\xcf\xc0\xe8\xce\xd2\xb0\xae\xc4\xe3\xa3\xac\xd3\xf1\xc1\xd6'

    data = bytearray(data)

    for i in range(len(data)):
        crc = jl_crc16(bytes([magic[i % len(magic)]]), crc)
        data[i] ^= crc & 0xff

    return bytes(data)


def hexdump(data, width=16):
    for i in range(0, len(data), width):
        s = '%8X: ' % i

        for j in range(width):
            if (i+j) < len(data):
                s += '%02X ' % data[i+j]
            else:
                s += '-- '

        s += ' |'

        for j in range(width):
            if (i+j) < len(data):
                c = data[i+j]
                if c < 0x20 or c >= 0x7f: c = ord('.')
                s += chr(c)
            else:
                s += ' '

        s += '|'

        print(s)
    print()

################################################################################

scsi = None

for ntry in range(2, -1, -1):
    print("Waiting for `%s`" % sys.argv[1], end='', flush=True)

    while True:
        print(".", end='', flush=True)

        try:
            scsi = SCSI(sys.argv[1])

            print("connected")
            break

        except FileNotFoundError:
            pass

        except Exception as e:
            print("failed\n", e)
            exit(1)

        time.sleep(0.5)

    inquiry = scsi.xfer_fromdev(b'\x12\x00\x00\x00\x24\x00', 0x24)
    print('Inquiry: [%s] [%s] [%s]' % (str(inquiry[8:16], 'ascii'),
                                       str(inquiry[16:32], 'ascii'),
                                       str(inquiry[32:36], 'ascii')))

    if inquiry[16:21] == b'UBOOT':
        break

    else:
        if ntry > 0:
            print("This is not an UBOOT device yet, try to enter...")

            # reset cmd
            scsi.xfer_fromdev(b'\xfc\x0c\x00\x00\x00\x01', 16)

        else:
            print("This is not an JieLi device!")
            exit(1)

    scsi.close()

    time.sleep(.5)

################################################################################

with scsi:
    def JL_mem_write(addr, data):
        scsi.xfer_todev(b'\xfb\x06' + addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big') +
                        b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

    def JL_mem_read(addr, len):
        return scsi.xfer_fromdev(b'\xfd\x07' + addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

    def JL_mem_call(addr, arg=0x4777):
        res = scsi.xfer_fromdev(b'\xfb\x08' + addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'), 16)
        assert(res[:2] == b'\xfb\x08')

    #-------------------------------------------------------

    with open(sys.argv[2], 'rb') as f:
        JL_mem_write(0x12000, jl_cryptcrc(f.read()))
        JL_mem_call(0x12000)

        data = jl_cryptcrc(JL_mem_read(0x20000, 0x4000))
        sys.stdout.buffer.write(data[2:2+int.from_bytes(data[:2], 'little')])

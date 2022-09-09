from scsiio import SCSI
import crcmod, time, sys


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
    def JL_flash_eraseBlock(addr):
        res = scsi.xfer_fromdev(b'\xfb\x00' + addr.to_bytes(4, 'big'), 16)
        assert(res[:2] == b'\xfb\x00')

    def JL_flash_eraseSector(addr):
        res = scsi.xfer_fromdev(b'\xfb\x01' + addr.to_bytes(4, 'big'), 16)
        assert(res[:2] == b'\xfb\x01')

    def JL_flash_eraseChip():
        res = scsi.xfer_fromdev(b'\xfb\x02\x00\x00\x00\x00', 16)
        assert(res[:2] == b'\xfb\x02')

    def JL_flash_program(addr, data):
        scsi.xfer_todev(b'\xfb\x04' + addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big'), data)

    def JL_flash_read(addr, len):
        return scsi.xfer_fromdev(b'\xfd\x05' + addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

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

    #hexdump(JL_flash_read(0, 0x100))

    hexdump(scsi.xfer_fromdev(b'\xe4\x03\x00\x00\x00\x00', 256))

    JL_flash_eraseChip()

    '''
    with open('/home/kagaimiq/Desktop/JieLi/00!@FiwmareDumps/JL_MODULE_HW770-_V0.2_ac6965a.bin', 'rb') as f:
        addr = 0
        while True:
            rd = f.read(0x1000)
            if len(rd) < 1: break

            JL_flash_program(addr, rd)

            addr += len(rd)
    '''

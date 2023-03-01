import crcmod

jl_crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

def jl_crypt_enc(data, key=0xffff):
    data = bytearray(data)

    for i in range(len(data)):
        data[i] ^= key & 0xff
        key = ((key << 1) ^ (0x1021 if (key >> 15) else 0)) & 0xffff

    return bytes(data)

def jl_crypt_mengli(data, key=0xffffffff):
    crc = key & 0xffff
    crc = jl_crc16(bytes([key >> 16 & 0xff, key >> 24 & 0xff]), crc)

    magic = bytes("孟黎我爱你，玉林", "gb2312")
    data = bytearray(data)

    for i in range(len(data)):
        crc = jl_crc16(bytes([magic[i % len(magic)]]), crc)
        data[i] ^= crc & 0xff

    return bytes(data)

def jl_crypt_rxgp(data):
    data = bytearray(data)
    aboba = 0x70477852 # 'RxGp' / 'pGxR'

    for i in range(len(data)):
        aboba = (aboba * 16807) + (aboba // 127773) * -0x7fffffff
        data[i] ^= aboba & 0xff

    return data

#------------------------------------------------

def hexdump(data, width=16, address=0):
    for i in range(0, len(data), width):
        s = '%8X: ' % (i + address)

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

#------------------------------------------------

if __name__ == '__main__':
    with open('loaderblobs/usb/dv15loader.enc', 'rb') as f:
        while True:
            blk = f.read(512)
            if blk == b'': break
            hexdump(jl_crypt_rxgp(blk))

    dat = jl_crypt_rxgp(b'Helvetica standard 2606 JIELI TECHNOLOGY -> SCIENCE PREPARATION ROOM (nakamura)\xff')
    hexdump(dat)
    hexdump(jl_crypt_rxgp(dat))

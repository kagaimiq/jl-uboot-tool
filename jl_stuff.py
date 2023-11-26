import crcmod

#------------------------------------------------

jl_crc16 = crcmod.mkCrcFun(0x11021,     initCrc=0x0000,     rev=False)
jl_crc32 = crcmod.mkCrcFun(0x104C11DB7, initCrc=0x26536734, rev=True)

#------------------------------------------------

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
    for off in range(0, len(data), width):
        line = data[off:off+width]

        #
        # Make a hex line
        #
        hexline = ''
        for i in range(width):
            if (i % 8) == 0:
                hexline += ' '

            if i >= len(line):
                hexline += '-- '
            else:
                hexline += '%02x ' % line[i]

        #
        # Make a text line
        #
        line = bytearray(line + (b' ' * (width - len(line))))
        for i, b in enumerate(line):
            if b < 0x20: # or b >= 0x7F:
                line[i] = ord('.')

        txtline = line.decode('1251', errors='replace')  # 1251 rocks!

        print('%08x:%s %s' % (off+address, hexline, txtline))

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

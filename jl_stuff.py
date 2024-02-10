import crcmod

#------------------------------------------------

jl_crc16 = crcmod.mkCrcFun(0x11021,     initCrc=0x0000,     rev=False)
jl_crc32 = crcmod.mkCrcFun(0x104C11DB7, initCrc=0x26536734, rev=True)

#------------------------------------------------

def jl_crypt_enc_in(buff, offset, size, key=0xFFFF):
    for i in range(size):
        buff[offset+i] ^= key & 0xff
        key = ((key << 1) ^ (0x1021 if (key >> 15) else 0)) & 0xffff

def jl_crypt_yulin_in(buff, offset, size, key=0xFFFFFFFF):
    crc = jl_crc16(int.to_bytes(key >> 16, 2, 'little'), key & 0xffff)
    magic = bytes("孟黎我爱你，玉林", "gb2312")

    for i in range(size):
        mi = i % len(magic)
        crc = jl_crc16(magic[mi:mi+1], crc)
        buff[offset+i] ^= crc & 0xff

def jl_crypt_rxgp_in(buff, offset, size):
    rng = 0x70477852    # "RxGp"
    for i in range(size):
        rng = (rng * 16807) + (rng // 127773) * -0x7fffffff
        buff[offset+i] ^= rng & 0xff

def jl_crypt_enc(data, key=0xffff):
    data = bytearray(data)
    jl_crypt_enc_in(data, 0, len(data), key)
    return bytes(data)

def jl_crypt_mengli(data, key=0xffffffff):
    data = bytearray(data)
    jl_crypt_yulin_in(data, 0, len(data), key)
    return bytes(data)

def jl_crypt_rxgp(data):
    data = bytearray(data)
    jl_crypt_rxgp_in(data, 0, len(data))
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

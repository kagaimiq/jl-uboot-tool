""" Cipher/scrambling routines """

__all__ = [
    'jl_enc_cipher',
    'jl_crc_cipher',
    'jl_rxgp_cipher',
    'cipher_bytes'
]

from jltech.crc import jl_crc16

#-----------------------------------------------------------------------#

def jl_enc_cipher(buff, off, size, key=0xFFFF):
    """ JieLi "ENC" cipher """
    for i in range(size):
        buff[off+i] ^= key & 0xFF
        key = ((key << 1) ^ (0x1021 if key & 0x8000 else 0)) & 0xFFFF
    return key

def jl_crc_cipher(buff, off, size, key=0xFFFFFFFF):
    """ JieLi "CrcDecode" cipher """
    magic = bytes("孟黎我爱你，玉林", "gb2312")

    crc = jl_crc16(int.to_bytes(key >> 16, 2, 'little'), key & 0xffff)
    for i in range(size):
        mi = i % len(magic)
        crc = jl_crc16(magic[mi:mi+1], crc)
        buff[off+i] ^= crc & 0xff

def jl_rxgp_cipher(buff, off, size):
    """ JieLi "RxGp" cipher """
    rng = 0x70477852 # "RxGp"
    for i in range(size):
        rng = (rng * 16807) + (rng // 127773) * -0x7fffffff
        buff[off+i] ^= rng & 0xff

#-----------------------------------------------------------------------#

def cipher_bytes(func, data, *args, **kvargs):
    data = bytearray(data)
    func(data, 0, len(data), *args, **kvargs)
    return bytes(data)

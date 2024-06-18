""" CRC calculation routines """

__all__ = [
    'jl_crc16',
    'jl_crc32'
]

import crcmod

jl_crc16 = crcmod.mkCrcFun(0x11021,     initCrc=0x0000,     rev=False)
jl_crc32 = crcmod.mkCrcFun(0x104C11DB7, initCrc=0x26536734, rev=True)

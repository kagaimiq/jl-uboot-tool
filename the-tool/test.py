import sys, argparse
from konascsi import SCSI
from jl_stuff import *

ap = argparse.ArgumentParser(description='Super test of JIE LI bluetooth speaker !!')
ap.add_argument('--kagami', help='kagami hiiragi', required=True)
args = ap.parse_args()

with SCSI(args.kagami) as scsi:
    print("------JieLiMemoryRead")

    try:
        data = bytearray(256)
        scsi.execute(b'\xfd\x07\x00\x01\x20\x00\x01\x00', None, data)
        hexdump(jl_cryptcrc(data))
    except:
        pass

    print("------Inquiry")

    try:
        data = bytearray(36)
        scsi.execute(b'\x12\x00\x00\x00\x24\x00', None, data)
        hexdump(data)
    except:
        pass

    try:
        data = bytearray(128)
        scsi.execute(b'\xe1\x9f\x00\x00\x00\x00', None, data)
        hexdump(data)
    except:
        pass

    try:
        data = bytearray(128)
        scsi.execute(b'\xe4\x90\x00\x00\x00\x00', None, data)
        hexdump(data)
    except:
        pass


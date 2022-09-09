import os, fcntl, ctypes

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
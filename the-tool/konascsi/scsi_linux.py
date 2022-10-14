from konascsi.scsi_common import *
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

SG_IO = 0x2285

SG_INTERFACE_ID_ORIG = ord('S')

SG_DXFER_NONE     = -1
SG_DXFER_TO_DEV   = -2
SG_DXFER_FROM_DEV = -3

SG_INFO_OK_MASK   = 0x1
SG_INFO_OK        = 0x0
SG_INFO_CHECK     = 0x1

SG_INFO_DIRECT_IO_MASK = 0x6
SG_INFO_INDIRECT_IO    = 0x0
SG_INFO_DIRECT_IO      = 0x2
SG_INFO_MIXED_IO       = 0x4

class SCSI(SCSIbase):
    def open(self, path):
        self.fd = os.open(path, os.O_RDWR)

        self.is_open = True

    def close(self):
        if self.is_open:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None

            self.is_open = False

    def execute(self, cdb, data_out, data_in, max_sense_len=32):
        sgio = sg_io_hdr()
        sgio.interface_id = SG_INTERFACE_ID_ORIG

        sgio.timeout = 1000 # TODO

        #---- Sense
        sgio.mx_sb_len = max_sense_len
        sensebuff = ctypes.create_string_buffer(sgio.mx_sb_len)
        sgio.sbp = ctypes.cast(sensebuff, ctypes.POINTER(ctypes.c_ubyte))

        #---- CDB
        sgio.cmd_len = len(cdb)
        sgio.cmdp = ctypes.cast(ctypes.create_string_buffer(cdb), ctypes.POINTER(ctypes.c_ubyte))

        #---- Data
        if data_out and data_in:
            raise NotImplemented('Bidirectional I/O is not supported.')

        elif data_out:
            sgio.dxfer_direction = SG_DXFER_TO_DEV
            sgio.dxfer_len = len(data_out)
            databuff = ctypes.create_string_buffer(data_out)
            sgio.dxferp = ctypes.cast(databuff, ctypes.POINTER(ctypes.c_ubyte))

        elif data_in:
            sgio.dxfer_direction = SG_DXFER_FROM_DEV
            sgio.dxfer_len = len(data_in)
            databuff = ctypes.create_string_buffer(sgio.dxfer_len)
            sgio.dxferp = ctypes.cast(databuff, ctypes.POINTER(ctypes.c_ubyte))

        else:
            sgio.dxfer_direction = SG_DXFER_NONE

        #---- Do transfer
        res = fcntl.ioctl(self.fd, SG_IO, sgio)
        if res < 0:
            raise OSError(res, 'SG_IO ioctl failed')

        #---- Check
        if sgio.info & SG_INFO_OK_MASK != SG_INFO_OK:
            raise Exception('Transfer failed... info:%x host:%x driver:%x' % (sgio.info, sgio.host_status, sgio.driver_status))

        #---- Get data
        if data_in:
            inlen = sgio.dxfer_len
            data_in[:inlen] = bytearray(databuff.raw[:inlen])

        return sgio.resid

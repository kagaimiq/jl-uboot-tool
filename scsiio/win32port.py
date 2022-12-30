from scsiio.common import *
import ctypes

from ctypes.wintypes import HANDLE, BOOL
from ctypes.wintypes import LPCWSTR, LPCSTR
from ctypes.wintypes import BYTE, WORD, DWORD

class SCSI_PASS_THROUGH_DIRECT(ctypes.Structure):
    _fields_ = [
        ('len',       WORD),
        ('status',    BYTE),
        ('path_id',   BYTE),
        ('target_id', BYTE),
        ('lun',       BYTE),
        ('cdb_len',   BYTE),
        ('sense_len', BYTE),
        ('dir',       BYTE),
        ('data_len',  DWORD),
        ('timeout',   DWORD),
        ('data_ptr',  ctypes.POINTER(BYTE)),
        ('sense_off', DWORD),
        ('cdb',       BYTE * 16)
    ]

LPSECURITY_ATTRIBUTES = DWORD

INVALID_HANDLE_VALUE = HANDLE(-1).value

GENERIC_READ     = 1
GENERIC_WRITE    = 2

FILE_SHARE_READ  = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING    = 3

IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x4d014

SCSI_IOCTL_DATA_OUT         = 0
SCSI_IOCTL_DATA_IN          = 1
SCSI_IOCTL_DATA_UNSPECIFIED = 2 # maybe?

#-------------

kernel32 = ctypes.WinDLL('kernel32')

CreateFile = kernel32.CreateFileW
CreateFile.restype  = HANDLE
CreateFile.argtypes = [LPCWSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE]

CloseHandle = kernel32.CloseHandle
CloseHandle.restype  = BOOL
CloseHandle.argtypes = [HANDLE]

DeviceIoControl = kernel32.DeviceIoControl
DeviceIoControl.restype  = BOOL
#DeviceIoControl.argtypes = [HANDLE, DWORD, ctypes.c_voidp, DWORD, ctypes.c_voidp, DWORD, ctypes.POINTER(DWORD), DWORD]

#-----------------------------------------------

class SCSIDev(SCSIDevBase):
    """
    SCSI I/O device implementation for Win32's SCSI_PASS_THROUGH_DIRECT ioctl
    """

    def open(self, path):
        self.fhandle = CreateFile(path, GENERIC_READ|GENERIC_WRITE,
                             FILE_SHARE_READ|FILE_SHARE_WRITE, 0,
                             OPEN_EXISTING, 0, 0)

        if self.fhandle == INVALID_HANDLE_VALUE:
            raise Exception('Could not open SCSI device: %s' % ctypes.WinError())

        self.is_open = True

    def close(self):
        if self.is_open:
            if self.fhandle is not None:
                CloseHandle(self.fhandle)
                self.fhandle = None

            self.is_open = False

    def execute(self, cdb, data_out, data_in, max_sense_len=32, return_sense_buffer=False):
        sptd = SCSI_PASS_THROUGH_DIRECT()
        sptd.len = ctypes.sizeof(sptd)

        sptd.path_id   = 0
        sptd.target_id = 1
        sptd.lun       = 0

        sptd.timeout = 10 # TODO ; in seconds

        #sptd.sense_off = 0
        #sptd.sense_len = max_sense_len

        sptd.cdb_len = len(cdb)
        for i in range(sptd.cdb_len):
            sptd.cdb[i] = cdb[i]

        if data_out and data_in:
            raise NotImplemented('Indirect I/O is not supported')

        elif data_out:
            sptd.dir      = SCSI_IOCTL_DATA_OUT
            sptd.data_len = len(data_out)

            databuff = ctypes.create_string_buffer(data_out)
            sptd.data_ptr = ctypes.cast(databuff, ctypes.POINTER(BYTE))

        elif data_in:
            sptd.dir      = SCSI_IOCTL_DATA_IN
            sptd.data_len = len(data_in)

            databuff = ctypes.create_string_buffer(sptd.data_len)
            sptd.data_ptr = ctypes.cast(databuff, ctypes.POINTER(BYTE))

        else:
            sptd.dir      = SCSI_IOCTL_DATA_UNSPECIFIED

        # after the ioctl the data_len field might change to the actual amount
        # of data transferred, so use this for the residue...
        datalen = sptd.data_len

        xlen = DWORD()

        sptdp = ctypes.cast(ctypes.addressof(sptd), ctypes.POINTER(BYTE))

        res = DeviceIoControl(self.fhandle, IOCTL_SCSI_PASS_THROUGH_DIRECT,
                              sptdp, sptd.len, ctypes.byref(sptd), sptd.len,
                              ctypes.byref(xlen), 0)

        if not res:
            raise SCSIException('Transfer failed... %s' % ctypes.WinError())

        if data_in:
            inlen = sptd.data_len
            data_in[:inlen] = bytearray(databuff.raw[:inlen])

        # TODO, residue & sense buffer! #
        if return_sense_buffer:
            return datalen - sptd.data_len, b''
        else:
            return datalen - sptd.data_len

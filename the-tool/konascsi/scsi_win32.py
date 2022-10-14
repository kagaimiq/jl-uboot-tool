from konascsi.scsi_common import *
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

class SCSI(SCSIbase):
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

    def execute(self, cdb, data_out, data_in, max_sense_len=32):
        sptd = SCSI_PASS_THROUGH_DIRECT()
        sptd.len       = ctypes.sizeof(sptd)
        sptd.path_id   = 0
        sptd.target_id = 1
        sptd.lun       = 0

        sptd.timeout   = 1 # TODO

        #---- Sense
        #sptd.sense_off = 0
        #sptd.sense_len = max_sense_len

        #---- CDB
        sptd.cdb_len = len(cdb)
        for i in range(sptd.cdb_len):
            sptd.cdb[i] = cdb[i]

        #---- Data
        if data_out and data_in:
            raise NotImplemented('Bidirectional I/O is not supported.')

        elif data_out:
            sptd.dir      = 0
            sptd.data_len = len(data_out)

            databuff = ctypes.create_string_buffer(data_out)
            sptd.data_ptr = ctypes.cast(databuff, ctypes.POINTER(BYTE))

        elif data_in:
            sptd.dir      = 1
            sptd.data_len = len(data_in)

            databuff = ctypes.create_string_buffer(sptd.data_len)
            sptd.data_ptr = ctypes.cast(databuff, ctypes.POINTER(BYTE))

        #---- Do transfer
        xlen = DWORD()

        sptdp = ctypes.cast(ctypes.addressof(sptd), ctypes.POINTER(BYTE))

        res = DeviceIoControl(self.fhandle, IOCTL_SCSI_PASS_THROUGH_DIRECT,
                              sptdp, sptd.len, ctypes.byref(sptd), sptd.len,
                              ctypes.byref(xlen), 0)

        #---- Check
        if not res:
            raise Exception('Transfer failed... %s' % ctypes.WinError())

        #---- Get data
        if data_in:
            inlen = sptd.data_len
            data_in[:inlen] = bytearray(databuff.raw[:inlen])

        return 0  #<-- TODO

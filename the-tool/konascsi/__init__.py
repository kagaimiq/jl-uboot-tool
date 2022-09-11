import sys

if sys.platform == 'win32':
    from konascsi.scsi_win32 import SCSI

elif sys.platform == 'linux':
    from konascsi.scsi_linux import SCSI

else:
    raise ImportError("Platform '%s' is not supported (yet)" % sys.platform)

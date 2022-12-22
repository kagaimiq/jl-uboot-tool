class SCSIDevBase:
    """
    SCSI I/O device base class
    """

    def __init__(self, path=None):
        self.is_open = False
        self.path = path

        if path is not None:
            self.open(path)

    def __enter__(self):
        if (self.path is not None) and (not self.is_open):
            self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

class SCSIException(Exception):
    """
    SCSI Exception...
    """

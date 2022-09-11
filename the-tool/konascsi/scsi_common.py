class SCSIbase:
    """
    SCSI base class. Provides the stuff that is common to all platform classes,
    including __init__, __enter__, __exit__, etc.
    """

    def __init__(self, path):
        self.open(path)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    # konascsi
    def xfer_fromdev(self, cdb, len):
        data = bytearray(len)
        self.execute(cdb, None, data)
        return bytes(data)

    def xfer_todev(self, cdb, data):
        self.execute(cdb, data, None)

    # cython-sgio
    #def execute(self, cdb, data_out, data_in, max_sense_len=32):
    #    print('execute', cdb, data_out, data_in, max_sense_len)


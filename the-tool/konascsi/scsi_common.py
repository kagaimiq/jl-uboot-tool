class SCSIbase:
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

    # konascsi (deprecated!)
    def xfer_fromdev(self, cdb, len):
        data = bytearray(len)
        self.execute(cdb, None, data)
        return bytes(data)

    def xfer_todev(self, cdb, data):
        self.execute(cdb, data, None)

    # cython-sgio
    #def execute(self, cdb, data_out, data_in, max_sense_len=32):
    #    print('execute', cdb, data_out, data_in, max_sense_len)


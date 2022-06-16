import os, fcntl, ctypes
import crcmod
import sys

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

jl_crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)

with SCSI(sys.argv[1]) as scsi:
	def hexdump(data, width=16):
		for i in range(0, len(data), width):
			s = '%8X: ' % i

			for j in range(width):
				if (i+j) < len(data):
					s += '%02X ' % data[i+j]
				else:
					s += '-- '

			s += ' |'

			for j in range(width):
				if (i+j) < len(data):
					c = data[i+j]
					if c < 0x20 or c >= 0x7f: c = ord('.')
					s += chr(c)
				else:
					s += ' '

			s += '|'

			print(s)
		print()

	def JL_mem_write(addr, data):
		scsi.xfer_todev(b'\xfb\x06' + addr.to_bytes(4, 'big') + len(data).to_bytes(2, 'big') + \
		                b'\x00' + jl_crc16(data).to_bytes(2, 'little'), data)

	def JL_mem_read(addr, len):
		return scsi.xfer_fromdev(b'\xfd\x07' + addr.to_bytes(4, 'big') + len.to_bytes(2, 'big'), len)

	def JL_mem_call(addr, arg=0x4777):
		print(scsi.xfer_fromdev(b'\xfb\x08' + addr.to_bytes(4, 'big') + arg.to_bytes(2, 'big'), 16))

	with open(sys.argv[2], 'rb') as f:
		JL_mem_write(0x2000, f.read())
		JL_mem_call(0x2000)

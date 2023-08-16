# USB protocol

A chip under USB download (UBOOT) mode shows up as an Mass Storage device with SCSI command interface, which uses some custom SCSI commands
to interact with the chip.

## General info

The command block (CB) contains the opcode (e.g. 0xFB, 0xFC, 0xFD), the sub-opcode and zero or more argument bytes.
isd_download, etc. always sends 16-byte command blocks, but actually they don't have to be exactly 16 bytes.

As for the data, there is three possible variations:
- Response packet
- Data in (to chip)
- Data out (from chip)

Data in and Data out is rather self-explaining. Here's the actual data being transferred, for example the data to write into flash or the data read from flash.

The response packet can be up to 16 bytes long and the first two bytes contain the first two bytes of the CB (that is, opcode and sub-opcode, respectively),
however sometimes they doesn't quite match (e.g. in br17loader's "Get loader version" command.

## Protocols

There are few different variants of these, look:
- [AC4100 loader](ac4100loader.md) - allegedly the v1 protocol, see also [CD03 isd download](cd03isddownload.md) and [HB001 USB IDE](hb001usbide.md)
- [USB loader v2](usb-loader-v2.md) - a newer protocol spoken by most chips at that point.

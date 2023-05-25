# JieLi UBOOT tool

JieLi chip flasher/dumper and etc. using the USB download "UBOOT" protocol
or the UART download protocol (not implemented yet.)

## Tools

### jluboottool.py

The main tool for dumping/flashing and etc.

It contains a builtin command shell where you can do some stuff.

Note that this is not stable and might change drastically.

### jlrunner.py

A simple script that loads a code binary into RAM and executes it with optionally given argument.

### jldevfind.py

A script that prints out all possibly-JieLi-related devices it found.
i.e. the ones that start with "UBOOT", "UDISK" or "DEVICE"

It is also used to find and choose devices when no '--device' argument was given.

## Supported chips

Realistically you can expect it to work with AC69xx/AC70xx/etc series chips for now.

## See also

- [What is UBOOT](docs/what-is-uboot.md)
- [How to enter UBOOT mode](docs/how-to-enter-uboot.md)
- [USB protocol](docs/usb-protocol.md)

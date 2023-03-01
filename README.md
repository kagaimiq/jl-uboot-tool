# JieLi UBOOT tool

very early tech development for the JieLi "UBOOT" USB download protocol.

- [What is UBOOT](docs/what-is-uboot.md)
- [How to enter UBOOT mode](docs/how-to-enter-uboot.md)
- [USB protocol](docs/usb-protocol.md)

## Tools

### jltest.py

A very unstable thing out there. This is where all stuff gets tested on, and so it is subject to heavy changes.

By itself it contains a builtin command shell where you can do stuff like reading and writing flash, etc;
the help entries of the commands should be obvious to understand.

### jlrunner.py

A simple script that loads a code binary into RAM and executes it with optionally given argument.

### jldevfind.py

A script that prints out all possibly-JieLi-related devices it found.
i.e. the ones that start with "UBOOT", "UDISK" or "DEVICE"

It is also used in test.py to find the devices when no '--device' argument was given.

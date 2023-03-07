# What is "UBOOT"

"UBOOT" (not to be confused with "Das U-Boot"), Upgrade or Download mode is the mode which is used to download firmware into a builtin flash of the device
(either one built into the chip itself or as a separate discrete component) over the USB bus.

So when the chip under UBOOT mode is connected to the USB bus, it will show up as a disk like "BR17 UBOOT1.00", "BR21 UBOOT1.00", "DV15 UBOOT1.00", etc.

## Variants

There are at least two 'variants' (or 'versions'?) of the UBOOT mode: "UBOOT1.00" and "UBOOT2.00".

### UBOOT1.00

This variant is provided by the MaskROM which boots up the chip, and so, as it always happens, it has really barebones functionality - you can only read/write memory and execute the code in memory.

So to do the real flashing you need to load a "loader" binary (e.g. "br17loader.bin", "br21loader.bin", etc), like it happens with most SoCs out there...

### UBOOT2.00

This variant is provided by the "uboot.boot" bootloader (a second stage bootloader), which doesn't require any loader binaries
as it provides the required functionality by itself, as, for example it can update the firmware (or the bluetooth settings)
from the "bfu" files on the USB stick or SD card. (it can even recrypt the firmware from the 0xFFFF key into the one that's burned into the efuses!)

Although on SDKs for newer chips (BR23/BR25/BR28/etc) the uboot.boot has shrunk down in size a lot, and so the only option that's left is the
UBOOT1.00 from the MaskROM.

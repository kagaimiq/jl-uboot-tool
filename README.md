# JieLi UBOOT tool

very early tech development for the JieLi "UBOOT" USB download protocol.

## What is "UBOOT"

"UBOOT" (not to be confused with "Das U-Boot"), Upgrade or Download mode is the mode which is used to download firmware into a builtin flash of the device (either one built into the chip itself or as a separate discrete component),
which is available over USB on most chips and over UART on newer chips of the bluetooth audio series (e.g. BR23/BR25/BR28/BR30/etc),
which seem to allow e.g. upgrading the earbud's firmware when it's in the charging case (as usually the UART pin it uses is mixed with the LDO_IN pin).

So when the chip is under the UBOOT mode, on USB it will show up as a disk which is named like `BR17 UBOOT1.00`, `BR21 UBOOT1.00`, etc.

There are two 'versions' (or 'variants') of the UBOOT mode: "UBOOT1.00" and "UBOOT2.00".

The "UBOOT1.00" is provided by the BootROM which boots up the chip, and so, as it always happens, it have really bare bones functionality - you can only read memory, write memory and jump to it.

So to do anything else you need to use a "loader" binary (e.g. "br17loader.bin" "br21loader.bin", etc), just like you are doing with Allwinner (FES), Rockchip (rk30usbplug), Mediatek (download agent), Spreadtrum (FDL1+FDL2) or pretty much anything else.

The "UBOOT2.00" on other hand is provided some "uboot.boot" second stage bootloaders (e.g. in BR17 or BR21 SDK), which allows to do flashing without any loader binaries, as the uboot.boot by itself can flash the updates from the BFU files. And seems like it can also recrypt a firmware encrypted with the 0xffff key to the one that's burned into chip's efuses (the chip key)

## How to enter this mode

### Via dongle

The primary way of entering this mode is via using the "forced upgrade" / "USB Updater" dongle.

When booting up, the BootROM checks for a special signal on the USB lines, and if it found these, then it enters the UBOOT mode.

That special signal is the bits 0x16EF (0001011011101111) applied to USB like so:
```
D- | ______--__----__------__-------- ...
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- ...
```
Thus, the D- is the data line an D+ is the clock line. Clock frequency used by the dongle is around 50 kHz.

You send this sequence repeatedly until the D- and D+ lines gets pulled down by the chip as an acknowledge.

A thing that's worth noting is that the chips like BR17 or BR21 doesn't care what bit it has received first, it will evenually synchronize and finally enter the UBOOT mode, which will **time out** in ~4 seconds, so you need to connect USB really quick until this will eventially time out.
```
5v | ______________ ... ________----------------------------------------------------------------
D- | ______--__---- ... __----__---- ... ______--__----__------__--------______--____________---
D+ | _-_-_-_-_-_-_- ... _-_-_-_-_-_- ... _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-__________-_-
     |                          |        \............................../          \......../
  starting to send    the power is       valid sequence                         chip acknowlegdes
  out signals         applied to the     starts there                           this
                      chip
```

But with e.g. BR25 or BR28 chips, you *have* to send out the bits correctly.
So you need to turn on power to the chip, delay a bit (like 20ms or so), and *only* then send out the signal. The chip will then enter the UBOOT mode, which seem to not have any timeouts.
```
5v | ___________--------------------------------------------------------------------
D- | __________________________________--__----__------__--------________________---
D+ | _____________________________-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-__________-_-
     |          | \............./\............................../      \......../
   don't      apply    wait for          start to send out           chip acknowledges
   send     power to   a little bit        the sequence              this
 anything   the chip   for chip to
    yet                be ready
```

Also worth noting that chips like BR23 seem to have issues with this method and so it uses a completely different sequence to enter into this mode, which seems to use some hardware protocols like ISD (in system debug?)

### Having trouble on booting

Second way of doing that is when the chip can't boot into the main firmware due to erased flash or a corrupted firmware,
and so a blank chip will enter this boot automatically because it doesn't have any valid firmware to start with.

### From a running firmware

Third way is entering this mode via a firmware that runs currently on the chip.

If after connecting the device to USB it recognises as an USB disk like `BR21 DEVICE` or `BR25 UDISK`,
then you can enter this mode just via sending any SCSI command with opcodes 0xFB, 0xFC or 0xFD (the opcodes used by the UBOOT mode on USB),
and after sending one of these commands the chip will reboot into the UBOOT mode.

## Tools

### test.py

A very unstable thing out there. This is where all stuff gets tested on, and so it is subject to heavy changes.

By itself it contains a builtin command shell where you can do stuff like reading and writing flash, etc;
the help entries of the commands should be obvious to understand.

### jlrunner.py

A simple script that loads a code binary into RAM and executes it with optionally given argument.

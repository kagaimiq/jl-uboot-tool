# How to enter UBOOT mode

## Via dongle

This is the primary way of entering this mode, which is done via a "USB Updater" / "Forced upgrade tool" dongle.

When booting up, the MaskROM checks for a special signal on the USB lines, which 'skips' the boot process ("bootskip") and goes straight into the UBOOT mode.

This special signal is the bits 0x16EF (0001011011101111) which is applied to the USB lines like so:
```
D- | ______--__----__------__-------- ...
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- ...
```
Here, the D- is the data line an D+ is the clock line. Clock frequency used by the dongle is around 50 kHz.

You send this sequence repeatedly until the chip acknowledges this by pulling the D+/D- lines to ground.

Things that's worth noting:

Chips like BR17/BR21 (and possibly any older chips as well) do not care what bit it received first when it finally started to sample the USB lines.
Thus, you can just send out the signals, then power up the chip at any moment, and it will eventually synchronize and enter the UBOOT mode,
which will **time out in ~4 seconds** so be sure to connect the USB really quick!
```
5v | ______________ ... ________----------------------------------------------------------------
D- | ______--__---- ... __----__---- ... ______--__----__------__--------______--____________---
D+ | _-_-_-_-_-_-_- ... _-_-_-_-_-_- ... _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-__________-_-
     |                          |        \............................../          \......../
  starting to send    the power is       valid sequence                         chip acknowledges
  out signals         applied to the     starts there                           this
                      chip
```

But chips like BR23/BR25 (and anything newer) *do* care about that, which means that you should apply power to the chip *first*, then
wait a little bit (like 20 ms or so) and *then* only send out the signals.
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

Also a thing worth noting is that BR23 seem to have some troubles with this method (althrough I didn't check that since i don't have any BR23 chip yet),
and so to enter the UBOOT mode on these chips a completely different way is used, which seem to use some hardware protocols like ISD.

## Having trouble on booting

If the chip can't boot into the main firmware (or more like the uboot.boot, which then boots into the rest) due to some issues with the firmware header,
which is caused by erased (empty) flash, corrupted firmware, disconnected flash, etc; then it will enter the UBOOT mode.

So this also means that a blank chip from the factory will enter the UBOOT mode just as well, because it doesn't have any valid firmware to start with.

## From a running firmware

You can also enter this mode through the firmware that's on the chip.

If after connecting the device to USB it recognises as a disk like "BR21 DEVICE" or "BR25 UDISK",
then you can enter this mode just via sending any SCSI command with opcodes 0xFB, 0xFC or 0xFD (the opcodes used by the UBOOT mode on USB),
and after sending one of these commands the chip will reboot into the UBOOT mode.

Chips like BR17 or BR21 will enter the UBOOT2.00 variant that's on the uboot.boot, but BR23/BR25/etc will enter the UBOOT1.00 from the MaskROM
as their uboot.boot is just so small that it can't just hold a USB stack with required flashing stuff.

Note that this obviosly applies to the firmware that's compiled from the official SDK. (i.e. 100% of the devices i guess)

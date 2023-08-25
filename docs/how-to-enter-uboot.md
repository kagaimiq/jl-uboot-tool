# How to enter USB download (UBOOT) mode

## Via dongle (USB key)

This is the primary way of entering the USB download mode, which seems to be called "USB_KEY".

When the chip boots off its Boot ROM, it checks for a special key on the USB lines, and if it found one, it proceeds to enter the UBOOT mode.

The key itself is a 16-bit value 0x16EF (0001 0110 1110 1111), which is sent over the USB lines like so:

```
D- | ______--__----__------__-------- ...
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- ...
```

Here, the D- is the clock line and D+ is the data line.
The data is sampled by the chip at the clock's rising edge.

This key is sent continuously until the chip acknowledges it by pulling both D+ and D- to ground for at least 2ms:

```
D- | ______--__----__------__--------______________________________________--
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_________________________________-_-_-_-
     \______________________________/\_______________________________/
           valid 0x16EF key                  acknowledge
                              (not to scale)
```

After receiving the acknowledge you stop sending the key and proceed to connecting proper USB to the chip.

However, sometimes there are some considerations that does not line up with the ROM operation from the logical point of view,
which probably depend more on the implementation of the dongle rather than the chip itself, which does not let to tell right away
how to send the key so that the entry into USB download mode would be guaranteed to work on many chips without any trouble.

For example, chips like BR23 or BR25 really doesn't like to have USB connected too late, if you'll do so then it won't respond to any activity on the USB bus the chip will just reboot likely by being reset by the watchdog because of a crash or something like that. Maybe a busy loop?

On other hand, chips like BR17 or BR21 does not have these strict requirements on the USB connection - you can connect the USB to the chip
whenever you want, until the chip gets reset by the watchdog after ~4 seconds likely because of the USB SOF detection code having a busy loop
without feeding the watchdog. But anyway, there the situation is not so strict as in BR23/BR25 case.

At least I can suggest connecting the USB to the chip as quickly as possible, as well as using robust USB switching method,
so that the chip picks up the USB without any trouble.

This likely will require switching the power to the chip so that the response could be received without any trouble too, as
if you'll e.g. use your MCU's internal pullups, then there is a great chance that when you apply it to the chip that is not connected
to power, the voltage will drop out significantly as the pullup voltage will go through a diode on the chip's I/O line to the VDDIO which then 
tries to power up the chip, which starts to consume quite a current that makes the weak pullup's voltage to fall below the threshold
where the GPIO pin is considered in LOW state, which will then provide a false acknowledge signal.

Another possible solution is the power up the chip, wait a little bit (somewhere about 10-20ms or so) and then send the key *once*.
After you sent the key, you just switch the USB to the host side without catching the acknowledge from chip.
This is really a hack but seemingly it works too.

## Via dongle (ISP key)

Another variant of transferring the chip into the USB download mode via dongle is by using the ISP key.

This method doesn't rely on some code in ROM but instead relies on the hardware stuff like the ISP interface and possibly the "mode_det" too.

There the principle is that the chip is transferred into the ISP mode and then a special code blob is written into memory which can either simply enter the ROM, after preparing some stuff like the boot mode in NVMEM, or can set up an internal LRC oscillator so that you can flash the chip even without an external crystal. (useful with e.g. AC608N series)

This method appeared somewhere in BR23 or even in the BR22 chips. 

## Having troubles on booting

The chip can automatically enter the USB download mode if it couldn't boot off the main flash.
(for example if the flash is disconnected or if it doesn't have a valid firmware)

So on blank chips, where the flash is erased from the factory, this will lead to chip immediatly entering the USB download mode, as there's obviously no valid firmware to boot.

## From the firmware

The firmware built from the vendor's SDK usually has ability to use the USB download commands one way or another.

The device in question should show up as an USB disk (e.g. `BR17 DEVICE V1.00`, `BR25 UDISK`, etc.).

The behavior of this disk in our case basically can be one of these:

- In chips where the CPU runs off the flash, executing the UBOOT commands will transfer the chip into UBOOT2.00 mode or UBOOT1.00 mode, mainly depending on the chip series in question. For example, BR17-BR21 enter the UBOOT2.00 mode in the `uboot.boot` second-stage bootloader, which also provides upgrades from USB drive or SD card, and OTA via Bluetooth (`BT_UPDATA` device). BR23 onwards has the `uboot.boot` heavily stripped down, thus the only option is to enter UBOOT1.00 in the ROM itself.

- In chips where the CPU runs e.g. off the SDRAM (in case of DVxx chips - AC5xxx series) the firmware provides the protocol by itself, so there is no transfer to UBOOT1.00/UBOOT2.00 is done.

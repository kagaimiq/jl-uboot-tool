# How to enter USB download (UBOOT) mode

## Via dongle (USB key)

This is the primary way of entering the USB download mode, which seems to be called "USB_KEY".

When the chips boots up off its ROM, it checks for a special key signal on the USB lines, and if it found one, it skips the boot procss
and goes straight to the USB download mode.

The key itself is a 16-bit value 0x16EF (0001 0110 1110 1111), which is sent over the USB lines like so:

```
D- | ______--__----__------__-------- ...
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- ...
```

Here, the D- line is the data and D+ line is the clock.
The data is sent MSB-first and sampled by the clock's rising edge.

This key is sent continuously until the chip acknowledges it by pulling both D+ and D- to ground for at least 2ms:

```
D- | ______--__----__------__--------______________________________________--
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_________________________________-_-_-_-
     \______________________________/\_______________________________/
           valid 0x16EF key                  acknowledge
                              (not to scale)
```

And then after detecting the acknowledge you stop sending the key and proceed to switch the USB to the host side.

However, sometimes there are some considerations that does not line up with the ROM operation from the logical point of view,
which probably depend more on the implementation of the dongle rather than the chip itself, which does not let to tell right away
how to send the key so that the entry into USB download mode would be guaranteed to work on many chips without any trouble.

For example, chips like BR23 or BR25 really doesn't like to have USB connected too late, if you'll do so then it won't really
respond to any USB control packets and the chip will just reboot likely by being reset by the watchdog because of a crash or something like that.

On other hand, chips like BR17 or BR21 does not have these strict requirements on the USB connection - you can connect the USB to the chip
whenever you want, until the chip gets reset by the watchdog after ~4 seconds likely because of the USB SOF detection code having a busy loop
without feeding the watchdog. But anyway, here the situation is not so strict as in BR23/BR25 case.

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

## Having troubles on booting

The chip can automatically enter the USB download mode if it for whatever reason it couldn't boot off the flash
(for example if the flash is disconnected or there is not valid firmware in it)

So on blank chips, where the flash is erased from the factory, this will lead to chip immediatly entering the USB download mode,
as there's obviously no valid firmware to boot.

## From the firmware

The firmware built from the vendor's SDK usually has ability to use the USB download commands one way or another.

First of all, the device in question should detect on USB as an USB disk (like BR17 DEVICE V1.00, BR25 UDISK V1.00)
which is used to interact or enter the USB download mode, depending on the chip series in question.

The behavior of this disk in our case basically can be one of two:

- In chips where the CPU runs off the flash, executing the UBOOT commands will transfer the chip into either a UBOOT2.00 mode (in the uboot.boot, which is self-contained)
  or into UBOOT1.00 (in the chip's ROM)

- In chips where the CPU doesn't run off flash (but rather runs off SDRAM, for example), executing the UBOOT commands will work as intended (i.e. no transfer to the UBOOT1.00/2.00),
  and usually it is also self-contained (like UBOOT2.00).

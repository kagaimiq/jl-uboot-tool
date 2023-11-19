# How to enter USB download (UBOOT) mode

## Via dongle

Normally you'd use the vendor's "USB Updater" dongle to enter this mode.

The dongle itself basically consists of an JL chip (either something of the AC69xx series (e.g. AC6925B in V2/V3 dongle) or AC5213B chip as in case of the V4 dongle),
a simple power switch, and a USB switch (either a simple SPDT switch or a dedicated USB switch as in case of the V4 dongle).

The dongle does nothing more than sending a special signal on the USB bus and then passing through the bus to the host.
That's it.

### USB_KEY

This is the primary way of entering the USB download mode, which seems to be called "USB_KEY".

When the chip boots off its Boot ROM, it checks for a special key signal on the USB bus, which will abort the boot process and enter the USB download mode.

The key itself is a 16-bit number 0x16EF (0001 0110 1110 1111), which is sent over the USB lines like so:

```
D- | ______--__----__------__-------- ...
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- ...
```

Here, the D- is the clock line and D+ is the data line.
The data is sampled by the chip at the clock's rising edge.

This key is sent continuously until the chip acknowledges it by pulling both D+ and D- to ground for at least 1-2ms:

```
D- | ______--__----__------__--------______________________________________--
D+ | _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_________________________________-_-_-_-
     \______________________________/\_______________________________/
           valid 0x16EF key                  acknowledge
                              (not to scale)
```

After receiving the response, you connect the proper USB bus to the chip.

Note that in order to sample an ACK you can't just use MCU's (weak) builtin pullups as this would result in a false-positive because the pulldowns on the chip side would make the voltage fall under the '0' threshold. JL chips on other hand have ~10k pullups, so they can get away with using builtin pullups.
In that case you either need to use a strong external pullup or sample for the D+ pullup, which is easier to do but you risk shorting your MCU's outputs to the ground while the chip signals an ACK.
Also I think the latter works only when there are some external pulldowns attached too (e.g. the 15k pulldowns on downstream USB ports)...

### ISP_KEY

There's another way of entering the download mode, which is present on fairly recent chip series (probably due to the fact that on these chips the ISP signals are fully mapped on the USB pins, so it is in the reach of dongle's USB port)

This method uses the ISP protocol to upload a special payload into the chip, which can either simply setup some bits and enter the Boot ROM directly,
or do something like initializing a precise-ish LRC oscillator for chips where there's no option for a crystal oscillator, like in AC608N series that are BR25 (AC696N) but they lack Bluetooth, and consequently, the BT_OSC oscillator inputs.

## Having troubles on booting

The chip can automatically enter the USB download mode if it couldn't boot off the main flash.
(for example if the flash is disconnected or if it doesn't have a valid firmware)

Thus blank chips, which have empty flash from the factory, will immediatly enter the USB download mode.

## From the SDK firmware

- In chips where the CPU runs off the flash, executing the UBOOT commands will transfer the chip into UBOOT2.00 mode or UBOOT1.00 mode, mostly depending on the chip series in question.
  - For example, BR17/BR20/BR21 enter the UBOOT2.00 mode in the `uboot.boot` second-stage bootloader, which also provides upgrades from USB drive or SD card, and OTA via Bluetooth (`BT_UPDATA` device), thus it has ability to alter the chip's flash contents.
  - BR23 onwards has the `uboot.boot` heavily stripped down, thus the only option is to enter UBOOT1.00 in the ROM itself. (the ROM also got ability to directly enter the UBOOT mode via an NVRAM boot mode tag)

- In chips where the CPU runs e.g. off the SDRAM (in case of DVxx chips - AC5xxx series) the firmware provides the protocol by itself, so there is no transfer to UBOOT1.00/UBOOT2.00 is done, as the flash is basically free in this case (no XIP is ever done).

## USB bus consideration - OSC frequency detection via SOFs

Important part of the entry into the USB download mode is the part where the chip pretends to be a USB device in order to receive SOF packets from host.
This is needed to precisely calculate the frequency of an oscillator it will use as the PLL's reference clock. There are no precise on-chip oscillators, thus an external precise-enough source is needed.

In case of the case with a "failed boot attempt", after attempting to boot it will do a SOF check once, and then do all over again. If the SOF check succeeded, then it will proceed into the USB mode.

In case of the forced entry into the download mode, the chip will check for SOF forever, well until BR23 or so where it now only does it three times. <sup>(verify)</sup>

The SOF check is performed by pulling the D+ up, so that the host sees that something was connected to the bus,
and since you can't just enumerate as an high-speed device by just pulling D+, it is enumerated as a full-speed device, even if the download mode itself might use high-speed (on chips with high-speed USB).

Then the chip sets up a timer, which captures falling edges on the D+ signal, so each interrupt should correspond to a SOF packet which comes each 1 ms for full speed devices.
Thus the result should be 1/1000th of the actual clock frequency.

If more-or-less the same period was obtained four times, then it is assumed that everything went fine and the SOF detection is complete.

Otherwise, if nothing succeed in a second or so, it will disable a pullup on D+ and try again (if there were still any attempts left).
So if you correctly send the key but don't connect the chip to USB yet, then you should see periodic pulses on D+ - that's the chip waiting for a SOF and tries again each time.

The issue with the "4 second timeout" on the AC690N/AC692N/etc chips was actually a matter of the wrong way to send the key - if it is sent correctly, then there are no timeouts whatsoever!

The important thing is that, being a very primitive way to sample the SOF (as there is no proper USB hardware is currently available to use),
any packets on a bus may disrupt the SOF detection and lead either to a failure to catch a SOF or even to miscalculating the actual clock frequency.

Thus, the bus should be isolated one way or another from other full/low speed devices at that point.
This can be accomplished e.g. by using a different USB controller in the system, where there are no conflicting devices attached, or using a USB 2.0 hub, connected to a high-speed bus,
which will isolate the bus or even isolate ports from themselves (if you have a MTT hub).

If you wonder,

The thing with USB 2.0 hubs is that on a high-speed bus you can't just directly send a full/low speed packet, like how a low-speed packet is sent on a full-speed bus, by prepending it with a preamble sent in FS and then directly sending the packet at its 1.5 Mbps.

High-speed bus has so-called "split transactions" which are meant to transfer packets to connected FS/LS devices on a hub through a Transaction Translator (TT).

Split transactions can target a specific port in a specific hub, so if you have a STT (single TT) hub (the vast majority of cheap hub chips, for example: HS8836(A), SL2.1, FE1.1s, etc.), then you have a hub-level isolation, if you have a MTT (multiple TT) hub (with chips like FE1.1, FE2.1 or something else) then you get per-port isolation too.

Maybe that's why JL chose the Terminus FE2.1 (an MTT hub) to be the "JieLi Hub", perhaps?

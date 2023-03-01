# UBOOT's USB protocol

The chip under the UBOOT mode is visible on the USB bus as an ordinary mass storage device,
and so it uses custom SCSI commands to do stuff.

## UBOOT1.00 commands

The base command set that is provided by the UBOOT1.00 variant that lives in the MaskROM.
Basically the only thing it can do is access the memory and enter the code,
and so to do more things you need to run a loader binary first.

### Write memory

- Command: `FB 06 AA:aa:aa:aa SS:ss -- cc:CC`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

**Note:** Some chips accept the data encrypted with the "CRC" encryption!
They do it via writing the raw data into the target memory address, and then decrypting it.

### Read memory

- Command: `FD 07 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
- Data out: data that was read

**Note:** Some chips return the data encrypted with the "CRC" encryption!
They do it via encrypting the *target* address *first*, then sending the block and finally decrypting it back.
This means that SRAM will be read out encrypted (but be careful, you might break the ROM runtime with this!),
however MaskROM (and other read-only areas such as the SFC map or reserved areas) won't,
as well as the peripheral registers (it absolutely will mess up these!)

### Jump to memory

- Command: `FB 08 AA:aa:aa:aa BB:bb`
  * AA:aa:aa:aa = Memory address
  * BB:bb = Argument

The code is called with a pointer to the "arglist" stored in register R0,
which has the following structure:
```c
struct JieLi_LoaderArgs {
	void (*msd_send)(void *ptr, int len);		// send data
	void (*msd_recv)(void *ptr, int len);		// receive data
	int (**msd_hook)(struct usb_msc_cbw *cbw);	// SCSI command hook
	uint32_t arg;		// a passed argument
	uint32_t wtw_10;	// ? toggles on BR17, always zero on BR25..
};
```

The response to this command is sent after the code returns, and if the SCSI command hook was set,
then it will be called on *all* SCSI commands received.

If the hook returns zero then the command will be handled by the MaskROM/etc.

The hook gets reset when this command is executed.

### Write memory (encrypted)

**Note: DV15-specific**

- Command: `FB 31 AA:aa:aa:aa SS:ss -- cc:CC`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

This command is similar to the regular write memory command (FB 06),
however it takes data encrypted with something different than what the regular write command takes in some chips.

Look at the *dv15loader.enc* for an example of data transferred via this command (data is transmitted in 512 byte blocks)

## Loader/UBOOT2.00 commands (BR17/BR21/etc)

Additional command set provided by the loader binary or an UBOOT2.00 variant (e.g. from uboot.boot)
being valid for the BR17/BR21/etc families

### Erase flash block (64k)

- Command: `FB 00 AA:aa:aa:aa`
  * AA:aa:aa:aa = Address of the block
- Data out: `FB 00 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Erase flash sector (4k)

- Command: `FB 01 AA:aa:aa:aa`
  * AA:aa:aa:aa = Address of the sector
- Data out: `FB 01 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Erase flash chip

- Command: `FB 02 -- -- -- --`
- Data out: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

*Note:* seems to be not always present..

### Write flash

- Command: `FB 04 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Address
  * SS:ss = Size of data
- Data in: data to be written

### Read flash

- Command: `FD 05 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Address
  * SS:ss = Size of data
- Data out: data that was read

### Get chipkey

- Command: `FC 09 AA:aa:aa:aa`
  * AA:aa:aa:aa = magic value, for AC69xx it's 0xAC6900
- Data out: `FC 09 -- -- -- -- KK:kk -- -- -- -- -- -- -- --`
  * KK:kk = Chipkey (little-endian value gets encrypted then put there in big-endian...)

### Get online device

- Command: `FC 0A -- -- -- --`
- Data out: `FC 0A AA -- bb:bb:bb:BB -- -- -- -- -- -- -- --`
  * AA = Device type:
    * 0 - no device
    * 1 - SDRAM
    * 2 - SD card
    * 3 - SPI0 NOR flash
    * 4 - SPI0 NAND flash
    * 5 - OTP (id reports as 0x4f545010 "OTP\x10", at least on BR20)
    * 16 = SD card
    * 17 = SD card
    * 18 = SD card
    * 19 = ?
    * 20 = ?
    * 21 = ?
    * 22 = SPI1 NOR flash
    * 23 = SPI1 NAND flash
  * bb:bb:bb:BB = Device ID (for SPI flash it's the JEDEC ID returned with command 0x9F)

### Reset

- Command: `FC 0C AA:aa:aa:aa`
  * AA:aa:aa:aa = reset code? set to 1..
- Data out: `FC 0C -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Burn chipkey

- Command: .....

### Get flash CRC16

- Command: `FC 13 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Address
  * SS:ss = Size
- Data out: `FC 13 CC:cc -- -- -- -- -- -- -- -- -- -- -- --`
  * CC:cc = Calculated CRC16

### Get max flash page size

- Command: `FC 14 -- -- -- --`
- Data out: `FC 14 SS:ss:ss:ss -- -- -- -- -- -- -- -- -- --`
  * SS:ss:ss:ss = Page size (or maximum amount of data that can be read/written at once)

# USB protocol

A chip under UBOOT mode 

# Commands & stuff


## Opcodes

- 0xF5 = ??
- 0xFB = "Write flash"
- 0xFC = "Other"
- 0xFD = "Read flash"

### 0xFB sub-opcodes

- 0x00 = [Erase flash block (64k)](#erase-flash-block-64k)
- 0x01 = [Erase flash sector (4k)](#erase-flash-sector-4k)
- 0x02 = [Erase flash chip](#erase-flash-chip)
- 0x04 = [Write flash](#write-flash)
- 0x06 = [Write memory](#write-memory)
- 0x08 = [Jump to memory](#jump-to-memory)
- 0x31 = [Write memory (encrypted)](#write-memory-encrypted)

### 0xFC sub-opcodes

- 0x09 = [Get chipkey](#get-chipkey)
- 0x0A = [Get online device](#get-online-device)
- 0x0C = [Reset](#reset)
- 0x0E = Seemingly "Get flash CRC16" of the DV15/etc loader
- 0x13 = [Get flash CRC16](#get-flash-crc16)
- 0x14 = [Get flash max page size](#get-flash-max-page-size)

### 0xFD sub-opcodes

- 0x05 = [Read flash](#read-flash)
- 0x07 = [Read memory](#read-memory)

## UBOOT1.00 commands

The base command set that is provided by the UBOOT1.00 variant that lives in the MaskROM.
Basically the only thing it can do is access the memory and run the code,
and so to do more things you need to load a "loader" binary first.

### Write memory

- Command: `FB 06 AA:aa:aa:aa SS:ss -- cc:CC`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

**Note:** Some chips accept the data encrypted with the "MengLi" encryption!
They do it via writing the raw data into the target memory address, and then decrypting it.

### Read memory

- Command: `FD 07 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
- Data out: data that was read

**Note:** Some chips return the data encrypted with the "MengLi" encryption!
They do it via encrypting the *target* address *first*, then sending the block and finally decrypting it back.
This means that SRAM will be read out encrypted (but be careful, you might break the ROM runtime with this!),
however MaskROM (and other read-only areas such as the SFC map or reserved areas) won't,
as well as the peripheral registers (it absolutely will mess up these!)

### Jump to memory

- Command: `FB 08 AA:aa:aa:aa BB:bb`
  * AA:aa:aa:aa = Memory address
  * BB:bb = Argument

The response to this command is sent after the code returns back. (so that the host may wait for e.g. when the loader intializes everything)

In most chips, the loader is called with the register r0 holding a pointer to the "arglist", which has the following structure:
```c
struct jl_loader_args {
	void (*msd_send)(void *, int);			// send data
	void (*msd_recv)(void *, int);			// receive data
	int (**msd_hook)(struct usb_msc_cbw *, void *);	// SCSI command hook
	uint32_t arg;		// a passed argument
	uint32_t wtw_10;	// ? toggles on BR17, always zero on BR25..
};
```

The target code can set a SCSI command hook which will receive all requests first,
and if it returned a nonzero, then this command is not processed by the USB stack.

The hook is called with the pointer to the CBW structure in r0, and a pointer to a temporary buffer (usually 64 bytes long) in r1.

This hook also gets reset each time this command executes, before calling the code.

The argument field is understood by the vendor's loaders this way:
- bit0..3 = Target memory (dlmode)
  * 1 = SPI flash
  * 7 = OTP
- bit4..11 = Clock speed
  * 0 = div1
  * 1..255 = div1..255
  * Clock base is usually 48 MHz
- bit12..15 = SPI mode
  * 0 = Half-duplex SPI (2wire 1bit)
  * 1 = SPI (3wire 1bit)
  * 2 = DSPI (3wire 2bit)
  * 3 = QSPI (3wire 4bit)

**Please note** that the loader's variant of this command is a little bit different:
- The response is sent *before* calling the code.
- There is no arglist or stuff like that.
- There's no SCSI hooks too.

### Write memory (encrypted)

**Note: (at least) DV15-specific**

- Command: `FB 31 AA:aa:aa:aa SS:ss -- cc:CC`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

This command is similar to the regular write memory command (FB 06),
however it takes data encrypted with something different than what the regular write command may take on some chips.

Look at the *dv15loader.enc* for an example of data transferred via this command (data is transmitted in 512 byte blocks)

## Loader/UBOOT2.00 commands

This is common overview of the commands, for more specfic details for each loader, check out:
- [AC4100 loader](ac4100-loader.md)
- [BR17 loader](br17-loader.md)

### Get online device

- Command: `FC 0A -- -- -- --`
- Data out: `FC 0A AA -- bb:bb:bb:BB -- -- -- -- -- -- -- --`
  * AA = Device type:
    * 0x00 - no device
    * 0x01 - SDRAM
    * 0x02 - SD card
    * 0x03 - SPI NOR flash (on SPI0)
    * 0x04 - SPI NAND flash (on SPI0)
    * 0x05 - OTP
    * 0x10 = SD card
    * 0x11 = SD card
    * 0x12 = SD card
    * 0x13 = ?
    * 0x14 = ?
    * 0x15 = ?
    * 0x16 = SPI NOR flash (on SPI1)
    * 0x17 = SPI NAND flash (on SPI1)
  * bb:bb:bb:BB = Device ID
    * for SPI (NOR) flash it's the JEDEC ID returned by the 0x9F command
    * for OTP, it is 0x4f545010 "OTP\x10"
    * for SD card, it is 0x73647466 "sdtf" (maybe - assumed)

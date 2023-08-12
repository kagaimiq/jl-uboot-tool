# USB protocol

A chip under USB download (UBOOT) mode shows up as an Mass Storage device with SCSI command interface, which uses some custom SCSI commands
to interact with the chip.

## General info

The command block (CB) contains the opcode (e.g. 0xFB, 0xFC, 0xFD), the sub-opcode and zero or more argument bytes.
isd_download, etc. always sends 16-byte command blocks, but actually they don't have to be exactly 16 bytes.

As for the data, there is three possible variations:
- Response packet
- Data in (to chip)
- Data out (from chip)

Data in and Data out is rather self-explaining. Here's the actual data being transferred, for example the data to write into flash or the data read from flash.

The response packet can be up to 16 bytes long and the first two bytes contain the first two bytes of the CB (that is, opcode and sub-opcode, respectively),
however sometimes they doesn't quite match (e.g. in br17loader's "Get loader version" command.

# UBOOT1.00

The command set that is understood by the UBOOT1.00 mode in the chip's ROM.
Basically it only allows to read and write memory, as well as running the code in memory,
which also can set the SCSI command hook which allows to do more.

So to do anything else a loader binary needs to be loaded first.

## Opcodes

- 0xFB = "Write flash"
- 0xFD = "Read flash"

### 0xFB sub-opcodes

- 0x06 = [Write memory](#write-memory)
- 0x08 = [Jump to memory](#jump-to-memory)
- 0x31 = [Write memory (encrypted)](#write-memory-encrypted)

### 0xFD sub-opcodes

- 0x07 = [Read memory](#read-memory)

## Commands

### Write memory

- Command: `FB 06 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

**Note:** Some chips accept the data encrypted with the "MengLi" encryption!
They do it via writing the raw data into the target memory address, and then decrypting it.

### Read memory

- Command: `FD 07 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
- Data out: data that was read

**Note:** Some chips return the data encrypted with the "MengLi" encryption!
They do it via encrypting the *target* address *first*, then sending the block and finally decrypting it back.
This means that SRAM will be read out encrypted (but be careful, you might break the ROM runtime with this!),
however MaskROM (and other read-only areas such as the SFC map or reserved areas) won't,
as well as the peripheral registers (it absolutely will mess up these!)

### Jump to memory

- Command: `FB 08 AA:aa:aa:aa BB:bb -- -- -- -- -- -- -- --`
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

- Command: `FB 31 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Size of data
  * cc:CC = CRC16 of data
- Data in: data to be written

This command is similar to the regular write memory command (FB 06),
however it takes data encrypted with something different than what the regular write command may take on some chips.

Look at the *dv15loader.enc* for an example of data transferred via this command (data is transmitted in 512 byte blocks)

# Loader/UBOOT2.00 commands

There are few different variants of these, look:
- [AC4100 loader](ac4100loader.md) - allegedly the v1 protocol
- [USB loader v2](usb-loader-v2.md) - protocol used by most chips (which speak the UBOOT1.00 protocol described above)

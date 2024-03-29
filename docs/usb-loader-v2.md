# USB loader protocol v2

This is the protocol version is used by most loaders, as well as the UBOOT1.00 or UBOOT2.00 devices.

This is all-inclusive list of commands and their behavior,
for more specific info on each loader look there:

- [bc51loader](bc51loader.md)
- [br17loader](br17loader.md)

## Protocol variations/implementations

There are three variations of the V2 loader protocol, which differ by the feature set and behavior:

- UBOOT1.00
- UBOOT2.00
- Loader

The **UBOOT1.00** variant is provided by the on-chip Boot ROM, which means that you can only read/write memory and jump into memory location, so to do anything else you have to load a special "loader" binary, which then provides the Loader protocol variant.

The **UBOOT2.00** variant is an enhanced variant of UBOOT1.00 in the sense that it has the same UBOOT1.00 features (for example, the ability for a called code to setup a hook for MSC commands), but at the same time it also has most Loader features like reading/writing flash, etc.

This variant was provided by the `uboot.boot` second-stage bootloader in SDKs for (at least) the AC690N and AC692N series.

The **Loader** variant is provided by the loader binary that has been loaded into the chip via the memory write and memory jump commands.

It can have more features than UBOOT2.00 (e.g. burning the chipkey/efuses), but at the same time it may have a different implementation of some UBOOT commands.

## Loader differences

These are the differences between loaders and their protocol support.

- dv12loader
  * __Base protocol__
  * Flash erasing (FB00, FB01, FB02)
  * Flash write (FB04) and read (FD05)
  * Memory write (FB06) and read (FD07)
  * Memory jump (FB08) - different from UBOOT1.00 one!
- [bc51loader](bc51loader.md)
  * Nothing changed
- [br17loader](br17loader.md)
  * Flash writes does not require CRCs
  * Adds flash CRC16 calculation (FC0E, FC13)
  * Adds things fetch commands (FC0F, FC10, FC11)
  * Adds chipkey write command (FC12)
  * USB buffer size, loader version info (FC14, FC15)
  * Flash reading needs to be unlocked via "Read chipkey" (FC09) command, so..
  * ..the "read key" command now got an argument, which should be 0xac6900 to be able to unlock the flash reading
- br20loader
  * New memory type: OTP (7)
  * Adds "Get MaskROM ID" command (FC16)
  * Flash reading now doesn't need any unlocking (only specific to br17loader?)
  * ????

## Arguments field

Most loaders accept an argument in form of a 16-bit value, passed by the UBOOT's "Jump to memory" command, which is laid out like this:

- bit0..3 = Target memory (dlmode)
  * 0 = SDRAM
  * 1 = SPI NOR flash
  * 2 = SPI NAND flash
  * 3 = SD card
  * 4 = SPI NOR flash (again)
  * 5 = SPI NOR flash (again)
  * 7 = OTP
- bit4..11 = Clock speed divider
  * 0 = "default" (div1)
  * 1..255 = div1..255
- bit12..15 = SPI mode
  * 0 = Half-duplex SPI (2wire 1bit)
  * 1 = SPI (3wire 1bit)
  * 2 = DSPI (3wire 2bit)
  * 3 = QSPI (3wire 4bit)

## Opcodes

- 0xFB = "Write flash"
  - 0x00 = [Erase flash block](#erase-flash-block)
  - 0x01 = [Erase flash sector](#erase-flash-sector)
  - 0x02 = [Erase flash chip](#erase-flash-chip)
  - 0x04 = [Write flash](#write-flash)
  - 0x06 = [Write memory](#write-memory)
  - 0x08 = [Jump to memory](#jump-to-memory)
  - 0x31 = [Write memory (RxGp encrypted, DV15 specific?)](#write-memory-rxgp-encrypted)
- 0xFC = "Other"
  - 0x03 = [Read status](#read-status)
  - 0x09 = [Read key](#read-key)
  - 0x0A = [Get online device](#get-online-device)
  - 0x0B = [Read ID](#read-id)
  - 0x0C = [Run app](#run-app)
  - 0x0D = [Set flash command](#set-flash-command)
  - 0x0E = [Flash CRC16](#flash-crc16)
  - 0x0F = fetch thing1
  - 0x10 = fetch thing2
  - 0x11 = fetch thing3
  - 0x12 = [Write key](#write-key)
  - 0x13 = [Flash CRC16 (raw)](#flash-crc16-raw)
  - 0x14 = [Get USB buffer size](#get-usb-buffer-size)
  - 0x15 = Get loader version
  - 0x16 = [Get MaskROM ID](#get-maskrom-id)
- 0xFD = "Read flash"
  - 0x05 = [Read flash](#read-flash)
  - 0x07 = [Read memory](#read-memory)
  - 0x0B = [Read ID](#read-id) (same as in FC-0B)

## Commands

### Erase flash block

Erases a block in SPI NOR or NAND flash.

- Command: `FB 00 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
- Data out: `FB 00 RR -- -- -- -- -- -- -- -- -- -- -- -- --`
  * RR = Result, zero means successful (only applicable to SPI NAND)

### Erase flash sector

Erases a sector in SPI NOR flash.

- Command: `FB 01 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
- Data out: `FB 01 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Erase flash chip

Erases whole flash chip.

- Command: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

**Note:** This command is not always implemented!

### Write flash

Writes data into flash.

- Command: `FB 04 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Address (for SD card it's still byte-based)
  * SS:ss = Data size
  * cc:CC = CRC16 of data _(now absent)_
- Data in: Data to write into flash

**Note:** Prior to BR17 (or so) the flash was written only when the CRC check succeeded, but since then the command does not take a CRC argument anymore!

### Read flash

Reads data from flash.

- Command: `FD 05 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address (for SD card it's still byte-based)
  * SS:ss = Data size
- Data out: Data read from flash

#### br17loader note

The flash readout is locked out until you execute the [Read key](#read-key) command
with argument of 0xAC6900. It can be also locked again by specifying something other than 0xAC6900.

### Write memory

Writes data into a specified memory location.

- Command: `FB 06 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Data size
  * cc:CC = CRC16 of data
- Data in: Data to write

**Note:** The data is written into the target location only when the CRC check succeed.

#### UBOOT1.00 note

Some chip's UBOOT1.00 implementation (starting from BR23 or so) accept the data in the MengLi-encrypted form. This is implemented by writing data into the target location and then decrypting it at the place.
However the loaders for the same chips don't decrypt data! Also they seem to ignore the CRC argument completely!!

### Read memory

Reads data from a specified memory location.

- Command: `FD 07 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Data size
- Data out: Data read from memory

#### UBOOT1.00 note

Similar to the [Write memory](#write-memory) case, some chips return the data in the MengLi-encrypted form. This is implemented by encrypting the target memory location, then sending it out and finally decrypting it back.

So care should be taken when accessing critical parts like parts of the ROM's runtime or something like that. Peripherals can be screwed up as well! and read-only ares like the ROM or reserved memory areas won't be encrypted at all!

This behavior is rather a limitation of the bufferless approach, where the transfers are done directly via USB's DMA (for sending to host) or the endpoint buffers (for receiving from host) rather than having a buffer that is then manipulated and transfered over USB.

The loaders for the same chips also do not return data in encrypted form.

### Jump to memory

Jumps into the specified memory location.

- Command: `FB 08 AA:aa:aa:aa BB:bb -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * BB:bb = Argument
- Data out: `FB 08 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

The response to this command is sent after the code returns back, so that the host may wait for e.g. when the loader initializes everything and finally setups the MSC hook.

The code being called with the register `r0` holding a pointer to the "arglist" structure, which is laid as follows:

```c
struct jl_loader_args {
  /* Send data to host */
  void (*msd_send)(void *, int);
  /* Receive data from host */
  void (*msd_recv)(void *, int);
  /* MSC command hook */
  int (**msd_hook)(struct usb_msc_cbw *, void *);
  /* Passed argument (really 16-bit) */
  uint32_t arg;
  /* something! Toggles on BR17, always zero on BR25... */
  uint32_t wtw;
}
```

The code may then setup a MSC command hook, which will receive all commands *first*,
and then if the hook returned a nonzero, then the command won't be processed by the UBOOT implementation.

The hook is called with a pointer to the raw CBW structure as the first argument, and a pointer to a small temporary buffer (usually 64 bytes long) as a second argument.

Here's an example of a hook that handles opcode `0xE0`:
```c
struct jl_loader_args *largs;

int my_hook(struct usb_msc_cbw *cbw, uint8_t *pbuff) {
  switch (cbw->cb[0]) {
  case 0xE0:
    /* E0 -- -- -- 49 4A 5A 55 */
    pbuff[0] = cbw->cb[0];
    *(uint32_t *)&pbuff[4] = 0x555a4a49;
    largs->msd_send(pbuff, 8);
    return 1;   /* Handled */
  }

  return 0;     /* Not handled */
}

void loader_main(uint32_t r0) {
  largs = (void *)r0;
  *largs->msd_hook = my_hook;
}
```

The hook is reset each time this command gets executed, before entering code.

#### Loader note

Some (or most) loaders also implement this command (instead of falling back to the UBOOT's implementation), but the implementation differs from the described above.

Basically in that case the command lacks the "argument" field, and it also does not pass anything to the code that's being called.
Also the response is sent *before* calling the code, rather than doing it after.
Maybe it has something to do with the fact that the code can't setup the hooks and whatnot, so there's nothing to wait for until receiving the next command.

### Read key

Reads a key from the device. (usually this is also called a "chipkey")

- Command: `FC 09 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = "address" argument _(usually ignored)_
- Data out: `FC 09 -- -- -- -- KK:kk -- -- -- -- -- -- -- --`
  * KK:kk = The key

The key read from this command is encrypted with the MengLi crypto when the key was in little-endian form, so to decrypt it you need to convert it from big-endian into little-endian, then decrypt it and finally convert it to int.

#### br17loader note

The flash reading will be unlocked if this command will be executed with "address" argument set to 0xAC6900. Then it could be locked back by specifying something other than 0xAC6900.

### Get online device

Gets the device type and its ID that is currently "online".

- Command: `FC 0A -- -- -- -- -- -- -- -- -- -- -- -- -- --`
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
    * for SD card, it is 0x73647466 "sdtf"

### Read ID

Reads the online device ID.

- Command: `FC 0B -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FC 0B AA:aa:aa -- -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa = Device ID

The Device ID is basically the ID from the [Get online device](#get-online-device) command but shifted 8 bits right (so you get bits 31..8 of it)

### Run app

Runs the application in some way. (sometimes this command is also called "Reset" and in this case it resets the device)

- Command: `FC 0C AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = something
- Data out: `FC 0C -- -- -- -- -- -- -- -- -- -- -- -- -- --`

The implementation of this command depends, some reset the chip, some do not do anything.

### Flash CRC16

Calculates the CRC16 of a given region in flash.

- Command: `FC 0D AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size
- Data out: `FC 0D CC:cc -- -- -- -- -- -- -- -- -- -- -- --`
  * CC:cc = Calculated CRC16

The CRC might be different from what is on the flash given what region you access.
For a raw CRC16 calculation the [Flash CRC16 (raw)](#flash-crc16-raw) command is used instead..

### Write key

Writes the key into device.

**Warning: this operation is usually irreversible due to the fact that the key is usually store in the eFuses or the OTP!**

- Command: `FC 12 -- -- KK:kk -- -- -- -- -- -- -- -- -- --`
  * KK:kk = key to write
- Data out: `FC 12 RR:rr:rr:rr -- -- -- -- -- -- -- -- -- --`
  * RR:rr:rr:rr = result code

### Flash CRC16 (raw)

Calculates the CRC16 of a given region in flash. (without any possible alterations unlike [regular command](#flash-crc16))

- Command: `FC 13 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size
- Data out: `FC 13 CC:cc -- -- -- -- -- -- -- -- -- -- -- -- --`
  * CC:cc = Calculated CRC16

### Set flash command

This command sets the command opcodes that is used for interaction with SPI NOR or SPI NAND flash.

- Command: `FC 0D -- -- -- -- SS:ss -- -- -- -- -- -- -- --`
  * SS:ss = command table length
- Data in: command table data

For SPI NOR the table has the following structure:

| Byte | Default | Description                |
|------|---------|----------------------------|
| 0    | 0xC7    | Chip erase                 |
| 1    | 0xD8    | Block erase                |
| 2    | 0x20    | Sector erase               |
| 3    | 0x03    | Read                       |
| 4    | 0x02    | Program                    |
| 5    | 0x05    | Read status register       |
| 6    | 0x06    | Write enable               |
| 7    | 0x01    | Write status register      |

For SPI NAND the table has the following structure instead:

| Byte | Default | Description                |
|------|---------|----------------------------|
| 0    | 0xD8    | Block erase                |
| 1    | 0xA0    |                            |
| 2    | 0x9F    | Read ID                    |
| 3    | 0x13    | Page read to cache         |
| 4    | 0x03    | Read from cache            |
| 5    | 0x84    | Program load random data   |
| 6    | 0x02    | Program load               |
| 7    | 0x10    | Program execute            |
| 8    | 0xC0    |                            |
| 9    | 0x06    | Write enable               |
| 10   | 0x04    | Write disable              |

Please note that the size argument in the command is only used for the length of the reception itself, while the copy into the command table itself will be done always with the size of that table (i.e. 8 or 11 bytes)

### Get USB buffer size

This command returns the size of the USB buffer. If this command wasn't implemented then assume buffer size of 512 bytes.

- Command: `FC 14 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FC 14 SS:ss:ss:ss -- -- -- -- -- -- -- -- -- --`
  * SS:ss:ss:ss = USB buffer size

### Get MaskROM ID

This command reads the "MaskROM ID".

- Command: `FC 16 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FC 16 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = MaskROM ID

The ID value is usually obtained by calling a stub in the MaskROM which returns a 32-bit integer that is usually next to the stub itself.

### Write memory (RxGp encrypted)

Similar to the [Write memory](#write-memory) command, but it accepts data in the RxGp-encrypted form.
So far it was seen in DV15's UBOOT1.00 implementation, which also had the loader file encrypted in the same way.

- Command: `FB 31 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Data size
  * cc:CC = CRC16 of data
- Data in: Data to write (RxGp encrypted)

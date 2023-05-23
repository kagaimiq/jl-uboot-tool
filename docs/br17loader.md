# br17loader

This describes commands and their behavior specific to the br17loader (v204).

## Arguments field

- bit0..3 = Target memory (dlmode)
  * 1 = SPI flash
- bit4..11 = Clock speed
  * 0 = div1
  * >0 = div1..255
  * Clock base is usually 48 MHz
- bit12..15 = SPI mode
  * 0 = Half-duplex SPI (2wire 1bit)
  * 1 = SPI (3wire 1bit)
  * 2 = DSPI (3wire 2bit)
  * 3 = QSPI (3wire 4bit)

## Opcodes

- 0xFB = writing stuff
- 0xFC = misc
- 0xFD = reading stuff

### 0xFB sub-opcodes

- 0x00 = [Erase flash block (64k)](#erase-flask-block-64k)
- 0x01 = [Erase flash sector (4k)](#erase-flash-sector-4k)
- 0x02 = [Erase flash chip](#erase-flash-chip)
- 0x04 = [Write flash](#write-flash)
- 0x06 = [Write memory](#write-memory)
- 0x08 = [Jump to memory](#jump-to-memory)

### 0xFC sub-opcodes

- 0x03 = [Read status](#read-status)
- 0x09 = [Read (chip)key](#read-key)
- 0x0A = [Get online device](#get-online-device)
- 0x0B = [Read ID](#read-id)
- 0x0C = [Run app](#run-app)
- 0x0D = [Set flash command](#set-flash-command)
- 0x0E = [Flash CRC16 (special)](#flash-crc16-special)
- 0x0F = fetch thing1 (ver.bin)
- 0x10 = fetch thing2 (BTIF)
- 0x11 = fetch thing3 (VMIF)
- 0x12 = [Write (chip)key](#write-key)
- 0x13 = [Flash CRC16](#flash-crc16)
- 0x14 = [Get USB buffer size](#get-usb-buffer-size)
- 0x15 = [Get loader version](#get-loader-version)

### 0xFD sub-opcodes

- 0x05 = [Read flash](#read-flash)
- 0x07 = [Read memory](#read-memory)
- 0x0B = [Read ID](#read-id)

## Commands

### Erase flash block (64k)

- Command: `FB 00 AA:aa:aa:aa`
  * AA:aa:aa:aa = Block address
- Data out: `FB 00 SS -- -- -- -- -- -- -- -- -- -- -- -- --`
  * SS = result code

### Erase flash sector (4k)

- Command: `FB 01 AA:aa:aa:aa`
  * AA:aa:aa:aa = Sector address
- Data out: `FB 01 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Erase flash chip

- Command: `FB 02 -- -- -- --`
- Data out: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Read status

- Command: `FC 03 -- -- -- --`
- Data out: `FC 03 SS -- -- -- -- -- -- -- -- -- -- -- -- --`
  * SS = Status code (always 0x00)

### Write flash

- Command: `FB 04 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Flash address
  * SS:ss = Data size
- Data in: Data to write

### Read flash

- Command: `FB 05 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Flash address
  * SS:ss = Read size
- Data out: Data read from flash

**Note:** This command won't be processed if you didn't execute the "read key" command with 'address' argument set to 0xAC6900.
Executing the same command with a different 'address' argument also locks the ability to read flash.

### Write memory

- Command: `FB 06 AA:aa:aa:aa SS:ss cc:CC`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Data size
  * cc:CC = CRC16 of data
- Data in: Data to write

**Note:** The data is written into the target location only when the CRC check succeed.
There is address check before everything will be done (even before receiving the data).
Seems like you can't write past 0x6000 or something like that...

### Read memory

- Command: `FB 07 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Memory address
  * SS:ss = Data size
- Data out: Data read from memory

### Jump to memory

- Command: `FB 08 AA:aa:aa:aa`
  * AA:aa:aa:aa = Memory address
- Data out: `FB 08 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

**Note:** The response to this command is sent *before* the code runs (as opposed to the ROM)
The calling convention is different from what's in the ROM: there's no arguments passed to the code,
and before calling code the timer is stopped and the interrupts are disabled.

### Read key

- Command: `FC 09 AA:aa:aa:aa`
  * AA:aa:aa:aa = 'address', should be 0xAC6900 to be able to read flash
- Data out: `FC 09 -- -- -- -- KK:kk -- -- -- -- -- -- -- --`
  * KK:kk = chipkey

**Note:** the chipkey value is first encrypted in little-endian using Mengli crypt,
and then stored there in big-endian.

**Note:** Reading flash won't work until this command is executed with the 'address' argument set to 0xAC6900.
Similarly, executing this command with the 'address' set to something other than 0xAC6900 will lock out flash reading.

### Get online device

- Command: `FC 0A -- -- -- --`
- Data out: `FC 0A TT -- ii:ii:ii:II -- -- -- -- -- -- -- --`
  * TT = Device type
    * 0x00 = None
    * 0x03 = SPI flash (on SPI0)
  * ii:ii:ii:II = Device ID (SPI flash JEDEC ID)
    * yes, it's indeed in little-endian, the ID value is just memcpy-ed into the response buffer.

**Note:** for complete list of the device types, look [here](usb-protocol.md#get-online-device)

### Read ID

- Command: `FD/FC 0B -- -- -- --`
- Data out: `FC 0B AA:aa:aa -- -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa = Device ID (bits 31..8 - so it lacks the third byte of the SPI flash's JEDEC ID)

### Run app

- Command: `FC 0C AA:aa:aa:aa`
  * AA:aa:aa:aa = address?
- Data out: `-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --`

**Spoiler alert: it does NOTHING**

### Set flash command

- Command: `FC 0D -- -- -- -- SS:ss`
  * SS:ss = data length (=8 bytes)
- Data in: `aa bb cc dd ee ff gg hh`
  * aa = Chip erase command (e.g. 0xC7)
  * bb = Block erase command (e.g. 0xD8)
  * cc = Sector erase command (e.g. 0x20)
  * dd = Read command (e.g. 0x03)
  * ee = Program command (e.g. 0x02)
  * ff = Read status register command (e.g. 0x05)
  * gg = Write enable command (e.g. 0x06)
  * hh = Write status register command (e.g. 0x01)

### Flash CRC16 (special)

- Command: `FC 0E AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Flash address
  * SS:ss = Size
- Data out: `FC 0E CC:cc`
  * CC:cc = Calculated CRC16 of the flash area

**Note:** the special stuffs are:

If address 0x0 was requested, it fills the 0x1e0-0x1ff of the buffer with 0xff.

If the address is 0x200 below the syd size (decrypted block 0x00-0x20's bytes 0x04-0x07),
then the bytes 0x1fc-0x1ff is filled with byte at 0x1fb.

### Write key

**WARNING: BE CAREFUL, THIS OPERATION IS IRREVERSIBLE!**

- Command: `FC 12 -- -- KK:kk`
  * KK:kk = chipkey value
- Data out: `FC 12 VV:vv:vv:vv`
  * VV:vv:vv:vv = result code (or written data)

### Flash CRC16

- Command: `FC 13 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Flash address
  * SS:ss = Size
- Data out: `FC 13 CC:cc`
  * CC:cc = Calculated CRC16 of the flash area

... the CRC16 register is updated on the SPI DMA ?!

### Get USB buffer size

- Command: `FC 14 -- -- -- --`
- Data out: `FC 14 SS:ss:ss:ss`
  * SS:ss:ss:ss = USB buffer size (0x8000 / 32768 bytes)

### Get loader version

- Command: `FC 15 -- -- -- --`
- Data out: `FC 13 XX vv:vv:vv:VV`
  * *Yes, there IS mismatch in command codes!*
  * XX = 0x00
  * vv:vv:vv:VV = Version code in ASCII (e.g. 0x76323034 = v204) ~ yes, it's in little-endian


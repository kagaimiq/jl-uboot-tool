# BC51 loader

This describes commands and their behavior specific to the bc51loader.

As there's no command to get the USB buffer size, the buffers seems to be 512 bytes long there.
And there are two buffers: for data to be written (flash/memory write, set flash cmd) and data to be read (flash/memory read)

## Arguments field

- bit0..3 = Target memory (dlmode)
  * 1 = SPI flash
  * 4 = SPI flash (again)
  * 5 = SPI flash (again)
- bit4..11 = Clock speed
  * 0 = div1
  * 1..255 = div1..255
  * Clock base is probably 48 MHz

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

- Command: `FD 05 AA:aa:aa:aa SS:ss`
  * AA:aa:aa:aa = Flash address
  * SS:ss = Read size
- Data out: Data read from flash

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

- Command: `FD 07 AA:aa:aa:aa SS:ss`
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

- Command: `FC 09 -- -- -- --`
- Data out: `FC 09 -- -- -- -- KK:kk -- -- -- -- -- -- -- --`
  * KK:kk = chipkey

**Note:** the chipkey value is first encrypted in little-endian using Mengli crypt,
and then stored there in big-endian.

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

- Command: `FC/FD 0B -- -- -- --`
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


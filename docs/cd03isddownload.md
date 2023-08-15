# CD03 isd download

Directly related with [ac4100loader](ac4100loader.md) and likely [USB IDE](hb001usbide.md) too.

## Opcodes

- 0xFB
  - 0x00 = [Erase flash block](#erase-flash-block)
  - 0x01 = [Write flash](#write-flash)
  - 0x04 = [Write memory](#write-memory) ~ write loader
  - 0x07 = [Write something](#write-something) ~ write xdata?
  - 0x08 = [Read something](#read-something) ~ read xdata?
  - 0x09 = [Jump to memory](#jump-to-memory) ~ run loader
- 0xFC
  - 0x01 = [something1](#something1)
  - 0x02 = [Reset chip](#reset-chip)
  - 0x09 = [something2](#something2)
  - 0x0A = [Get chipkey-ish](#get-chipkey-ish)
  - 0x0B = [Get online device](#get-online-device)
  - 0x0C = [SPI flash select](#spi-flash-select)
- 0xFD
  - 0x01 = [Read flash](#read-flash)

## Commands

### Erase flash block

- Command: `FB 00 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Block address
- Data out: `FB 00 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Write flash

- Command: `FB 01 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size to write
  * cc:CC = a checksum ?? (ac4100loader uses CRC16)
- Data in: Data to write into flash

### Write memory

Used to write the loader

- Command: `FB 04 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size to write
- Data in: Data to write into memory

### Write something

Maybe it writes XDATA?

- Command: `FB 07 AA:aa:aa:aa SS:ss XX:xx YY:yy -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size to write
  * XX:xx = .. weird thing derived from addr and size
  * YY:yy = .. another weird thing derived from data
- Data in: Data to write into something

### Read something

Maybe it reads XDATA?

- Command: `FB 08 AA:aa:aa:aa SS:ss XX:xx -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size to read
  * XX:xx = .. weird thing derived from addr and size
- Data out: Data that was read from something

### Jump to memory

Used to run the loader

- Command: `FB 09 AA:aa:aa:aa BB:bb -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * BB:bb = Argument?
- Data out: `FB 09 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### something1

- Command: `FC 01 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FC 01 XX ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`
  * XX = something

### Reset chip

- Command: `FC 02 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Value (in ac4100loader, the top 8 bits is used to setup the watchdog timeout - makes sense)
- Data out: `FC 02 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### something2

- Command: `FC 09 XX -- -- -- -- -- -- -- -- -- -- -- -- --`
  * XX = something
- Data out: `FC 09 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Get chipkey-ish

It reads the chipkey? Or something similar?

- Command: `FC 0A -- -- -- -- AA:aa -- -- -- -- -- -- -- --`
  * AA:aa = Something (= 0x1000)
- Data out: `FC 0A -- -- -- -- RR:rr -- -- -- -- -- -- -- --`
  * RR:rr = Response (encrypted with the MengLi/Yulin thing!!!)

### Get online device

- Command: `FC 0B -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FC 0B DD ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`
  * DD = Device type:
    * 0x00 - no device
    * 0x01 - SPI flash
    * 0x02 - SD card

### SPI flash select

- Command: `FC 0C TT -- -- -- -- -- -- -- -- -- -- -- -- --`
  * TT = SPI flash type:
    * 0x00 = SPI_FLASH_CODE
    * 0x01 = SPI_FLASH_DATA
- Data out: `FC 0C ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Read flash

- Command: `FD 01 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size to read
- Data out: Data read from flash

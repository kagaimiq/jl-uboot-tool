# AC4100 loader

This describes commands and their behavior specific to ac4100loader

## Opcodes

- 0xFB = "Write Flash"
- 0xFC = "Other"
- 0xFD = "Read Flash"

### 0xFB sub-opcodes

- 0x00 = [Erase flash block](#erase-flash-block)
- 0x01 = [Write flash](#write-flash)
- 0x02 = [Erase flash chip](#erase-flash-chip)
- 0x03 = [Erase flash sector](#erase-flash-sector)
- 0x04 = [Memory Write](#memory-write)
- 0x05 = //
- 0x06 = //
- 0x07 = //
- 0x08 = //
- 0x09 = [something1](#something1)

### 0xFC sub-opcodes

- 0x00 = [Get flash JEDEC ID](#get-flash-jedec-id)
- 0x01 = [something2](#something2)
- 0x02 = [Enable Watchdog](#enable-watchdog)
- 0x03 = //
- 0x04 = //
- 0x05 = //
- 0x06 = //
- 0x07 = [something2](#something2)
- 0x08 = //
- 0x09 = //
- 0x0A = //
- 0x0B = [Get online device](#get-online-device)
- 0x0C = [Select SPI flash](#select-spi-flash)

### 0xFD sub-opcodes

- 0x00 = [Get flash JEDEC ID](#get-flash-jedec-id)
- 0x01 = [Read flash](#read-flash)

## Commands

### Erase flash block

Erases a 64k block in the flash

- Command: `FB 00 AA:aa:aa:aa`
  * AA:aa:aa:aa = Address of the block
- Data out: `FB 00 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Write flash

Writes data into flash or SD card

- Command: `FB 01 AA:aa:aa:aa SS -- ss cc:CC`
  * AA:aa:aa:aa = Address (byte-based both for flash and SD card)
  * SS -- ss = Size of data
  * cc:CC = CRC16 of data
- Data in: Data to be written

### Erase flash chip

Erases whole flash chip

- Command: `FB 02 -- -- -- --`
- Data out: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Erase flash sector

Erases a 4k sector in the flash

- Command: `FB 03 AA:aa:aa:aa`
  * AA:aa:aa:aa = Address of the sector
- Data out: `FB 03 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Memory write

Simply receives data into the specified memory location

- Command: `FB 04 AA:aa:aa:aa SS -- ss`
  * AA:aa:aa:aa = Address
  * SS -- ss = Size of data
- Data in: Data to be written

### something1

... does nothing??

- Command: `FB 09 AA:aa:aa:aa BB -- bb`
  * AA:aa:aa:aa = something1 (address?)
  * BB -- bb = something2 (size?)
- Data out: `FB 09 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Get flash JEDEC ID

Reads the flash's JECEC ID (via command 0x9F, receives 3 bytes)

- Command: `FC/FD 00 -- -- -- --`
- Data out: `FC 00 II:ii:ii -- -- -- -- -- -- -- -- -- --`
  * II:ii:ii = Flash JEDEC ID

### something2

- Command: `FC 01/07 -- -- -- --`
- Data out: `FC 01 AA -- -- -- -- -- -- -- -- -- -- -- -- --`
  * AA = var (always returns 0? that var is written to 0 before it gets sent...)

### Enable Watchdog

Enables the watchdog timer

- Command: `FC 02 TT -- -- --`
  * TT = timeout value (`WDT_CON = (timeout & 0xf) | 0x10;`)
- Data out: ?? `FC 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Get online device

Gets the device that is currently online (present)

- Command: `FC 0B -- -- -- --`
- Data out: `FC 0B DD -- -- -- -- -- -- -- -- -- -- -- -- --`
  * DD = Device type:
    * 0x00 - no device
    * 0x01 - SPI flash
    * 0x02 - SD card

### Select SPI flash

Selects the SPI flash that will be used..

- Command: `FC 0C TT -- -- --`
  * TT = SPI flash type:
    * 0x00 = SPI_FLASH_CODE
    * 0x01 = SPI_FLASH_DATA
- Data out: `FC 0C -- -- -- -- -- -- -- -- -- -- -- -- -- --`

### Read flash

Reads data from flash or SD card

- Command: `FD 01 AA:aa:aa:aa SS -- ss`
  * AA:aa:aa:aa = Address (byte-based both for flash and SD card)
  * SS -- ss = Size of data
- Data out: Data that was read

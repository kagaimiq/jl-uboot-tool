# USB loader protocol v2

This is the protocol version is used by most loaders, and so far by the UBOOT2.00 too.

This is all-inclusive list of commands, which might be available in some loaders, but some are not.
For specifics on each loader, check out these:

- [br17loader](br17loader.md)

## Opcodes

- 0xFB = "Write flash"
- 0xFC = "Other"
- 0xFD = "Read flash"

### 0xFB sub-opcodes

- 0x00 = Erase flash block (64k)
- 0x01 = Erase flash sector (4k)
- 0x02 = Erase flash cip
- 0x04 = Write flash (device)
- 0x06 = Write memory
- 0x08 = Jump to memory

### 0xFC sub-opcodes

- 0x03 = Read status
- 0x09 = Read chipkey
- 0x0A = [Get online device](#get-online-device)
- 0x0B = Read (device) ID
- 0x0C = Run app
- 0x0D = Set flash command
- 0x0E = Flash (device) CRC16 (special)
- 0x0F = fetch thing1
- 0x10 = fetch thing2
- 0x11 = fetch thing3
- 0x12 = Write (chip)key
- 0x13 = Flash (device) CRC16
- 0x14 = Get USB buffer size
- 0x15 = Get loader version
- 0x16 = Get MaskROM ID

### 0xFD sub-opcodes

- 0x05 = Read flash (device)
- 0x07 = Read memory
- 0x0B = Read (device) ID

## Commands

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

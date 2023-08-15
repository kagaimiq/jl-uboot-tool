# MC02 JTAG thing

Protocol used by `load.exe` of the mc02 sdk thing...

## Opcodes

- 0xFA
  - 0x00 = [Get JTAG test chip ID](#get-jtag-test-chip-id)
  - 0x06 = [Write dbg wb block32](#write-dbg-wb-block32)
  - 0x0F = [Run MCU thing](#run-mcu-thing)
  - 0x11 = [Read is Pro Ok](#read-is-pro-ok)
  - 0x12 = [something](#something)

## Commands

### Get JTAG test chip ID

- Command: `FA 00 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? AA:aa:aa:aa`
  * AA:aa:aa:aa = JTAG Test chip ID (should be 0x28A988A1)

### Write dbg wb block32

- Command: `FA 06 AA:aa:aa:aa -- -- -- -- SS:ss CC:cc:cc:cc`
  * AA:aa:aa:aa = Address
  * SS:ss = Data length
  * CC:cc:cc:cc = CRC32 of data (initial value 0x8BA1992D)
- Data in: Data (the first 4 bytes is replaced with a CRC32?)

### Run MCU thing

- Command: `FA 0F AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = npc value
- Data out: `?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? RR:rr`
  * RR:rr = result code

### Read is Pro Ok

- Command: `FA 11 00 00 80 00 -- -- -- -- -- -- -- -- -- --`
- Data out: `?? ?? ?? ?? ?? ?? rr:rr:rr:RR ?? ?? ?? ?? ?? ?? ??`
  * RR:rr:rr:rr = response
    * 0x00000008
    * 0x0000000C
    * 0x12345678
    * 0x55667788
    * 0xAABBCCDD

### something

- Command: `FA 12 -- -- -- -- -- -- -- -- 00 04 -- -- -- --`
- Data out: `?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

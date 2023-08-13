# USB IDE

The First-generation USB download mode for the USB IDE thing for AC209N/AC309N series and such.
(back in 2011!)

The protocol more or less matches with that of [ac4100loader](ac4100loader.md)
(see [CD03 isd download](cd03isddownload.md))

## Device search

The USB IDE device is searched by this criteria:
- The vendor name should be one of:
  * "USB IDE "
  * "YULIN   "
- Then the vendor+product string (converted to lowercase) should contain one of:
  * "usb ide "
  * "actions auto mp3" (hmm.. that's interesting.. actions = Actions Semiconductor?)
  * "yulin "
  * "mengli" (ha!)

## Opcodes

- 0xFB
- 0xFC
- 0xFD

### 0xFB sub-opcodes

- 0x00 = [Erase flash block](#erase-flash-block)
- 0x01 = [Write flash](#write-flash)
- 0x02 = [Erase flash chip](#erase-flash-chip)
- 0x04 = [Write something](#write-something)
- 0x07 = [ISD start thing](#isd-start-thing)
- 0x08 = [Read something](#read-something)

### 0xFC sub-opcodes

- 0x01 = [something1](#something1)
- 0x04 = [something2](#something2)
- 0x05 = [something3](#something3)
- 0x07 = [something4](#something4)
- 0x09 = [something5](#something5)

### 0xFD sub-opcodes

- 0x01 = [Read flash](#read-flash)

## Commands

### Erase flash block

- Command: `FB 00 AA:aa:aa:aa -- -- -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
- Data out: `FB 00 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Write flash

- Command: `FB 01 AA:aa:aa:aa SS:ss -- cc:CC -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size of data
  * cc:CC = Data CRC16
- Data in: Data to write into flash

### Erase flash chip

- Command: `FB 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --`
- Data out: `FB 02 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Write something

- Command: `FB 04 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Size of data
- Data in: Data to write

### ISD start thing

- Command: `FB 07 AA:aa:aa:aa SS:ss XX:xx Yy:yy -- -- -- --`
  * AA:aa:aa:aa = Address?
  * SS:ss = Size of data
  * XX:xx = Weird thing 1
  * YY:yy = Weird thing 2
- Data in: Some data

### Read something

- Command: `FB 08 AA:aa:aa:aa SS:ss XX:xx -- -- -- -- -- --`
  * AA:aa:aa:aa = Address?
  * SS:ss = Size to read
  * XX:xx = Weird thing
- Data out: Some data read

### something1

- Command: `FC 01 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Value (0)
  * SS:ss = Size (16)
- Data out: `FC 01 AA ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`
  * AA = some value

### something2

- Command: `FC 02 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Value (0)
  * SS:ss = Size (16)
- Data out: `FC 04 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### something3

- Command: `FC 05 AA -- -- -- -- -- -- -- -- -- -- -- -- --`
  * AA = some value
- Data out: `FC 05 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### something4

- Command: `FC 07 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Value (0)
  * SS:ss = Size (16)
- Data out: `FC 07 AA ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`
  * AA = some value

### something5

- Command: `FC 09 AA -- -- -- -- -- -- -- -- -- -- -- -- --`
  * AA = some value
- Data out: `FC 09 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??`

### Read flash

- Command: `FD 01 AA:aa:aa:aa SS:ss -- -- -- -- -- -- -- --`
  * AA:aa:aa:aa = Address
  * SS:ss = Length to read
- Data out: Data read from flash

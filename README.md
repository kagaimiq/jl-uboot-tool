# JieLi UBOOT tool

JieLi chip flasher/dumper and etc. using the USB download "UBOOT" protocol
or the UART download protocol (not implemented yet.)

## Tools

### jluboottool.py

The main shell into the JL UBOOT tool, from which everything is currently done.

This is also the main reason why there are a little of supported chips working - everything there is tied to the protocol of these chips. This is not good.

Here is an overview of some important commands:

- `exit`: the most important of all. Get out of that!
- `read <address> <length> <file>`: Read `<length>` bytes of flash at `<address>` into `<file>`
- `write <address> <file>`: Write `<file>` into flash at `<address>`
- `erasechip`: Erase whole flash
  * Might not work as it executes a "flash chip erase" command which is sometimes not implemented.
- `erase <address> <length>`: Erase `<length>` bytes of flash at `<address>`.
  * Note that it does not preserve contents when address/length is not on a eraseblock boundary.
- `dump <address> [<length>]`: Hex dump `<length>` bytes of flash at `<address>`
  * If length is unspecified, then it defaults to 256 bytes

### jlrunner.py

A simple script that loads a code binary into RAM and executes it with optionally given argument.

### jldevfind.py

A script that prints out all possibly-JieLi-related devices it found.
i.e. the ones that start with "UBOOT", "UDISK" or "DEVICE"

It is also used to find and choose devices when no '--device' argument was given.
(until a proper solution is found)

## Supported chips

Realistically you can expect it to work with the AC690-AC696N series chips (BR17-BR25), for now.

Other chips have some quirks in the protocol (compared to the on in the chips listed above) which should've been handled properly, but they aren't.

Some (e.g. AC410N) have a completely different protocol (command set), thus it is also out of question right now.

Chip series it's currently aware of is listed below:

| Family | Series                | Status        | Notes              |
|--------|-----------------------|---------------|--------------------|
| CD03   | AC410N                | n/a           | different protocol |
| BT15   | AC460N                | maybe working |                    |
| BC51   | AC461N                | maybe working |                    |
| DV12   | AC520N                | maybe working | not working?       |
| DV15   | AC521N                | Working       |                    |
| DV16   | AC540N/AC560N         | unknown       |                    |
| SH54   | AD14N/AD104N          | unknown       |                    |
| SH55   | AD15N/AD105N          | n/a           | UART loader only   |
| UC03   | AD16N                 | unknown       | loader was in some weird format |
| BD19   | AC632N                | unknown       |                    |
| BD29   | AC630N                | unknown       |                    |
| BR17   | AC690N                | Working       |                    |
| BR20   | AC691N                | Working       | need to work out how to do selection of the memory type (OTP or Flash) in the loader argument field |
| BR21   | AC692N                | Working       |                    |
| BR22   | AC693N                | maybe working |                    |
| BR23   | AC695N/AC635N         | Working       |                    |
| BR25   | AC696N/AC636N/AC608N  | Working       |                    |
| BR28   | AC701N                | seems to work |                    |
| BR30   | (AC/AD/JL)697N/AC897N | seems to work |                    |
| BR34   | AC638N/AD698N         | seems to work |                    |
| BR36   | (AC/JL)700N           | n/a           | no loaders for it yet |
| WL80   | AC790N                | unknown       |                    |
| WL82   | AC791N                | unknown       |                    |

## See also

- [What is UBOOT](docs/what-is-uboot.md)
- [How to enter UBOOT mode](docs/how-to-enter-uboot.md)
- [USB protocol](docs/usb-protocol.md)

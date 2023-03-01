# UART protocol

The UART is initialized to 9600 baud, typically on the PB5 port which is shared with the LDO_IN line,
which seeminly allows to e.g. flash the earbuds from the charging case or something like that..

sync string: `55 AA 01 20 22 75 61 72 74`

```
on <uart_cmd_verify>

 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15
 -- -- -- -- -- DD-DD-DD-DD-DD-DD-DD-DD-DD-DD cc-CC -- -- -- -- --

DD... = data
cc-CC = CRC16 of data

on <uart_recv_loader>

 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15
 -- -- -- -- -- aa-aa-aa-AA ll-ll-ll-LL cc-CC -- -- GG RR -- -- --

aa-aa-aa-AA = load&execute address
ll-ll-ll-LL = data length
cc-CC = CRC16 of data
GG = flags [b1 = encrypted data]
RR = uart baudrate on data reception (in 10000 baud units, if 0 defaults to 10 -> 100000 baud,
                                      and so the baudrate has to be in multiples of 10k baud)

* the called loader receives a pointer to the received command as an argument (in r0 register)
```


# UBOOT's UART protocol

The UART is initialized at 9600 baud, then the speed is rised on transmission of the loader..

```
 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15
 55 AA 01 20 22 75 61 72 74 


on <uart_cmd_verify>

 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15
 xx xx xx xx xx DD-DD-DD-DD-DD-DD-DD-DD-DD-DD cc-CC xx xx xx xx xx

DD... = data
cc-CC = CRC16 of data

on <uart_recv_loader>

 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15
 xx xx xx xx xx aa-aa-aa-AA ll-ll-ll-LL cc-CC ** ** GG RR xx xx xx

aa-aa-aa-AA = load&execute address
ll-ll-ll-LL = data length
cc-CC = CRC16 of data
GG = flags [b1 = encrypted data]
RR = uart baudrate on data reception (in 10000 baud steps, if 0 defaults to 10 -> 100000 baud)

* the called loader receives a pointer to the received command as an argument

```


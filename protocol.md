# JieLi UBOOT protocol description

## USB

### Base protocol

```
@@ Write memory
  <= fb 06 AA-aa-aa-aa SS-ss -- cc-CC -- -- -- -- --
  <- DD...

  AAaaaaaa = address
  SSss = size
  ccCC = CRC16 of data
  DD... = data, `SSss` bytes

====================================================

@@ Read memory
  <= fd 07 AA-aa-aa-aa SS-ss -- -- -- -- -- -- -- --
  -> DD...

  AAaaaaaa = address
  DD... = data, `SSss` bytes

====================================================

@@ Jump to memory location
  <= fb 08 AA-aa-aa-aa BB-bb -- -- -- -- -- -- -- --
  -> fb 08 -- -- -- -- -- -- -- -- -- -- -- -- -- --

  AAaaaaaa = address
  BBbb = argument -
      set to 17 in ISD Download 3.2.3.3 (AC690X SDK);
      set to the 'type' arg of 'wr' cmd in ISD Download 3.5.0.9 (AC692X SDK)
        (1 = Flash, 7 = OTP)

  The code is called with the R0 set to pointer of "arglist", which is defined as follows:
        struct JieLi_LoaderArgs {
                int (*msd_send)(void *ptr, int len);            // send request data
                int (*msd_recv)(void *ptr, int len);            // receive request data
                int (**msd_hook)(struct usb_msc_cbw *cbw);      // SCSI request hook
                uint32_t arg;           // Argument
                uint32_t wtw_10;        // set to zero?!
        };

  The WDT is running so you need to either disable it or feed it,
    otherwise the system will reset.

  The response to this SCSI request is sent after the your program returns,
    and if you set the SCSI hook, then it will now handle *ALL* requests *first* -
      if you handled it, then you return a nonzero,
      otherwise you return zero and it will be processed
      by the thing that runs this protocol....
```

### Loader protocol

```
@@ whatever (BR25 UBOOT)
  <= f5 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
  -> AA...
  
  AA... = 256 bytes of something

====================================================

@@ Erase flash block (64k)
  <= fb 00 AA-aa-aa-aa -- -- -- -- -- -- -- -- -- --
  -> fb 00 -- -- -- -- -- -- -- -- -- -- -- -- -- --
  
  AAaaaaaa = address

====================================================

@@ Erase flash sector (4k)
  <= fb 01 AA-aa-aa-aa -- -- -- -- -- -- -- -- -- --
  -> fb 01 -- -- -- -- -- -- -- -- -- -- -- -- -- --

  AAaaaaaa = address

====================================================

@@ Erase flash chip
  <= fb 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --
  -> fb 02 -- -- -- -- -- -- -- -- -- -- -- -- -- --

====================================================

@@ Write flash
  <= fb 04 AA-aa-aa-aa SS-ss -- -- -- -- -- -- -- --
  <- DD...
  
  AAaaaaaa = address
  SSss = size
  DD... = data, `SSss` bytes

====================================================

@@ Read flash
  <= fd 05 AA-aa-aa-aa SS-ss -- -- -- -- -- -- -- --
  -> DD...
  
  AAaaaaaa = address
  SSss = size
  DD... = data, `SSss` bytes

====================================================

@@ Get chip key
  <= fc 09 AA-aa-aa-aa -- -- -- -- -- -- -- -- -- --
  -> fc 09 -- -- -- -- KK-kk -- -- -- -- -- -- -- --
  
  AAaaaaaa = whatever (0xAC6900 for AC69XX, but seems to be not required)
  KKkk = chip key

====================================================

@@ Get device status (Get online device)
  <= fc 0a -- -- -- -- -- -- -- -- -- -- -- -- -- --
  -> fc 0a AA -- bb-bb-bb-BB -- -- -- -- -- -- -- --
  
  AA = device type
        0  - no device
        1  - sdram
        2  - sd card
        3  - spi nor flash
        4  - spi nand flash
        16 - sd card
        17 - sd card
        18 - sd card
        19 - ?
        20 - ?
        21 - ?
        22 - spi nor flash
        23 - spi nand flash
        
  bbbbbbBB = device id (for spi flash it's the JEDEC id)

====================================================

@@ Reset
  <= fc 0c AA-aa-aa-aa -- -- -- -- -- -- -- -- -- --
  -> fc 0c -- -- -- -- -- -- -- -- -- -- -- -- -- --
  
  AAaaaaaa = whatever (set to 1 in isd download)

====================================================

@@ Get flash CRC16
  <= fc 13 AA-aa-aa-aa SS-ss -- -- -- -- -- -- -- --
  -> fc 13 CC-cc -- -- -- -- -- -- -- -- -- -- -- --
  
  AAaaaaaa = address
  SSss = size
  CCcc = CRC16

====================================================

@@ Get max flash page size
  <= fc 14 -- -- -- -- -- -- -- -- -- -- -- -- -- --
  -> fc 14 SS-ss-ss-ss -- -- -- -- -- -- -- -- -- --
  
  SSssssss = flash max page size (maximum amout of data you can read/write at a time)

--------------------------------------------------------------
```
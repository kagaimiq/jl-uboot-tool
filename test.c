#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>

#include "scsi_io.h"
#include "jlusbisd.h"
#include "jl_stuff.h"

void hexdump(uint8_t *ptr, int len) {
	for (int i = 0; i < len; i += 16) {
		printf("%p: ", ptr + i);
		
		for (int j = 0; j < 16; j++) {
			if (i+j >= len) {
				printf("-- ");
			} else {
				printf("%02X ", ptr[i+j]);
			}
		}
		
		printf(" |");
		
		for (int j = 0; j < 16; j++) {
			if (i+j >= len) {
				putchar(' ');
			} else {
				uint8_t b = ptr[i+j];
				putchar(b<0x20||b>=0x7f?'.':b);
			}
		}
		
		printf("|\n");
	}
}


#include "binbo.h"

int jl_uploadAndRunBuff(const void *data, int len, uint32_t addr, uint16_t wtw) {
	int rc = -1;
	
	for (uint32_t xaddr = addr; len > 0;) {
		int cnt = len > 512 ? 512 : len;
		
		if (jlUsbIsd_WriteMemory(xaddr, (void*)data, cnt) < 0) {
			printf("[%s] failed to write %d bytes into memory addr %x!\n",
				__func__, cnt, xaddr);
			goto Exit;
		}
		
		uint8_t buff2[512];
		if (jlUsbIsd_ReadMemory(xaddr, buff2, cnt) < 0) {
			printf("[%s] failed to read %d bytes from memory addr %x!\n",
				__func__, cnt, xaddr);
			goto Exit;
		}
		
		if (memcmp(data, buff2, cnt)) {
			printf("[%s] Memory contents at addr %x doesn't match!\n",
				__func__, xaddr);
			goto Exit;
		}
		
		data += cnt;
		xaddr += cnt;
		len -= cnt;
	}
	
	if (jlUsbIsd_JumpMemory(addr, wtw) < 0) {
		printf("[%s] failed to jump into memory addr %x with wtw=%x!\n",
			__func__, addr, wtw);
		goto Exit;
	}

	rc = 0;
Exit:
	return rc;
}

/*=========================================================*/

uint8_t jlDevType=0;
uint32_t jlDevId=0xdeadbeef;
uint16_t jlChipKey=0x5bd0;
uint16_t jlUserAppKey=0xffff;
uint32_t jlFlashPageSize=512;
uint32_t jlFlashSize=0xffffffff;

int jl_DeviceInit(void) {
	uint8_t cdb[6] = {0x12,0x00,0x00,0,36,0x00};
	uint8_t inquiry[36] = {};
	if (scsi_io_transfer(cdb, sizeof(cdb), inquiry, sizeof(inquiry), 0) < sizeof(inquiry)) {
		puts("can't do inquiry!!");
		return -1;
	}
	
	printf("Inquiry-> [%.8s] [%.16s] [%.4s]\n",
		&inquiry[8], &inquiry[16], &inquiry[32]);
	
	if (!memcmp(&inquiry[16], "UBOOT1.00", 9)) {
		puts("Need to run loader!");
		
		if (!memcmp(&inquiry[8], "BR17", 4)) {
			puts(".... This is BR17!");
			if (jl_uploadAndRunBuff(br17loader_bin, sizeof(br17loader_bin), 0x2000, 0x0011) < 0) {
				puts("failed to run br17loader!");
				return -1;
			}
		} else if (!memcmp(&inquiry[8], "BR21", 4)) {
			puts(".... This is BR21!");
			if (jl_uploadAndRunBuff(br21loader_bin, sizeof(br21loader_bin), 0x2000, 0x0001) < 0) {
				puts("failed to run br21loader!");
				return -1;
			}
		} else {
			printf(".... I don't know who [%.8s] is!\n",
				&inquiry[8]);
		}
	}
	
	return 0;
}

int jl_GetDeviceInfo(void) {
	if (jlUsbIsd_GetDeviceStatus(&jlDevType, &jlDevId) < 0) {
		puts("failed to get device status!");
		return -1;
	}
	
	if (jlUsbIsd_GetChipKey(0xAC6900, &jlChipKey) < 0) {
		puts("failed to get chip key!");
		return -1;
	}
	
	if (jlUsbIsd_GetFlashPageSize(&jlFlashPageSize) < 0) {
		printf("failed to get max flash page size! using default %d bytes\n",
			jlFlashPageSize);
	}
	
	jlUserAppKey = jlChipKey;
	jl_crypt2((uint8_t*)&jlUserAppKey, sizeof(jlUserAppKey), 0xffffffff); /* not big-endian friendly ! */
	
	char *jlDevTypeStr = "<unknown>";
	
	switch (jlDevType) {
	case JLDFU_DEV_TYPE_NONE:	jlDevTypeStr = "No device";		break;
	case JLDFU_DEV_TYPE_SDRAM:	jlDevTypeStr = "SDRAM";			break;
	case JLDFU_DEV_TYPE_SDCARD:	jlDevTypeStr = "SD Card";		break;
	case JLDFU_DEV_TYPE_SPI0_NOR:	jlDevTypeStr = "SPI NOR Flash";		break;
	case JLDFU_DEV_TYPE_SPI0_NAND:	jlDevTypeStr = "SPI NAND Flash";	break;
	case JLDFU_DEV_TYPE_SDCARD2:	jlDevTypeStr = "SD Card (2)";		break;
	case JLDFU_DEV_TYPE_SDCARD3:	jlDevTypeStr = "SD Card (3)";		break;
	case JLDFU_DEV_TYPE_SDCARD4:	jlDevTypeStr = "SD Card (4)";		break;
	case JLDFU_DEV_TYPE_whatever:	jlDevTypeStr = "Something (1)";		break;
	case JLDFU_DEV_TYPE_whatever2:	jlDevTypeStr = "Something (2)";		break;
	case JLDFU_DEV_TYPE_whatever3:	jlDevTypeStr = "Something (3)";		break;
	case JLDFU_DEV_TYPE_SPI1_NOR:	jlDevTypeStr = "SPI NOR Flash (2)";	break;
	case JLDFU_DEV_TYPE_SPI1_NAND:	jlDevTypeStr = "SPI NAND Flash (2)";	break;
	}
	
	if (jlDevType == JLDFU_DEV_TYPE_SPI0_NOR || jlDevType == JLDFU_DEV_TYPE_SPI1_NOR) {
		jlFlashSize = jlDevId & 0xff;
		if (jlFlashSize < 0x10) jlFlashSize = 0x14; /* smaller than 64k - 1M */
		if (jlFlashSize > 0x18) jlFlashSize = 0x18; /* bigger than 16M - 16M */
		jlFlashSize = 1 << jlFlashSize;
	} else {
		printf("... Right now no way to calc the size for dev type %d (%s) -- default to %d KB\n",
			jlDevType, jlDevTypeStr, jlFlashSize / 1024);
	}
	
	printf("Device type     =%d [%s]\n"
	       "Device ID       =%x\n"
	       "Chip key        =%04x\n"
	       "`user.app` key  =%04x\n"
	       "Flash page size =%d\n"
	       "Flash size      =%d KB\n",
	
		jlDevType, jlDevTypeStr,
		jlDevId,
		jlChipKey,
		jlUserAppKey,
		jlFlashPageSize,
		jlFlashSize / 1024
	);
	
	return 0;
}

int JLFlashRead(uint32_t addr, void *buff, int len) {
	printf("Read flash:    %08x %p %d\n",
		addr, buff, len);
	
	while (len > 0) {
		int cnt = (len > jlFlashPageSize) ? jlFlashPageSize : len;
		
		if (jlUsbIsd_ReadFlash(addr, buff, cnt) < 0) {
			printf("[%s] Failed to read %d bytes from flash @ %x!\n",
				__func__, cnt, addr);
			return -1;
		}
		
		len -= cnt;
		addr += cnt;
		buff += cnt;
	}
	
	return 0;
}

int JLFlashProg(uint32_t addr, void *buff, int len) {
	printf("Program flash: %08x %p %d\n",
		addr, buff, len);
	
	while (len > 0) {
		int cnt = (len > jlFlashPageSize) ? jlFlashPageSize : len;
			
		if (jlUsbIsd_WriteFlash(addr, buff, cnt) < 0) {
			printf("[%s] Failed to write %d bytes into flash @ %x!\n",
				__func__, cnt, addr);
			return -1;
		}
		
		uint16_t crc, crc2 = jl_crc16_buff(0, buff, cnt);
		if (jlUsbIsd_GetFlashCRC16(addr, cnt, &crc) >= 0) {
			if (crc != crc2) {
				printf("[%s] CRC of data [%04x] and flash [%04x] doesnt match @ %x!\n",
					__func__, crc2, crc, addr);
				return -1;
			}
		}
		
		len -= cnt;
		addr += cnt;
		buff += cnt;
	}
	
	return 0;
}

int JLFlashErase(uint32_t addr, int len) {
	printf("Erase flash:   %08x %d\n",
		addr, len);
	
	while (len > 0) {
		int blksz = 0x10000;
		if ((addr & 0xf000) || (len < 0x10000))
			blksz = 0x1000;
		
		uint32_t baddr = addr & ~(blksz-1);
		int      boffs = addr &  (blksz-1);
		
		int cnt = blksz - boffs;
		cnt = (len > cnt) ? cnt : len;
		
		uint8_t tmp[blksz];
		
		/* read old sector data (if needed) */
		if (cnt < blksz) {
			if (JLFlashRead(baddr, tmp, blksz) < 0)
				return -1;
		}
		
		/* erase sector */
		if (blksz < 0x10000) {
			if (jlUsbIsd_EraseFlashSector(baddr) < 0) {
				printf("[%s] Failed to erase flash sector @ %x!\n",
					__func__, addr);
				return -1;
			}
		} else {
			if (jlUsbIsd_EraseFlashBlock(baddr) < 0) {
				printf("[%s] Failed to erase flash block @ %x!\n",
					__func__, addr);
				return -1;
			}
		}
		
		/* check erase */
		{
			uint16_t crc = 0, crc2;
			
			/* crc of the erased flash */
			for (int i = 0; i < jlFlashPageSize; i++)
				jl_crc16(&crc, 0xff);
			
			for (int i = 0; i < blksz; ) {
				int cnt = blksz - i;
				cnt = (cnt > jlFlashPageSize) ? jlFlashPageSize : cnt;
				
				if (jlUsbIsd_GetFlashCRC16(baddr + i, cnt, &crc2) < 0)
					break;
				
				if (crc2 != crc) {
					printf("[%s] CRC of erased flash [%04x] and actual flash [%04x] doesnt match @ %x!\n",
						__func__, crc2, crc, baddr + i);
					return -1;
				}
				
				i += cnt;
			}
		}
		
		/* write back the erased data (if needed) */
		if (boffs > 0) { /* part before */
			if (JLFlashProg(baddr, tmp, boffs) < 0)
				return -1;
		}
		
		if ((boffs + cnt) < blksz) { /* part after */
			if (JLFlashProg(addr + cnt, &tmp[boffs + cnt], blksz - boffs - cnt) < 0)
				return -1;
		}
		
		len -= cnt;
		addr += cnt;
	}
	
	return 0;
}

int JLFlashWrite(uint32_t addr, void *buff, size_t len) {
	if (JLFlashErase(addr, len) < 0)
		return -1;
	
	if (JLFlashProg(addr, buff, len) < 0)
		return -1;
	
	return 0;
}


int JLRecrypt(uint16_t skey, uint16_t dkey) {
	printf("Jieli Recrypt!!! SKEY=%04x TKEY=%04x\n", skey, dkey);
	
	struct jl_syd_head sydhead;
	uint16_t crc;
	
	if (JLFlashRead(0, &sydhead, sizeof(sydhead)) < 0) {
		printf("Failed to read SYD Header!\n");
		return 1;
	}
	
	jl_crypt((uint8_t *)&sydhead, sizeof(sydhead), 0xffff);
	
	crc = jl_crc16_buff(0x0000, (uint8_t *)&sydhead.crc16_list, sizeof(sydhead) - 2);
	if (crc != sydhead.crc16_head) {
		printf("CRC16 of header [%04x] and the calculated one [%04x] doesn't match!\n",
			sydhead.crc16_head, crc);
		return 1;
	}
	
	uint32_t recrypt_start=0xffffffff, recrypt_end=0;
	
	for (int i = 0; i < sydhead.file_count; i++) {
		struct jl_syd_entry sydentry;
		
		if (JLFlashRead(sizeof(sydhead) + (i * sizeof(sydentry)), &sydentry, sizeof(sydentry)) < 0) {
			printf("couldn't read entry %d!", i);
			return 1;
		}
		
		jl_crypt((uint8_t *)&sydentry, sizeof(sydentry), 0xffff);
		
		if (sydentry.file_type == 3) { /* special zone file */
			struct jl_syd_entry sydentry2;
			
			for (int j = 0; j < sydentry.size / sizeof(sydentry2); j++) {
				if (JLFlashRead(sydentry.addr + (j * sizeof(sydentry2)), &sydentry2, sizeof(sydentry2)) < 0) {
					printf("couldn't read specialentry %d!", j);
					return 1;
				}
				
				if ((sydentry2.file_type == 2) || (sydentry2.file_type == 6)) { /* user.app or sys.cfg */
					if (sydentry2.addr < recrypt_start)
						recrypt_start = sydentry2.addr;
					
					if (recrypt_end < (sydentry2.addr + sydentry2.size - 1))
						recrypt_end = sydentry2.addr + sydentry2.size - 1;
				}
			}
		} else if (sydentry.file_type == 2) { /* user.app */
			if (sydentry.addr < recrypt_start)
				recrypt_start = sydentry.addr;
			
			if (recrypt_end < (sydentry.addr + sydentry.size - 1))
				recrypt_end = sydentry.addr + sydentry.size - 1;
		}
	}
	
	if (recrypt_start >= recrypt_end) {
		puts("Nothing to recrypt!");
		return 2;
	}
	
	recrypt_end = recrypt_end - recrypt_start + 1;
	
	printf("recrypting: %d bytes @ %x\n", recrypt_end, recrypt_start);
	
	for (int i = 0; i < recrypt_end;) {
		uint8_t buff[65536];
		
		int cnt = sizeof(buff) - ((recrypt_start + i) % sizeof(buff));
		if (cnt > (recrypt_end - i)) cnt = recrypt_end - i;
		
		if (JLFlashRead(recrypt_start + i, buff, cnt) < 0) {
			printf("Failed to read flash @ %x!\n",
				recrypt_start + i);
			return 3;
		}
		
		for (int j = 0; j < cnt; j += 32) {
			jl_crypt(&buff[j], 32, skey ^ ((i+j) >> 2));
			jl_crypt(&buff[j], 32, dkey ^ ((i+j) >> 2));
		}
		
		if (JLFlashWrite(recrypt_start + i, buff, cnt) < 0) {
			printf("Failed to write flash @ %x!\n",
				recrypt_start + i);
			return 3;
		}
		
		i += cnt;
	}
	
	return 0;
}



int main(int argc, char **argv) {
	puts(
		" ______________                           \n"
		"     |    |                               \n"
		"     |    |            _                  \n"
		"     |    |        _| |_ | |  |_  _   _  |\n"
		"     |    |       |_| |  |_|  |_ |_| |_| |\n"
		" \\___|    |____                          \n"
		"\n" 
		"build @ "__DATE__" - "__TIME__"\n"
	);
	
	if (argc < 3) {
		printf("Usage: %s <path to jl disk> <command>...\n", argv[0]);
		printf(
			"Where: \n"
			"  <path to jl disk> - path to the jl dfu disk device\n"
			"                       (e.g. /dev/sg2 on Linux or \\\\.\\E: on Windows)\n"
			"\n"
			"  <command>... - commands!\n"
			"\n"
			"Available commands:\n"
			"  read <addr> <len> <file>\n"
			"    - read <len> bytes of flash at <addr> into <file>\n"
			"      if <len> is zero then whole flash will be read\n"
			"\n"
			"  write <addr> <file>\n"
			"   - write <file> into flash at <addr>\n"
			"\n"
			"  erase <addr> <len>\n"
			"   - erase <len> bytes of flash at <addr>\n"
			"     if <len> is zero then whole flash will be erased\n"
			"\n"
			"  memread <addr> <len> <file>\n"
			"   - read <len> byte of memory at <addr> into <file>\n"
			"\n"
			"  memwrite <addr> <file>\n"
			"   - write <file> into memory at <addr>\n"
			"\n"
			"  memjump <addr> <wtw>\n"
			"   - jump to memory address <addr> with <wtw>\n"
			"\n"
			"  jlrecrypt <fromkey> <tokey>\n"
			"   - recrypt the flash from <fromkey> to <tokey>\n"
			"     if <fromkey> or <tokey> is zero then it will be\n"
			"     replaced with the device key.\n"
			"     THE RECRYPTED DATA WILL BE PUT INTO THE DEVICE FLASH!!\n"
			"     SO DONT FOREGET TO RECRYPT BACK WHEN YOU RECRYPTED FROM THE\n"
			"     DEVICE KEY TO OTHER KEY IF YOU WANT TO HAVE THE DEVICE STILL WORK\n"
			"\n"
		);
		return 1;
	}

	if (scsi_io_open(argv[1])) {
		printf("failed to open deivce `%s`.\n", argv[1]);
		return 2;
	}
	
	int rc = 2;

	/* ---------------------------------------------------- */
	puts("-------------------------------------------");
	if (jl_DeviceInit()) {
		puts("Failed to init device!");
		goto Exit;
	}
	
	if (jl_GetDeviceInfo()) {
		puts("Faield to get device info!");
		goto Exit;
	}
	
	puts("-------------------------------------------");
	
	int xargc = argc - 2;
	char **xargv = argv + 2;
	
	while (xargc > 0) {
		char *cmd = *xargv++; xargc--;
		printf("=============[%s]============\n", cmd);
		
		if (!strcmp(cmd, "read")) {
	/*---------------------- READ ---------------------*/
			if (xargc < 3) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			int len = strtol(*xargv++, NULL, 0); xargc--;
			char *fname = *xargv++; xargc--;
			
			if (addr > jlFlashSize) addr = jlFlashSize;
			if (len <= 0) len = jlFlashSize;
			if ((len + addr) > jlFlashSize) len = jlFlashSize - addr;
			
			printf("Reading %d bytes from flash at %x into file [%s]...\n",
				len, addr, fname);
			
			FILE *fp = fopen(fname, "wb");
			if (!fp) {
				printf("Failed to open file <%s> for writing! %d:%s\n",
					fname, errno, strerror(errno));
				break;
			}
			
			while (len > 0) {
				uint8_t tmp[65536];
				int cnt = sizeof(tmp) - (addr % sizeof(tmp));
				cnt = (len > cnt) ? cnt : len;
				
				if (JLFlashRead(addr, tmp, cnt) < 0) {
					printf("Failed to read %d bytes from flash at %x!\n",
						cnt, addr);
					break;
				}
				
				fwrite(tmp, 1, cnt, fp);
				
				len -= cnt;
				addr += cnt;
			}
			
			fclose(fp);
		} else if (!strcmp(cmd, "write")) {
	/*---------------------- WRITE ---------------------*/
			if (xargc < 2) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			char *fname = *xargv++; xargc--;
			
			printf("Writing file [%s] into flash at %x...\n",
				fname, addr);
			
			FILE *fp = fopen(fname, "rb");
			if (!fp) {
				printf("Failed to open file <%s> for reading! %d:%s\n",
					fname, errno, strerror(errno));
				break;
			}
			
			while (1) {
				uint8_t tmp[65536];
				int cnt = fread(tmp, 1, sizeof(tmp) - (addr % sizeof(tmp)), fp);
				if (cnt <= 0) break;
				
				if (JLFlashWrite(addr, tmp, cnt) < 0) {
					printf("Failed to read %d bytes from flash at %x!\n",
						cnt, addr);
					break;
				}
				
				addr += cnt;
			}
			
			fclose(fp);
		} else if (!strcmp(cmd, "erase")) {
	/*---------------------- ERASE ---------------------*/
			if (xargc < 2) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			int len = strtol(*xargv++, NULL, 0); xargc--;
			
			if (addr > jlFlashSize) addr = jlFlashSize;
			if (len <= 0) len = jlFlashSize;
			if ((len + addr) > jlFlashSize) len = jlFlashSize - addr;
			
			printf("Erasing %d bytes of flash at %x...\n",
				len, addr);
			
			if (JLFlashErase(addr, len) < 0) {
				printf("Failed to erase %d bytes of flash at %x!\n",
					len, addr);
				break;
			}
		} else if (!strcmp(cmd, "memread")) {
	/*---------------------- MEMREAD ---------------------*/
			if (xargc < 3) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			int len = strtol(*xargv++, NULL, 0); xargc--;
			char *fname = *xargv++; xargc--;
			
			printf("Reading %d bytes from memory at %x into file [%s]...\n",
				len, addr, fname);
			
			FILE *fp = fopen(fname, "wb");
			if (!fp) {
				printf("Failed to open file <%s> for writing! %d:%s\n",
					fname, errno, strerror(errno));
				break;
			}
			
			while (len > 0) {
				uint8_t tmp[4096];
				int cnt = (jlFlashPageSize > sizeof(tmp)) ? sizeof(tmp) : jlFlashPageSize;
				cnt = (len > cnt) ? cnt : len;
				
				if (jlUsbIsd_ReadMemory(addr, tmp, cnt) < 0) {
					printf("Failed to read %d bytes from memory at %x!\n",
						cnt, addr);
					break;
				}
				
				fwrite(tmp, 1, cnt, fp);
				
				len -= cnt;
				addr += cnt;
			}
			
			fclose(fp);
		} else if (!strcmp(cmd, "memwrite")) {
	/*---------------------- MEMWRITE ---------------------*/
			if (xargc < 2) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			char *fname = *xargv++; xargc--;
			
			printf("Writing file [%s] into memory at %x...\n",
				fname, addr);
			
			FILE *fp = fopen(fname, "rb");
			if (!fp) {
				printf("Failed to open file <%s> for reading! %d:%s\n",
					fname, errno, strerror(errno));
				break;
			}
			
			while (1) {
				uint8_t tmp[4096];
				int cnt = fread(tmp, 1, (jlFlashPageSize > sizeof(tmp)) ? sizeof(tmp) : jlFlashPageSize, fp);
				if (cnt <= 0) break;
				
				if (jlUsbIsd_WriteMemory(addr, tmp, cnt) < 0) {
					printf("Failed to write %d bytes to memory at %x!\n",
						cnt, addr);
					break;
				}
				
				addr += cnt;
			}
			
			fclose(fp);
		} else if (!strcmp(cmd, "memjump")) {
	/*---------------------- MEMJUMP ---------------------*/
			if (xargc < 2) break;
			uint32_t addr = strtol(*xargv++, NULL, 0); xargc--;
			uint16_t wtw = strtol(*xargv++, NULL, 0); xargc--;
			
			printf("Jumping into memory at %x... with wtw %x\n",
				addr, wtw);
			
			if (jlUsbIsd_JumpMemory(addr, wtw) < 0) {
				printf("Failed to jump to memory at %x with wtw %x!\n",
					addr, wtw);
			}
		} else if (!strcmp(cmd, "jlrecrypt")) {
	/*---------------------- JLRECRYPT ---------------------*/
			if (xargc < 2) break;
			uint16_t skey = strtol(*xargv++, NULL, 0); xargc--;
			if (skey == 0) skey = jlUserAppKey;
			uint16_t tkey = strtol(*xargv++, NULL, 0); xargc--;
			if (tkey == 0) tkey = jlUserAppKey;
			
			printf("Recrypt =====>%d\n", JLRecrypt(skey, tkey));
		} else {
	/*---------------------- ????? ---------------------*/
			printf("unknown command [%s]!\n", cmd);
			break;
		}
	}
	
	puts("----------------- Reset chip! ---------------");
	jlUsbIsd_Reset(1);
	
	/* ---------------------------------------------------- */
	
	rc = 0;
Exit:
	scsi_io_close();
	return rc;
}
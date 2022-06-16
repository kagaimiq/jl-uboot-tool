#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>
#include <getopt.h>
#include <unistd.h>

#include "scsi_io.h"
#include "jlusbisd.h"
#include "jl_stuff.h"

void hexdump(uint8_t *ptr, int len) {
	for (int i = 0; i < len; i += 16) {
		printf("%8x: ", i);

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

	puts("");
}


const char *opts_short = "hd:";
const struct option opts_long[] = {
	{"help",	0, NULL, 'h'},
	{"device",	1, NULL, 'd'},
	{ NULL }
};

void usage(char *progname) {
	fprintf(stderr, "Usage: %s [--help|-d <device path>]\n", progname);
	fprintf(stderr,
		"\n"
		"Tool for dumping and flashing JieLi AC690N/AC692N SoCs and probably more...\n"
		"     <<< Some inspiration goes from flashrom >>>\n"
		"\n"
		" -h | --help              print this help text\n"
		" -d | --device=path       specify path to the JL UBOOT disk device\n"
		"                          (e.g. /dev/sg2 on Linux or \\.\\\\E: on Windows)\n"
		"\n"
		"If no operation is specified, JLDFUTool will only print device info.\n"
		"\n"
	);
}

#include "binbo.h"     // jl blobs

uint8_t jl_deviceType = JLDFU_DEV_TYPE_NONE;
uint32_t jl_deviceID = 0x4d697a75; // "Mizu"
uint16_t jl_chipKey = 0x5ba0;
uint32_t jl_flashPageSize = 512;



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


int jl_uploadAndRunFile(char *path, uint32_t addr, uint16_t wtw) {
	int rc = -1;
	FILE *fp;

	if (!(fp = fopen(path, "rb"))) {
		printf("[%s] failed to open file '%s'! %d:%s\n",
				__func__, path, errno, strerror(errno));
		goto Exit;
	}

	for (uint32_t xaddr = addr;;) {
		uint8_t buff[512];
		int cnt = fread(buff, 1, sizeof(buff), fp);
		if (cnt <= 0) break;

		if (jlUsbIsd_WriteMemory(xaddr, buff, cnt) < 0) {
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

		if (memcmp(buff, buff2, cnt)) {
			printf("[%s] Memory contents at addr %x doesn't match!\n",
				__func__, xaddr);
			goto Exit;
		}

		xaddr += cnt;
	}

	if (jlUsbIsd_JumpMemory(addr, wtw) < 0) {
		printf("[%s] failed to jump into memory addr %x with wtw=%x!\n",
			__func__, addr, wtw);
		goto Exit;
	}

	rc = 0;
Exit:
	if (fp) fclose(fp);
	return rc;
}


int main(int argc, char **argv) {
	puts(
		 "      _____________                           :\n"
		 "     /___  __  ___/     <<Kagami-sama>>       :\n"
		 "        / / / /         _                     :\n"
		 "   _   / / / /      _| |_ | |  |_  _   _  |   :\n"
		"  | \\_/ / / /___   |_| |  |_|  |_ |_| |_| |   :\n"
		"   \\___/ /_____/                              :\n"
		 "..............................................:\n"
		"\n" 
		"built on "__DATE__" - "__TIME__"\n"
	);

	char *dev_path = NULL;

	while (1) {
		int opt = getopt_long(argc, argv, opts_short, opts_long, NULL);
		if (opt == -1) break;

		switch (opt) {
		case '?':
			usage(argv[0]);
			return 1;
		case 'h':
			usage(argv[0]);
			return 0;

		case 'd':
			dev_path = optarg;
			break;
		}
	}

	argc -= optind;
	argv += optind;

	if (dev_path) {
		if (scsi_io_open(dev_path)) {
			fprintf(stderr, "failed to open deivce `%s`.\n", dev_path);
			return 2;
		}
	} else {
		fprintf(stderr,
			"autodetection or something like that is not present yet.\n"
			"\n"
			"Please specify the device path with the --device parameter.\n"
		);
		return 2;
	}

	int rc = 2;

	/*==========================================================*/

	#if 0
	jl_uploadAndRunBuff(br21loader_bin, sizeof(br21loader_bin), 0x2000, 0x0001);

	#if 1
	// no checks whatsoever //
	jlUsbIsd_GetDeviceStatus(&jl_deviceType, &jl_deviceID);
	jlUsbIsd_GetChipKey(0xAC6900, &jl_chipKey);
	jlUsbIsd_GetFlashPageSize(&jl_flashPageSize);
	
	printf("Device type     >> %d\n", jl_deviceType);
	printf("Device ID       >> %06X\n", jl_deviceID);
	printf("Chip key        >> %04X\n", jl_chipKey);
	printf("Flash page size >> %d\n", jl_flashPageSize);
	#endif

	{
		uint8_t tmp[512];
		FILE *fp;

		if ((fp = fopen("JL_DUMP_2022.bin", "wb"))) {
			for (int i = 0; i < 0x80000; i += sizeof(tmp)) {
				jlUsbIsd_ReadFlash(i, tmp, sizeof(tmp));
				//hexdump(tmp, sizeof(tmp));
				fwrite(tmp, 1, sizeof(tmp), fp);
			}
	
			fclose(fp);
		}
	}
	#endif

	jl_uploadAndRunFile("../payload.bin", 0x10000, 0x4777);

	/*==========================================================*/
	
	rc = 0;
Exit:
	scsi_io_close();
	return rc;
}
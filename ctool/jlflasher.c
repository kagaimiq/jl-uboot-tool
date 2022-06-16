#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>

#include "scsi_io.h"
#include "jlusbisd.h"
#include "jl_stuff.h"


//#include "binbo.h"     // jl blobs

uint8_t jl_deviceType = JLDFU_DEV_TYPE_NONE;
uint32_t jl_deviceID = 0x4d697a75; // "Mizu"
uint16_t jl_chipKey = 0x5ba0;
uint32_t jl_flashPageSize = 512;

uint16_t jl_encKey;
uint32_t jl_flashSize;





int main(int argc, char **argv) {
	if (argc < 2) {
		fprintf(stderr,
			"Usage: %s <dev path> ...\n"
			"\n"
			"   read <file> [<addr> <len>]\n"
			"   write <file> [<addr>]\n"
			"   erase [<addr> <len>]\n"
			"\n",
			argv[0]
		);
		return 1;
	}

	if (scsi_io_open(argv[1])) {
		fprintf(stderr, "failed to open deivce `%s`.\n", argv[1]);
		return 2;
	}

	int rc = 2;

	/* ================================================================ */
	/* >>> Load the loader <<< */

	#if 0
	{
		uint8_t inquiry[36];
		uint8_t cdb[6] = {0x12,0x00,0x00,0,36,0x00};

		if (scsi_io_transfer(cdb, sizeof(cdb), inquiry, sizeof(inquiry), 0) != sizeof(inquiry)) {
			fprintf(stderr, "Couldn't do Inquiry request!\n");
			goto Exit;
		}

		printf("[%.8s] [%.16s] [%.4s]\n",
			&inquiry[8],&inquiry[16],&inquiry[32]);

		if (!memcmp(&inquiry[16], "UBOOT1.00", 9)) {
			puts("This is indeed UBOOT1.00");

			if (!memcmp(&inquiry[8], "BR17", 4)) {
				puts(">>>BR17");
			} else 
			if (!memcmp(&inquiry[8], "BR21", 4)) {
				puts(">>>BR21");
			}
		}
	}

	puts("");
	#endif

	/* ================================================================ */
	/* >>> Get device infos <<< */

	if (jlUsbIsd_GetDeviceStatus(&jl_deviceType, &jl_deviceID)) {
		fprintf(stderr, "Couldn't get device status!\n");
		goto Exit;
	}

	if (jlUsbIsd_GetChipKey(0xAC6900, &jl_chipKey)) {
		fprintf(stderr, "Couldn't get chip key!\n");
		goto Exit;
	}

	if (jlUsbIsd_GetFlashPageSize(&jl_flashPageSize)) {
		fprintf(stderr, "Couldn't get flash page size, default to %d.\n",
			jl_flashPageSize);
	}

	// too small size
	if (jl_flashPageSize <= 0) jl_flashPageSize = 512;
	// bigger than max of uint16
	if (jl_flashPageSize > 65535) jl_flashPageSize = 32768;

	{
		char *devtype = "<unknown>";

		switch (jl_deviceType) {
		case JLDFU_DEV_TYPE_NONE:      devtype = "None"; break;
		case JLDFU_DEV_TYPE_SDRAM:     devtype = "SDRAM"; break;
		case JLDFU_DEV_TYPE_SDCARD:    devtype = "SD Card"; break;
		case JLDFU_DEV_TYPE_SDCARD2:   devtype = "SD Card [2]"; break;
		case JLDFU_DEV_TYPE_SDCARD3:   devtype = "SD Card [3]"; break;
		case JLDFU_DEV_TYPE_SDCARD4:   devtype = "SD Card [4]"; break;
		case JLDFU_DEV_TYPE_SPI0_NOR:  devtype = "SPI NOR Flash on SPI0"; break;
		case JLDFU_DEV_TYPE_SPI1_NOR:  devtype = "SPI NOR Flash on SPI1"; break;
		case JLDFU_DEV_TYPE_SPI0_NAND: devtype = "SPI NAND Flash on SPI0"; break;
		case JLDFU_DEV_TYPE_SPI1_NAND: devtype = "SPI NAND Flash on SPI1"; break;
		}

		printf("Device type     >> %d (%s)\n", jl_deviceType, devtype);
		printf("Device ID       >> %06X\n", jl_deviceID);
		printf("Chip key        >> %04X\n", jl_chipKey);
		printf("Flash page size >> %d\n", jl_flashPageSize);
	}

	if ((jl_deviceType != JLDFU_DEV_TYPE_SPI0_NOR) &&
	    (jl_deviceType != JLDFU_DEV_TYPE_SPI1_NOR))
	{
		fprintf(stderr, "Sorry, but this tool only supports the SPI NOR flash!\n");
		goto Exit;
	}

	/* make the encryption key out of chip key */ {
		// endian agonistic
		uint8_t tmp[2] = {jl_chipKey, jl_chipKey>>8};
		jl_crypt2(tmp, sizeof(tmp), 0xffffffff);
		jl_encKey = tmp[0] | (tmp[1] << 8);
	}

	printf("Encryption key  >> %04X\n", jl_encKey);

	/* rough calculation of the flash size */ {
		// grab the bits0~7 of the JEDEC ID -> usually it's log2 of the flash size
		jl_flashSize = jl_deviceID & 0xff;
		// sanity check
		if (jl_flashSize > 0x19) jl_flashSize = 0x16; // > 32 MiB? 4 MiB.
		if (jl_flashSize < 0x11) jl_flashSize = 0x14; // < 128 KiB? 1 MiB.
		// real size
		jl_flashSize = 1 << jl_flashSize;
	}

	printf("Flash size      >> %d (%d KiB)\n",
		jl_flashSize, jl_flashSize/1024);

	puts("");

	/* ================================================================ */
	/* >>> Main stuff <<< */

	if (argc > 2) {
		char *op = argv[2];
		char **opargv = &argv[3];
		int opargc = argc - 3;

		if (!strcmp(op, "read")) {
			uint32_t addr = 0;
			uint32_t size = jl_flashSize;

			if (opargc >= 3) {
				addr = strtoul(opargv[1], NULL, 0);
				size = strtoul(opargv[2], NULL, 0);
			}

			printf("Will read %d bytes of flash from addr %08x into '%s'\n",
				size, addr, opargv[0]);

			if (opargc >= 1) {
				FILE *fp = fopen(opargv[0], "wb");
				if (!fp) {
					fprintf(stderr, "Can't open file '%s' for writing: %d:%s\n",
						opargv[0], errno, strerror(errno));
					goto Exit;
				}

				while (size > 0) {
					int cnt = size > jl_flashPageSize ? jl_flashPageSize : size;

					printf(">>> %08x %d\n", addr,cnt);

					uint8_t *tmp = malloc(cnt);
					if (tmp) {
						jlUsbIsd_ReadFlash(addr, tmp, cnt);
						fwrite(tmp, 1, cnt, fp);
						free(tmp);
					}

					size -= cnt;
					addr += cnt;
				}

				fclose(fp);
			} else {
				fprintf(stderr, "You need to specify the file where the flash will be written to!\n");
				goto Exit;
			}
		} else {
			fprintf(stderr, "Unknown operation '%s'.\n", op);
			goto Exit;
		}
	} else {
		fprintf(stderr, "No operations specified.\n");
	}

	/* ================================================================ */

	rc = 0;
Exit:
	scsi_io_close();
	return rc;
}

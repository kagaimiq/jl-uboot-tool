#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stddef.h>
#include <errno.h>
#include <string.h>

#include "scsi_io.h"
#include "jlusbisd.h"
#include "jl_stuff.h"

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

		printf("Writing... %08x\n", xaddr);

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

	printf("Jumping to %08x with arg %04x\n", addr, wtw);

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
	if (argc < 4) {
		fprintf(stderr,
			"Usage: %s <dev path> <address> <file> [<arg>]\n",
			argv[0]
		);
		return 1;
	}

	if (scsi_io_open(argv[1])) {
		fprintf(stderr, "failed to open deivce `%s`.\n", argv[1]);
		return 2;
	}

	int rc = jl_uploadAndRunFile(
		argv[3],
		strtoul(argv[2], NULL, 0),
		(argc > 4) ? strtoul(argv[4], NULL, 0) : 0x4777
	);

	if (rc) rc = 2;

	scsi_io_close();
	return rc;
}

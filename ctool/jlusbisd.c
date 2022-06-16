#include <stdio.h>
#include <string.h>
#include "scsi_io.h"
#include "jlusbisd.h"
#include "jl_stuff.h"

int jlUsbIsd_EraseFlashBlock(uint32_t addr) {
	uint8_t cdb[16] = {
		0xfb,
		0x00,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}

	return 0;
}

int jlUsbIsd_EraseFlashSector(uint32_t addr) {
	uint8_t cdb[16] = {
		0xfb,
		0x01,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	return 0;
}

int jlUsbIsd_EraseFlashChip(void) {
	uint8_t cdb[16] = {
		0xfb,
		0x02,
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	return 0;
}

int jlUsbIsd_WriteFlash(uint32_t addr, void *data, uint16_t len) {
	uint8_t cdb[16] = {
		0xfb,
		0x04,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		len >> 8,
		len >> 0
	};
	
	int cnt = scsi_io_transfer(cdb, sizeof(cdb), data, len, 1);
	if (cnt < 0) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if (cnt != len) {
		printf("[%s] we have different data length >>> %d != %d\n",
			__func__, cnt, len);
	}

	return 0;
}

int jlUsbIsd_ReadFlash(uint32_t addr, void *data, uint16_t len) {
	uint8_t cdb[16] = {
		0xfd,
		0x05,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		len >> 8,
		len >> 0
	};
	
	int cnt = scsi_io_transfer(cdb, sizeof(cdb), data, len, 0);
	if (cnt < 0) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if (cnt != len) {
		printf("[%s] we have different data length >>> %d != %d\n",
			__func__, cnt, len);
	}

	return 0;
}

int jlUsbIsd_WriteMemory(uint32_t addr, void *data, uint16_t len) {
	uint16_t crc = jl_crc16_buff(0x0000, data, len);

	uint8_t cdb[16] = {
		0xfb,
		0x06,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		len >> 8,
		len >> 0,
		0x00,
		crc >> 0,
		crc >> 8
	};
	
	int cnt = scsi_io_transfer(cdb, sizeof(cdb), data, len, 1);
	if (cnt < 0) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if (cnt != len) {
		printf("[%s] we have different data length >>> %d != %d\n",
			__func__, cnt, len);
	}

	return 0;
}

int jlUsbIsd_ReadMemory(uint32_t addr, void *data, uint16_t len) {
	uint8_t cdb[16] = {
		0xfd,
		0x07,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		len >> 8,
		len >> 0
	};
	
	int cnt = scsi_io_transfer(cdb, sizeof(cdb), data, len, 0);
	if (cnt < 0) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if (cnt != len) {
		printf("[%s] we have different data length >>> %d != %d\n",
			__func__, cnt, len);
	}

	return 0;
}

int jlUsbIsd_JumpMemory(uint32_t addr, uint16_t wtw) {
	uint8_t cdb[16] = {
		0xfb,
		0x08,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		wtw >> 8,
		wtw >> 0
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	return 0;
}

int jlUsbIsd_GetChipKey(uint32_t wtw, uint16_t *key) {
	uint8_t cdb[16] = {
		0xfc,
		0x09,
		wtw >> 24,
		wtw >> 16,
		wtw >> 8,
		wtw >> 0
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	*key = (resp[6] << 8) |
	       (resp[7] << 0);
	
	return 0;
}

int jlUsbIsd_GetDeviceStatus(uint8_t *type, uint32_t *id) {
	uint8_t cdb[16] = {
		0xfc,
		0x0a,
		0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	*type = resp[2];
	
	*id = (resp[4] << 0) |
	      (resp[5] << 8) |
	      (resp[6] << 16) |
	      (resp[7] << 24);
	
	return 0;
}

int jlUsbIsd_Reset(uint32_t wtw) {
	uint8_t cdb[16] = {
		0xfc,
		0x0c,
		wtw >> 24,
		wtw >> 16,
		wtw >> 8,
		wtw >> 0
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	return 0;
}

int jlUsbIsd_GetFlashCRC16(uint32_t addr, uint16_t len, uint16_t *crc) {
	uint8_t cdb[16] = {
		0xfc,
		0x13,
		addr >> 24,
		addr >> 16,
		addr >> 8,
		addr >> 0,
		len >> 8,
		len >> 0
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	*crc = (resp[2] << 8) |
	       (resp[3] << 0);
	
	return 0;
}

int jlUsbIsd_GetFlashPageSize(uint32_t *size) {
	uint8_t cdb[16] = {
		0xfc,
		0x14,
	};
	
	uint8_t resp[16];
	if (scsi_io_transfer(cdb, sizeof(cdb), resp, sizeof(resp), 0) != sizeof(resp)) {
		printf("[%s] failed to do the command %02x:%02x!\n",
			__func__, cdb[0],cdb[1]);
		return -1;
	}
	
	if ((resp[0] != cdb[0]) || (resp[1] != cdb[1])) {
		printf("[%s] response check failed! %02x:%02x != %02x:%02x\n",
			__func__, resp[0],resp[1], cdb[0],cdb[1]);
		return -1;
	}
	
	*size = (resp[2] << 24) |
	        (resp[3] << 16) |
	        (resp[4] << 8) |
	        (resp[5] << 0);
	
	return 0;
}
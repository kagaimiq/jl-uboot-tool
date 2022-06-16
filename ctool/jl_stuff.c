#include "jl_stuff.h"

/* The heart */
#define JL_CRC16SR(crc)	crc = (crc << 1) ^ ((crc >> 15) ? 0x1021 : 0)

void jl_crc16(uint16_t *crc, uint8_t val) {
	*crc ^= val << 8;
	for (int i = 0; i < 8; i++)
		JL_CRC16SR(*crc);
}

uint16_t jl_crc16_buff(uint16_t crc, uint8_t *buff, int len) {
	while (len--) {
		crc ^= *buff++ << 8;
		for (int i = 0; i < 8; i++)
			JL_CRC16SR(crc);
	}
	
	return crc;
}

/* The Hyper Secret And The Most Sophisticated Encryption Algos! */
void jl_crypt(uint8_t *buff, int len, uint16_t key) {
	while (len--) {
		*buff++ ^= key;
		JL_CRC16SR(key);
	}
}

void jl_crypt2(uint8_t *buff, int len, uint32_t key) {
	uint16_t crc = key;
	jl_crc16(&crc, key >> 16);
	jl_crc16(&crc, key >> 24);
	
	const uint8_t magic_array[16] = {
		/* btw you can also see these exact bytes in the uboot.boot! */
		0xc3,0xcf,0xc0,0xe8,0xce,0xd2,0xb0,0xae,0xc4,0xe3,0xa3,0xac,0xd3,0xf1,0xc1,0xd6
	};
 
	for (int i = 0; i < len; i++) {
		jl_crc16(&crc, magic_array[i%16]);
		*buff++ ^= crc;
	}
}
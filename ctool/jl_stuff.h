#ifndef _JL_STUFF_H
#define _JL_STUFF_H

#include <stdint.h>

// previously known as "kagami-mochi"
//  but now it's better

struct jl_bankcb_head {
	uint16_t bank_num;	// bank count <?>
	uint16_t size;		// bank data size
	uint32_t bank_addr;	// bank load adress <?>
	uint32_t data_addr;	// bank data offset in file
	uint16_t data_crc16;	// crc16 of data
	uint16_t head_crc16;	// crc16 of previous 14 bytes
};

struct jl_syd_head {
	uint16_t crc16_head;	// crc16 of next 30 bytes
	uint16_t crc16_list;	// crc16 of file entry list
	uint32_t info1;		// syd end? / header offset? / syd size? | <class+0xa0>
	uint32_t info2;		// <class+0xc8> -- ??
	uint32_t file_count;	// count of files
	uint32_t version1;	// <class+0xc0> -- ??
	uint32_t version2;	// <class+0xbc> -- ??
	uint32_t chiptype1;	// <class+0xc4> -- ??
	uint32_t chiptype2;	// <class+0xb8> -- ??
};

struct jl_syd_entry {
	uint8_t file_type;	// file type
	uint8_t resvd;		// reserved
	uint16_t crc16;		// crc16 of file data
	uint32_t addr;		// file address
	uint32_t size;		// file size
	uint32_t num;		// file number
	char name[16];		// zero-terminated file name
};

enum {
	JLDFU_DEV_TYPE_NONE = 0,
	JLDFU_DEV_TYPE_SDRAM,
	JLDFU_DEV_TYPE_SDCARD,
	JLDFU_DEV_TYPE_SPI0_NOR,
	JLDFU_DEV_TYPE_SPI0_NAND,
	JLDFU_DEV_TYPE_SDCARD2 = 16,
	JLDFU_DEV_TYPE_SDCARD3,
	JLDFU_DEV_TYPE_SDCARD4,
	JLDFU_DEV_TYPE_whatever,
	JLDFU_DEV_TYPE_whatever2,
	JLDFU_DEV_TYPE_whatever3,
	JLDFU_DEV_TYPE_SPI1_NOR,
	JLDFU_DEV_TYPE_SPI1_NAND,
};

void jl_crc16(uint16_t *crc, uint8_t val);
uint16_t jl_crc16_buff(uint16_t crc, uint8_t *buff, int len);
void jl_crypt(uint8_t *buff, int len, uint16_t key);
void jl_crypt2(uint8_t *buff, int len, uint32_t key);

#endif
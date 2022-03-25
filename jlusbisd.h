#ifndef _JL_USB_ISD
#define _JL_USB_ISD

#include <stdint.h>

int jlUsbIsd_EraseFlashBlock(uint32_t addr);
int jlUsbIsd_EraseFlashSector(uint32_t addr);
int jlUsbIsd_EraseFlashChip(void);
int jlUsbIsd_WriteFlash(uint32_t addr, void *data, uint16_t len);
int jlUsbIsd_ReadFlash(uint32_t addr, void *data, uint16_t len);
int jlUsbIsd_WriteMemory(uint32_t addr, void *data, uint16_t len);
int jlUsbIsd_ReadMemory(uint32_t addr, void *data, uint16_t len);
int jlUsbIsd_JumpMemory(uint32_t addr, uint16_t wtw);
int jlUsbIsd_GetChipKey(uint32_t wtw, uint16_t *key);
int jlUsbIsd_GetDeviceStatus(uint8_t *type, uint32_t *id);
int jlUsbIsd_Reset(uint32_t wtw);
int jlUsbIsd_GetFlashCRC16(uint32_t addr, uint16_t len, uint16_t *crc);
int jlUsbIsd_GetFlashPageSize(uint32_t *size);

#endif
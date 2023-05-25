/*
 * Special register access thing...
 *  [Mizu-DEC TEKKNO Co Ltd]
 */
#ifndef _REG_ACCESS_H
#define _REG_ACCESS_H

#include <stdint.h>

/*============================================================================*/

#define reg_wsmask(reg, shift, mask, val) \
	(reg) = ((reg) & ~((mask) << (shift))) | (((val) & (mask)) << (shift))

#define reg_wmask(reg, shift, mask, val) \
	(reg) = ((reg) & ~(mask)) | ((val) & (mask))

#define reg_rsmask(reg, shift, mask) \
	(((reg) >> (shift)) & (mask))

/*------------------------------------------------------*/

#define REG8(addr) \
	(*(volatile uint8_t *)(addr))

#define REG16(addr) \
	(*(volatile uint16_t *)(addr))

#define REG32(addr) \
	(*(volatile uint32_t *)(addr))

/*------------------------------------------------------*/

#define reg32_read(addr) \
	REG32(addr)

#define reg32_write(addr, val) \
	REG32(addr) = val

#define reg32_wsmask(addr, shift, mask, val) \
	reg_wsmask(REG32(addr), shift, mask, val)

#define reg32_rsmask(addr, shift, mask) \
	reg_rsmask(REG32(addr), shift, mask)

/*============================================================================*/

#define _REG_MKVAL(addr, shift, mask, val)	(((val) & (mask)) << (shift))
#define REG_MKVAL(regdef, val)			_REG_MKVAL(regdef, val)

#define _REG_GETVAL(addr, shift, mask, val)	(((val) >> (shift)) & (mask))
#define REG_GETVAL(regdef, val)			_REG_GETVAL(regdef, val)

#define _REG_SMASK(addr, shift, mask)	((mask) << (shift))
#define REG_SMASK(regdef)			_REG_SMASK(regdef)

#endif

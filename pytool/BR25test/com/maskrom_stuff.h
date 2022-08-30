#ifndef _MASKROM_STUFF_H
#define _MASKROM_STUFF_H

#include <stdint.h>

////////////////////////////////////////////////////////
// IRQ //
/////////

void local_irq_enable(void);
void local_irq_disable(void);

////////////////////////////////////////////////////////
// P33 //
/////////

uint8_t p33_buf       (uint8_t val);
void    p33_xor_1byte (uint16_t addr, uint8_t val);
void    p33_and_1byte (uint16_t addr, uint8_t val);
void    p33_or_1byte  (uint16_t addr, uint8_t val);
void    p33_tx_1byte  (uint16_t addr, uint8_t val);
uint8_t p33_rx_1byte  (uint16_t addr);
void    P33_CON_SET   (uint16_t addr, char shift, char nbits, uint8_t val);	// kinda wsmask!

#endif

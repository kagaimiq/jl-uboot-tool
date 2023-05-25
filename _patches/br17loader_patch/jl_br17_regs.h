/*
 * Register defitinion for JieLi BR17 (AC690N)
 */
#ifndef _JL_BR17_REGS_H
#define _JL_BR17_REGS_H

#include <stdint.h>
#include "regaccess.h"

/*============================================================================*/
/********* Low-speed bus **********/
/* SYSTEM - system stuff */

struct JL_SYSTEM_regs {
	volatile uint32_t	CHIP_ID;	/* [00] Chip ID */
	volatile uint32_t	MODE_CON;	/* [04] ~Mode control reg */
	uint32_t Reserved_08[31];
	volatile uint32_t	LDO_CON;	/* [84] LDO control reg */
	volatile uint32_t	LVD_CON;	/* [88] LVD control reg */
	volatile uint32_t	WDT_CON;	/* [8C] WDT control reg */
	volatile uint32_t	OSA_CON;	/* [90] ~OSA control reg */
	volatile uint32_t	EFUSE_CON;	/* [94] eFuse control reg */
};

/*---------------------------------------*/
/* WAKEUP - port wakeup */

struct JL_WAKEUP_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	CON2;		/* Control reg 2 */
	volatile uint32_t	CON3;		/* Control reg 3 */
};

/*---------------------------------------*/
/* IOMAP - port io mapping */

struct JL_IOMAP_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	CON2;		/* Control reg 2 */
	volatile uint32_t	CON3;		/* Control reg 3 */
};

/*---------------------------------------*/
/* POWER - power control */

struct JL_POWER_regs {
	volatile uint32_t	CON;		/* Control reg */
};

/*---------------------------------------*/
/* CLOCK - clock config */

struct JL_CLOCK_regs {
	volatile uint32_t	SYS_DIV;	/* System clock divider */
	volatile uint32_t	CLK_CON0;	/* Clock control reg 0 */
	volatile uint32_t	CLK_CON1;	/* Clock control reg 1 */
	volatile uint32_t	CLK_CON2;	/* Clock control reg 2 */
	uint32_t Reserved_54[11];
	volatile uint32_t	PLL_CON;	/* PLL control reg */
};

/*---------------------------------------*/
/* PORT - gpio port */

struct JL_PORT_regs {
	volatile uint32_t	OUT;		/* Output level */
	volatile uint32_t	IN;		/* Input level */
	volatile uint32_t	DIR;		/* Direction (1 = input) */
	volatile uint32_t	DIE;		/* Digital input enable */
	volatile uint32_t	PU;		/* Pullup enable */
	volatile uint32_t	PD;		/* Pulldown enable */
	volatile uint32_t	HD;		/* High-drive enable */
};

/*---------------------------------------*/
/* TIMER - period/pwm timer */

struct JL_TIMER_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	CNT;		/* Counter */
	volatile uint32_t	PRD;		/* Period */
	volatile uint32_t	PWM;		/* PWM compare (duty) */
};

/*---------------------------------------*/
/* UART - universal asynchronous receiver-transmitter */

struct JL_UARTx_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BAUD;		/* Baudrate divider */
	volatile uint32_t	BUF;		/* Data reg */
	volatile uint32_t	OTCNT;		/* OT */		/* Overtime/Timeout count */
	volatile uint32_t	TXADR;		/* DMA_RD_ADR */	/* TX DMA address */
	volatile uint32_t	TXCNT;		/* DMA_RD_CNT */	/* TX DMA length */
	volatile uint32_t	RXSADR;		/* DMA_WR_SADR */	/* RX DMA start address */
	volatile uint32_t	RXEADR;		/* DMA_WR_EADR */	/* RX DMA end address */
	volatile uint32_t	RXCNT;		/* DMA_WR_CNT */	/* RX DMA count */
};

struct JL_UART2_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BUF;		/* Data reg */
	volatile uint32_t	BAUD;		/* Baudrate divider */
};

/*---------------------------------------*/
/* SPI - serial peripheral interface */

struct JL_SPI_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BAUD;		/* Clock divider */
	volatile uint32_t	BUF;		/* Data reg */
	volatile uint32_t	ADR;		/* DMA address */
	volatile uint32_t	CNT;		/* DMA length */
};

/*---------------------------------------*/
/* PAP - parallel active port */

struct JL_PAP_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	DAT0;		/* Data reg 0 */
	volatile uint32_t	DAT1;		/* Data reg 1 */
	uint32_t Reserved_0C;
	volatile uint32_t	ADR;		/* DMA address */
	volatile uint32_t	CNT;		/* DMA length */
};

/*---------------------------------------*/
/* SD - sd/mmc host */

struct JL_SD_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	CON2;		/* Control reg 2 */
	volatile uint32_t	CPTR;		/* Command buffer address */
	volatile uint32_t	DPTR;		/* Data buffer address */
};

/*---------------------------------------*/
/* IIC - inter-integrated circuit (i2c) */

struct JL_IIC_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BUF;		/* Data reg */
	volatile uint32_t	BAUD;		/* Clock divider */
};

/*---------------------------------------*/
/* LCDC - lcd controller */

struct JL_LCDC_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	uint32_t Reserved_04;
	volatile uint32_t	SEG_IOEN0;	/* Segment IO enable 0 */
	volatile uint32_t	SEG_IOEN1;	/* Segment IO enable 1 */
};

/*---------------------------------------*/
/* LSOTH - others (ls bus) */

struct JL_PWM4_regs {
	volatile uint32_t	CON;		/* Control reg */
};

/*---------------------------------------*/
/* IRTC - internal real time clock/counter */

struct JL_IRTC_regs {
	volatile uint32_t	CON;		/* Control reg */
};

/*---------------------------------------*/
/* IRFLT - infrared (signal) filter */

struct JL_IRFLT_regs {
	volatile uint32_t	CON;	/* FLT_CON*/	/* Control reg */
};

/*---------------------------------------*/
/* AUDIO - audio codec / adda / dac */

struct JL_AUDIO_regs {
	volatile uint32_t	DAC_LEN;	/* DAC buffer length */
	volatile uint32_t	DAC_CON;	/* DAC control reg */
	volatile uint32_t	DAC_ADR;	/* DAC buffer address */
	volatile uint32_t	DAC_TRML;	/* DAC trim left */
	volatile uint32_t	DAC_TRMR;	/* DAC trim right */
	uint32_t Reserved_14[3];
	volatile uint32_t	LADC_CON;	/* LADC control reg */
	uint32_t Reserved_24[2];
	volatile uint32_t	LADC_ADR;	/* LADC buffer address */
	volatile uint32_t	LADC_LEN;	/* LADC buffer length */
	uint32_t Reserved_34[3];
	volatile uint32_t	DAA_CON0;	/* DAC analog control reg 0 */
	volatile uint32_t	DAA_CON1;	/* DAC analog control reg 1 */
	volatile uint32_t	DAA_CON2;	/* DAC analog control reg 2 */
	volatile uint32_t	DAA_CON3;	/* DAC analog control reg 3 */
	volatile uint32_t	DAA_CON4;	/* DAC analog control reg 4 */
	volatile uint32_t	DAA_CON5;	/* DAC analog control reg 5 */
	uint32_t Reserved_58[10];
	volatile uint32_t	ADA_CON0;	/* ADC analog control reg 0 */
	volatile uint32_t	ADA_CON1;	/* ADC analog control reg 1 */
	volatile uint32_t	ADA_CON2;	/* ADC analog control reg 2 */
};

/*---------------------------------------*/
/* ALNK - audio link (inter-integrated sound / i2s) */

struct JL_ALNK_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	CON2;		/* Control reg 2 */
	volatile uint32_t	ADR0;		/* Buffer address 0 */
	volatile uint32_t	ADR1;		/* Buffer address 1 */
	volatile uint32_t	ADR2;		/* Buffer address 2 */
	volatile uint32_t	ADR3;		/* Buffer address 3 */
	volatile uint32_t	LEN;		/* Buffer length */
};

/*---------------------------------------*/
/* NFC - near field communication */

struct JL_NFC_regs {
	uint32_t Reserved_00;
	volatile uint32_t	CON0;
	volatile uint32_t	CON1;
	volatile uint32_t	CON2;
	volatile uint32_t	BUF0;
	volatile uint32_t	BUF1;
	volatile uint32_t	BUF2;
	volatile uint32_t	BUF3;
};

/*---------------------------------------*/
/* USB - universal serial bus */

struct JL_USB_regs {
	volatile uint32_t	IO_CON;		/* GPIO control */
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	EP0_CNT;	/* EP0 (tx) transfer size */
	volatile uint32_t	EP1_CNT;	/* EP1 (tx) transfer size */
	volatile uint32_t	EP2_CNT;	/* EP2 (tx) transfer size */
	volatile uint32_t	EP3_CNT;	/* EP3 (tx) transfer size */
	volatile uint32_t	EP0_ADR;	/* EP0 buffer address */
	volatile uint32_t	EP1_TADR;	/* EP1.IN buffer address */
	volatile uint32_t	EP1_RADR;	/* EP1.OUT buffer address */
	volatile uint32_t	EP2_TADR;	/* EP2.IN buffer address */
	volatile uint32_t	EP2_RADR;	/* EP2.OUT buffer address */
	volatile uint32_t	EP3_TADR;	/* EP3.IN buffer address */
	volatile uint32_t	EP3_RADR;	/* EP3.OUT buffer address */
};

/* USB indirect registers (MUSB!! but altered ... like Allwinner)
 * (common usb regs)
 * 00 - FADDR			00 FAddr
 * 01 - POWER			01 Power
 * 02 - INTRTX1			02 IntrTx
 * 03 - INTRTX2			03 IntrTx
 * 04 - INTRRX1			04 IntrRx
 * 05 - INTRRX2			05 IntrRx
 * 06 - INTRUSB			0A IntrUSB
 * 07 - INTRTX1E		06 IntrTxE
 * 08 - INTRTX2E		07 IntrTxE
 * 09 - INTRRX1E		08 IntrRxE
 * 0A - INTRRX2E		09 IntrRxE
 * 0B - INTRUSBE		0B IntrUSBE
 * 0C - FRAME1			0C Frame
 * 0D - FRAME2			0D Frame
 * 0E - INDEX			0E Index
 * (additional control & config regs)
 * 0F - DEVCTL			60 DevCtl
 * (indexed endpoint regs)
 * 10 - TXMAXP			10 TxMaxP
 * 11 - CSR0 / TXCSR1		12 CSR0 / TxCSRL
 * 12 - TXCSR2			13 TxCSRH
 * 13 - RXMAXP			14 RxMaxP
 * 14 - RXCSR1			16 RxCSRL
 * 15 - RXCSR2			17 RxCSRH
 * 16 - COUNT0 / RXCOUNT1	18 Count0 / RxCount
 * 17 - RXCOUNT2		19 RxCount
 * (--- host-only)
 * 18 - TXTYPE			1A TxType
 * 19 - TXINTERVAL		1B TxInterval
 * 1A - RXTYPE			1C RxType
 * 1B - RXINTERVAL		1D RxInterval
 */

/*---------------------------------------*/
/* CRC - cyclic redundancy check (CRC16-CCITT) */

struct JL_CRC_regs {
	volatile uint32_t	FIFO;		/* CRC FIFO */
	volatile uint32_t	REG;		/* CRC shift register */
};

/*---------------------------------------*/
/* RAND - (pseudo-)random number generator (64 bit) */

struct JL_RAND_regs {
	volatile uint32_t	R64L;		/* Low 32 bits */
	volatile uint32_t	R64H;		/* High 32 bits */
};

/*---------------------------------------*/
/* ADC - analog-digital converter */

struct JL_ADC_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	RES;		/* Conversion result */
};

/*---------------------------------------*/
/* PLCNT - pulse counter */

struct JL_PLCNT_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	VL;	/* TVL */	/* Value */
};

/*---------------------------------------*/
/* PD - power down */

struct JL_PD_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	DAT;		/* Data reg */
};

/*---------------------------------------*/
/* CTM - charge time measurement */

struct JL_CTM_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	RES;		/* Result */
};

/*---------------------------------------*/
/* SPDET - speed detection */

struct JL_SPDET_regs {
	volatile uint32_t	CON0;	/* DETCON0 */
	volatile uint32_t	CON1;	/* DETCON1 */
	volatile uint32_t	PULSE_CNT0;
	volatile uint32_t	PULSE_CNT1;
	volatile uint32_t	PULSE_CNT2;
	volatile uint32_t	PULSE_CNT3;
	volatile uint32_t	PULSE_CNT4;
	volatile uint32_t	PULSE_CNT5;
	volatile uint32_t	WIDTH_CNT0;
	volatile uint32_t	WIDTH_CNT1;
	volatile uint32_t	WIDTH_CNT2;
	volatile uint32_t	WIDTH_CNT3;
	volatile uint32_t	WIDTH_CNT4;
	volatile uint32_t	WIDTH_CNT5;
	volatile uint32_t	DET0_PR;
	volatile uint32_t	DET1_PR;
	volatile uint32_t	DET2_PR;
	volatile uint32_t	DET3_PR;
	volatile uint32_t	DET4_PR;
	volatile uint32_t	DET5_PR;
};

/*---------------------------------------*/
/* WLA - wireless analog (bluetooth radio) */

struct JL_WLA_regs {
	volatile uint32_t	CON0;
	volatile uint32_t	CON1;
	volatile uint32_t	CON2;
	volatile uint32_t	CON3;
	volatile uint32_t	CON4;
	volatile uint32_t	CON5;
	volatile uint32_t	CON6;
	volatile uint32_t	CON7;
	volatile uint32_t	CON8;
	volatile uint32_t	CON9;
	volatile uint32_t	CON10;
	volatile uint32_t	CON11;
	volatile uint32_t	CON12;
	volatile uint32_t	CON13;
	volatile uint32_t	CON14;
	volatile uint32_t	CON15;
	volatile uint32_t	CON16;
	volatile uint32_t	CON17;
	volatile uint32_t	CON18;
	volatile uint32_t	CON19;
	volatile uint32_t	CON20;
	volatile uint32_t	CON21;
	uint32_t Reserved_58[4];
	volatile uint32_t	CON26;
	volatile uint32_t	CON27;
	volatile uint32_t	CON28;
	volatile uint32_t	CON29;
	volatile uint32_t	CON30;
	volatile uint32_t	CON31;
	volatile uint32_t	CON32;
	volatile uint32_t	CON33;
	volatile uint32_t	CON34;
	volatile uint32_t	CON35;
	volatile uint32_t	CON36;
	volatile uint32_t	CON37;
};

/*---------------------------------------*/
/* FMA - fm analog (fm radio) */

struct JL_FMA_regs {
	volatile uint32_t	CON0;
	volatile uint32_t	CON1;
	volatile uint32_t	CON2;
	volatile uint32_t	CON3;
	volatile uint32_t	CON4;
	volatile uint32_t	CON5;
	volatile uint32_t	CON6;
	volatile uint32_t	CON7;
	volatile uint32_t	CON8;
	volatile uint32_t	CON9;
};

/*===========================================================*/
/********* High-speed bus *********/
/* DSP - dsp stuff */

struct JL_DSP_regs {
	volatile uint32_t	CON;		/* Control reg */
};

/*---------------------------------------*/
/* NVIC - nested vectored interrupt controller (latch & priority) */

struct JL_NVIC_regs {
	volatile uint32_t	ILAT1;		/* Interrupt latch 1 */
	volatile uint32_t	ILAT1_SET;	/* Interrupt latch 1 (set) */
	volatile uint32_t	ILAT1_CLR;	/* Interrupt latch 1 (clear) */
	volatile uint32_t	ILAT0;		/* Interrupt latch 0 */
	volatile uint32_t	ILAT0_SET;	/* Interrupt latch 0 (set) */
	volatile uint32_t	ILAT0_CLR;	/* Interrupt latch 0 (clear) */
	volatile uint32_t	IPCON0;		/* Interrupt priority 0 */
	volatile uint32_t	IPCON1;		/* Interrupt priority 1 */
	volatile uint32_t	IPCON2;		/* Interrupt priority 2 */
	volatile uint32_t	IPCON3;		/* Interrupt priority 3 */
};

/*---------------------------------------*/
/* TICK - tick timer */

struct JL_TICK_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	CNT;		/* Counter */
	volatile uint32_t	PRD;		/* Period */
};

/*---------------------------------------*/
/* DEBUG - debug stuff */

struct JL_DEBUG_regs {
	volatile uint32_t	DSP_BF_CON;
	volatile uint32_t	WR_EN;
	volatile uint32_t	MSG;
	volatile uint32_t	MSG_CLR;
	volatile uint32_t	DSP_PC_LIMH;
	volatile uint32_t	DSP_PC_LIML;
	volatile uint32_t	DSP_EX_LIMH;
	volatile uint32_t	DSP_EX_LIML;
	volatile uint32_t	PRP_EX_LIMH;
	volatile uint32_t	PRP_EX_LIML;
	volatile uint32_t	PRP_MMU_MSG;
	volatile uint32_t	LSB_MMU_MSG_CH;
	volatile uint32_t	PRP_WR_LIMIT_MSG;
	volatile uint32_t	LSB_WR_LIMIT_CH;
};

/*---------------------------------------*/
/* SFC - serial flash controller */

struct JL_SFC_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BAUD;		/* Clock divider */
	volatile uint32_t	CODE;
	volatile uint32_t	BASE_ADR;	/* Flash base address */
};

/*---------------------------------------*/
/* ENC - "encryptor" */

struct JL_ENC_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	KEY;		/* Key */
	volatile uint32_t	ADR;
	volatile uint32_t	UNENC_ADRH;	/* SFC unenc address high boundary */
	volatile uint32_t	UNENC_ADRL;	/* SFC unenc address low boundary */
};

/*---------------------------------------*/
/* HSOTH - others (hs bus) */

struct JL_HSOTH_regs {
	volatile uint32_t	WL_CON0;
	volatile uint32_t	WL_CON1;
	volatile uint32_t	WL_CON2;
	volatile uint32_t	WL_CON3;
	volatile uint32_t	WL_LOFC_CON;
	volatile uint32_t	WL_LOFC_RES;
};

/*---------------------------------------*/
/* AES - advanced encryption standard */

struct JL_AES_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	DATIN;		/* Data input */
	volatile uint32_t	KEY;		/* Key */
	volatile uint32_t	ENCRES0;	/* Encrypted result 0 */
	volatile uint32_t	ENCRES1;	/* Encrypted result 1 */
	volatile uint32_t	ENCRES2;	/* Encrypted result 2 */
	volatile uint32_t	ENCRES3;	/* Encrypted result 3 */
	volatile uint32_t	DECRES0;	/* Decrypted result 0 */
	volatile uint32_t	DECRES1;	/* Decrypted result 1 */
	volatile uint32_t	DECRES2;	/* Decrypted result 2 */
	volatile uint32_t	DECRES3;	/* Decrypted result 3 */
};

/*---------------------------------------*/
/* FFT - fast fourier transform */

struct JL_FFT_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	ADRI;		/* Input buffer address */
	volatile uint32_t	ADRO;		/* Output buffer address */
	volatile uint32_t	ADRW;		/* Window data address */
};

/*---------------------------------------*/
/* EQ - equalizer */

struct JL_EQ_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	LEN;		/* Buffer length */
	volatile uint32_t	ADRI;		/* Input buffer address */
	volatile uint32_t	ADRO;		/* Output buffer address */
	volatile uint32_t	CADR;		/* Coefficient data address ? */
};

/*---------------------------------------*/
/* SRC - sample rate conversion */

struct JL_SRC_regs {
	volatile uint32_t	CON0;		/* Control reg 0 */
	volatile uint32_t	CON1;		/* Control reg 1 */
	volatile uint32_t	CON2;		/* Control reg 2 */
	volatile uint32_t	CON3;		/* Control reg 3 */
	volatile uint32_t	IDAT_ADR;	/* Input data address */
	volatile uint32_t	IDAT_LEN;	/* Input data length */
	volatile uint32_t	ODAT_ADR;	/* Output data address */
	volatile uint32_t	ODAT_LEN;	/* Output data length */
	volatile uint32_t	FLTB_ADR;	/* .?.fltb.?. address */
};

/*---------------------------------------*/
/* FMRX - fm receiver */

struct JL_FMRX_regs {
	volatile uint32_t	CON;		/* Control reg */
	volatile uint32_t	BASE;		/* Data buffer address */
	volatile uint32_t	ADC_CON;	/* ADC control */
	volatile uint32_t	HF_CON0;	/* HF control reg 0 */
	volatile uint32_t	HF_CON1;	/* HF control reg 1 */
	volatile uint32_t	HBT_RSSI;
	volatile uint32_t	ADCI_RSSI;
	volatile uint32_t	ADCQ_RSSI;
	volatile uint32_t	HF_CRAM;
	volatile uint32_t	HF_DRAM;
	volatile uint32_t	LF_CON;		/* LF control reg 0 */
	volatile uint32_t	LF_RES;
};

/*---------------------------------------*/
/* MCPWM - motor control pwm */

struct JL_MCPWM_regs {
	volatile uint32_t	TMR0_CON;	/* Timer 0 control reg */
	volatile uint32_t	TMR0_CNT;	/* Timer 0 counter */
	volatile uint32_t	TMR0_PR;	/* Timer 0 period */
	volatile uint32_t	TMR1_CON;	/* Timer 1 control reg */
	volatile uint32_t	TMR1_CNT;	/* Timer 1 counter */
	volatile uint32_t	TMR1_PR;	/* Timer 1 period */
	volatile uint32_t	TMR2_CON;	/* Timer 2 control reg */
	volatile uint32_t	TMR2_CNT;	/* Timer 2 counter */
	volatile uint32_t	TMR2_PR;	/* Timer 2 period */
	volatile uint32_t	TMR3_CON;	/* Timer 3 control reg */
	volatile uint32_t	TMR3_CNT;	/* Timer 3 counter */
	volatile uint32_t	TMR3_PR;	/* Timer 3 period */
	volatile uint32_t	TMR4_CON;	/* Timer 4 control reg */
	volatile uint32_t	TMR4_CNT;	/* Timer 4 counter */
	volatile uint32_t	TMR4_PR;	/* Timer 4 period */
	volatile uint32_t	TMR5_CON;	/* Timer 5 control reg */
	volatile uint32_t	TMR5_CNT;	/* Timer 5 counter */
	volatile uint32_t	TMR5_PR;	/* Timer 5 period */
	volatile uint32_t	FPIN_CON;	/* .?.fpin.?. control reg */
	volatile uint32_t	CH0_CON0;	/* Channel 0 control reg 0 */
	volatile uint32_t	CH0_CON1;	/* Channel 0 control reg 1 */
	volatile uint32_t	CH0_CMP;	/* Channel 0 compare */
	volatile uint32_t	CH1_CON0;	/* Channel 1 control reg 0 */
	volatile uint32_t	CH1_CON1;	/* Channel 1 control reg 1 */
	volatile uint32_t	CH1_CMP;	/* Channel 1 compare */
	volatile uint32_t	CH2_CON0;	/* Channel 2 control reg 0 */
	volatile uint32_t	CH2_CON1;	/* Channel 2 control reg 1 */
	volatile uint32_t	CH2_CMP;	/* Channel 2 compare */
	volatile uint32_t	CH3_CON0;	/* Channel 3 control reg 0 */
	volatile uint32_t	CH3_CON1;	/* Channel 3 control reg 1 */
	volatile uint32_t	CH3_CMP;	/* Channel 3 compare */
	volatile uint32_t	CH4_CON0;	/* Channel 4 control reg 0 */
	volatile uint32_t	CH4_CON1;	/* Channel 4 control reg 1 */
	volatile uint32_t	CH4_CMP;	/* Channel 4 compare */
	volatile uint32_t	CH5_CON0;	/* Channel 5 control reg 0 */
	volatile uint32_t	CH5_CON1;	/* Channel 5 control reg 1 */
	volatile uint32_t	CH5_CMP;	/* Channel 5 compare */
};

/*============================================================================*/

/********* Low-speed bus **********/
#define JL_SYSTEM	((struct JL_SYSTEM_regs *)0x60000)
#define JL_WAKEUP	((struct JL_WAKEUP_regs *)0x60008)
#define JL_IOMAP	((struct JL_IOMAP_regs  *)0x60018)
#define JL_POWER	((struct JL_POWER_regs  *)0x60040)
#define JL_CLOCK	((struct JL_CLOCK_regs  *)0x60044)

#define JL_PORTA	((struct JL_PORT_regs   *)0x60100)
#define JL_PORTB	((struct JL_PORT_regs   *)0x60120)
#define JL_PORTC	((struct JL_PORT_regs   *)0x60140)
#define JL_PORTD	((struct JL_PORT_regs   *)0x60160)

#define JL_TIMER0	((struct JL_TIMER_regs  *)0x60200)
#define JL_TIMER1	((struct JL_TIMER_regs  *)0x60210)
#define JL_TIMER2	((struct JL_TIMER_regs  *)0x60220)
#define JL_TIMER3	((struct JL_TIMER_regs  *)0x60230)

#define JL_UART0	((struct JL_UARTx_regs  *)0x60300)
#define JL_UART1	((struct JL_UARTx_regs  *)0x60324)
#define JL_UART2	((struct JL_UART2_regs  *)0x60348)

#define JL_SPI0		((struct JL_SPI_regs    *)0x60400)
#define JL_SPI1		((struct JL_SPI_regs    *)0x60414)
#define JL_SPI2		((struct JL_SPI_regs    *)0x60428)

#define JL_PAP		((struct JL_PAP_regs    *)0x60500)

#define JL_SD0		((struct JL_SD_regs     *)0x60600)
#define JL_SD1		((struct JL_SD_regs     *)0x60614)

#define JL_IIC		((struct JL_IIC_regs    *)0x60700)
#define JL_LCDC		((struct JL_LCDC_regs   *)0x60800)

#define JL_PWM4		((struct JL_PWM4_regs   *)0x60900)
#define JL_IRTC		((struct JL_IRTC_regs   *)0x60904)
#define JL_IRFLT	((struct JL_IRFLT_regs  *)0x60908)	/* IR */

#define JL_AUDIO	((struct JL_AUDIO_regs  *)0x60A00)
#define JL_ALNK		((struct JL_ALNK_regs   *)0x60B00)	/* IIS */
#define JL_NFC		((struct JL_NFC_regs    *)0x60C00)
#define JL_USB		((struct JL_USB_regs    *)0x60D00)
#define JL_CRC		((struct JL_CRC_regs    *)0x60E00)
#define JL_RAND		((struct JL_RAND_regs   *)0x60F00)	/* rand64 */
#define JL_ADC		((struct JL_ADC_regs    *)0x61000)
#define JL_PLCNT	((struct JL_PLCNT_regs  *)0x61100)	/* PLL_COUNTER */
#define JL_PD		((struct JL_PD_regs     *)0x61200)	/* POWER_DOWN */
#define JL_CTM		((struct JL_CTM_regs    *)0x61300)
#define JL_SPDET	((struct JL_SPDET_regs  *)0x61400)	/* SP */
#define JL_WLA		((struct JL_WLA_regs    *)0x61C00)
#define JL_FMA		((struct JL_FMA_regs    *)0x61D00)

/********* High-speed bus *********/
#define JL_DSP		((struct JL_DSP_regs    *)0x70000)
#define JL_NVIC		((struct JL_NVIC_regs   *)0x70004)
#define JL_TICK		((struct JL_TICK_regs   *)0x70040)

#define JL_DEBUG	((struct JL_DEBUG_regs  *)0x70100)
#define JL_SFC		((struct JL_SFC_regs    *)0x70200)
#define JL_ENC		((struct JL_ENC_regs    *)0x70300)
#define JL_HSOTH	((struct JL_HSOTH_regs  *)0x70400)
#define JL_AES		((struct JL_AES_regs    *)0x70500)
#define JL_FFT		((struct JL_FFT_regs    *)0x70600)
#define JL_EQ		((struct JL_EQ_regs     *)0x70700)
#define JL_SRC		((struct JL_SRC_regs    *)0x70800)
#define JL_FMRX		((struct JL_FMRX_regs   *)0x70900)
#define JL_MCPWM	((struct JL_MCPWM_regs  *)0x70A00)	/* PWM */

/*============================================================================*/

#endif

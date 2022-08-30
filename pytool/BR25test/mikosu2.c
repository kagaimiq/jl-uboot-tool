#include <stdint.h>
#include <xprintf.h>
#include <jl_regs.h>
#include <maskrom_stuff.h>


void uputc(int c) {
	reg32_write(UART0_BASE+UARTx_BUF, c);
	while (!reg32_rsmask(UART0_BASE+UARTx_CON0_TPND));
	reg32_wsmask(UART0_BASE+UARTx_CON0_CLRTPND, 1);
}


void hexdump(void *ptr, int len) {
	for (int i = 0; i < len; i += 16) {
		xprintf("%08x: ", ptr+i);

		for (int j = 0; j < 16; j++) {
			if (i+j < len)
				xprintf("%02X ", *(uint8_t*)(ptr+i+j));
			else
				xputs("-- ");
		}

		xputs(" |");

		for (int j = 0; j < 16; j++) {
			uint8_t c = ' ';
			if (i+j < len) {
				c = *(uint8_t*)(ptr+i+j);
				if (c < 0x20 || c >= 0x7f) c = '.';
			}
			xputc(c);
		}

		xputs("|\n");
	}
}


void sflash_init(void) {
	reg32_wsmask(PORTD_BASE+PORTx_DIRn(0), 0); // PD0 out  -> SCK
	reg32_wsmask(PORTD_BASE+PORTx_DIRn(1), 0); // PD1 out  -> MOSI
	reg32_wsmask(PORTD_BASE+PORTx_DIRn(2), 1); // PD2 in   -> MISO
	reg32_wsmask(PORTD_BASE+PORTx_DIRn(3), 0); // PD3 out  -> CS
	reg32_wsmask(PORTD_BASE+PORTx_DIRn(4), 0); // PD4 out  -> ?? HOLD? Power?!

	reg32_wsmask(PORTD_BASE+PORTx_OUTn(3), 1); // PD3 high
	reg32_wsmask(PORTD_BASE+PORTx_OUTn(4), 1); // PD4 high
}

void sflash_sel(char sel) {
	reg32_wsmask(PORTD_BASE+PORTx_OUTn(3), !sel); // CS
}

uint8_t sflash_spixfer(uint8_t val) {
	uint8_t rval = 0;

	for (uint8_t mask = 0x80; mask; mask >>= 1) {
		reg32_wsmask(PORTD_BASE+PORTx_OUTn(1), !!(mask & val)); // PD1 set
		reg32_wsmask(PORTD_BASE+PORTx_OUTn(0), 1); // PD0 high
		if (reg32_rsmask(PORTD_BASE+PORTx_INn(2))) rval |= mask; // PD2 get
		reg32_wsmask(PORTD_BASE+PORTx_OUTn(0), 0); // PD0 low
	}

	return rval;
}


struct usb_msc_cbw {
	uint32_t sign;		// 0x55534243 "USBC"
	uint32_t tag;
	uint32_t xfer_len;
	uint8_t flags;
	uint8_t lun;
	uint8_t cdb_len;
	uint8_t cdb[16];
};

struct JieLi_LoaderArgs {
	int (*msd_send)(void *ptr, int len);		// send request data
	int (*msd_recv)(void *ptr, int len);		// receive request data
	int (**msd_hook)(struct usb_msc_cbw *cbw);	// SCSI request hook
	uint32_t arg;		// Argument
	uint32_t wtw_10;	// set to zero?!
};

struct JieLi_LoaderArgs *largs;



int KonaHook(struct usb_msc_cbw *cbw) {
	xprintf(
		"\e[1;45;33m---- SCSI Request ----\e[0m\n"
		"Tag: %08x, Flags: %02x, LUN: %d\n"
		"Xfer length: %u\n"
		"CDB: [%d] { ",
		cbw->tag, cbw->flags, cbw->lun, cbw->xfer_len, cbw->cdb_len
	);

	for (int i = 0; i < cbw->cdb_len; i++)
		xprintf("%02x ", cbw->cdb[i]);

	xputs("}\n\n");

	//============================================

	switch (cbw->cdb[0]) {
	case 0x55:
		largs->msd_send("kagami", 6);
		return 666;
	}

	return 0;
}

void JieLi(uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3) {
	#if 0 // Remember that voodoo magic! ...basically like everything else??!?! ( i mean... )
	reg32_write(UART2_BASE+UARTx_CON0, 1); // 8n1, en
	reg32_write(UART2_BASE+UARTx_BAUD, 48000000/4/115200);
	reg32_wsmask(IOMAP_BASE+IOMAP_CON1, 14, 3, 3); // UART2 to PC4/PC5
	reg32_wsmask(IOMAP_BASE+IOMAP_CON3, 10, 1, 0); // UART2 ... IO SEL -> IOMUX ?
	reg32_wsmask(IOMAP_BASE+IOMAP_CON3, 11, 1, 1); // UART2 I/O enable
	reg32_wsmask(PORTC_BASE+PORTx_DIRn(4), 0); // PC4 out
	reg32_wsmask(PORTC_BASE+PORTx_DIRn(5), 1); // PC5 in
	#endif

	// init UART0 on PB5
	reg32_write(UART0_BASE+UARTx_CON0, 1); // 8n1, en
	reg32_write(UART0_BASE+UARTx_BAUD, 48000000/4/115200);
	reg32_wsmask(IOMAP_BASE+IOMAP_CON0, 3, 3, 2); // UART0 to PB5
	reg32_wsmask(IOMAP_BASE+IOMAP_CON3, 2, 1, 0); // UART0 ... IO SEL -> IOMUX ?
	reg32_wsmask(IOMAP_BASE+IOMAP_CON3, 3, 1, 1); // UART0 I/O enable
	reg32_wsmask(PORTB_BASE+PORTx_DIRn(5), 0); // PB5 out

	xdev_out(uputc);
	xputs("\n\e[1;37;41;5m==== JieLi AC6965A! "__DATE__" "__TIME__" ====\e[0m\n");
	xprintf("r0: <%08x>  r1: <%08x>  r2: <%08x>  r3: <%08x>\n", r0,r1,r2,r3);

	largs = (void *)r0;
	xprintf(">>msd_send = %08x\n", largs->msd_send);
	xprintf(">>msd_recv = %08x\n", largs->msd_recv);
	xprintf(">>msd_hook = %08x\n", largs->msd_hook);
	xprintf(">>arg      = %08x\n", largs->arg);
	xprintf(">>wtw_10   = %08x\n", largs->wtw_10);

	/*==================================================================*/

	*largs->msd_hook = KonaHook;

	sflash_init();

	/*sflash_sel(1);
		sflash_spixfer(0x03);
		sflash_spixfer(0x00);
		sflash_spixfer(0x00);
		sflash_spixfer(0x00);
		for (int i = 0; i < 0x1000; i++)
			*(uint8_t *)(0x1f000 + i) = sflash_spixfer(0xff);
	sflash_sel(0);*/

	//for (int i = 0; i < 0x100; i += 4) {
	//	xprintf("%02x: %08x\n", i, reg32_read(AUDIO_BASE+i));
	//}

	reg32_write(SPI0_BASE+SPIx_CON, 0x20);
	reg32_write(SPI0_BASE+SPIx_BAUD, 255);
	reg32_wsmask(SPI0_BASE+SPIx_CON_SPIE, 1);

	memset((void *)0x1f000, 0xfe, 0x1000);

	sflash_sel(1);

		reg32_wsmask(SPI0_BASE+SPIx_CON_DIR, 0);

		reg32_write(SPI0_BASE+SPIx_BUF, 0x9f);
		while (!reg32_rsmask(SPI0_BASE+SPIx_CON_PND));
		reg32_wsmask(SPI0_BASE+SPIx_CON_PCLR, 1);

		reg32_write(SPI0_BASE+SPIx_BUF, 0x00);
		while (!reg32_rsmask(SPI0_BASE+SPIx_CON_PND));
		reg32_wsmask(SPI0_BASE+SPIx_CON_PCLR, 1);

		reg32_write(SPI0_BASE+SPIx_BUF, 0x00);
		while (!reg32_rsmask(SPI0_BASE+SPIx_CON_PND));
		reg32_wsmask(SPI0_BASE+SPIx_CON_PCLR, 1);

		reg32_write(SPI0_BASE+SPIx_BUF, 0x00);
		while (!reg32_rsmask(SPI0_BASE+SPIx_CON_PND));
		reg32_wsmask(SPI0_BASE+SPIx_CON_PCLR, 1);

		reg32_wsmask(SPI0_BASE+SPIx_CON_DIR, 1);
		reg32_write(SPI0_BASE+SPIx_ADR, 0x20000);
		reg32_write(SPI0_BASE+SPIx_CNT, 0x1000);
		while (!reg32_rsmask(SPI0_BASE+SPIx_CON_PND));
		reg32_wsmask(SPI0_BASE+SPIx_CON_PCLR, 1);

	sflash_sel(0);

	hexdump((void *)0x20000, 0x100);
}

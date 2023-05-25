#include <stdint.h>
#include "jl_br17_regs.h"

/*============================================================================*/
/* some exports */

void loader_main(void *arg);
int printf(const char *fmt, ...);
void loader_jumpto(uint32_t addr);
int loader_cmd_fb08(void *cbw, void *buffp);

/*============================================================================*/

void putchar(int c) {
	while (!(JL_UART2->CON & (1<<15)));
	JL_UART2->BUF = c;
}

int puts(char *str) {
	while (*str) {
		putchar(*str++);
	}

	return 0;
}



void puthex(uint32_t val, int n) {
	for (int i = n - 1; i >= 0; i--) {
		char c = (val >> (i * 4)) & 0xf;

		if (c < 10)
			c += '0';
		else
			c += 'A' - 10;

		putchar(c);
	}
}

void puthex32(uint32_t val) {
	putchar('<');
	puthex(val, 8);
	putchar('>');
}

void puthex16(uint16_t val) {
	puthex(val, 4);
}

void puthex8(uint8_t val) {
	puthex(val, 2);
}



void hexdump(void *ptr, int len) {
	for (int off = 0; off < len; off += 16) {
		uint8_t *bptr = ptr + off;

		int n = len - off;
		if (n > 16) n = 16;

		puthex32((uint32_t)bptr);
		putchar(':');

		for (int i = 0; i < 16; i++) {
			if (i == 8) putchar(' ');

			if (i < n) {
				putchar(' ');
				puthex8(bptr[i]);
			} else {
				puts("   ");
			}
		}

		puts(" | ");

		for (int i = 0; i < 16; i++) {
			uint8_t c = ' ';

			if (i < n) {
				c = bptr[i];
				if (c < 0x20 || c >= 0x7f) c = '.';
			}

			putchar(c);
		}

		putchar('\n');
	}

	//putchar('\n');
}

/*============================================================================*/

int put_reljump16(uint16_t *dst, void *jumpdst) {
	int32_t rel = (uint32_t)jumpdst - (uint32_t)(dst + 1);

	/* 11-bit relative limit */
	if (rel < -0x800 || rel > 0x7fe)
		return 0;

	rel >>= 1;

	/* 00001Aaaaaaaaaaa  -  goto s`Aaaaaaaaaaa0` */
	dst[0] = 0x0800 | (rel & 0x7ff);

	return 1;
}

int put_reljump32(uint16_t *dst, void *jumpdst) {
	int32_t rel = (uint32_t)jumpdst - (uint32_t)(dst + 2);

	/* 24-bit relative limit */
	if (rel < -0x1000000 || rel > 0xfffffe)
		return 0;

	rel >>= 1;

	/* 11111010AaaaaaaaaaaaaaaaaaaaBbbb  -  goto s`BbbbAaaaaaaaaaaaaaaaaaaa0` */
	dst[0] = 0xFA00 |
		 ((rel & 0x0ff000) >> 12);
	dst[1] = ((rel & 0xf00000) >> 20) |
		 ((rel & 0x000fff) << 4);

	return 2;
}

/* decrementing patch pool pointer just below the loader area */
uint16_t *patchpool = (void *)loader_main;

void patchstub(uint32_t addr, void *func) {
	uint16_t *dst = (uint16_t *)addr;

	puts("patching stub at "); puthex32(addr);
	puts(" with "); puthex32((uint32_t)func);
	puts(": ");

	if (put_reljump16(dst, func)) {
		puthex16(dst[0]);
		puts(" patched with ins16!\n");
		return;
	}

	patchpool -= 2;
	puthex32((uint32_t)patchpool); putchar('=');

	put_reljump32(patchpool, func);
	put_reljump16(dst, patchpool);

	puthex16(patchpool[0]);
	puthex16(patchpool[1]);
	putchar('/');
	puthex16(dst[0]);
	puts(" patched with ins32!\n");
}

/*============================================================================*/

void initfunc1(void) {
	uint32_t tmp;
	asm volatile ("%0 = rets" : "=r"(tmp));

	puts("\e[1;32m!!! Loader works!\e[0m\n");

	printf("dead beef rets=%x\n", tmp);

	puts("\e[1;32m!!! ----Exiting preinit!\e[0m\n");
}


struct usb_msc_cbw {
	uint32_t sign; /* USBC */
	uint32_t tag;
	uint32_t data_len;
	uint8_t flags;
	uint8_t lun;
	uint8_t cb_len;
	uint8_t cb[16];
};

struct jl_loader_args {
	void (*msd_send)(void *, int);
	void (*msd_recv)(void *, int);
	int (**msd_hook)(struct usb_msc_cbw *, void *);
	uint32_t arg;
	uint32_t wtw;
};


void (*msd_send)(void *, int);
void (*msd_recv)(void *, int);

int (*loader_scsihook)(struct usb_msc_cbw *, void *);

#if 0
int our_scsi_hook(struct usb_msc_cbw *cbw, void *buffp) {
	printf("%02x/%02x\n", cbw->cb[0], cbw->cb[1]);

	

	return 0;
}

int scsi_hook(struct usb_msc_cbw *cbw, void *buffp) {
	/* handle ours first */
	if (our_scsi_hook(cbw, buffp))
		return 1;

	/* then handle loader's */
	if (loader_scsihook(cbw, buffp))
		return 1;

	/* then let the ROM handle it */
	return 0;
}
#endif


void patch_main(struct jl_loader_args *args) {
	/* Init UART at PA3 */
	reg_wsmask(JL_CLOCK->CLK_CON1, 10, 0x3, 0x1);	/* uart_clk = pll_48m */

	JL_UART2->CON = 1;
	JL_UART2->BAUD = (48000000 / 4 / 115200) - 1;

	reg_wsmask(JL_IOMAP->CON1, 14, 0x3, 'A'-'A');
	reg_wsmask(JL_IOMAP->CON3, 8, 0x7, 0x0);
	JL_IOMAP->CON3 |= (1<<11);

	JL_PORTA->DIR &= ~(1<<3);	/* PA3 out */

	/* Print out something */
	puts("\n\n\e[1;33m======= HELLO! br17loader patcher =======\e[0m\n");
	puts("arg is: "); puthex16(args->arg); putchar('\n');

	/*
	 @ 25B4: jump to putchar stub from printchar func
	 ----
	 @ 25B8: ? stub (?unused)
	 @ 25BA: ? stub (?unused)
	 @ 25BC: ? stub (?unused)
	 @ 25BE: ? stub (?unused)
	 @ 25C0: ? stub
	 @ 25C2: ? stub (?unused)
	 @ 25C4: UART init stub?
	 @ 25C6: puts stub (simply loops through the whole string and then returns 0)
	 @ 25D0: putchar stub
	 @ 25D2: ? stub (returns 0) -- called by the timer isr
	 @ 25D6: ? stub (?unused)
	 @ 25D8: puthex32 stub
	 @ 25DA: ? stub (?unused)
	 @ 25DC: ? stub (?unused)
	 @ 25DE: ? stub (?unused)
	 @ 25E0: puthex8 stub
	 @ 25E2: hexdump stub
	*/

	/* Patch the stubs (in backwards) */
	patchstub(0x25E2, hexdump);
	patchstub(0x25E0, puthex8);
	patchstub(0x25D8, puthex32);
	patchstub(0x25D0, putchar);
	patchstub(0x25C6, puts);
	patchstub(0x25C4, initfunc1);

	puts("\e[1;31m!!!>>>>>>>>>>>>>>> Entering the loader!\e[0m\n");

	/* Call the loader code itself */
	loader_main(args);
	//((void (*)(void *))0x2000)(arg);

	puts("\n\e[1;31m!!!<<<<<<<<<<<<<<< Loader exited!\e[0m\n");

	msd_send = args->msd_send;
	msd_recv = args->msd_recv;

	/* replace the SCSI hook with ours to intercept it! */
	loader_scsihook = *args->msd_hook;
	//*args->msd_hook = scsi_hook;

	puts("\e[1;35m!!! Returning to ROM\e[0m\n");
}

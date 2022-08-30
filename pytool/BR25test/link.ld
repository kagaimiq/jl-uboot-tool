MEMORY {
	RAM (rwx): ORIGIN = 0x12000, LENGTH = 0x10000-0x2000
}


/* MaskROM stubs */
local_irq_enable						= 0x117D40;
local_irq_disable						= 0x117D44;
p33_buf								= 0x117D48;
p33_xor_1byte							= 0x117D4C;
p33_and_1byte							= 0x117D50;
p33_or_1byte							= 0x117D54;
p33_tx_1byte							= 0x117D58;
p33_rx_1byte							= 0x117D5C;
P33_CON_SET							= 0x117D60;
memmem								= 0x117D64;
memcpy								= 0x117D68;
memmove								= 0x117D6C;
memcmp								= 0x117D70;
memset								= 0x117D74;
strcmp								= 0x117D78;
strcpy								= 0x117D7C;
strlen								= 0x117D80;
strncmp								= 0x117D84;
strstr								= 0x117D88;


ENTRY(_start);

SECTIONS {
	.text : {
		*(.text.startup)
		*(.text)
		*(.text.*)
	} >RAM

	.rodata : {
		*(.rodata)
		*(.rodata.*)
	} >RAM

	.data : {
		*(.data)
		*(.data.*)
		*(.sdata)
		*(.sdata.*)
	} >RAM

	.bss : {
		_sbss = .;
		*(.sbss)
		*(.sbss.*)
		*(.scommon)
		*(.bss)
		*(.bss.*)
		*(COMMON)
		_ebss = .;
	} >RAM

	/*.stack : {
		. = . + 4096;
		. = ALIGN(8);
		__usp = .;
	} >RAM*/

	end = .;
};

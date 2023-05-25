MEMORY {
	/* Loader address: 0x2000 */
	/* Upper margin: 0x8000 (from there on it's used by loader) */
	/* Guard area: 0x2000 (where the loader sits in between) */
	RAM (rwx): ORIGIN = 0x2000+0x2000, LENGTH = 0x8000-0x2000-0x2000
}

ENTRY(_start);

/*=====================================================*/
/* Loader stuff */

loader_main			= 0x2000;
printf				= 0x2278;

/*=====================================================*/

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
	} >RAM

	.bss : {
		_sbss = .;
		*(.bss)
		*(.bss.*)
		*(COMMON)
		_ebss = .;
	} >RAM

	end = .;
};

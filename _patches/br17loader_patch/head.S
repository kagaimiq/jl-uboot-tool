	.section .text.startup
	.global _start

_start:
	[--sp] = {r6-r4}

	r4 = _sbss
	r5 = _ebss
	r6 = 0
1:	cmp r4, r5
	if (nzcv >= 0) goto 2f
	[r4 ++= 4] = r6
	goto 1b
2:

	{r6-r4} = [sp++]

	goto patch_main

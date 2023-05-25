# Loader patching stuff

This is the loader patches which have a custom code blob bolted on top of the loader,
which then gets executed _first_ and it then patches the loader's code with jumps to our code.

Currently this is done to patch the log output stubs with actual code that prints stuff to UART.

To use this within jluboottool, specify this argument: `--custom-loaders=_patches/patchedloaders.yaml`.

Using on the stock isd_download/etc currently is not possible due to the fact that the patch blob
is located *after* the loader code, thus the jump address needs to be different from the load address.
Probably this can be mitigated by placing a long jump instruction to the beginning, and then restore/emulate
these first 4 bytes of the loader code prior to entering the actual loader code.

Not that this is really useful for something, this is rather a proof of concept.

Anyway...

---------------------------------------------

The UART pin is PA3 with baudrate of 115200 baud.

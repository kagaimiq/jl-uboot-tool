TARGET=JLDFUTool
OBJS=test.o scsi_io.o jlusbisd.o jl_stuff.o

CFLAGS=-Werror
LDFLAGS=

#when compiling for Windows, uncomment this
#LDFLAGS+=-s -static
#OBJS+=mizudec2.o
# also if you cross-compiling, set the CROSS_COMPILE to e.g. 'i686-w64-mingw32-'

CC=$(CROSS_COMPILE)gcc
WINDRES=$(CROSS_COMPILE)windres

all: $(TARGET) 
#payload.bin

clean:
	rm -f $(OBJS)
	rm -f $(TARGET)
	rm -f $(TARGET).exe
	rm -f payload.bin
	#$(MAKE) -C jieli-payload clean

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o "$@"

payload.bin:
	$(MAKE) -C jieli-payload

%.o: %.res
	$(WINDRES) "$<" "$@"

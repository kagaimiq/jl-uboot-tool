TARGET ?= JLDFUTool
OBJS = scsi_io.o jlusbisd.o jl_stuff.o

CFLAGS = -Werror
LDFLAGS =

#when compiling for Windows, uncomment this
#LDFLAGS += -s -static
#OBJS += mizudec2.o
# also if you cross-compiling, set the CROSS_COMPILE to e.g. 'i686-w64-mingw32-'

ifeq ($(TARGET), jlUsbIsdTest)
OBJS += test.o
endif

ifeq ($(TARGET), JLDFUTool)
OBJS += jldfutool.o
endif

ifeq ($(TARGET), JLFlasher)
OBJS += jlflasher.o
endif

ifeq ($(TARGET), JLRunner)
OBJS += jlrunner.o
endif


CC      = $(CROSS_COMPILE)gcc
WINDRES = $(CROSS_COMPILE)windres

all: $(TARGET) 

clean:
	rm -f $(OBJS)
	rm -f $(TARGET)
	rm -f $(TARGET).exe
	rm -f payload.bin

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o "$@"

%.o: %.res
	$(WINDRES) "$<" "$@"

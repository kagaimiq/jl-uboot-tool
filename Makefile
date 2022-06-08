TARGET ?= JLDFUTool
OBJS = scsi_io.o jlusbisd.o jl_stuff.o

CFLAGS = -Werror
LDFLAGS =

ifeq ($(TARGET), jlUsbIsdTest)
OBJS += test.o
endif

ifeq ($(TARGET), JLDFUTool)
OBJS += jldfutool.o
endif

ifeq ($(TARGET), JLRunner)
OBJS += jlrunner.o
endif

CC      = $(CROSS_COMPILE)gcc

all: $(TARGET) 

clean:
	rm -f $(OBJS)
	rm -f $(TARGET)
	rm -f $(TARGET).exe
	rm -f payload.bin

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o "$@"

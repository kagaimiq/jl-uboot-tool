TARGET = JLDFUTool

OBJS = scsi_io.o jlusbisd.o jl_stuff.o test.o

CFLAGS = -Werror
LDFLAGS =

CC = $(CROSS_COMPILE)gcc

all: $(TARGET) 

clean:
	rm -f $(OBJS)
	rm -f $(TARGET)
	rm -f $(TARGET).exe

$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o "$@"

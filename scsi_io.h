#ifndef _SCSI_IO_H
#define _SCSI_IO_H

#include <stdint.h>

/* right now you can only open single device! */
int scsi_io_open(char *path);
void scsi_io_close(void);
int scsi_io_transfer(const uint8_t *cdb, int cdblen, uint8_t *data, int datalen, char dir);

#endif
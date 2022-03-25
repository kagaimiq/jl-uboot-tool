#include <stdio.h>
#include <string.h>

#ifdef WIN32 /* Windows */
	#include <stddef.h>
	#include <windows.h>
#else /* Linux */
	#include <errno.h>
	#include <unistd.h>
	#include <fcntl.h>
	#include <sys/ioctl.h>
	#include <scsi/sg.h>
#endif

#include "scsi_io.h"

#ifdef WIN32 /* Windows */
	/* we need to define these structures because MinGW doesn't have WinDDK stuff! */
	struct scsiPassThroughDirect {
		uint16_t len;
		uint8_t status;
		uint8_t pathId;
		uint8_t targetId;
		uint8_t lun;
		uint8_t cdbLen;
		uint8_t senseLen;
		uint8_t dir;
		uint32_t dataLen;
		uint32_t timeout;
		void *dataPtr;
		uint32_t senseOffset;
		uint8_t cdb[16];
	};

	struct scsiPassThroughDirectWithBuff {
		struct scsiPassThroughDirect sptd;
		uint8_t senseBuff[24]; /* <-pointed by sptd.senseOffset & sptd.senseLen */
	};

	HANDLE scsi_io_dev = INVALID_HANDLE_VALUE;
	
	static char *strerror_win(DWORD errcode) {
		static char str[256];
		
		FormatMessage(
			FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS | FORMAT_MESSAGE_MAX_WIDTH_MASK,
			NULL,
			errcode,
			MAKELANGID(LANG_ENGLISH, SUBLANG_DEFAULT),
			str,
			sizeof(str),
			NULL);
		
		return str;
	}
#else /* Linux */
	int scsi_io_dev = -1;
#endif

int scsi_io_open(char *path) {
#ifdef WIN32 /* Windows */
	scsi_io_dev = CreateFile(
		path,                               /* lpFileName            */
		GENERIC_READ | GENERIC_WRITE,       /* dwDesiredAcccess      */
		FILE_SHARE_READ | FILE_SHARE_WRITE, /* dwShareMode           */
		NULL,                               /* lpSecurityAttributes  */
		OPEN_EXISTING,                      /* dwCreationDisposition */
		0,                                  /* dwFlagsAndAttributes  */
		NULL                                /* hTemplateFile         */
	);
	
	if (scsi_io_dev == INVALID_HANDLE_VALUE) {
		printf("failed to open scsi device `%s` - %d (%s)\n",
			path, GetLastError(), strerror_win(GetLastError()));
		
		return -1;
	}
#else /* Linux */
	scsi_io_dev = open(path, O_RDWR);
	if (scsi_io_dev < 0) {
		printf("failed to open scsi device `%s` - %d (%s)\n",
			path, errno, strerror(errno));
		
		return -1;
	}
#endif

	return 0;
}

void scsi_io_close(void) {
#ifdef WIN32 /* Windows */
	CloseHandle(scsi_io_dev);
#else /* Linux */
	close(scsi_io_dev);
#endif
}

int scsi_io_transfer(const uint8_t *cdb, int cdblen, uint8_t *data, int datalen, char dir) {
	if (!cdb || cdblen < 1 || cdblen > 16) return 1; /* sanity check for cdb / cdblen */
	if (!data || datalen < 0) datalen = 0; /* sanity check for datalen */
	
#ifdef WIN32 /* Windows */
	struct scsiPassThroughDirectWithBuff sptdwb = {
		.sptd = {
			.len = sizeof(struct scsiPassThroughDirect),
			.pathId = 0,
			.targetId = 1,
			.lun = 0,
			.cdbLen = cdblen,
			.dir = dir?0:1,
			.dataLen = datalen,
			.dataPtr = data,
			.timeout = 1,
		},
	};
	memcpy(sptdwb.sptd.cdb, cdb, cdblen);
	sptdwb.sptd.senseLen = sizeof(sptdwb.senseBuff);
	sptdwb.sptd.senseOffset = offsetof(struct scsiPassThroughDirectWithBuff, senseBuff);
	
	DWORD br;
	if (!DeviceIoControl(scsi_io_dev, 0x4d014, &sptdwb, sizeof(sptdwb), &sptdwb, sizeof(sptdwb), &br, NULL)) {
		printf("failed to do IOCTL_SCSI_PASS_THROUGH_DIRECT ioctl - %d (%s)\n",
			GetLastError(), strerror_win(GetLastError()));
		
		return -1;
	}
	
	if (sptdwb.sptd.status != 0) {
		printf("command failed - %d\n", sptdwb.sptd.status);
		
		return -1;
	}
	
	return sptdwb.sptd.dataLen; /* TODO residue whatever thing */
#else /* Linux */
	uint8_t senseBuff[32]; /* not actually required, but why not */
	
	sg_io_hdr_t ioHdr = {
		.interface_id    = 'S',
		.sbp             = senseBuff,
		.mx_sb_len       = sizeof(senseBuff),
		.cmd_len         = cdblen,
		.cmdp            = (uint8_t*)cdb,
		.dxfer_direction = dir?SG_DXFER_TO_DEV:SG_DXFER_FROM_DEV,
		.dxfer_len       = datalen,
		.dxferp          = data,
		.timeout         = 1000,
	};
	
	if (ioctl(scsi_io_dev, SG_IO, &ioHdr) < 0) {
		printf("failed to do SG_IO ioctl - %d (%s)\n",
			errno, strerror(errno));
		
		return -1;
	}
	
	if ((ioHdr.info & SG_INFO_OK_MASK) != SG_INFO_OK) {
		printf("io is not ok, so we need to investigate that !!!\n");
		printf(" info          = %08x\n", ioHdr.info);
		printf(" status        = %08x\n", ioHdr.status);
		printf(" masked_status = %08x\n", ioHdr.masked_status);
		printf(" msg_status    = %08x\n", ioHdr.msg_status);
		printf(" host_status   = %08x\n", ioHdr.host_status);
		printf(" driver_status = %08x\n", ioHdr.driver_status);
		/* if (ioHdr.msg_status || ioHdr.host_status || ioHdr.driver_status) { */
		return -1;
	}
	
	return ioHdr.dxfer_len - ioHdr.resid;
#endif
}
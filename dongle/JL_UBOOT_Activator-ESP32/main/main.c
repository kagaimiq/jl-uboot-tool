#include <stdio.h>
#include <unistd.h>
#include <driver/gpio.h>

#define JLDFU_LED		18   // Status LED
#define JLDFU_CLK		22   // D+ / Green
#define JLDFU_DAT		23   // D- / White
#define JLDFU_USBSW		19   // Enable PC side USB
#define JLDFU_POWER		0   // Power switch


void SendSignals(void) {
	/* disable PC side USB */
	gpio_set_level(JLDFU_USBSW, 0);
	usleep(10000); // settle

	/* config pins to drive -- pullup open drain i/o */ {
		gpio_config_t cfg = {
			.pin_bit_mask = (1<<JLDFU_CLK)|(1<<JLDFU_DAT),
			.mode = GPIO_MODE_INPUT_OUTPUT, //_OD,
			//.pull_up_en = 1,
		};
		gpio_config(&cfg);
	}

	puts("Sending....");

	for (;;) {
		for (uint16_t m = 0x8000; m; m >>= 1) {
			gpio_set_level(JLDFU_DAT, !!(0x16ef & m));
			gpio_set_level(JLDFU_CLK, 0);
			usleep(20);
			gpio_set_level(JLDFU_CLK, 1);
			usleep(20);
		}

		// what's up

		//gpio_set_level(JLDFU_DAT, 1);
		int lvl = gpio_get_level(JLDFU_DAT);
		if (!lvl) break;
	}

	puts("!!! YEAH! Connect JIELI Real quick!!");

	/* config pins to not drive -- release usb */ {
		gpio_config_t cfg = {
			.pin_bit_mask = (1<<JLDFU_CLK)|(1<<JLDFU_DAT),
			.mode = GPIO_MODE_DISABLE,
		};
		gpio_config(&cfg);
	}

	/* enable PC side USB */
	gpio_set_level(JLDFU_USBSW, 1);
	usleep(10000); // settle
}



void app_main(void) {
	/* config pins */ {
		gpio_config_t cfg = {
			.pin_bit_mask = (1<<JLDFU_USBSW)|(1<<JLDFU_POWER)|(1<<JLDFU_LED),
			.mode = GPIO_MODE_OUTPUT,
		};
		gpio_config(&cfg);
	}

	puts("============ Power cycle =============");

	gpio_set_level(JLDFU_POWER, 0); // Turn off JieLi
	usleep(100000);
	gpio_set_level(JLDFU_POWER, 1); // Turn on JieLi

	puts("======= Send activation signal =======");

	SendSignals();
}

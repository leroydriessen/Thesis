#define F_CPU 8000000UL

// PORTA
#define MCPCS	1 << PA0
#define MCPCLK	1 << PA1
#define MCPSDI	1 << PA2
#define CURADC	1 << PA3
#define RPICLK	1 << PA4
#define RPIMISO	1 << PA5
#define RPIMOSI	1 << PA6
#define RPICS	1 << PA7

// PORTB
#define LEDPWR	1 << PB0
#define LEDERR	1 << PB1
#define LEDDBG	1 << PB2
#define RESET	1 << PB3

// PID constants
#define PIDKP	0.04
#define PIDKI	0.005
#define PIDKD	0

// Settings
#define SMPLEN	3

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <stdbool.h>

volatile unsigned char msg[2] = {0, 0};
volatile unsigned char command[5];
volatile int counter;
volatile bool newCommand;

ISR(PCINT0_vect) {
	if (PINA & RPICS) {		 			//CS rising edge
		newCommand = true;
		USICR &= ~(1 << USIOIE); 		//disable SPI byte received interrupt
	} else {							//CS falling edge
		counter = 0;
		USISR = 0;						//reset counter and overflow flag
		USICR |= 1 << USIOIE;	 		//enable SPI byte received interrupt
	}
}

ISR(USI_OVF_vect) {						//SPI byte received or sent
	command[counter++] = USIDR;
	USISR |= 1 << USIOIF;				//reset SPI functionality
}

int main(void) {
	unsigned char adcbuffer[2];
	unsigned char i;
	unsigned char pos;

	unsigned short adcvalue[SMPLEN];
	unsigned short temp;

	float reference = 0;
	float measurement;
	float p_error;
	float i_error = 0;

	int setpoint = 2048;

	DDRA |= RPIMISO | MCPCS | MCPCLK | MCPSDI;
	DDRB |= LEDPWR | LEDERR | LEDDBG;
	PORTA |= MCPCS;

	PORTB |= LEDPWR;
	_delay_ms(50);
	PORTB = 0;
	_delay_ms(50);
	PORTB |= LEDPWR;

	ADMUX |= 1 << MUX1 | 1 << MUX0;
	ADCSRA |= 1 << ADEN | 1 << ADPS2 | 1 << ADPS1 | 1 << ADPS0;
	DIDR0 |= 1 << ADC3D;

	PCMSK0 |= 1 << PCINT7;
	GIMSK |= 1 << PCIE0;

	USICR |= 1 << USIWM0 | 1 << USICS1;

	sei();

	for (;;) {
		if (newCommand) {
			switch (command[0] & 0xF0) {
				case 0x00:
					reference = ((command[0] & 0x0F) << 8) + command[1];
					if (reference < 0) {
						reference = 0;
					} else if (reference > 1023) {
						reference = 1023;
					}
					reference -= 512;
					reference /= 1024.0;
					reference *= 10;
					break;
				default:
					PORTB |= LEDERR;
					break;
			}
			newCommand = false;
			i_error = 0;
		}

		for (i = 0; i < SMPLEN; i++) {
			ADCSRA |= 1 << ADSC;
			while (ADCSRA & 1 << ADSC);
			adcbuffer[1] = ADCL;
			adcbuffer[0] = ADCH;
			adcvalue[i] = adcbuffer[0] << 8 | adcbuffer[1];
			pos = i;
			temp = adcvalue[i];
			while (pos > 0 && adcvalue[pos] < adcvalue[pos-1]) {
				adcvalue[pos] = adcvalue[pos-1];
				adcvalue[--pos] = temp;
			}
		}

		measurement = (float) (adcvalue[SMPLEN/2] / 1024.0 * 10 - 5);

		p_error = reference - measurement;
		i_error += p_error;
		if (i_error > 1) {
			i_error = 1;
		} else if (i_error < -1) {
			i_error = -1;
		}

		int change = (int) (4096 * (PIDKP * p_error + PIDKI * i_error) * (1 - PIDKD));

		/*
		if (change == 1 || change = -1) {
			change = 0;
		}
		*/

		if (change) {
			setpoint += change;
			if (setpoint < 0) {
				setpoint = 0;
			} else if (setpoint > 4095) {
				setpoint = 4095;
			}

			PORTA &= ~(MCPCS | MCPCLK | MCPSDI);
			PORTA |= MCPCLK;
			PORTA |= MCPSDI;
			for (int i = 0; i < 3; i++) {
				PORTA &= ~MCPCLK;
				PORTA |= MCPCLK;
			}
			for (int i = 11; i >=0; i--) {
				PORTA &= ~MCPCLK;
				if (setpoint & 1 << i) {
					PORTA |= MCPSDI;
				} else {
					PORTA &= ~MCPSDI;
				}
				PORTA |= MCPCLK;
			}
			PORTA |= MCPCS;
		}
		_delay_ms(100);
	}
	return 0;
}

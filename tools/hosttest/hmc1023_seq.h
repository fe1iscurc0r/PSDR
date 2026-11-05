/*
 * HMC1023 register-write sequence builder - host-testable, no hardware.
 *
 * Source: HMC1023LP5E v01.0113, "RC Calibration" procedure (p.25):
 *   1. clock doubler on if CALCK < 40 MHz        Reg 01h[5] = 1
 *   2. write the applied clock period in ps      Reg 05h[14:0]
 *   3. enable the RC calibration circuit         Reg 01h[1] = 1
 *   4. write 152d = 0x96                         Reg 06h[8:0] = 152
 *   5. start the calibration cycle               Reg 04h = 0
 *   6. poll Reg 08h[4] until 0 (done); fine code Reg 08h[3:0], auto-copied to Reg 03h[3:0]
 *
 * The SPI transport is deliberately not here: the 32-clock frame layout
 * (3-bit Chip_ID + address + data) has to be checked against Figure 38 on the
 * datasheet, which the text extraction does not reproduce.  Wiring this to a
 * board is a later step; this file only proves the sequence.
 */
#ifndef HMC1023_SEQ_H
#define HMC1023_SEQ_H

#include <stdint.h>
#include <stddef.h>

typedef struct
{
  uint8_t  addr;
  uint16_t value;
  uint8_t  is_read;   /* 1 = read-back step (poll/read), value unused */
} hmc1023_write_t;

/*
 * Reg 05h[14:0] holds the period in ps and only has 15 bits, so it cannot hold
 * the period of a 20-40 MHz clock (50000-25000 ps).  The datasheet's clock
 * doubler is what makes it fit: when CALCK < 40 MHz the part runs on 2*CALCK,
 * so the value written is the period of the doubled clock.  This helper does
 * that arithmetic; pass its result as period_ps.
 */
uint32_t hmc1023_period_ps_for(uint32_t calck_hz);

/* Fills out[] and returns the number of entries (0 if out is too small). */
size_t hmc1023_calibration_sequence(uint32_t calck_hz,
                                    uint32_t period_ps,
                                    hmc1023_write_t *out,
                                    size_t max);

#endif /* HMC1023_SEQ_H */

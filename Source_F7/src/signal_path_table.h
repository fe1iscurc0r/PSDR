/*
 * Pin levels for the seven signalPaths states, kept in one table so that a
 * state can no longer inherit the previous case's body by falling through.
 *
 * valid = 0 means "write nothing".  That is the shipped behaviour of the three
 * states that never had a body (4, 5, 6) and is kept deliberately until the
 * hardware side is measured.
 *
 * Rows 0, 2 and 3 copy the values of the shipped switch
 * (PSDR_F7 @ ab2c8fd, Source/src/main.c:823-922).
 * Row 1 (recieve_with_filter) used to be an empty case that fell into row 2's
 * transmit branch; it now uses the receive path.  FILTER_S0/S1 is still the
 * same (1,0) bypass address because the CB3Q/CBTLV truth table has not been
 * measured yet -- see the TODO there.
 */
#ifndef SIGNAL_PATH_TABLE_H
#define SIGNAL_PATH_TABLE_H

/*
 * States 5/6 (the two VNA paths) are deliberately left at "write nothing".
 * The relay combination cannot be derived from the files we hold: the DPDT
 * datasheet only exists as a mirror (truth table known, physical pin-to-port
 * mapping not), and the 74CB3Q/CBTLV mux truth table has not been measured.
 * See docs/PSDR-switch-maps.md for the two measurements that unblock them.
 * Do not fill these rows with guesses.
 */

#include <stdint.h>

typedef struct
{
  uint8_t valid;
  uint8_t amp_power;      /* 1 = off */
  uint8_t five_volt_en;   /* 1 = on  */
  uint8_t amp_sw_a;
  uint8_t amp_sw_b;
  uint8_t imp_br_a;
  uint8_t imp_br_b;
  uint8_t tx_rf_a;
  uint8_t tx_rf_b;
  uint8_t dac_mux;        /* 0 = speaker/earphone, 1 = RF */
  uint8_t trx_switch;     /* 0 = RX, 1 = TX */
  uint8_t filter_s0;
  uint8_t filter_s1;
} signal_path_state_t;

/* Indexed by enum signalPaths (0..6). */
static const signal_path_state_t SIGNAL_PATH_TABLE[7] =
{
  /* 0 recieve_no_filter             */ {1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0},
  /* 1 recieve_with_filter (was TX)  */ {1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0}, /* TODO: filter address when the mux truth table is measured */
  /* 2 transmit_no_amp_no_filter     */ {1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0},
  /* 3 transmit_with_amp_no_filter   */ {1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0},
  /* 4 tramsmit_with_amp_with_filter */ {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  /* 5 vna_reflected (see header note) */ {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  /* 6 vna_through   (see header note) */ {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
};

#endif /* SIGNAL_PATH_TABLE_H */

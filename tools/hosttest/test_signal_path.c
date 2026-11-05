/* Host-side test for the signalPath table (no firmware toolchain needed).
 *
 * It compiles Source_F7/src/signal_path_table.h on the host and checks the
 * matrix that docs/PSDR-signalpath-pinmap.md lists.  The point is to pin the
 * values: state 1 must not carry the transmit branch any more, and states 4-6
 * must stay "write nothing" until the hardware side is measured.
 *
 * Build/run:  gcc -std=c99 -Wall -Wextra -o /tmp/tsp test_signal_path.c && /tmp/tsp
 */
#include <stdio.h>
#include <stdlib.h>
#include "../../Source_F7/src/signal_path_table.h"

static int failures = 0;

static void expect(int state, const char *field, int got, int want)
{
  if (got != want)
  {
    printf("FAIL state %d %-12s got %d want %d\n", state, field, got, want);
    failures++;
  }
}

int main(void)
{
  /* state 0: receive, bypass, amp off, filter bypass */
  expect(0, "amp_power",   SIGNAL_PATH_TABLE[0].amp_power,   1);
  expect(0, "five_volt",   SIGNAL_PATH_TABLE[0].five_volt_en,0);
  expect(0, "amp_a",       SIGNAL_PATH_TABLE[0].amp_sw_a,    0);
  expect(0, "amp_b",       SIGNAL_PATH_TABLE[0].amp_sw_b,    1);
  expect(0, "dac_mux",     SIGNAL_PATH_TABLE[0].dac_mux,     0);
  expect(0, "trx",         SIGNAL_PATH_TABLE[0].trx_switch,  0);
  expect(0, "filter_s0",   SIGNAL_PATH_TABLE[0].filter_s0,   1);
  expect(0, "filter_s1",   SIGNAL_PATH_TABLE[0].filter_s1,   0);

  /* state 1: receive path, NOT the transmit branch that the fall-through used */
  expect(1, "valid",       SIGNAL_PATH_TABLE[1].valid,       1);
  expect(1, "dac_mux",     SIGNAL_PATH_TABLE[1].dac_mux,     0);
  expect(1, "trx",         SIGNAL_PATH_TABLE[1].trx_switch,  0);
  expect(1, "amp_power",   SIGNAL_PATH_TABLE[1].amp_power,   1);
  expect(1, "five_volt",   SIGNAL_PATH_TABLE[1].five_volt_en,0);

  /* state 2: transmit, no amp */
  expect(2, "dac_mux",     SIGNAL_PATH_TABLE[2].dac_mux,     1);
  expect(2, "trx",         SIGNAL_PATH_TABLE[2].trx_switch,  1);
  expect(2, "amp_power",   SIGNAL_PATH_TABLE[2].amp_power,   1);

  /* state 3: transmit with amp - amp powered, relay still bypass (see #16) */
  expect(3, "amp_power",   SIGNAL_PATH_TABLE[3].amp_power,   0);
  expect(3, "five_volt",   SIGNAL_PATH_TABLE[3].five_volt_en,1);
  expect(3, "amp_a",       SIGNAL_PATH_TABLE[3].amp_sw_a,    0);
  expect(3, "amp_b",       SIGNAL_PATH_TABLE[3].amp_sw_b,    1);

  /* states 4-6: no writes at all */
  for (int s = 4; s <= 6; s++)
  {
    expect(s, "valid", SIGNAL_PATH_TABLE[s].valid, 0);
  }

  /* every valid row writes FILTER_S0/S1 = (1,0) today */
  for (int s = 0; s <= 3; s++)
  {
    expect(s, "filter_s0", SIGNAL_PATH_TABLE[s].filter_s0, 1);
    expect(s, "filter_s1", SIGNAL_PATH_TABLE[s].filter_s1, 0);
  }

  if (failures)
  {
    printf("RESULT: FAIL (%d)\n", failures);
    return 1;
  }
  printf("RESULT: PASS (7 states x 12 lines)\n");
  return 0;
}

#include <stdio.h>
#include "hmc1023_seq.h"

static int failures = 0;

static void expect(size_t i, const hmc1023_write_t *w, int addr, int value, int rd)
{
  if (w->addr != addr || (!rd && w->value != value) || w->is_read != rd)
  {
    printf("FAIL step %u: got addr=%02X value=%04X read=%d, want addr=%02X value=%04X read=%d\n",
           (unsigned)i, w->addr, w->value, w->is_read, addr, value, rd);
    failures++;
  }
}

int main(void)
{
  hmc1023_write_t w[8];
  size_t n;

  /* CALCK = 26 MHz -> doubler must be enabled first */
  n = hmc1023_calibration_sequence(26000000u, hmc1023_period_ps_for(26000000u), w, 8);
  if (n != 6) { printf("FAIL count %u != 6\n", (unsigned)n); return 1; }
  expect(0, &w[0], 0x01, 0x0020, 0);
  expect(1, &w[1], 0x05, 19231, 0);   /* 1e9 / 52 MHz, doubled clock */
  expect(2, &w[2], 0x01, 0x0002, 0);
  expect(3, &w[3], 0x06, 0x0096, 0);
  expect(4, &w[4], 0x04, 0x0000, 0);
  expect(5, &w[5], 0x08, 0x0000, 1);

  /* CALCK = 60 MHz -> no doubler, five writes + read */
  n = hmc1023_calibration_sequence(60000000u, hmc1023_period_ps_for(60000000u), w, 8);
  if (n != 5) { printf("FAIL count %u != 5\n", (unsigned)n); return 1; }
  expect(0, &w[0], 0x05, 16667, 0);   /* 1e9 / 60 MHz */
  expect(1, &w[1], 0x01, 0x0002, 0);
  expect(2, &w[2], 0x06, 0x0096, 0);
  expect(3, &w[3], 0x04, 0x0000, 0);
  expect(4, &w[4], 0x08, 0x0000, 1);

  if (failures) { printf("RESULT: FAIL (%d)\n", failures); return 1; }
  printf("RESULT: PASS (calibration sequence, both CALCK ranges)\n");
  return 0;
}

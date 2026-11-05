#include "hmc1023_seq.h"

uint32_t hmc1023_period_ps_for(uint32_t calck_hz)
{
  uint32_t f = calck_hz;
  if (!f)
    return 0;
  if (f < 40000000u)
    f *= 2u;                 /* clock doubler is on for CALCK < 40 MHz */
  return (uint32_t)((1000000000000ULL + (unsigned long long)(f / 2u)) / (unsigned long long)f); /* ps, rounded */
}

size_t hmc1023_calibration_sequence(uint32_t calck_hz,
                                    uint32_t period_ps,
                                    hmc1023_write_t *out,
                                    size_t max)
{
  size_t n = 0;

  if (!out)
    return 0;

  /* The datasheet needs at most 6 entries; refuse silently rather than overflow. */
  if (max < 6)
    return 0;

  if (calck_hz < 40000000u)
  {
    out[n].addr = 0x01; out[n].value = 0x0020; out[n].is_read = 0; n++; /* bit 5: doubler */
  }

  out[n].addr = 0x05; out[n].value = (uint16_t)(period_ps & 0x7FFFu); out[n].is_read = 0; n++; /* period, 15 bits */
  out[n].addr = 0x01; out[n].value = 0x0002; out[n].is_read = 0; n++;                          /* bit 1: RC cal enable */
  out[n].addr = 0x06; out[n].value = 0x0096; out[n].is_read = 0; n++;                          /* 152d */
  out[n].addr = 0x04; out[n].value = 0x0000; out[n].is_read = 0; n++;                          /* start calibrate */
  out[n].addr = 0x08; out[n].value = 0x0000; out[n].is_read = 1; n++;                          /* poll bit 4, read [3:0] */

  return n;
}

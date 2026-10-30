/* Minimal UART adapter replacing upstream src/uart.c for HAL-only builds.
 *
 * Upstream uart.c is SPL-era code: it calls USART_ITConfig / USART_Cmd /
 * hal_setupUart1..3, none of which exist in a HAL-only project, so it cannot
 * link. Upstream's .cproject therefore excluded it -- but TinyGPS.c:172 still
 * calls uart_getChar(), which left the symbol undefined. This file supplies
 * only what TinyGPS actually needs.
 *
 * Hardware inconsistency in upstream (left as-is, deliberately):
 * main.c's configUartPeripheral() initialises USART6 (GPIO AF8) for the GPS,
 * but hal.h:57 defines hal_gpsUart as USART1. Callers pass hal_gpsUart; the
 * handle behind both is the USART6 one, so the uart argument is ignored here.
 */

#include "hal.h"

/* Defined (tentatively) in main.h; initialised by configUartPeripheral(). */
extern UART_HandleTypeDef UartHandle;

int
uart_getChar (uint8_t uart, char *c)
{
  (void) uart;

  if (c == NULL)
    return -1;

  /* Timeout 0 makes HAL_UART_Receive a non-blocking poll: HAL_OK only when a
     byte is already waiting. Depends on HAL_GetTick() advancing, i.e. on
     SysTick_Handler calling HAL_IncTick(). */
  if (HAL_UART_Receive (&UartHandle, (uint8_t *) c, 1, 0) == HAL_OK)
    return 0;

  return -1;
}

int
uart_putChar (uint8_t uart, char c)
{
  (void) uart;

  if (HAL_UART_Transmit (&UartHandle, (uint8_t *) &c, 1, 10) == HAL_OK)
    return 0;

  return -1;
}

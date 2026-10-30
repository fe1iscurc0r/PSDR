# PSDR 最小构建修复集 (基于 master @ 45acd0f59)
# 全部为"让项目能在现代 Linux + arm-none-eabi-gcc 上构建"的必要修复
# 未修改任何射频逻辑

--- a/Source/src/misc.c
+++ b/Source/src/misc.c
@@
 #include "misc.h"
+#include "stm32f4xx_hal_conf.h"   /* 提供 assert_param 宏; 缺失时它被当作隐式函数声明 -> 链接失败 */

--- a/Source/src/hal.c
+++ b/Source/src/hal.c
@@ (新增 hal_checkTimeout 实现)
+/* TinyGPS 依赖此函数, 但上游从未实现 */
+uint32_t hal_checkTimeout(uint32_t startTime_ms, uint32_t interval_ms)
+{
+    uint32_t now = HAL_GetTick();
+    return (uint32_t)(now - startTime_ms) >= interval_ms;
+}

--- a/Source/src/uart.c
+++ b/Source/src/uart.c
@@
-USART_HandleTypeDef usart;
+UART_HandleTypeDef usart;        /* 原为 USART_HandleTypeDef, 与 HAL_USART_* API 不兼容 */
+                                 /* 且本文件被 .cproject Debug 配置排除 -> uart_getChar 断链 */

--- a/Source/.cproject
+++ b/Source/.cproject
@@
 Debug 配置需解除以下排除, 否则 adc.c/dac.c 引用 *_ex.c 中的 __weak 回调 -> 断链:
   system/src/stm32f4-hal/stm32f4xx_hal_adc_ex.c
   system/src/stm32f4-hal/stm32f4xx_hal_dac_ex.c
 Debug 配置需解除以下排除, 否则 CMSIS DSP 的 arm_bitreversal_32 断链:
   DSP_Lib/Source/TransformFunctions/arm_cfft_radix2_*.c  (保留其它)

链接脚本必须三个一起传, 否则 ORIGIN(RAM) 不解析, _estack = 0xFFFFFFFF (静默错误):
  -Tldscripts/mem.ld -Tldscripts/libs.ld -Tldscripts/sections.ld

--- 新增: Source/Makefile.linux
+++ Source/Makefile.linux
  (见同目录 Makefile.linux, 完整可复现构建)

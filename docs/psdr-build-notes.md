# PSDR 固件构建说明 · Linux 交叉编译复现

> 工单任务 B 的产物。基准：`master @ 45acd0f`，工作分支
> `workorders/2026-10-30-psdr-takeover-linux-build-kicad`。
> 未触碰任何射频逻辑。

## 1. 构建步骤

编译在真正的 Linux 文件系统上做，**不要在 `/mnt/c/` 下编译**（WSL2 跨 9p/drvfs
访问极慢，142 个编译单元会卡到看不出在动）。

```bash
sudo apt update && sudo apt install -y gcc-arm-none-eabi make git python3
git clone https://github.com/fe1iscurc0r/PSDR.git ~/PSDR     # Linux 版 git，天然 LF
cd ~/PSDR
git checkout workorders/2026-10-30-psdr-takeover-linux-build-kicad
stat -f -c %T .                                              # 须为 ext2fs/ext4
cd Source && make -f Makefile.linux -j
make -f Makefile.linux anchors                               # 锦点自证
```

`make ... anchors` 会打印 `_estack`，并调用
`docs/psdr-handoff/anchor_check.py` 与仓内 `Source/Debug/PSDR.hex`（作者 2016 产物）
比对初始 SP 与 Reset 向量，PASS/FAIL 直接反映在退出码上。

## 2. 修掉的构建缺陷

工单列了 4 个，实测下来是 5 个——多出的第 5 个不影响链接，但让 TinyGPS 的时间
逻辑整体失效，属于"能链接但功能错"那一类，所以一并修了。

| # | 文件 | 缺陷 | 修复 |
|---|---|---|---|
| 1 | `src/misc.c` | 只 include `misc.h`，`assert_param` 被当隐式函数声明 → 链接失败 | 补 `#include "stm32f4xx_hal_conf.h"` |
| 2 | `src/hal.c` | `hal_checkTimeout()` 在 `hal.h:175` 声明但全仓无实现，`TinyGPS.c:166/184` 依赖 | 在 `.c` 里给外部定义（见 §2.1） |
| 3 | `src/uart.c` | SPL 时代代码，`USART_ITConfig`/`USART_Cmd`/`hal_setupUart1..3` 共 26 处在 HAL-only 工程里不存在 | 排除本文件，新增 `src/uart_hal_stub.c` |
| 4 | `src/main.c` | 全仓无 `HAL_IncTick()` 调用点 → `HAL_GetTick()` 恒为 0 | 在已有的 `SysTick_Handler` 里加 `HAL_IncTick();`（见 §2.2） |
| 5 | `src/hal.c` | `halMilliseconds` 只有声明，唯一的自增语句在注释块里 → `hal_getCurrentTime_ms()` 恒为 0，而 TinyGPS 的时间戳全部取自它 | `hal_getCurrentTime_ms()` 改读 `HAL_GetTick()`，删掉已死的 static |

### 2.1 缺陷 2：返回类型跟头文件，不跟 PATCH-NOTES

`hal.h:174` 的声明是 `extern inline bool hal_checkTimeout(uint32_t, uint32_t)`，
而 `docs/psdr-handoff/PATCH-NOTES.md` 给的实现返回 `uint32_t`。按头文件为准
（调用方 `TinyGPS.c:184` 也是当 `bool` 用的）。

`extern inline` 在 C99 语义下要求恰好一个外部定义，所以实现必须落在 `.c` 里；
只在头文件里写 inline 函数体是链接不上的。

### 2.2 缺陷 4：改 main.c 那个，不要碰 stm32f4xx_it.c

`main.c:345` 有真正生效的 `SysTick_Handler`（`millis++` / `timer_tick()` /
`Tick()` / `timingDelay--`），`stm32f4xx_it.c:145` 那个是 `__attribute__((weak))`
空壳。在 `stm32f4xx_it.c` 里新建会直接 `multiple definition of SysTick_Handler`。

### 2.3 缺陷 5 与 4 是配套的

缺陷 2 的实现用 `HAL_GetTick()`，缺陷 5 让 `hal_getCurrentTime_ms()` 也读
`HAL_GetTick()`。如果只按 PATCH-NOTES 改 `hal_checkTimeout` 而不修
`hal_getCurrentTime_ms()`，两处会用上不同的时钟：时间戳恒 0、超时判据用真实
tick，结果是上电 1100 ms 后 GPS 被永久判定为"已超时/无信号"。所以两者必须
收敛到同一个 ms 时钟。

顺带确认：`hal_delay_ms()` 走的是 `timingDelay`，而 `timingDelay` 确实由
`main.c` 的 SysTick 递减，所以延时一直是好的——坏的只有 `halMilliseconds`。

### 2.4 硬件不一致（按工单要求保持原样）

`main.c:717 configUartPeripheral()` 配的是 **USART6**（`GPIO_AF8`，收发 GPS），
但 `include/hal.h:57` 把 `hal_gpsUart` 定义成 **USART1**。`uart_hal_stub.c` 按
实际的 USART6 句柄走，忽略调用方传入的 uart 号，并在文件头注释写清了这个不一致。
没有改 `hal.h` 的宏。

## 3. 构建配置要点

1. **三个链接脚本必须一起传**：`-Tldscripts/mem.ld -Tldscripts/libs.ld -Tldscripts/sections.ld`。
   只传 `sections.ld` 时 `ORIGIN(RAM)` 不解析，`_estack` 变成 `0xFFFFFFFF`——
   **不报错，但固件必挂**。`mem.ld` 才是 MEMORY 定义源，`libs.ld` 是空壳 `GROUP()`。
2. **`-fcommon` 必须加**：GCC 10+ 默认 `-fno-common`，而 `include/main.h:84`
   写的是 `UART_HandleTypeDef UartHandle;`（tentative definition，没有 extern），
   每个 include 它的 TU 都会出一份。这不是掩盖问题，是回到原 GCC 4.7 语义。
3. **`.cproject` 的排除表自相矛盾**：Debug 配置排除了 `stm32f4xx_hal_adc_ex.c` /
   `_dac_ex.c` / `_rtc_ex.c`，但保留的 `adc.c`/`dac.c`/`rtc.c` 引用了它们里的
   `__weak` 回调 → 断链。本 Makefile 不再排除这三个。
4. **`.S` 要单独编译规则**：`arm_bitreversal_32` 只定义在
   `DSP_Lib/Source/TransformFunctions/arm_bitreversal2.S`（`.c` 里只有 `extern`
   引用，见 `arm_cfft_f32.c:51`）。只 wildcard `*.c` 会 `undefined reference to arm_bitreversal_32`。
5. **`--gc-sections` 用 `GC` 开关控制**，默认 `GC=1`，因为上游 `.cproject` 的
   `linker.gcsections` 是 `value="true"`。`make -f Makefile.linux GC=0` 可复现
   交接材料里那个未回收的尺寸。

## 4. 关于交接材料里两个对不上的 size 数字

`docs/PSDR-TAKEOVER-WORKORDER-2026-10-30.md` 写 `text 984908 / data 3004 / bss 18220`，
`docs/PSDR-TAKEOVER-EVALUATION-2026-10-30.md` §3.2 写 `text 1077236 / data 2988 / bss 18216`。
同工具链、同脚本，text 差 92,328 字节。

最可能的解释是 `--gc-sections` 的开与关：92 KB 这个量级正好是 CMSIS DSP_Lib 里
未被引用的函数（本 Makefile 会编入 `FastMathFunctions`/`BasicMathFunctions`/
`ComplexMathFunctions` 全部文件，`-ffunction-sections` 已经把每个函数切成独立
section）。`GC=1` 与 `GC=0` 各跑一次即可证实，两种结果都记在
`docs/WO-psdr-takeover.md` 的对照表里，不挑一个报。

需要说明：`-Wl,--gc-sections`、`.S` 规则、以及 UART 的取舍都不改变向量表头两个
字，因此**锦点验收与这处口径争议无关**。

## 5. 与上游 Debug 配置尚未对齐的选项（记录，未改）

上游 `.cproject` Debug 还带 `-fsigned-char -ffreestanding -g3 -O0`。
`docs/psdr-handoff/Makefile.linux` 只给了 `-O0`（默认即 -O0）与函数/数据分段，
没有 `-fsigned-char`。`-fsigned-char` 会影响 codegen，所以这里的 size 与
Eclipse 直接产出的产物**不是逐字节可比**；锦点可比。
为保持与交接脚本的最小差异（便于把任何残差归因到唯一变量），本轮没有补这个
选项，也没有补 `-g3`。

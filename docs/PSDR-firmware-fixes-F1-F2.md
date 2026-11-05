# 固件局部修复 F-1 / F-2（fork-only，不上游）

日期：2026-11-04。范围：只做 `docs/PSDR-revB-local-plan.md` 里的 **F-1（I2C 有界等待）** 与
**F-2（`signalPath` 表化 + 修 fall-through）**。**没有 PR、没有推上游分支**；只进本 fork 的 `next`。

## 1. F-1：Si5338 就绪等待改为有界

* 位置：`Source_F7/src/main.c`（`handleI2C` 初始化之后）。
* 原代码（`PSDR_F7 @ ab2c8fd`）：

```c
HAL_StatusTypeDef result = HAL_ERROR;
while(result!= HAL_OK)
  result = HAL_I2C_IsDeviceReady(&handleI2C, (0x70 << 1), 100, 100);
```

* 改为**最多 2 s（20 次 × 100 ms）**，失败时 `trace_puts("Si5338 not ready - continuing without synthesizer");` 后继续。
* 行为变化：Si5338 不应答时不再卡死，显示初始化能继续；后续 `i2cSetup()/setFreq()` 若写失败只影响频率。

## 2. F-2：`signalPath()` 表化 + 状态 1 不再落进发射分支

* 新增 `Source_F7/src/signal_path_table.h`：`signal_path_state_t` + `SIGNAL_PATH_TABLE[7]`（12 根线 × 7 态）。
* `Source_F7/src/main.c` 的 `signalPath()` 改为读表写 12 根线；**非法值打印后返回**；`valid=0` 的态（4/5/6）保持"什么都不写"。
* 关键修复：**`recieve_with_filter`（状态 1）过去是空 case，落进 `transmit_no_amp_no_filter`**，
  会写 `DAC_MUX=1`、`TRX_SWITCH=1`（发射路径）。现在它写**接收路径**（`TRX=0`、`DAC=0`）。
* **未改**：`FILTER_S0/S1` 仍全为 `(1,0)`（CB3Q 真值表未实测，表里留 `TODO`）；状态 3 仍"加电但继电器旁路"（#16 的观察，未动）。

## 3. 验证

* **主机测试**（新增 `tools/hosttest/test_signal_path.c`，不需要固件工具链）：

```
$ gcc -std=c99 -Wall -Wextra -o /tmp/tsp test_signal_path.c && /tmp/tsp
RESULT: PASS (7 states x 12 lines)
```

* **目标构建**（WSL + `arm-none-eabi-gcc` 13.2.1，`make -f Makefile.linux -j4`）：
  **0 errors**；`text 113916 / data 18488 / bss 18260`（改动前 114068 / 18488 / 18260，代码小了 152 B）。
* **没有上板**，只到"能编过、矩阵测试过"。

## 4. 与上游镜像的关系（必须记住）

`Source_F7/` 原先是 `upstream/PSDR_F7` 的**逐字节镜像**（`main.c` blob `5af0e159`）；
本次改动后**不再镜像**：

| 文件 | 现在 blob | 说明 |
|---|---|---|
| `Source_F7/src/main.c` | `e8238ed3` | 含 F-1 + F-2 |
| `Source_F7/src/signal_path_table.h` | `e33844c2` | 新增 |
| `tools/hosttest/test_signal_path.c` | `50b7a2c0` | 新增，主机测试 |

⇒ 以后引用"与上游零差异"时，必须限定到 **本次改动之前的提交**（`4bd4164` 及其以前）；
`docs/PSDR-firmware-survey.md` 与 `README.fork.md` 的措辞已同步改写。

## 5. 回滚

```bash
git checkout 4bd4164 -- Source_F7/src/main.c
rm Source_F7/src/signal_path_table.h tools/hosttest/test_signal_path.c
```

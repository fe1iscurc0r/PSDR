# 工单 · PSDR (PortableSDR) 接手 · 天选7 完整克隆 + Linux 构建复现 + Eagle→KiCad 转换

> **执行方**：Qoder ｜ **目标仓库**：`https://github.com/fe1iscurc0r/PSDR`（fork of `MichaelRColton/PSDR`）
> **工作分支**：`workorders/2026-10-30-psdr-takeover-linux-build-kicad`（**已开好**，基于 master `45acd0f`）
> **素材**（已随本单放在**本仓库同一分支**下，无需跨仓取用）：
> - `docs/PSDR-TAKEOVER-EVALUATION-2026-10-30.md` — 接手评估报告（所有技术细节的出处）
> - `docs/psdr-handoff/Makefile.linux` — **已验证可编译**的 Linux 构建脚本，直接用
> - `docs/psdr-handoff/PATCH-NOTES.md` — 4 处缺陷的最小修复说明

---

## 一句话目标

在**天选7** 上完整克隆 PSDR 仓库，把固件改成能在现代 Linux + arm-none-eabi-gcc 上构建出来，把 Eagle 格式硬件文件转成 KiCad 供嘉立创EDA 导入，并产出规范化命名的 Gerber 包。

## 背景：上游是什么

**PortableSDR**：一台独立的 HF 全频段软件定义收发信机（0–35 MHz），Michael Colton 的 Kickstarter 产物。

| 项 | 值 |
|---|---|
| MCU | STM32F429（master 分支）/ STM32F756（2.6.1 硬件，在 `PSDR_F7` 分支）|
| 射频链 | 双 AD9834 DDS + 二次采样正调检波 + AD8302（兼 VNA / 天线分析仪）|
| 模式 | AM / USB / LSB / CW，收发均可 |
| 许可 | **MIT**（2026-09-11 落地，末句含硬件设计文件）。**授权已闭环，勿再纠缠许可。** |

⚠️ **别和 OpenHPSDR 的 PowerSDR 搞混** —— 完全无关的两个项目。

### 上游现状（已实测，勿重复调研）

- 仓库 182 MB（.git）/ master 工作树 72 MB / 749 文件 / 7 个分支
- **上游最后一次改固件是 2016-05-01，代码已 10 年未动**
- 未决 issue：#6 #8 #9 #13 #14 **#16（核心：前置放大器）**
- **上游从未有过可链接的构建**（用 2016 原始源码 + 原始 Eclipse 配置编译同样失败）

> **"能编译"是本单新增的价值，不是复现。**

---

## 任务 A · 天选7 完整克隆

**云服不落盘源码**（师傅明确要求），克隆只在本地做。

```bash
git clone https://github.com/fe1iscurc0r/PSDR.git
cd PSDR
git remote add upstream https://github.com/MichaelRColton/PSDR.git
git fetch upstream
git log --oneline -1 upstream/master    # 应为 45acd0f
git checkout workorders/2026-10-30-psdr-takeover-linux-build-kicad
```

**验收**：
```bash
git branch -a | wc -l          # >= 15
git log --oneline -1 master    # 45acd0f
du -sh .git                    # 约 182M，偏差 >10% 要报告
```

⚠️ **必须带全 7 个分支**：`PSDR_F7` 是 STM32F756 平台，**而 2.6.1 版 BOM 用的正是 STM32F756** —— 只留 master 会缺最接近目标硬件的固件线。
⚠️ GitHub 内地可能不通：配代理或换镜像，**不要因此只拉 master**。

---

## 任务 B · Linux 交叉编译复现（核心）

**工具链**：`sudo apt install gcc-arm-none-eabi`（实测 13.2.1 可用）。**不要用 Eclipse**（依赖 Windows + 联网插件源）。

### B-1 · 四处上游构建缺陷（逐条修，改源码）

| # | 文件 | 缺陷 | 修法 |
|---|---|---|---|
| 1 | `Source/src/misc.c` | 只 include `misc.h`，**缺 `stm32f4xx_hal_conf.h`** → `assert_param` 被当隐式函数声明 → 链接失败 | 加 `#include "stm32f4xx_hal_conf.h"` |
| 2 | `Source/src/hal.c` | `hal_checkTimeout()` 在 `hal.h:175` 声明但**全仓无实现**，TinyGPS 依赖 | 实现它（见下方陷阱） |
| 3 | `Source/src/uart.c` | `USART_HandleTypeDef usart` 应为 `UART_HandleTypeDef` | 改类型 |
| 4 | `Source/src/main.c` | `HAL_IncTick()` **全仓无调用点** → `HAL_GetTick()` 恒为 0 | 在 main.c 已有的 `SysTick_Handler`（第 345 行）里加 `HAL_IncTick();` |

#### ⚠️ 缺陷 2 的三个陷阱（务必读清）

1. `hal.h` 里声明是 `extern inline bool hal_checkTimeout(...)` —— C99 inline 语义要求**外部定义**，只在头文件写 inline 函数**链接不上**。必须放在 `.c` 里。
2. **不能用 `HAL_GetTick()`**：修好缺陷 4 之前它恒为 0。（修好缺陷 4 后可以用，但见第 3 点。）
3. **注意 SysTick_Handler 已经存在**：`main.c:345` 有真正的 `SysTick_Handler`（含 `millis++`、`timer_tick()`、`Tick()`），而 `stm32f4xx_it.c:145` 有个**空的 weak 版本**。
   - ❌ **别在 `stm32f4xx_it.c` 里新建** → 会和 main.c 重复定义，链接报 `multiple definition of SysTick_Handler`。
   - ✅ **改 main.c 里那个**（它才是真正生效的）。
   - 计数来源：`main.c` 里已有 `millis` 变量，直接用它，别再造一个。

#### ⚠️ 缺陷 3 改完还不够 —— `uart.c` 是 SPL 时代代码

改完类型后 `uart.c` **仍然编译不过**：

```
src/uart.c:471:31: error: incompatible type for argument 1 of 'HAL_USART_GetState'
src/uart.c:477:30: error: incompatible type for argument 1 of 'HAL_USART_Receive_IT'
```

原因：该文件把句柄**值**传给 HAL API（HAL 要**指针**），且整体依赖旧版 SPL 的 `USART_ITConfig` / `USART_Cmd` / `hal_setupUart1..3` —— 这些在 HAL-only 工程里全都不存在。

**正解**：新增 `Source/src/uart_hal_stub.c`，提供 TinyGPS 实际需要的最小功能：

```c
/* 最小 UART 适配层 (替代上游 uart.c)
 * 上游 uart.c 是 SPL 时代移植代码, 依赖 USART_ITConfig / USART_Cmd /
 * hal_setupUart1..3 等 SPL API, 在 HAL-only 工程里无法链接,
 * 故上游 .cproject 直接把它排除 —— 但 TinyGPS.c 依赖其中的 uart_getChar(),
 * 导致链接失败。本文件提供 TinyGPS 实际需要的最小功能。
 */
#include "hal.h"
#ifdef USE_HAL_DRIVER
#include "stm32f4xx_hal.h"
#endif
extern UART_HandleTypeDef UartHandle;   /* main.c 的 configUartPeripheral() 初始化 */

int uart_getChar(uint8_t uart, char *c) {
    (void)uart;
    if (c == NULL) return -1;
    if (HAL_UART_Receive(&UartHandle, (uint8_t*)c, 1, 0) == HAL_OK) return 0;  /* 0=success */
    return -1;
}
int uart_putChar(uint8_t uart, char c) {
    (void)uart;
    if (HAL_UART_Transmit(&UartHandle, (uint8_t*)&c, 1, 10) == HAL_OK) return 0;
    return -1;
}
```

同时在 Makefile 里排除 `src/uart.c`（保留 `uart_hal_stub.c`）。

> **硬件不一致（已实测）**：`main.c` 的 `configUartPeripheral()` 配置的是 **USART6**（GPIO AF8，接收 GPS），但 `include/hal.h:57` 把 `hal_gpsUart` 定义成了 **USART1**。实现按 USART6 走，并在注释里写明这个上游不一致。**这是已知待议项，不要擅自改 `hal.h` 的宏**——改了对不上 TinyGPS 的调用方。

### B-1.5 · 宿主环境：不必"完全复现"，但有三个必须注意的点

编译 STM32 是**交叉编译**，工具链自包含。所需仅四项：`arm-none-eabi-gcc` / `make` / `git` / `python3`（python3 只用于锚点比对脚本）。
**没有任何一项依赖 Ubuntu 特有功能** —— Kali(Debian 系)、WSL2 Ubuntu、原生 Linux 均可。

**真正要锁死的不是发行版，是二进制锚点**（见 B-3）：
`_estack=0x20030000` 与 `Reset=0x080001B5` 与编译器版本无关（不换 MCU 与链接脚本的前提下）。
**gcc 小版本不同只会让 size 漂几字节，锚点不变。不要为了追版本号折腾。**

⚠️ **三个必踩的坑（按宿主环境二选一）**：

**坑 1 · Windows 换行符会毁掉 Makefile**（天选7 用 Git for Windows 克隆时必中）
- 已实测：上游仓库**全部文件为 LF（0 个 CRLF）**，但**仓库内没有 `.gitattributes`** —— 即无任何保护。
- Git for Windows 默认 `core.autocrlf=true` 会把 LF 转成 CRLF。Makefile 的 recipe 行靠 **Tab** 缩进，
  CRLF 转换后 Tab 变成 `Tab+CR`，`make` 报 `missing separator` 直接罢工。
- ✅ 克隆前先设：
  ```bash
  git config --global core.autocrlf input
  ```
  或克隆后在仓内 `git config core.autocrlf false && git checkout -- .`
- ❌ 不要用 `git config --global core.autocrlf false` 之外的方式"绕过"——**不要**手动开编辑器改换行符，会引入无关 diff。

**坑 2 · WSL2 里不要在 `/mnt/c/` 下编译**
- WSL2 跨文件系统（9p/drvfs）访问 `/mnt/c` 极慢，749 个源文件编译会卡死到看不出在动。
- ✅ 仓库放 WSL2 **原生 ext4** 内（`~/PSDR`），编译产物再拷回 Windows。
- 验证：`cd ~/PSDR && stat -f -c %T .` 应输出 `ext2fs`/`ext4`，若是 `drvfs`/`9p` 就换位置。

**坑 3 · Kali 注意 PEP 668**
- Kali 的 Python 禁止系统级 `pip install`。本项目**不需要 pip 装任何东西**（python3 仅跑标准库脚本），
  但若临时要装工具：`python3 -m venv` 建虚拟环境。

**推荐分工**：编译验证放 Kali（真 Linux，apt 装包零障碍，无 CRLF 问题）；
天选7 的 WSL2 当"本地仓"存放代码即可（注意坑 1、坑 2）。
无论在哪台机器做，验收标准完全一样 —— 见 B-3。

### B-2 · 构建配置的两个坑（照做，否则固件静默失效）

1. **链接脚本要三个一起传**：
   ```
   -Tldscripts/mem.ld -Tldscripts/libs.ld -Tldscripts/sections.ld
   ```
   只传 `sections.ld` → `ORIGIN(RAM)` 不解析 → `_estack = 0xFFFFFFFF` → **不报错，但固件必挂**。
   （`libs.ld` 是空壳 `GROUP()`，`mem.ld` 才是 MEMORY 定义源）
2. **必须加 `-fcommon`**：GCC 10+ 默认 `-fno-common`，老代码靠 tentative definition 会爆大量 `multiple definition`。这是对齐原 GCC 4.7 语义，**不是掩盖问题**。
3. **`.cproject` 的排除表自相矛盾**：Debug 配置排除了 `stm32f4xx_hal_adc_ex.c` / `stm32f4xx_hal_dac_ex.c` / `stm32f4xx_hal_rtc_ex.c`，但被保留的 `adc.c` / `dac.c` / `rtc.c` 引用了它们里面的 `__weak` 回调 → 断链。**构建时不要排除这三个文件。**
4. **汇编源要单独编译规则**：`arm_bitreversal_32` 定义在 `DSP_Lib/Source/TransformFunctions/arm_bitreversal2.S`，只 wildcard `*.c` 会漏掉它 → `undefined reference to arm_bitreversal_32`。Makefile 需加：
   ```make
   ASM_SRCS = $(wildcard DSP_Lib/Source/TransformFunctions/*.S)
   OBJS += $(addprefix $(OBJDIR)/,$(ASM_SRCS:.S=.o))
   $(OBJDIR)/%.o: %.S
   	@mkdir -p $(dir $@)
   	$(CC) $(CPU) -c $< -o $@
   ```

### B-3 · Makefile.linux

`docs/psdr-handoff/Makefile.linux` 是**已验证可编译的版本**（含上述全部坑位处理），直接复制到 `Source/` 下用：

```bash
cd Source && make -f Makefile.linux
```

**预期结果（硬指标）**：
```
0 error / 365 warning
text 984908 / data 3004 / bss 18220
```

**二进制锚点验收（最硬的证据，必须贴真实输出）**：
```bash
arm-none-eabi-nm build_linux/PSDR.elf | grep -E "_estack|__stack"
```
必须得到 **`_estack = 0x20030000`**，且 Reset 向量 **`0x080001B5`** —— 与上游 2016 年的 `Source/Debug/PSDR.hex` **逐字节一致**。

> 这两个值对不上 = 构建配置错了，**不是"编译器差异"**。先自查再报。
> 对比脚本：
> ```python
> import subprocess
> def parse_ihex(path):
>     mem={}; base=0
>     for line in open(path):
>         line=line.strip()
>         if not line.startswith(':'): continue
>         b=bytes.fromhex(line[1:]); n=b[0]; addr=(b[1]<<8)|b[2]; typ=b[3]; data=b[4:4+n]
>         if typ==0x04: base=((data[0]<<8)|data[1])<<16
>         elif typ==0x00:
>             for i,v in enumerate(data): mem[base+addr+i]=v
>     return mem
> orig=parse_ihex('Debug/PSDR.hex'); a=min(orig)
> w=lambda m,o: m[o]|m[o+1]<<8|m[o+2]<<16|m[o+3]<<24
> d=subprocess.run(['arm-none-eabi-objcopy','-O','binary','--only-section=.isr_vector',
>    'build_linux/PSDR.elf','/tmp/nv.bin'],capture_output=True)
> mine=open('/tmp/nv.bin','rb').read()
> r=lambda b,o: b[o]|b[o+1]<<8|b[o+2]<<16|b[o+3]<<24
> print("SP   upstream=0x%08X new=0x%08X" % (w(orig,a), r(mine,0)))
> print("RST  upstream=0x%08X new=0x%08X" % (w(orig,a+4), r(mine,4)))
> ```

---

## 任务 C · Eagle → KiCad 转换（为嘉立创EDA 导入）

**障碍（已核实）**：
- 硬件文件是 **Eagle 二进制格式**：`Hardware/PSDR.sch` / `Hardware/PSDR.pcb`（`file` 显示 `data`，非 XML）
- 无 `.brd`（Eagle 6+ 格式）
- Gerber 是**老式扩展名**（`.GTL/.GBL/.G1/.G2/.GTS/.GBS/.GBO/.GKO`），嘉立创要 `.gbr`
- `Hardware/Enclosure/` 是 **SolidWorks**（`.SLDPRT`），嘉立创EDA **不吃**
- 板子共 4 块：`PSDR1` / `PSDR2 Main Board` / `PSDR2 Encoder Board` / `PSDR2 Amp Board`

**做法**：
1. 找 Eagle → KiCad 转换工具（`eagle2kicad` / `kicad-cli` 的 Eagle 导入 / SKiDL 生态脚本），把 `PSDR.sch` + `PSDR.pcb` 转成 `.kicad_sch` + `.kicad_pcb`
2. 转不了的（3D 壳体、装配图）**如实标 SKIP 并说明**，不要假装成功
3. 产出规范化 Gerber 包：
   `.GTL→顶层铜.gbr`、`.GBL→底层铜.gbr`、`.GTS/.GBS→阻焊.gbr`、`.GTO/.GBO→丝印.gbr`、`.GKO→板框.gbr`、`.TXT/.drl→.drl`
4. **对照 `Hardware/BOMs/PSDR_2.6.1/` 的 BOM 核对元件**，标出停产件：
   - `599-1068-1-ND` RF 放大器 U304 → 替代 `SXB-2089Z`（Win Source）
   - `1465-1374-1-ND` RF DPDT 开关 U16/U24/U30 → 替代 `MASWSS0129TR-3000`（Richardson）

**验收**：
```bash
ls -la dist/kicad/            # .kicad_pcb + .kicad_sch
ls -la dist/gerber/           # 全部 .gbr + .drl
kicad-cli pcb drc dist/kicad/PSDR.kicad_pcb    # 若可用, 贴真实输出
```
> **DRC 报错是预期的**（老设计）。要**列出违规条目并判断是否影响生产**，不许把 DRC 失败写成"通过"，也不许因为报错就跳过 DRC。

---

## 任务 D · 交付与归档

**提交到**：`fe1iscurc0r/PSDR` 的 `workorders/2026-10-30-psdr-takeover-linux-build-kicad` 分支。

**提交清单**：
- `Source/Makefile.linux`（新增）
- `Source/src/uart_hal_stub.c`（新增）
- `Source/src/hal.c` / `Source/src/main.c` / `Source/src/misc.c` / `Source/src/uart.c`（4 处修复）
- `docs/psdr-build-notes.md`（新增：构建步骤 + 坑位记录）
- `dist/kicad/`、`dist/gerber/`（转换产物；大件如 SolidWorks 勿进仓）
- `docs/WO-psdr-takeover.md`（施工记录，含验收证据）

**施工记录必须含**：
1. 真实构建输出（`make` 日志尾部 + `arm-none-eabi-size` 结果）
2. **锚点比对表**：`_estack` 与 Reset 向量的实际值 vs 期望值
3. 转换产物清单 + **哪些 SKIP 了、为什么**
4. DRC 违规清单 + 判断
5. 你新踩到的坑（我可能还有没发现的）

---

## 边界（重要）

- ❌ **不要给上游 `MichaelRColton/PSDR` 提 PR / issue / 评论** —— 那是"对外公开发布"，**须先经师傅过目**。本单只推自己的 fork。
- ❌ **不要修射频逻辑**（前置放大器、低通滤波器配置、issue #6/#8/#9）—— 那是需要**实物硬件**的活，本单不碰。
- ❌ **不要动 `PSDR_F7` 分支** —— 它与 master 差 15 万行，是另一套代码，混用会毁掉一切。
- ❌ **不要在云服落盘源码** —— 师傅明确要求，克隆只在本地。
- ⚠️ **`Hardware/Enclosure/` 的 SolidWorks 文件不要试图转换** —— 嘉立创EDA 无对应能力，如实标 SKIP。

## 一句提醒

**这个项目的历史包袱比代码多。** 上游最后一次改固件是 2016 年，作者自己说"没时间"。做这单时**别假设"改好就能用"**——射频链在量产板上从未工作（前置放大器缺约 50 dB 灵敏度）。

**本单的交付目标是「固件能在现代工具链上构建 + 硬件能进嘉立创EDA」，不是「电台能通联」。** 后者需要实物 + 作者手里的器件 + issue #16 的滤波器寄存器序列，**那要另开工单**。

**开工前若有疑问，先问师傅，别猜。**

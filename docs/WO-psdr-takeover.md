# 施工记录 · PSDR 接手工单（2026-10-30）

分支：`workorders/2026-10-30-psdr-takeover-linux-build-kicad`
执行机：天选7P（Windows 11 26300）+ WSL2 Ubuntu 24.04（构建用）

> **当前状态：任务 A 完成并通过验收；任务 B 源码修复完成、构建验证待 WSL2 重启后执行；
> 任务 C / D 未开始。** 本记录不含任何未经真实命令验证的"已完成"。

---

## 任务 A · 完整克隆 —— 通过

工作目录 `D:\my git\PSDR`（新建空目录，未复用任何旧目录）。

| 验收项 | 期望 | 实测 | 结论 |
|---|---|---|---|
| `git rev-parse --is-shallow-repository` | `false` | `false` | ✅ |
| `git branch -a \| wc -l` | ≥ 15 | `19` | ✅ |
| `git log --oneline -1 master` | `45acd0f` | `45acd0f Update LICENSE.md` | ✅ |
| `git log --oneline -1` | `479ee18d2` | `f30b11a`（见 §A-2） | ⚠️ 分支已前移 |
| `du -sh .git` | ≈182M | `183M`（+0.5%） | ✅ |
| `git remote -v` | origin=fork, upstream=MichaelRColton | 均已配置 | ✅ |
| `git fsck --full` | 无错误 | 空输出，exit 0 | ✅ |

7 个分支全部到位：`master` / `PSDR_F7` / `PSDR_F7_DMA` / `PSDR_Rebuild` /
`PSDR2.5_PCB` / `DMA_Video` / `DMA_Video_Alt`，origin 与 upstream 各一份。
浅克隆、`--single-branch`、`--filter`、tarball 均未使用。

### A-1 取码通道

`api.github.com` 直连可通（HTTP 200），但 `github.com` 的 git 协议被重置
（`info/refs?service=git-upload-pack` 返回 `000`）。改走本机 7890 代理后为 200。

用的是**单命令级**代理，没有落全局配置：

```bash
git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=http://127.0.0.1:7890 clone ...
```

### A-2 两处验收期望需要修正

1. `git log --oneline -1` 期望 `479ee18d2`：工单 commit 之后又压上了
   `9f07464`（开工提示词）与 `cc6dabf`/`f30b11a`（宿主环境定案），分支 tip 现在是
   `f30b11a`。`479ee18` 确认存在于历史且是 HEAD 的祖先。建议验收改成
   `git merge-base --is-ancestor 479ee18 HEAD`。
2. `git branch -a | wc -l ≥ 15`：只 fetch origin 时是 **10**（1 本地 + 8 远端 + 1 HEAD 符号）。
   要 ≥15 必须先 `git fetch upstream`。这个阈值隐含了 upstream 已对账，建议写明。

### A-3 Windows 换行符：工单的处方在这台机器上不够用

工单 B-1.5 坑 2 说得对，但给的处方在**已克隆之后**无效，实测过程：

- 本机 `core.autocrlf=true` 来自 **system 级** gitconfig（`C:/Program Files/Git/etc/gitconfig`），
  不是 global。克隆后工作树 585 个文件被转成 CRLF，而 HEAD blob 里只有 1 个文件含 CR
  （证实上游确实全 LF，工单的描述准确）。
- 工单给的"克隆后 `git config core.autocrlf false && git checkout -- .`"这条**不管用**：
  工作树相对 index 是"干净"的（git 用同一套转换规则双向比对），`checkout -- .` 与
  `checkout-index -a -f` 都会静默跳过，文件不动。
- 真正有效的两步：
  ```bash
  git config core.autocrlf false && git config core.eol lf
  # 必须先把文件删掉，checkout-index 才会重写
  git grep -I -l -z -e $'\r' -- . | xargs -0 -r sh -c 'rm -f "$@" && git checkout-index -- "$@"' sh
  # 此时 git status 会假报 584 个 modified（index stat cache 过期，git diff 内容为空）
  git diff --raw | wc -l        # 0，确认无真实内容差异后才可做下一步
  git reset --hard HEAD         # 清 stat cache
  ```
  终态：`git status` 空，工作树含 CR 文件数 1（与 HEAD blob 一致）。

**给后续施工的建议**：仓库里补一个 `.gitattributes`（`* text=auto eol=lf`，二进制除外），
比依赖每个人正确的 git 配置可靠。本轮没有加，因为它会改动全仓元数据、超出工单范围。

---

## 任务 B · Linux 交叉编译复现 —— 源码已修，构建待跑

### B-1 环境

本机无 WSL / 无 Docker。装 WSL2 的进展与卡点：

- `wsl --install --no-launch`（提权）成功装上 **WSL 3.0.3，内核 6.18.54.1**，无需重启即生效。
- `wsl --install -d Ubuntu-24.04 --no-launch` 返回
  `请求的操作成功。直到重新启动系统前更改将不会生效。`
  随后 `wsl -l -v` 仍是"没有已安装的分发"——**启用 `VirtualMachinePlatform`
  需要重启**，所以发行版还没注册。
- 因此构建验证卡在"需要一次重启"。在得到明确同意前没有重启机器。

版本口径核实（真实包索引）：

| 环境 | `gcc-arm-none-eabi` | 对得上交接材料的 13.2.1？ |
|---|---|---|
| Ubuntu 24.04 noble（universe） | `15:13.2.rel1-2` | ✅ 精确 |
| Debian 13 trixie（Kali 基座） | `15:14.2.rel1-1` | ❌ |
| Debian 12 bookworm | `15:12.2.rel1` | ❌ |
| MSYS2 | 16.2.0 | ❌ |

新工单 B-1.5 已定案"锦点与编译器版本无关，不要追版本号"，所以这里只作记录：
选 WSL2 Ubuntu 24.04 是因为它能用 apt 直接拿到 13.2.1，与出报告的人同版本。

### B-2 已完成的源码修复（5 处，非 4 处）

详见 `docs/psdr-build-notes.md` §2。改动文件：

```
Source/src/misc.c            M   缺陷 1
Source/src/hal.c             M   缺陷 2 + 缺陷 5
Source/src/main.c            M   缺陷 4
Source/src/uart_hal_stub.c   N   缺陷 3 的正解
Source/Makefile.linux        N   构建脚本（含 .S 规则与 GC 开关）
docs/psdr-handoff/anchor_check.py  N  锦点自证脚本
```

工单列 4 个缺陷，实测是 **5 个**：`hal.c:232` 的 `static uint32_t halMilliseconds`
唯一的自增语句在注释块里（`hal.c:251`），于是 `hal_getCurrentTime_ms()` 恒返回 0，
而 `TinyGPS.c:174/327/335` 的时间戳全部取自它。这个不影响链接，但让 GPS 超时判据
永久失效——工单和评估报告都没提到。

### B-3 已验证的部分（不需要编译器就能验的）

用 MSYS2 的 GNU Make 4.4.1 做了 dry-run 解析与源码集断言（`make -n`），全部通过：

| 断言 | 期望 | 实测 |
|---|---|---|
| Makefile 解析 | 无 `missing separator` | exit 0，142 个编译单元渲染正常 |
| `src/uart.c` | 被排除 | 0 次出现 |
| `src/uart_hal_stub.c` | 被编入 | 1 次 |
| `stm32f4xx_hal_adc_ex.c` / `_dac_ex.c` / `_rtc_ex.c` | 不排除 | 3 个都在 |
| `arm_bitreversal2.S` | 有编译规则 | 已作为编译单元出现 |
| `arm_cfft_radix2_*` | 排除 | 0 次 |
| `ILI9341_t3.c` | 排除 | 0 次 |
| 链接行 | 三个 `-T` + `-nostartfiles` + `--gc-sections` | 全部存在 |

**注意：这只证明 Makefile 结构正确，不证明能编译链接。** `0 error` 与锦点比对
必须等 WSL2 起来真跑一次才算。

### B-4 待办的硬指标

```
make -f Makefile.linux           → 0 error，warning 数百条
arm-none-eabi-size               → text/data/bss（见下）
make -f Makefile.linux anchors   → _estack=0x20030000, Reset=0x080001B5, PASS
```

`--gc-sections` 开与关各跑一次（`GC=1` / `GC=0`），把两组尺寸都记下来，用来判定
交接材料里 984908 与 1077236 哪个对应哪种配置。

---

## 交接材料内部的矛盾（工单未覆盖，逐条列出）

1. **尺寸数字冲突**：工单 `text 984908 / data 3004 / bss 18220 / 365 warning`
   vs 评估报告 `text 1077236 / data 2988 / bss 18216 / 354 warning`。差 92,328 字节。
   推测为 `--gc-sections` 开关差异，待 B-4 证实。
2. **`Makefile.linux` 号称"已验证可编译"，但它链接不上**：缺 `.S` 编译规则，
   而 `arm_bitreversal_32` 只定义在 `arm_bitreversal2.S` 里。工单 B-2.4 自己要求补
   这条规则——说明给出的脚本不是产出那组数字的版本。同时它也没有 `--gc-sections`，
   而上游 `.cproject` Debug 的 `linker.gcsections=true`。
3. **`uart.c` 取舍矛盾**：`Makefile.linux` 头注释第 2 条写"保留 `src/uart.c`
   （缺陷3 修好后它是可编译的）"，工单 B-1 却说改完类型仍编不过、必须排除并新增
   `uart_hal_stub.c`。实测 `src/uart.c` 有 26 处 `USART_ITConfig`/`USART_Cmd`/
   `hal_setupUart1..3`，工单的判断成立，Makefile 注释是错的。
4. **缺陷 #4 定义不一致**：工单 B-1 表里第 4 条是 `main.c` 缺 `HAL_IncTick()`；
   评估报告 §3.3 表里第 4 条是 `arm_bitreversal_32` 被排除。是两个不同的问题被
   编了同一个号。
5. **`hal_checkTimeout` 返回类型冲突**：`hal.h:174` 声明 `extern inline bool`，
   `PATCH-NOTES.md` 的实现返回 `uint32_t`。按头文件走。
6. **时钟源冲突**：`PATCH-NOTES.md` 让 `hal_checkTimeout` 用 `HAL_GetTick()`，
   但调用方 `TinyGPS.c` 的时间戳来自 `hal_getCurrentTime_ms()`。两者不收敛的话
   能链接但 GPS 逻辑永久判死（见缺陷 5）。

---

## 任务 C · Eagle → KiCad —— 未开始

已核实的现状（本机 `file` 命令）：

```
Hardware/PSDR.sch: data      ← Eagle 二进制格式，非 XML
Hardware/PSDR.pcb: data
Hardware/Enclosure/          ← SolidWorks .SLDPRT，嘉立创EDA 不吃
```

板子 4 块：`PSDR1` / `PSDR2 Main Board` / `PSDR2 Encoder Board` / `PSDR2 Amp Board`。
本机未装 KiCad；已确认用 winget 装 KiCad 9（KiCad 8+ 才有原生 Eagle 导入）。
SolidWorks 部分按工单要求如实标 SKIP，不试图转换。

## 任务 D · 提交归档 —— 未开始

不推上游 `MichaelRColton/PSDR`，不动 `PSDR_F7`，不碰射频逻辑。
推送 origin 属对外动作，等构建验收数据齐了再单独确认。

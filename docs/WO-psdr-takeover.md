# 施工记录 · PSDR 接手工单（2026-10-30）

分支：`workorders/2026-10-30-psdr-takeover-linux-build-kicad`
主线：`next`（2026-11-01 起，独立 fork 线，见 §E）
执行机：天选7P（Windows 11 26300）+ WSL2 Ubuntu 24.04（构建用）

> **当前状态：任务 A 通过验收；任务 B 通过（GC=1 与 GC=0 各一次完整构建，0 error、
> 365 warning、锚点 `_estack=0x20030000` / Reset `0x080001B5` 与 2016 上游 hex 一致，
> 尺寸对账见 §B-4）；任务 C 的 5 项 SKIP 已解除 3 项——`.kicad_sch` 已由 §C-12 生成，
> 4 铜层与真实焊盘见 §C-13，铺铜/真实板框/丝印见 §C-14；剩 2 项（SolidWorks 壳体、
> PADS 二进制原文件）见 §C-8。四层 KiCad 板已 0 断点，但仍有 795 条 DRC 违规
> （多为源设计允许的丝印压焊盘与紧间距），**制板仍以 2.6.1 的原始 Gerber 为准**；
> 任务 D 记录已写、已推 `origin`（fork），未碰上游。**
> 本记录不含任何未经真实命令验证的"已完成"。

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

## 任务 B · Linux 交叉编译复现 —— 通过

### B-1 环境

WSL2 的门槛是 `VirtualMachinePlatform`：装完 WSL 3.0.3 后 `wsl --install -d Ubuntu-24.04`
仍返回"直到重新启动系统前更改将不会生效"，`wsl -l -v` 里没有发行版。**重启一次**后才
注册成功（经确认后重启）。重启后的实际环境：

```
WSL 版本 3.0.3.0，内核 6.18.54.1-microsoft-standard-WSL2
Ubuntu 24.04.5 LTS，VERSION 2，24 vCPU，ext4 995G 可用
arm-none-eabi-gcc (15:13.2.rel1-2) 13.2.1 20231009
GNU size 2.42 / GNU Make 4.3 / git 2.43.0 / Python 3.12.3
```

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

### B-3 真实构建结果

在 WSL2 的 ext4 上从**本地工作树**克隆 `43497b3`（不是 GitHub：本地领先 origin 2 个
提交，从 GitHub 拉会拿到未修的树），`GC=1`（对齐上游 `.cproject` Debug 的
`linker.gcsections=true`）与 `GC=0` 各跑一次完整构建：

| 项 | GC=1（与 2016 真机同配置） | GC=0 |
|---|---|---|
| `make` 退出码 | 0 | 0 |
| `error:` | **0** | **0** |
| `warning:` | 365 | 365 |
| `text` | **133644** | **984844** |
| `data` | **2884** | **3004** |
| `bss` | **18152** | **18208** |
| `PSDR.bin` | 136580 B | 987900 B |
| anchors | PASS | PASS |

warning 构成：`array` 132 / `implicit` 28 / `conflicting` 13 / `size` 12 / `inline` 10 /
`passing` 8 / 其余分散。365 条与工单给的"365 warning"一致。

`make -f Makefile.linux GC=1 anchors` 原文：

```
reference hex base : 0x08000000
vector bytes       : new=804  ref=804
initial SP     upstream=0x20030000  new=0x20030000  expected=0x20030000  OK
reset vector   upstream=0x080001B5  new=0x080001B5  expected=0x080001B5  OK
byte-for-byte over vector table: 438/804 (54.5%)
first divergence at vector offset 8 (0x08)
RESULT: PASS
```

两个绑定锚点与 2016 年上游 `Debug/PSDR.hex` 完全一致。向量表只有 438/804 字节相同，
是因为从第 3 项起每个 handler 的地址都随代码布局移动；工单指定的判据就是这两个锚点。

构建产物不入仓，落在 `D:\my git\PSDR-build-artifacts\`（elf/hex/bin/map + 全部构建日志）。

### B-4 交接材料两个尺寸数字的来源（已证实）

| 来源 | text | data | bss | 对应配置 | 实测 | 差 |
|---|---|---|---|---|---|---|
| 工单 | 984908 | 3004 | 18220 | GC=0 + `.cproject` 的 HAL 排除表 | 984844 / 3004 / 18208 | −64 / 0 / −12 |
| 评估报告 | 1077236 | 2988 | 18216 | GC=0 + **不排除**任何 HAL 模块 | 1077356 / 3004 / 18212 | +120 / +16 / −4 |
| 2016 上游 hex | — | — | — | GC=1 + 排除表 | 我们 GC=1 镜像 136580 B | 参考 137656 B，−0.78% |

1. **两个数字之差不是 `--gc-sections`**，而是**有没有执行 `.cproject` 的 HAL 排除表**：
   全 HAL 比排除表多 92512 字节 text，正好填上交接材料里 92328 的缺口。
2. 两者都是 **GC=0**。GC 打开后 text 从 984844 掉到 133644，少掉的 851200 字节全在
   `.text`，主体是 CMSIS-DSP 的系数表（`Weights_8192` 64K、`twiddleCoef_*` 32K、
   `realCoef*` 32K…），它们只被无人调用的 DSP 函数引用。
3. **2016 年真机固件是 GC=1**：参考 hex 的镜像跨度 137656 字节，我们 GC=1 的镜像
   136580 字节，差 1076 字节（0.78%，来自 2016 年那套 GCC 与本机 13.2.1 的代码生成
   差异）。交接材料引用的两个尺寸都是"没开 GC 的废尺寸"，不能当验收目标。
4. 残差（−64/−12 与 +120/+16/−4 字节）来自源码状态差异，不是编译标志。实测把
   `.cproject` 的 `-fsigned-char -ffreestanding -g3 -O0` 补进 GC=0，得到
   984476/2996/18204，**离目标更远**（data 反而少 8）。
5. `mem.ld` 里 FLASH 是 2048K，1.08 MB 的变体也装得下——不能用"超 flash"来排除它。

### B-4.1 执行记录与本轮新坑

实际执行与原清单的差异：

- `wsl --install -d Ubuntu-24.04 --no-launch --web-download` 一次成功；`-u root` 确实
  跳过了首次进发行版的建号向导。
- 直连可用（`archive.ubuntu.com` 返回 200），**没有用代理**；apt 装出的正是 13.2.1。
- Git Bash 把 `/mnt/d/...` 当 POSIX 路径转成 Windows 路径再交给 `wsl.exe`，git 收到
  `C:/Program Files/Git/mnt/...` 并把 `C:` 当主机名，报 `Could not resolve hostname c`。
  必须加 `MSYS_NO_PATHCONV=1`。
- WSL 里 `/tmp` 是 tmpfs，`wsl.exe` 每次调用是独立会话，命令退出 VM 就停，`/tmp` 下的
  日志随即消失。日志一律落 `/root/`。
- `make CFLAGS+="..."` 在命令行是**替换**不是追加（GNU make 命令行变量语义），会把整个
  CFLAGS 换成只剩附加项。做对照构建要临时 `sed` 改 Makefile，跑完 `git checkout --` 还原。
- 365 条 warning 里有 12 条 `size of symbol 'oneSmall' changed from 2 ... to 144`，是
  `-fcommon` 下 `images.c` 的 144 字节定义与别处的 2 字节暂定定义合并时的提示；实测
  `oneSmall` 在 elf 里解析成 144 字节（`T oneSmall`），不影响产物。

---

## 交接材料内部的矛盾（工单未覆盖，逐条列出）

1. ~~尺寸数字冲突~~ **已解决（§B-4）**：工单 `984908/3004/18220` 与评估报告
   `1077236/2988/18216` 差 92,328 字节，原因不是 `--gc-sections`，而是后者多编了
   `.cproject` 排除掉的 HAL 模块；两者都没开 GC，而 2016 真机镜像证明出厂固件是 GC=1。
   warning 数两份材料写 365 与 354，我们两套配置实测都是 365——354 这一项无法复现。
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

## 任务 C · 硬件文件转换 —— 已完成（但转换源不是 Eagle，见 C-1）

### C-0 一句话结论

工单写的路径是 Eagle → KiCad。**这个前提不成立**：仓库里的 `.sch`/`.pcb` 不是 Eagle，
而是 **PADS Logic / PADS Layout 二进制**（`Hardware/README.md` 原文：
"Schematics and Board layout files are for Mentorgraphics PADS"；文件头
`00 fe 0d 00` / `00 ff 26 20`），KiCad 10 的 Eagle 插件当然读不了，见 C-2。
实际走的是两条有数据的通道：

1. `Hardware/BOMs/PSDR_2.6.1/psdr26.emn` + `.emp` 是 **PADS Layout 9.5 的 ASCII 导出**，
   里面有板框、孔表和 391 个器件的贴装坐标。从它生成 KiCad 板子，再用
   KiCad 自己的 plot 输出反解回来跟**原始 PADS Gerber** 对账，得到
   亚微米级偏差（C-5）。
2. `.emn`/`.emp` 没有铜走线，也没有真实焊盘形状。这两样改从
   `Hardware/PSDR.asc`（PADS Layout ASCII 全文，含 `*PARTDECAL*`/`*ROUTE*`）
   提取，生成四层板后与 2.6.1 原始 Gerber 逐 flash、逐钻孔对账（C-13）。

`.kicad_sch` 已由 C-12 生成（连通性模型，不是重画的图）；SolidWorks 壳体
**如实标 SKIP**（C-8）。

### C-1 交付物清单（真实 `ls`）

```
$ ls -la dist/kicad/
-rw-r--r-- 229724  PSDR_2.6.1-drc.json          # kicad-cli 10.0.6 DRC 报告（UTF-8, mm）
-rw-r--r-- 721924  PSDR_2.6.1.kicad_pcb         # 生成物
-rw-r--r--   2297  PSDR_2.6.1.kicad_prl         # KiCad 打开时自动创建
（无 .kicad_sch —— 见 C-8 SKIP-1）
（这是当时的快照；.kicad_sch 见 §C-12，四层板与 DRC 报告见 §C-13）

$ ls dist/gerber/          # 9 个板集，目录 + 同名 zip 各一份
Keychain/  MultiTest2/  MultiTestBoard/  PSDR1/  PSDR25_Encoder_Board/
PSDR25_Main_Board/  PSDR2_Amp_Board/  PSDR2_Encoder_Board/  PSDR2_Main_Board/
+ 9 个 .zip（Keychain 59925 … PSDR25_Main_Board 444355 B）

$ ls tools/
gerbparse.py 10762          # RS-274X 读：FS/MO/OF/AP/AD/AM/LP, G00-G04, G74/G75, D01-D03, 弧
gerber_normalize.py 16001   # 老式扩展名 → 规范名 + MANIFEST + sha256 自证
pads_parse.py 7021          # PADS 9.5 ASCII 固定列位读（.emn / .emp）
kicad_from_pads.py 14936    # .emn/.emp + Gerber 实测环宽 → KiCad 10 .kicad_pcb
kicad_board_header.kicad_pcb 2134   # KiCad 10.0.6 生成的板头，逐字复用
kicad_roundtrip_check.py 5963       # 反向对账（C-5 的判据）
```

`kicad_board_header.kicad_pcb` 是本轮补进去的：之前 `kicad_from_pads.py` 的
`--template` 指向 `%TEMP%\kctest\from_pads.kicad_pcb`，那是个会话临时文件，
新克隆上跑不起来。改成仓库内默认路径后重跑，产物与之前**除 UUID 外逐字节相同**
（`diff` 去掉 `(uuid` 行后 211611 = 211611 字节，无差异）。

### C-2 障碍核实：工单的四条，实测结论

| 工单断言 | 实测 | 处理 |
|---|---|---|
| `.sch`/`.pcb` 二进制，无 `.brd` | ✅ `file` 报 `data`；KiCad Eagle 插件报 `XML 解析错误：'not well-formed'`，**但 exit 0**（因为这些文件根本不是 Eagle，是 PADS） | 放弃 Eagle 路线，改走 PADS ASCII（`.emn`/`.emp`） |
| 老式 Gerber 扩展名 | ✅ `0 - drillfile.TXT` / `3 - top-art.GTL` / `9 - fabnotes.GBR` 等 9 套 | `tools/gerber_normalize.py` 规范化 |
| `Hardware/Enclosure/` 是 SolidWorks | ✅ `.SLDPRT`/`.SLDASM` | SKIP，不转换（工单也这么要求） |
| **"板子共 4 块"** | ❌ **实测 9 个 Gerber 板集** | 偏差报告见 C-3 |

**板集数量偏差（工单要求报告）**：除 PSDR1 / PSDR2 Main / Encoder / Amp 四块外，
还有 `PSDR25_Main_Board`、`PSDR25_Encoder_Board`（2.5 版）、`MultiTestBoard`、
`MultiTest2`、`Keychain`（测试板与配件板）。**9 vs 4**。

另外两条工单没提、但直接影响"能不能下单"的缺陷：

1. **板框层缺失**：9 套里只有 5 套有独立轮廓层。`PSDR25_Main_Board` 的轮廓是从
   `9 - fabnotes.GBR` 里**按刀线单独提取**恢复的（该文件只有 670 条画线、1 个孔径，
   是纯工艺标注层）。`Keychain`/`MultiTest*` 等没有可恢复轮廓。
2. **同一套 Gerber 内坐标格式混用 `3.5` 与 `3.4`**：`F_SilkS` 是 `3.4`，`F_Cu` 是 `3.5`。
   按 `3.5` 读 `3.4` 会把每个特征放大 10 倍。`gerber_normalize.py` 逐文件记 `FS=`。

### C-3 为什么 KiCad 自带的 PADS 导入器不能用

KiCad 10 的 PADS 导入器认的是 `*PADS-POWERPCB*` 方言；这里的文件是
`BOARD_FILE 3.0` 固定列位 ASCII（PADS Layout 9.5）。导入器**报成功但返回空板**，
这是个静默失败，不能靠它。所以写了 `tools/pads_parse.py` 按列位读：

```
OUTLINE_TAG=slice(0,6)  OUTLINE_X=slice(6,36)  OUTLINE_Y=slice(36,66)  OUTLINE_ARC=slice(66,96)
MOVE_X=slice(0,30) MOVE_Y=slice(30,60) MOVE_Z=slice(60,90) MOVE_ROT=slice(90,100)
MOVE_SIDE=slice(100,110) MOVE_STATE=slice(110,120)
NAME_TYPE=slice(0,45) NAME_DECAL=slice(45,90) NAME_REFDES=slice(90,None)
```

自检输出（`python tools/pads_parse.py` 的真实结果）：

```
units THOU | sections ['BOARD_OUTLINE','DRILLED_HOLES','HEADER','PLACEMENT']
outline 68 vertices, 25 arced, closed=True | stray ['35.4']
holes 466  plating {'PTH':439,'NPTH':27}  kind {'VIA':419,'PIN':47}
components 391  side {'BOTTOM':182,'TOP':209}  state {'PLACED':369,'MCAD':22}
decals 57 | .emp defines 57 | missing: none
```

`DRILLED_HOLES` 段每行的**名字列就是位号**（VIA 才是 `VIA`），这一点是后面把
47 个 PIN 孔挂回封装的依据。

### C-4 三个不能靠猜的约定，全部实测钉死

1. **PADS 圆弧**：角度记在**段的终点顶点**上，正负按 PADS 顶点顺序，幅值=包含角
   （可以 >180°）。圆心 = 弦中点 + sign(a)·左法向·r·cos(a/2)。
   证据：给 `gerbparse.py` 加了原生弧捕获（`Gerber.arcs`），把 `.emn` 的 25 段弧
   与原始 Gerber 的 25 段弧逐段配对，**25/25 命中，|圆心角| 与 |G02/G03 扫掠角|
   差 < 0.05°**。同时发现原始 Gerber 轮廓的**遍历方向与 PADS 相反**（所以 25 段全是
   G03，而 PADS 角度多为负），第一次测试因此两段都差 2.4 mm。
2. **KiCad 封装正变换**（用 3 个已知探针封装实测，F.Cu 与 B.Cu 同式）：
   `abs = origin + K(rot)·local`，`K(t) = [[cos t, sin t], [-sin t, cos t]]`，文件 Y 向下。
   挂孔要用**逆变换** `K(-rot)`。这里踩过坑：写成 `K(rot)` 后 rot=0 的 454 个孔全对，
   只有 12 个错（USB×4、J170×4、CW1×2、CW2×2），错 1.5–4 mm、有的落到板外负坐标。
3. **坐标系桥**：PADS THOU ×0.0254；Gerber 特征 = PADS 坐标 + 1.0 inch 绘图原点；
   KiCad 的 drill/gerber 导出对 Y 取负。

### C-5 往返验证（转换是否"对"的唯一硬证据）

`.emn` → KiCad → `kicad-cli` 反解回原始 PADS Gerber：

```
$ kicad-cli pcb export gerbers --layers "Edge.Cuts" -o /tmp/rt dist/kicad/PSDR_2.6.1.kicad_pcb
$ kicad-cli pcb export drill --format excellon --drill-origin absolute -u mm -o /tmp/rt dist/kicad/PSDR_2.6.1.kicad_pcb
$ python tools/kicad_roundtrip_check.py --edge-export /tmp/rt/PSDR_2.6.1-Edge_Cuts.gm1 \
                                        --drill-export /tmp/rt/PSDR_2.6.1.drl
board from .emn      : 99.9998 x 64.9986 mm
Edge.Cuts segments   : original 670 (25 arcs), KiCad re-export 670 (25 arcs)
outline extent       : original 99.9998 x 64.9986 mm, KiCad 99.9998 x 64.9986 mm
contour deviation    : KiCad->original max 0.00053 mm, original->KiCad max 0.00053 mm
drill hits exported  : 466 (from .emn: 466)
worst hole offset    : 0.00063 mm (tolerance 0.010 mm)
plated / unplated    : 439 / 27  (.emn says 439 PTH / 27 NPTH)
RESULT: PASS            rc=0
```

生成器的自述输出：

```
wrote D:\my git\PSDR\dist\kicad\PSDR_2.6.1.kicad_pcb  (721924 bytes)
  board 99.9998 x 64.9986 mm | Edge.Cuts 67 segments, 25 arcs
  footprints 391 (209 TOP / 182 BOTTOM), 0 with no .emp body polygon
  vias 419 | PIN holes 47 attached to 25 components, 0 unmatched
  copper rings 318/466 holes matched a F_Cu/B_Cu flash within 2 mil
```

**两处必须记住的降级**：
- `318/466`：148 个孔在配对的 2.5 版 Gerber 里找不到 flash（2.6.1 的贴装 vs 2.5 的
  制板文件，本就差一代），这些孔用默认环宽 32 mil 或 drill+2×0.15 mm 兜底 —— **环宽
  不是实测值**，DRC 的边距判定要按这条打折看（C-6 已逐条分开处理）。
- `.emp` 只有 57 个 body 多边形，**没有焊盘叠层**。所以焊盘是"孔 + 实测环"重建的
  圆形/环形近似，异形的 SMD 引脚形状丢了（`.emn` 里也没有 SMD 焊盘数据）。

### C-6 DRC：364 条，逐类判断是否影响生产

```
$ kicad-cli pcb drc --severity-all --format json --units mm \
      --output dist/kicad/PSDR_2.6.1-drc.json dist/kicad/PSDR_2.6.1.kicad_pcb
发现 364 条违规项
发现 0 个未连接的项目
保存 DRC 报告到 dist/kicad/PSDR_2.6.1-drc.json
rc=0
```

**不写成"通过"**：364 条真实存在。分类与判断：

| 类型 | 条数 | 级别 | 判断 |
|---|---|---|---|
| `lib_footprint_issues` | 199 | warning | **不影响生产**。391 个封装来自合成，磁盘上没有 `PSDR_PADS` 库；几何已内嵌在 `.kicad_pcb` 里，KiCad/嘉立创EDA 都按内嵌几何渲染。要消警就把封装导成 `.pretty` 并写 `.kicad_pro` 库表，本单没做（超出工单范围）。 |
| `courtyards_overlap` | 135 | error | **转换伪影，不影响生产**。`.emp` 从没有定义 courtyard，是我按 body 外扩 0.25 mm 合成的。RF 密板本来就这样。 |
| `npth_inside_courtyard` | 11 | error | 同上伪影（安装孔/定位孔落进合成 courtyard）。 |
| `pth_inside_courtyard` | 10 | error | 同上伪影。 |
| `copper_edge_clearance` | 9 | error | **需要分开的 5 + 4**，见下。 |

9 条边距逐条与**原始 2.5 Gerber 自身**对测（不经过我的转换器，用已经能复现
安装孔数字的同一套算法）：

| 对象 | KiCad mm | 原始 Gerber mm | 最近原始铜 | 判定 |
|---|---|---|---|---|
| M1 焊盘 1 | 0.1486 | **0.1487** | F_Cu ap151 flash 0.2244 in | 原设计如此 |
| M2 焊盘 1 | 0.1500 | **0.1500** | F_Cu ap151 flash | 原设计如此 |
| M3 焊盘 1 | 0.1500 | **0.1500** | F_Cu ap151 flash | 原设计如此 |
| USB 焊盘 1 | 0.4074 | **0.4074** | F_Cu ap72 flash 0.0620 in | 原设计如此 |
| USB 焊盘 4 | 0.4090 | **0.4089** | F_Cu ap72 flash | 原设计如此 |
| CW1 焊盘 1 | 0.3410 | — | **0.30 mm 内无原始铜** | 无法证实，环宽是兜底值 |
| CW1 焊盘 2 | 0.0000 | — | 同上 | 同上 |
| CW2 焊盘 1 | 0.0000 | — | 同上 | 同上 |
| CW2 焊盘 2 | 0.3411 | — | 同上 | 同上 |

- 前 5 条：**KiCad 报的数与原始 Gerber 量出的数在 0.0001 mm 内相同** ⇒ 转换器没造
  出边距问题，这 5 条是 2016 年原板属性。M1–M3 是 `MH3M_PLATED`（3 mm 安装孔）
  外围 5.70 mm 铜环距板边 0.15 mm；USB 是 `MICROUSB_H12192CT-ND` 固定孔。
  对生产：0.15 mm 已低于嘉立创 0.2 mm 的常规铜到板边要求，但这是**孔环**不是走线，
  且安装孔环本来就要贴边；下单时按"金属化安装孔、允许贴边"处理即可，不需要改板。
- 后 4 条：`CW1`/`CW2` = `MORSE_PADDLE_CONTACTS`（电键插孔，rot=315°/135°），落在
  板框右侧**内凹缺口**带（x>88.3 mm，y 16–26 mm）里。2.5 版 Gerber 在那儿根本没有铜，
  所以 0.0000 mm 是我给的兜底环跨过了板框，**不能当成原板缺陷上报**；要定论得拿
  2.6.1 的制板文件——它在 `PSDR_Rebuild` 的 `468dc41` 里确实存在
  （`Hardware/Gerbers/PSDR261 Main Board/`：钻孔 + GTO/GTS/GTL/G1/G2/GBL/GBS/GBO +
  fabnotes，共 10 个文件），只是 `master` 与任务 C 用的 `dist/gerber/` 里没有（见 §C-10）。

板框本身也确认了非线性：右侧在 y≈16–26 mm 处退到 x=88.3 mm，另有 100 mm 边界上的
多段台阶 + 25 段圆弧 —— 所以"板子 100×65 mm"只是外接矩形。

原始 Gerber 里铜离板边的总体事实（同一套量法，全板扫描）：F_Cu 有 **740** 个特征端点
在 0.50 mm 以内、B_Cu 有 **718** 个，其中 F_Cu 4 个 / B_Cu 9 个端点的铜越过最近的轮廓线
0.14–0.88 mm。这块板本来就大量把铜送到板边（边缘 SMA 连接器 + 电键插孔）。

### C-7 BOM 停产件核对（工单第 4 步）

工单要求核对两条。结论：**位号归属对，"替代件"的措辞需要修正 —— 两个"替代件"
都不是替代，而是本来就在 BOM 里的那个东西。**

原始 BOM（`Hardware/BOMs/PSDR_2.6.1/PSDR2.6.1_BOM.xls`，唯一 sheet `PSDR25BOM`）
用 LibreOffice 权威转 CSV 后的真实行：

```
Item 77 | Ref Des U304        | Qty 1 | Type MMIC-AMP_HMC482ST   | Vendor Digikey | Vendor Part # 599-1068-1-ND
        | 备注列: "Name mismatch is okay, The Digikey part # is the correct part"
Item 79 | Ref Des U16,24,30   | Qty 3 | Type RF_DPDT_MASWSS0129TR| Vendor Digikey | Vendor Part # 1465-1374-1-ND
```

四条独立证据：

1. **位号对上**：`psdr26.emn` 里 U304 = `MMIC-AMP-HMC482ST`（BOTTOM, rot=270），
   U16/U24/U30 都是 `RF_DPDT_MASWSS0129TR`（TOP, rot=0）。与工单的
   "RF 放大器 U304"、"RF DPDT 开关 U16/U24/U30" 完全一致。
2. **`.emp` 里有 `RF_DPDT_MASWSS0129TR` 这个 decal** ⇒ 2.6.1 设计里 MASWSS0129
   就是**已定案的原厂件**，不是"替代品"。工单写的 `MASWSS0129TR-3000` 与
   `MASWSS0129TR` 是**同一颗 MACOM/Peregrine GaAs pHEMT MMIC DPDT 开关**，
   `-3000` 是整盘（工厂包装 3000）订购码，工单列的 Richardson 是分销商。
   ⇒ **改的是采购渠道，不是料**。
3. **`599-1068-1-ND` 的真相**：`.xls` 里这一行的超链接是
   `https://www.digikey.com/product-detail/en/rfmd/SXB-2089Z/599-1068-1-ND/937042`
   ⇒ 这个 Digi-Key 料号指向的就是 **RFMD `SXB-2089Z`**，也就是工单说的"替代件"。
    designer 自己在 2.5 版就注了 `*Not the part listed in Type`，2.6/2.6.1 又注了
   `Name mismatch is okay, The Digikey part # is the correct part`。
   ⇒ **footprint/Type 名（HMC482ST，Hittite）是过期标签，实际买的从始至终是 SXB-2089Z**。
   真正要做的动作是把 BOM 的 `Mfg Part #` 补成 `SXB-2089Z` 并把 decal 改名，
   而不是"找个替代件"。
4. **`Mfg` / `Mfg Part #` 两列在 89 行里只有 5 行有值** —— 整张 BOM 是按 Digi-Key
   料号索引的，**没有原厂料号**。这才是这块板最大的采购风险：SKU 一失效就没有
   可搜索的料号。嘉立创/立创商城是按 MPN 索引的，**下单前必须把 89 行全部补出 MPN**。
   `Vendor` 列：Digikey 87 / Coilcraft 1 / Mini-Circuits 1。

**"停产"这个判据本身，本机没能独立验证**：`OctopartBOM.csv` 85 个有数据的行里
**只有 2 行**丢光了 Manufacturer/MPN/URL，正是这两个 SKU（强相关，但不是官方生命周期
状态）；直接查 Digi-Key 两个产品页都返回 `403 Forbidden`。所以工单的"DigiKey 停产"
当作**上游已核实的前提**接受，我不复述为实测结论。

#### C-7 补充（2026-10-31）：BOM ↔ 板子逐位号对账

工单没要求这一步，但它是"能不能照单买齐"的前提，也是"BOM 不匹配"这个印象的
可复核版本。方法：LibreOffice 转 CSV/HTML → 展开 Ref Des 里的省略前缀（`C3,10,13…`）
与区间（`238-240`、`R174-176`、`R97,-99`）→ 与 `.asc` 的 `*PART*` 段逐位号求差集。

```
BOM(2.6.1) 89 item 行 / 展开 324 个位号 / 去重 322 / 重复登记 R6、R14
板上 *PART* 段        391 个器件 = 342 常规位号 + 49 个网名式位号（+、GND、LO1P…）
板上常规 342 − BOM 322 = 20 个不在 BOM
BOM 有、板上没有      = 0 个（无幽灵行）
```

20 个里 19 个是机械件，**1 个是真漏**：

| decal | 数量 | 位号 | 性质 |
|---|---|---|---|
| `FIDUCIAL_1MM` | 6 | F1–F6 | 光学基准点 |
| `MH3M` | 4 | M4–M7 | 安装孔（非金属化） |
| `MH3M_PLATED` | 3 | M1–M3 | 安装孔（金属化） |
| `MH_80M` | 2 | X1/X2 | 80 mil 安装孔 |
| `MORSE_PADDLE_CONTACTS` | 2 | CW1/CW2 | 摩斯电键触点 |
| `PAD_1MM` | 2 | DAC1/DAC2 | 1 mm 测试焊盘 |
| `RES_0603` | 1 | **R98** | **真缺件** |

R98 有实际电路作用：网表里一端接 D101（红 LED）阳极网 `$$$10534`，另一端接
`LED_2`（U121 PE13）。BOM 第 52 行写的是 `R97,-99`（qty 3），展开只有 R97+R99 ——
**这里的 "–" 本意应是区间 `R97-99`**，于是红 LED 的限流电阻没有独立行。

**R6 / R14 重复登记**：第 41 行 Ref Des 仍写 `R6,14,268`、qty 由 2.6 的 3 改成 1，
但第 42/43 行又各自新增 `R14`（68R）、`R6`（180R）。41 行本该只剩 R268；
按 qty 求和会多算 2 个 0603。

**BOM 自带图例就是"改了什么"的权威答案**：`.xls` 首行写明 `Yellow is changed from 2.6`
/ `Red is something to take note of`。`soffice --convert-to 'html:HTML (StarCalc)'`
导出后填充色保留（`bgcolor="#FFFF00"` 69 格，红系 `#FF3333`/`#FF3300`/`#FF0000` 共 48 格），
黄行 + 逐行 diff 互相印证，2.6 → 2.6.1 的实际改动只有 5 处：

1. 第 53 行 R164：`270K` / `541-270KHCT-ND` → `240K` / `1276-4870-1-ND`
2. 第 42/43 行新增 R14 = 68R、R6 = 180R
3. 第 41 行 qty 3 → 1（对应 R6/R14 拆出去）
4. 第 12 行 C186 qty 1 → 0（不贴）
5. 第 61 行新增 SPEAKER qty 0 / `AS01508AO-3-R`，与第 62 行 `668-1513-ND` 二选一
6. 列结构：2.6 是 18 列（含 `Qty to Order`），2.6.1 删到 16 列 —— **下单数量列没了**

红系"留意"行：C307/C320 = `OPEN`；R72/R79 = `DNS`；EARPHONE、SPEAKER、
Battery connector、Encoder 四行为 `Buy but do not populate`；L39/L82 走 Coilcraft、
L41/L81 走 Mini-Circuits 直供（非 Digi-Key）。

**两版 BOM 的位号集合完全相同**（322 个，2.6 无重复）⇒ 上面那 20 个缺口是 2.6 就带过来的，
不是 2.6.1 新漏的。

#### C-7 补充二（M1，2026-11-01）：BOM 补丁已作为上游 PR #18 交付

`#14` 的维护者 jeffersonbenson 回了 "Please do!"，补丁按上面三条做：

| 文件 | 单元格 | 原值 | 新值 | 依据 |
|---|---|---|---|---|
| `PSDR2.6.1_BOM.xls` | 项 41（R45C2） | `R6,14,268` | `R268` | 项 42/43 已单列 R14(68R)/R6(180R)，41 行 qty=1 |
| `PSDR2.6.1_BOM.xls` | 项 52（R56C2） | `R97,-99` | `R97-99` | qty=3；按原写法只能读出 R97+R99，缺 R98 |
| `PSDR2.6_BOM.xls` | 项 50（R54C2） | `R97,-99` | `R97-99` | 同一笔误；该行 qty 与 Run Tot 本就按 3 颗算 |

- R98 是真器件：`Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf` 里
  R97/R98/R99 并排三颗 255R（LED_WHITE/LED_2/LED_3 对 D100/D101/D102）；
  BOM 项 24 写 D101 = `LED_0603 RED`；网表 `R98.1 ↔ D101.1`、
  `R98.2 ↔ LED_2/U121.43 (PE13)`。
- 补丁后的对账：展开 323 个常规位号、**0 重复**、**0 幽灵行**，板上没有 BOM
  行的只剩 19 个机械件（M1–M7、X1/X2、F1–F6、CW1/CW2、DAC1/DAC2）；
  补前是 322 唯一 + R6/R14 各两次 + R98 缺失（20 个没有行）。
- 文件完整性：LibreOffice 重存，逐单元格比对（文本/公式/缓存值/背景色/字体/
  行高/列宽）只有上述单元格不同，列宽因 .xls 单位换算窄 0.01–0.02 mm；
  CSV 导出 diff 也只有这两/三行。
- 交付：分支 `upstream-pr/bom-2.6.1-refdes-fix` @ `9c3ca93`（基于上游
  `master` 45acd0f），远端 blob `886c3d3…`/`04b470d…` 与本地逐位一致；
  **PR https://github.com/MichaelRColton/PSDR/pull/18**（正文含 AI 辅助声明
  与复现口径）。2.6 的历史 BOM 一并修了位号笔误（未改数量）。

### C-8 SKIP 清单（转不了的如实标，不假装成功）

| # | 项 | 原因（可复核） |
|---|---|---|
| SKIP-1 | `.kicad_sch` 图形化原理图 | **已由 §C-12 解除**（2026-10-31）。① 2.6.1 的 **10 页原理图 PDF** 与 **PADS Layout ASCII** 已复制进本分支（`Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`、`Hardware/PSDR.asc`）；② 从 `.asc` 提取的网表 391 器件 / 278 网 / 1132 引脚通过四重校验（§C-11）；③ 已生成根图 + 9 张子图 + 57 个符号，网表划分 278/278 一致、ERC 0 error、几何重合 0 冲突（§C-12）。它仍是**连通性模型**（靠全局标签连接，不是按 PDF 重画走线），"看图"以 2016 PDF 为准。 |
| SKIP-2 | `Hardware/Enclosure/` SolidWorks 壳体/装配 | `.SLDPRT`/`.SLDASM`，嘉立创EDA 无对应能力，工单也明确要求不要试图转换。 |
| SKIP-3 | `.sch`/`.pcb` 源文件 | 工单称 Eagle，实测是 **PADS Logic / PADS Layout 二进制**（`Hardware/README.md`："Schematics and Board layout files are for Mentorgraphics PADS"；头 `00 fe 0d 00` / `00 ff 26 20`）。KiCad 10.0.6 的 Eagle 插件报 `XML 解析错误：'not well-formed'` 却 **exit 0**（假成功）——因为它不是 Eagle XML。要转这两个二进制必须先有 PADS Logic/Layout 本体，本机没有；**但 2.6.1 的 PADS Layout ASCII（`Hardware/PSDR.asc`）已在库里，二进制不再阻塞网表**，只影响"图形原理图"（§C-11）。 |
| SKIP-4 | 铜走线 / 内层 / 网络 | **已由 §C-13 解除**（2026-11-01）。`.emn` 无 `TRACE` 段，所以 C-5 的 `PSDR_2.6.1.kicad_pcb` 只有 2 个铜层；另生成的 `PSDR_2.6.1_pcb_spike_full.kicad_pcb` 从 `Hardware/PSDR.asc` 的 `*ROUTE*` 取铜，是 **4 层 / 5034 段走线 / 22 段弧 / 419 个过孔 / 278 网**，与 2.6.1 原始 Gerber 逐 flash、逐钻孔对过。当时未覆盖的**铺铜、真实板框、丝印已由 §C-14 补齐**（12 个铺铜区 / 67 段板框 / 双向丝印对账）。 |
| SKIP-5 | 器件真实焊盘形状 | **已由 §C-13 解除**（2026-11-01）。pad stack 改从 `Hardware/PSDR.asc` 的 `*PARTDECAL*` 读，1194 个焊盘全部来自 decal（圆/方/圆角矩形/椭圆、旋转角、钻孔）。KiCad 10 的内层铜连接限制见 §C-13 的 pad-type 表。 |

**制板用哪套（2026-11-01 第二次更正）**：生产必须用 **2.6.1 的原始 Gerber**，
即上游 `468dc41` 的 `Hardware/Gerbers/PSDR261 Main Board/`（本分支没有复制进仓，
本轮提取到仓外 `D:\my git\PSDR-build-artifacts\gerber261\` 作对账基准，见 §C-13）。
`dist/gerber/` 是 **2.5** 主板的 Gerber，不是这块板；
`PSDR_2.6.1_pcb_spike_full.kicad_pcb` 现在有 4 层铜、12 个铺铜区、真实板框和丝印
（§C-14），与源 Gerber 逐 flash、逐钻孔对齐（§C-16），但 795 条 DRC 违规
（分类与处置见 §C-16）意味着它仍只是可编辑参考，不能直接投产。

### C-9 本轮新踩的坑（工单未覆盖）

1. `python` / `python3` 是 WindowsApps 存根，直接执行报 `Python was not found`；
   真解释器在 `C:\Users\ASUS\python-sdk\python3.13.2\python.exe`（从 `PATH` 里的
   `…\Scripts` 反推出来的），本轮所有 Python 都用绝对路径。
2. **KiCad 的 PADS 导入器静默返回空板并报成功**（C-3）。同理 Eagle 导入器
   打印错误但 `exit 0`。**"rc=0 不等于导入了东西"**，必须回读板子统计。
3. 圆弧 bug 定位法：把 `.emn` 的 25 段弧与原始 Gerber 的原生弧（给 `gerbparse.py`
   新加的 `Gerber.arcs`）配对，而不是靠肉眼看图 —— 第一次"两个符号都错 2.4 mm"
   就是因为没有原生弧可对。
4. `K(rot)` vs `K(-rot)`：454 对 / 12 错的分布非常有欺骗性（rot=0 时两者相同）。
5. 在 PADS 帧算完圆心再翻 Y；先翻 Y 再算圆心会得到 102.54 × 67.54 mm 的"放大板框"。
6. KiCad 10 的 s-表达式语法与 8 不同：`(footprint "LIB:NAME")`、`(property "Reference" …)`、
   `gr_arc` 要 `(start)(mid)(end)(stroke)`；手写的头文件在 line 91 报
   `Expecting symbol|number. Got '('` —— 正确写法抄自
   `share/kicad/demos/stickhub/StickHub.kicad_pcb`，最终固化成
   `tools/kicad_board_header.kicad_pcb`。
7. `kicad-cli pcb export pos -f ascii` 不认 `-f`，要用 `--format ascii`；且
   `attr … exclude_from_pos_files` 会把探针从位置文件里悄悄剔除。
8. DRC 的中文 `description` 在 GBK 控制台下显示为乱码 —— **文件本身是合法 UTF-8**
   （`decode('utf-8')` 不报错），用 `PYTHONIOENCODING=utf-8` 才看得对。别误判成
   KiCad 写坏了编码。
9. 读 `.xls`：本机没 `xlrd`；手撸 BIFF8 在一条带 rich-text 选项字节的 SST 字符串上
   失去同步（**已删除这个半成品工具**）。正解是 LibreOffice 无头转换，一条命令：
   ```
   "/c/Program Files/LibreOffice/program/soffice.exe" --headless --norestore \
     --convert-to 'csv:Text - txt - csv (StarCalc):44,34,76,1,,0,false,true,true,false,false,-1' \
     --outdir <dir> <file.xls>
   ```
   （最后的 `-1` = 每个 sheet 出一个文件。）
10. 转换器依赖 `%TEMP%` 里的模板文件（C-1）：**临时文件当输入 = 不可复现**，已入库。

### C-10 原理图与网表复核（2026-10-31 二次修正）

上一版 §C-10 有两处判断是错的，先认：

1. **"唯一可读的 PDF 是 2014 旧版"错**。`master` 上 `Hardware/PSDR Schematic.pdf`
   确实是 2014 的 8 页旧图，但 `git log --all` 显示 `PSDR_Rebuild` 的
   **`468dc41`（2016-07-31，"PSDR 2.6.1 PCB complete"）** 里还有一份
   **10 页、346,496 B 的 2.6.1 原理图 PDF**（`CreationDate` 2016-07-26，
   文字层含 `U121` / `U185` / `Si5338` / `HMC1023` / `STM32F746`）。
   `CreationDate` 只说明文档创建时间，**不能当版本判据**；判版本要看内容和全分支历史。
2. **"当前版本的原理图只在 PADS 二进制里"也错**。同一提交里还有
   `Hardware/PSDR.asc`——**PADS Layout 的 ASCII 设计数据库**
   （1,641,124 B，头 `!PADS-POWERPCB-V9.5-BASIC! DESIGN DATABASE ASCII FILE 1.0`），
   `*PARTTYPE*` / `*PART*` / `*ROUTE*` 三段直接给出引脚表、位号表和连接关系。
   它不是图形原理图，但它是**机器可读、可逐脚对账的 2.6.1 网表来源**。

现在的事实表：

| 文件 | 位置 | 是什么 | 版本证据 |
|---|---|---|---|
| `Hardware/PSDR Schematic.pdf` | `master` / 本分支 | 8 页，317,207 B | 2014-10-28，**另一版设计**（见下） |
| `Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf` | 本分支新增（源 `468dc41`） | 10 页，346,496 B | `CreationDate` 2016-07-26；含 2.6.1 器件 |
| `Hardware/PSDR.sch` | 本分支 | PADS Logic 二进制，525,874 B | 2016-05-07 提交；开源工具读不了 |
| `Hardware/PSDR.asc` | 本分支新增（源 `468dc41`） | **PADS Layout ASCII 1.0**，1,641,124 B | `468dc41`，2.6.1 PCB complete |
| `Hardware/BOMs/PSDR_2.6.1/psdr26.emn`/`.emp` | 本分支 | PADS IDX ASCII | 只有 `BOARD_OUTLINE`/`DRILLED_HOLES`/`PLACEMENT`，无 `NETS` |

**结论：网表问题已解决**（§C-11）。剩下的只有"图形化原理图"（`.kicad_sch`）：
现在既不需要从 PDF 反推连接，也不需要逆 PADS 二进制——连接关系有权威来源，
图形照 2.6.1 PDF 的 10 页版面生成即可。

**2026-10-31 更正**：上一版此处写"2014 旧版比 2.6.1 少 16 个位号"，这句站不住，
撤掉。用 PyMuPDF 提取文本层、正则 `\b([A-Z]{1,3}\d{1,4})\b` 取位号令牌实测：
2014 版 366 个、2016 版 400 个，**只有 156 个重合**（2014 独有 210、2016 独有 244）。
`U121`（MCU）、`U185`（GPS）、`U241`（Si5338）、`U287`（可变滤波）、`U304`（RF 放大）、
`J153`、`CW1`、`X1`、`C282`、`R310` 在 2014 版里**完全不存在**；2014 版电容编号
上限 `C168`，2.6.1 到 `C326`。⇒ 2014 版是**另一版更早的设计**，不是"2.6.1 少几个件"。
（令牌数依赖正则，只作量级参考；"某位号是否存在"是精确匹配，结论可靠。）

两份新增文件的字节与来源一致（`git show 468dc41:<path> | sha256sum` 与落盘文件相同）：

```
d479afe3238df038d76debf22cf8fdd382603fba2996bec8c2c2a3fb4204f231  Hardware/PSDR.asc
c366775af458b3a8b9cb220c4ae29f90b6f25961efc0b1fff2518d61f964b699  Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf
```

### C-11 从 PADS Layout ASCII 提取 2.6.1 网表（2026-10-31）

**输入**：`Hardware/PSDR.asc`。**工具**：`tools/pads_asc_netlist.py`（只依赖标准库）。
**产物**：`dist/netlist/PSDR_2.6.1_netlist.csv`（1132 行，列
`net,refdes,pin,pin_name,part_type`）与同名 `.json`（含未连接引脚表）。

三段各管一件事：

- `*PARTTYPE*`：每种封装的引脚表（`1.0.U.NC1` = 引脚 1、类型 U、名 NC1）；
- `*PART*`：位号 → 封装（`U287  VARIABLE_FILTER_HMC1023 …`）；
- `*ROUTE*`：每个 `*SIGNAL*` 是**一个连通簇**，簇内每行是两列 `位号.引脚`；
  同一网络被铜分成几块就有几个簇，取并集即该网全部引脚。

实测：

```
$ python tools/pads_asc_netlist.py Hardware/PSDR.asc \
      --csv dist/netlist/PSDR_2.6.1_netlist.csv \
      --json dist/netlist/PSDR_2.6.1_netlist.json
parts            391
part types       57
nets             278
signal clusters  364 (18 nets with >1 island)
connected pins   1132
unconnected pins 41
placed pins      1173
problems         0
```

网络大小分布：2 脚 169 个、3 脚 74 个、4 脚 13 个、5 脚 7 个、6 脚 3 个、7 脚 3 个，
其余 9/10/11/13/23/50/58/261 脚各 1–2 个（GND 261、+3V3 58、+3V3_CPU 50、
HALF_VCC 23）。**没有 1 脚网络**，所以不存在"孤立焊盘被当成了网"。

四重校验（都是独立证据，不是同一份数据换个说法）：

1. **位号集合**：391/391 与 `psdr26.emn` 的 placement 位号完全相同，双向差集为空。
2. **网名 vs 2.6.1 PDF**：132 个命名网络里 **131 个**能在 PDF 文字层找到
   （把 `/`、`-`、`\` 归一后比对），只差 `BOOST_LOOP`（图上没有可提取的标签）；
   另 146 个是 `$$$NNNNN` 自动名，图上本来就不显示。反向也查了：PDF 里 6.7 pt 的
   网标级文字，除标题/注释/封装名外全能在网表里找到（`SWCLK`/`SWDIO` 是 PDF 把
   `JTCK/SWCLK`、`JTMS/SWDIO` 拆成了两段），**没有"图上有、网表没有"的网络**。
3. **固件引脚表**：`Source/src/hal.c` 的 28 条 `Gpio_Pin` 定义，按"端口+脚号"
   在 PCB 里查找，**27 条落在同一网络**（其中 3 条只是取名不同：
   `MIC_SWITCH`→`MIC_SELECT`、`PREAMP_POWER`→`PREAMP_SHTDWN`、
   `FILTER_GAIN_POT_SCLK`→`FILTER/GAIN_POT_CLK`；`\EARPHONE_INSERTED`、
   `FLIP-FLOP_POWER`、`AUDIO_AMP_\SHDN` 的转义与连字符同样对上）。
4. **设计者自己在图上的注释**：2.6.1 PDF 第 3 页 Si5338 旁写
   "IN5/6: Feedback. **Leave 5 unconnected and 6 grounded**"；
   网表里 U241 pin 5 未连接、pin 6 在 GND，逐条对上。

**一条实质冲突（不是解析问题）**：

| 信号 | 固件 `Source/src/hal.c:169` | 2.6.1 PCB / PDF |
|---|---|---|
| `GPS_RESET` | `GPIOE, GPIO_PIN_15`（注释还写着 `//2.5`） | MCU **PD15（pin 62）**；PE15（pin 45）走 `LED_3` → R99 |

三份独立证据都指向 PD15：PCB 网表（`GPS_RESET` = `GPSR.1` + `U121.62` + `U185.8`）、
封装引脚名（pin 62 = `PD15_T4-4_*`）、PDF 第 2 页（引脚号 62 旁的网标就是
`GPS_RESET`）。`git blame` 显示这行自 2016-04-18 起没再改过，而 2.6.1 PCB 是
2016-07-31 完成的。⇒ 在 2.6.1 板上按现在的固件跑，`GPS_RESET` 的写操作会落到
`LED_3`（PE15），GPS 模块的复位脚（PD15）没有任何代码驱动。
**只记录，不改**（工单护栏：不碰固件/射频逻辑）。

**41 个未连接引脚**：F1–F6 基准点、M4–M7 安装孔、X1/X2 晶振外壳、L39/L82 的
pin 5（半孔）、U185 的 10 个 NC + VOUT、U241 的 7 个（IN3/IN5/INTR/CLK1B/CLK2B/
CLK3A/CLK3B）、U253/U260 的 pin 7（NC）、U287 VBG、U314 VREF、U15 HB、
U172 pin 4（NC）、U30 pin 6、J153 pin 6、EARPHONE pin 12。
其中 `VBG`/`VREF`/`HB` 是模拟偏置脚，**是否该外接电容要对照数据手册再定**
（本轮不下结论）；其余都有封装层面的 NC/机械解释。

**同提交里还有 2.6.1 真正的 4 层 Gerber**：`Hardware/Gerbers/PSDR261 Main Board/`
（钻孔 + GTO/GTS/GTL/G1/G2/GBL/GBS/GBO + fabnotes），`master` 上没有。
那批文件只存在于上游 `468dc41`，本分支**没有复制进仓**；本轮提取到仓外
`D:\my git\PSDR-build-artifacts\gerber261\Hardware\Gerbers\PSDR261 Main Board\`，
作为 §C-13 的对账基准（flash 与钻孔的位置真值）。任务 C 的 `dist/gerber/`
用的是 2.5 主板的原始 Gerber；**要出 2.6.1 生产包必须回到上游 `468dc41`
取这批 Gerber**，不用两块 KiCad 板。

本轮 PDF 侧的工具（poppler 24.02、PyMuPDF 1.28.2）和中间脚本留在
`D:\my git\PSDR-build-artifacts\sch_261\`、`sch_preview\`（不入仓）。

---

### C-12 由网表 + 2016 PDF 版面生成 KiCad 原理图（2026-10-31）

**先确认前提，避免做无用功**：上游 `PSDR_Rebuild`/`PSDR_F7`/`PSDR_F7_DMA`
的 `468dc41` 上同时存在 2.6.1 的 PADS Layout ASCII（`Hardware/PSDR.asc`）
和 10 页原理图 PDF——上游路径是 `Hardware/PSDR Schematic.pdf`（同一 blob
`5390527`，346496 B），本分支按日期重命名为
`Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`。注意 `master` 上同名文件
是 **2014 的 8 页旧版**（blob `bdf02d2`，317207 B），不是这一份。所以
①不需要装 PADS 二进制解析器，②"唯一可读的是旧版 PDF"不成立，
③.emn/IDX 里只有 `BOARD_OUTLINE`/`DRILLED_HOLES`/`PLACEMENT`，没有 `NETS`。
既然这一轮拿到了源，就不开 issue、也不提"补 PDF"的 PR（那是重复文件）。
上游真正缺的是 **KiCad 原生原理图**，这是本节做的事。

**输入三份，各管一件事**：

| 输入 | 提供 |
|---|---|
| `dist/netlist/PSDR_2.6.1_netlist.json`（§C-11） | 谁连谁 |
| PDF 文字层的 refdes 坐标 | 谁在哪一页、页内大致位置 |
| `dist/kicad/PSDR_2.6.1.kicad_pcb` | 位号全集 + 封装名 |

生成器 `tools/pads_asc_to_kicad.py`（标准库，无第三方依赖）。

**连接模型：每脚一个全局标签，不画线。** 每个引脚端点放一个与 PADS
网名同名的 `global_label`（1.0 mm 字号），未连接引脚放 `no_connect`。
理由：PDF 的走线是版面艺术品，重画既没有信息增益、又没法自动校验；
全局标签跨页生效，网表可以机检。代价是读图靠标签而不是靠线，见文末局限。

**符号**：按 `*PARTTYPE*` 引脚表生成 57 个矩形体符号，引脚左右各半、1 脚件
放右侧、间距 2.54 mm、引脚长 3.81 mm。符号坐标 Y 向上、原理图 Y 向下，
所以绝对引脚位置 = `(ox + px, oy - py)`。

**版面**：每张子图对应 PDF 一页，纸面直接取 PDF 页面尺寸
1584×1224 pt = 558.8×431.8 mm；根图 A2（594×420 mm），9 张层次图排 3×3。

```
$ python tools/pads_asc_to_kicad.py --asc Hardware/PSDR.asc \
      --pdf Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf \
      --pcb dist/kicad/PSDR_2.6.1.kicad_pcb --out dist/kicad
parts            391
part types       57
nets             278
connected pins   1132
pdf pages used   [2, 3, 4, 5, 6, 7, 8, 9, 10]
ambiguous refs   11 ['+', '-', '1PPS', 'CLK', 'DAC1', 'DAC2', 'GND', 'LIPO', 'NRST', 'SCL', 'SDA']
unplaced refs    []
page  parts  types  body-overlaps  file
   2     57     17             0  PSDR_2.6.1-p02.kicad_sch
   3     44      7             0  PSDR_2.6.1-p03.kicad_sch
   4     33      9             0  PSDR_2.6.1-p04.kicad_sch
   5     48      4             0  PSDR_2.6.1-p05.kicad_sch
   6     49     14             0  PSDR_2.6.1-p06.kicad_sch
   7     14      7             0  PSDR_2.6.1-p07.kicad_sch
   8     58     18             0  PSDR_2.6.1-p08.kicad_sch
   9     58     12             0  PSDR_2.6.1-p09.kicad_sch
  10     30      6             0  PSDR_2.6.1-p10.kicad_sch
```

页码→内容：2 MCU/GPS/USB、3 时钟(Si5338)、4 模拟开关/驱动、5 RX/TX 基带、
6 音频/麦克风、7 人机(桨/LED/LCD)、8 电源、9 射频前端、10 可变滤波器。
第 1 页 PDF 只有注释没有器件，不建子图。

**四道校验，都是独立证据**：

1. **网表对账**（能不能用）：

```
$ kicad-cli sch export netlist --format kicadxml \
      --output psdr261_kicad.xml dist/kicad/PSDR_2.6.1.kicad_sch
$ python tools/kicad_netlist_compare.py \
      --pads dist/netlist/PSDR_2.6.1_netlist.json --kicad psdr261_kicad.xml
pads nets            278
kicad nets (raw)     319
kicad nets (in pads) 278
pads connected pins  1132
kicad covered pins   1132
components           391
identical nets       278
only in pads         0
only in kicad        0
pins missing         0
pins in >1 net       0
RESULT: partitions identical
```

   比的是"引脚集合的划分"而不是网名顺序：278 个网逐个比对成员集合，
   278 个完全相同；1132 个已连引脚零遗漏。`kicad nets (raw) 319` 多出的
   41 个就是 no-connect 单脚网。网名 276/278 逐字符相同，另 2 个只差
   PADS 的上划线转义（`AUDIO_AMP_\SHDN` ↔ `AUDIO_AMP_~{SHDN}`、
   `\EARPHONE_INSERTED` ↔ `~{EARPHONE_INSERTED}`）。

2. **几何重合**（会不会连错）：`tools/kicad_sch_geomcheck.py` 把每个文件的
   引脚绝对坐标与标签锚点算出来找重合，10 个文件 **connection points 1173
   （= 1132 标签 + 41 no-connect）、conflicts 0**。（这一步是必须的：KiCad 里
   两个引脚落在同一点就是短路，而网表导出会照单全收。）

3. **ERC**：`kicad-cli sch erc --severity-all` → **0 error、391 warning**，
   391 条全是 `[footprint_link_issues] 当前配置中不包含封装库 'PSDR_PADS'`。
   这是预期的：封装数据内嵌在 `.kicad_pcb` 里，没有单独导出 .pretty 库。

4. **能解析、能升级**：kiutils 解析 10 个原理图（根图 9 张层次图；子图
   器件 57/44/33/48/49/14/58/58/30 = 391，全局标签 238/111/122/104/122/38/
   118/164/115 = 1132，no-connect 41）与 57 符号的 `.kicad_sym`；
   `kicad-cli sym upgrade` 报"符号库未更新"（已是当前格式），rc=0。

**三条踩过的坑（工单未覆盖）**：

1. **短桩 T 型短路**：最初在每脚引出 2.54 mm 短桩再放标签，相邻器件的
   桩端点会重合，6 个网被并成一个（GND、+3V3、+3V3_CPU、+5V_BOOST、
   `$$$14035`、`$$$19436`）。改成标签直接落在引脚端点后仍剩 5 个——这次是
   **两个相邻 2 脚元件本体被摆到引脚尖重合**（如 C119.2 与 C120.1 同在
   (370.425, 248.751)，一个 GND 一个 +3V3_CPU）。最终在布局的 relax() 里
   把碰撞包络从"本体宽度"扩到 `w/2 + 引脚长 + 0.5`，重生成后 0 重合。
   结论：**靠网表对账抓不住短路**，必须先做几何重合检查，否则两个网被
   合并后导出端看到的是"一个更大的网"，只在划分比对里表现为 2 个网缺失。
2. **上划线只转义了首字母**：PADS 用 `\WORD` 表示整词上划线，最初的正则
   只包住第一个字符（`AUDIO_AMP_~{S}HDN`）。改成整词 `~{WORD}`。
3. **多行文本要写 `\n` 转义**：根图注释一长条被页边裁掉。esc() 补上
   换行→`\n` 转义并手动分三行；同时把根图从 A3 换成 A2，因为 A3 的 3×3
   网格会压到右下角标题栏上。

**局限（如实列出，不假装是重画的图）**：

- 这是**连通性模型**：引脚之间没有导线，靠同名全局标签连接；原图的走线
  形状、器件符号外观、旁注都不在其中。要"看图"仍以 2016 PDF 为准。
- 11 个 1 脚测试焊盘的位号（`+` `-` `1PPS` `CLK` `DAC1` `DAC2` `GND`
  `LIPO` `NRST` `SCL` `SDA`）在 PDF 文字层里有多个同名候选，无法唯一
  定位，统一摆在各页底部条带；**连通性不受影响**（网表按位号取，不按坐标）。
- 封装链接指向未随仓发布的 `PSDR_PADS` 库，所以 ERC 恒有 391 条 warning。
- 没做：层次图的 sheet pin（全局标签已跨页，不需要）；按 PDF 重绘走线。

**产物**（`dist/kicad/`，合计 2137579 字节）：

```
PSDR_2.6.1.kicad_sch        6318 字节   根图，A2，9 张层次图
PSDR_2.6.1-p02..p10.kicad_sch        子图 9 张，合计 1042766 字节
PSDR_2.6.1.kicad_sym      133244 字节   57 个符号
PSDR_2.6.1.kicad_pro        1139 字节   工程文件（含 sheet 列表）
sym-lib-table                167 字节   ${KIPRJMOD} 相对路径
```

（`dist/kicad/` 里另有上一轮生成的 `PSDR_2.6.1.kicad_pcb` 721924 字节、
`.kicad_prl`、`-drc.json`，未变。）

新增工具：`tools/pads_asc_to_kicad.py`（生成器）、
`tools/kicad_netlist_compare.py`（网表划分比对）、
`tools/kicad_sch_geomcheck.py`（几何重合检查）。
UUID 用 `uuid5(NAMESPACE_URL, "psdr261/…")` 派生，同一输入重跑输出逐字节
相同，便于审阅 diff。

---

### C-13 从 PADS Layout ASCII 生成四层 KiCad PCB，并与 2.6.1 原始 Gerber 对账（2026-11-01）

**探针先跑通，再扩到全板。** 起点是方向 A 的最小闭环：一个 decal
（`CAP_0603`，焊盘 0.889 × 0.762 mm = 35 × 30 mil）+ 一个信号网络
（`TX-Q_DRIVER_P`：C252.2 → 3 段 B.Cu → 1 个过孔 → 2 段 F.Cu → U4.1）。
闭环成立（样例 DRC 0 断点），同一套解析器直接扩到 `--all`。

**结论**：`dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb` 是
**4 层 / 278 网 / 1194 焊盘 / 5034 段走线 / 22 段弧 / 419 过孔**。
与 2.6.1 原始 Gerber 的对账有两个独立判据：

1. **源侧全覆盖**：原始 Gerber 的每个 D03 flash 都能在 KiCad 同层 plot 的
   0.1 mil 内找到对应 flash，最差 0.0066 mil（0.17 µm）；
2. **数量可解释**：KiCad 侧每层 flash 数正好等于"焊盘在该层的出现次数 + 419 个过孔"，
   六层逐一对平；J170 的孤儿 PAD 20 在 §C-16 修复后不再产生兜底焊盘，
   B.Cu/B.Mask 各减少 1 个 flash，与 F 面完全对称。

**生成与复现**（只依赖 Python 标准库，1196 行：decal 283 + route 261 +
emitter 456 + compare 196）：

```
$ C:/Users/ASUS/python-sdk/python3.13.2/python.exe tools/pads_asc_pcb.py \
      Hardware/PSDR.asc --all -o dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
nets          278
parts         391
pads emitted  1194  (1132 carry a net, 62 do not)
track segments 5034 written (189 zero-length dropped) of 5223 distinct of 9364  layers ['B.Cu', 'F.Cu', 'In1.Cu', 'In2.Cu']
track arcs    22 distinct of 22
vias          419 distinct of 1164
outline       42 lines + 25 arcs, 100.00 x 65.00 mm
pours         12 zones {'In2.Cu': 1, 'In1.Cu': 3, 'F.Cu': 7, 'B.Cu': 1}
silk          162 decal pieces, 1495 board pieces {26: 753, 29: 742}, 4 free texts, 376 refdes labels (15 parts without one)
pad-net conflicts: 0 []
wrote         dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
```

（这是 §C-14 之后的输出；`outline`/`pours`/`silk` 三行是第三批时还没有的。
第三批的输出块记的是 `outline 100.00 x 65.00 mm` 包络矩形。§C-17 之后
`silk` 行变为 `1497 board pieces {26: 754, 29: 743}`，其余不变。）

同一输入重跑，`cmp` 逐字节相同（§C-14 末尾复核）。第一版 UUID 用 `uuid4`，
每次重跑都会改 UUID；现在按发射顺序用 `uuid5` 派生（与 §C-12 的原理图生成器一致）。

**源文件的 7 条约定**（每条都对着 Gerber 或钻孔量过，不是猜的）：

| # | 约定 | 证据 |
|---|---|---|
| 1 | 38100 ASCII 单位 = 1 mil | 板框 y 跨度 97,497,900 单位 = 2559.1 mil；decal 数值全是整数 mil |
| 2 | `*ROUTE*` 记录的 LAYER/WIDTH 属于**从该点出发**的一段；层号 0/65 不是铜层，是"点落在源/目标焊盘里" | `GND C119.2→U121.99`：16 mil 记录在 8 mil 段之前，Gerber 的 16 mil 笔画也正好画在两点之间 |
| 3 | 只有字面量 `STANDARDVIA` 是过孔标记，0x10000 标志位不是 | 按标志位判断会数出 1212 个过孔并凭空造出 48 个；按字面量是 419 个，与钻孔文件的 419 个 14 mil 孔、两面各 419 个 32 mil 圆 flash 完全对应 |
| 4 | `CW`/`CCW` 记录是弧心，不是顶点 | 全文件 22 条，全在 `*ROUTE*`；按顶点读会把弧画成折线且端点错位 |
| 5 | RF/OF 焊盘 = 以端子为中心、SIZE × FINLENGTH、从 decal 局部 +X 转 FINORI 度的矩形；R 是**圆** | C139 两个 35 × 30 mil 阻焊开窗的中心正好落在两个端子的 x 上；M3 的 224.41 mil 在 GTL 里是 `%ADD151C,0.22441*%` 圆，按方读会把 2.85 mm 圆外的走线吞掉 |
| 6 | PADS Y 向上、KiCad 板 Y 向下 ⇒ 每个 y 取负；焊盘角度符号只有 45° 的器件能分辨 | CW1/CW2 的 275 mil 桨形焊盘在 2.6.1 Gerber 里是 -45°；用错符号时两块焊盘沿自身长轴只隔 2.15 mm |
| 7 | decal 的 level -2 是器件所在面，level 0 是反面 | ANT/VNA-IN、VNA-OUT 是 B 面器件，但 pad 4/5 的铜只在 level 0，生成器必须把它们放到 F.Cu |

**KiCad 10.0.6 的焊盘类型，实测五种写法**（先在 4 层测试板上试，再定方案）：

| 写法 | 连到内层走线 | 各层铜 Gerber | 备注 |
|---|---|---|---|
| `smd` 单层 | ✅ | ✅ | 普通贴片 |
| `smd` + `(layers "*.Cu" ...)` | ❌ | ✅ | 铜画对了，但连接图不认 |
| `connect`（多层） | ❌ | ✅ | 同上 |
| `smd` + `(padstack front_inner_back)` | ❌ | ✅ | 同上 |
| `thru_hole` + `(drill 0)` | ✅ | ✅ | 不产生 Excellon 孔，但每个焊盘一条 `through_hole_pad_without_hole` DRC |

全板只有 4 个焊盘（CW1.1/2、CW2.1/2，Morse 桨）需要"无钻孔、贯穿所有铜层"，
用最后一种写法；DRC 里那 4 条 `through_hole_pad_without_hole` 就是它的代价，
是 KiCad 10 的表达上限，不是源数据的问题。

**对账一：flash**。KiCad 的 plot 与钻孔按

```
$ kicad-cli pcb export gerbers --no-protel-ext \
      -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask -o <fab> <board>
$ kicad-cli pcb export drill -o <fab> <board>
$ python tools/kicad_gerber_compare.py --pads "<上游 468dc41 的 PSDR261 Main Board>" \
      --fab <fab> --board PSDR_2.6.1_pcb_spike_full
```

输出（KiCad plot 的坐标 = PADS 坐标 − 1000 mil，两轴同号，无翻转）：

```
layer    pads file                src#  kicad#  dup  worst mil
F_Cu     3 - top-art.GTL           659    1013    0     0.0066
In1_Cu   4 - L2.p.G1               163     439    0     0.0046
In2_Cu   5 - L3.G2                 132     439    0     0.0050
B_Cu     6 - bot-art.GBL           602    1013    0     0.0066
F_Mask   2 - top-sm.GTS            242     594    2     0.0066
B_Mask   7 - bot-sm.GBS            185     594    2     0.0066
```

`dup` 是源文件里的完全重复 flash（PADS 在两层阻焊上各写了两个相同的 62 mil 开窗），
所以判据定成"每个源 flash 都必须被 KiCad flash 覆盖"，允许 KiCad 侧重用同一个点；
否则这两个重复会被误报成缺失。

KiCad 侧的数目逐层可推：

| 层 | KiCad flash | 组成 |
|---|---|---|
| F.Cu | 1013 | 574 个铜在 F.Cu 的 `smd` + 20 个 `thru_hole`（含 4 个 drill 0）+ 419 个过孔 |
| B.Cu | 1013 | 574 + 20 + 419 |
| In1.Cu / In2.Cu | 439 | 20 + 419 |
| F.Mask | 594 | 574 + 20 |
| B.Mask | 594 | 574 + 20 |

`np_thru_hole` 的 26 个孔（§C-16 补上 J170 第 4 个 3.2 mm 孔前是 25 个）
既不出铜（焊盘尺寸 = 钻孔尺寸，零环宽）也不出阻焊窗，与 PADS 一致；
第一次生成时给了 `*.Mask`，KiCad 每面多出 25 个开窗，已改掉（见下）。

**对账二：钻孔**（按直径分组，0.1 mil 容差）：

```
      mm   src# kicad#  missing  extra  worst mil
   0.356    419    419        0      0     0.0457
   0.850      2      2        0      0     0.0000
   0.940      9      9        0      0     0.0000
   0.950      4      4        0      0     0.0403
   1.200     14     14        0      0     0.0372
   2.032      2      2        0      0     0.0000
   3.000      7      7        0      0     0.0608
   3.200      4      4        0      0     0.0346
```

461 个源孔全部对上（461/461）。第三批曾缺 1 个 3.2 mm 孔，根因在生成器的
"只按端子发射焊盘"模型，不在源文件：

- J170 的 decal 把四个 3.2 mm NPTH 安装孔编号为 `PAD 20/21/22/23`，而它的
  端子是 `21/22/23/24`，于是 `PAD 20` 成了没有端子的孤儿，`T24` 没有同名
  焊盘、落到 `PAD 0` 的默认焊盘（2.3 × 1.5 mm）；
- 2.6.1 原始钻孔在 J170 四个角上都有孔，且全板只有 J170 这一个 decal
  同时具备"孤儿焊盘 + 无焊盘端子"，所以 PADS 只能把 `PAD 20` 放在 `T24` 上；
- 生成器原来按端子查同名 pad stack，`T24` 拿不到 `PAD 20`，第 4 个安装孔
  位置就变成了兜底 SMD 焊盘，少一个 3.2 mm 孔。

§C-16 用通用的"孤儿焊盘配最近编号的无焊盘端子"规则修掉了（不是 J170 特例），
修后 4/4 个 3.2 mm 孔对上，B.Cu/B.Mask 各少一个兜底 flash。

**对账三：NPTH 的阻焊**。KiCad 第一次生成时给 `np_thru_hole` 带了 `*.Mask`，
每面多 25 个阻焊开窗；PADS 的 GTS/GBS 在 25 个孔位上没有任何 stroke
（最近的 stroke 边缘也在 23.62 mil 外）。改成 `(layers "*.Cu")` 后重测：
两边都是 0/25，F.Mask 从 619 降到 594、B.Mask 从 620 降到 594（§C-16 后
两面各是 574 个 smd + 20 个 thru_hole），恰好等于"smd 焊盘 + 20 个 thru_hole"。

**DRC**（第三批状态，`kicad-cli pcb drc --severity-all`，重跑结果稳定；
下面这组数字已被 §C-14 的 **795 条 / 0 断点**取代，保留用于对比铺铜前后）：

```
199  lib_footprint_issues    封装库 'PSDR' 不在工程配置里（预期，封装数据内嵌在板上）
 52  clearance                最小实际 0.1174 mm，规则 0.2 mm
 38  hole_clearance           14 条是 0.0001 mm：J170 ×9、J153 ×5
 10  via_dangling
  5  copper_edge_clearance    板框是占位矩形，边上的铜按真实板框算就会好
  4  through_hole_pad_without_hole   4 个 drill 0 的 Morse 桨焊盘
  1  track_dangling
309 条违规 + 20 个 unconnected（全部 GND）
```

14 条 0.0001 mm 不是转换误差：J170/J153 的封装里，1.2 mm NPTH 孔与信号焊盘
的边正好相切（焊盘半宽 1.15 + 孔半径 0.6 = 1.7501 mm = decal 间距），PADS
允许，KiCad 的 0.25 mm 孔规则会报。当时 20 个断点全部落在 GND 上，与"还没有
铺铜"一致：GND 在源设计里靠电源层/地平面连成整张网；§C-14 补上铺铜后降到 0。

**单网样例**：`dist/kicad/PSDR_2.6.1_spike_TX-Q_DRIVER_P.kicad_pcb`，
只含 C252 与 U4 两个器件、5 段 8 mil 走线、1 个 0.8128/0.3556 mm 过孔，
DRC 2 条 warning（封装库）0 断点——这就是"一个 decal + 一个网"的原始探针产物。

**三件缺口的勘误**（§C-14 补做，2026-11-01）：

1. **铺铜**：12 条 `POUROUT` 确实存在（GND ×3、+3V3 ×2、+3V3_CPU ×3、
   +3V3_FLIP_FLOP、BOOST_LOOP、V_SUPPLY、+5V_BOOST，共 7 个网），但**文件里有
   `*POUR*` 段头**——`Hardware/PSDR.asc` 第 24084 行 `*POUR*       POUR ITEMS`。
   上一版"没有 `*POUR*` 段头、POUROUT 夹在 `*ROUTE*` 里"是错的。
2. **真实板框**：不在 `LINES` 的 15/16/17/18 层（那 277 段是装配/注释线）。
   整板只有一条 `BOARD` 记录，`CLOSED` 折线 68 个顶点 / 67 段
   （42 直线 + 25 圆弧）。上一版"258 段 OPEN/CIRCLE 包络、生成器画占位矩形"作废。
3. **丝印**：已生成（decal 图元 + 板级图元 + 位号 + 4 条自由文本），见 §C-14。

**第三批判定**（保留）：方向 A 的探针目标达成——ASCII → KiCad 的焊盘、走线、
过孔、弧全部可自动生成，flash 位置与原始 Gerber 在 0.17 µm 内一致
（钻孔最差 1.5 µm），且每一层铜的数量都能对账。

---

### C-14 铺铜、真实板框、丝印：三件缺口补齐（2026-11-01）

**板框**（`parse_outline`，只认 `*LINES*` 里唯一的 `BOARD` 记录）：

- 68 个顶点、67 段 = 42 直线 + 25 圆弧；包围盒 **100.00 × 65.00 mm**。
  KiCad 侧是 42 条 `gr_line` + 25 条 `gr_arc`，全在 `Edge.Cuts`。
- 对账基准是 `9 - fabnotes.GBR`——ASCII 自带的 CAM 文档写着
  `CAM_DOC_NAME Board Outline` → `DOC_OUTPUT_FILE 9 - fabnotes.GBR`、
  `DOC_BOARD Black`。按**真实弧线**每段采 32 点，共 2144 个采样点：

```
outline segments 67  lines 42  arcs 25
fabnotes strokes 670
samples 2144, >0.1 mm: 0, worst 0.0025 mm at segment 25
```

  （踩过的坑：最初按"直线段 + 弧的弦/中点"粗采样，得到 93/460 > 0.1 mm、
  最差 1.296 mm 的假警报；弧必须按圆心/起角/扫角采样。见仓外
  `PSDR-build-artifacts/outline_arc_check.py`。）

**铺铜**（`parse_pours`，从第 24084 行的 `*POUR*` 段读 `POUROUT` 多边形）：

| 网 | 层 | 顶点 | 网 | 层 | 顶点 |
|---|---|---|---|---|---|
| GND | In2.Cu | 4 | +3V3_CPU | F.Cu | 14 |
| GND | F.Cu | 4 | +5V_BOOST | F.Cu | 11 |
| GND | B.Cu | 4 | BOOST_LOOP | F.Cu | 5 |
| +3V3 | In1.Cu | 14 | V_SUPPLY | F.Cu | 8 |
| +3V3 | F.Cu | 10 | +3V3_CPU | In1.Cu | 4 |
| +3V3_CPU | F.Cu | 7 | +3V3_FLIP_FLOP | In1.Cu | 5 |

  12 个区 / 7 个网，层分布 In2 1、In1 3、F 7、B 1；全部闭合、无弧角。
  `HATOUT` 是源工具已经打好的剖面线岛，KiCad 从 zone 重新推导，不单独发射。

- **PADS 的铺铜多边形故意超出板框**（例如 In2 的 GND：x −13.18..110.16、
  y −8.76..75.23 mm），源 CAM 把铜裁到板边附近：0.254 mm 填充线中心线为
  0.635..99.365 × 0.635..64.364 mm，**铜边为 0.508..99.492 × 0.508..64.491 mm**。
  KiCad 用默认 0.5 mm 铜边间距填充，实测 0.500..99.499 × 0.500..64.498 mm，
  **两者铜边相差 0.008 mm**。早先写的"多 0.13 mm"是拿源中心线 0.635 与
  KiCad 铜边 0.500 相比得出的，作废（§C-16 重测）；未改板级规则。
- **生成物里的 zone 是未填充状态**（`filled_polygon` 0 个）。KiCad 的 CLI
  不会自动重填，必须显式加开关：
  - DRC：`kicad-cli pcb drc --severity-all --refill-zones`
  - 出 Gerber：`kicad-cli pcb export gerbers ... --check-zones`

  不加这两个开关，DRC 报 **796 条 / 20 断点**，Gerber 里一个 G36 区域都没有。
  这是本轮最隐蔽的坑：文件能打开、命令 rc=0、导出成功，但铺铜整层缺失。
- 加 `--check-zones` 后铜层 Gerber 出现 G36 区域：In2.Cu 1、In1.Cu 8、
  F.Cu 57、B.Cu 50。

**DRC**（`--severity-all --refill-zones`，重跑结果稳定；逐类定性见 §C-16）：

```
199  silk_overlap            丝印互相重叠（PADS 允许）
199  silk_over_copper        丝印压阻焊开窗（PADS 允许）
199  lib_footprint_issues    封装库 'PSDR' 不在工程配置（预期）
 55  silk_edge_clearance     丝印压板边
 52  clearance               最小实际 0.1174 mm，规则 0.2 mm
 39  copper_edge_clearance   16 条 PADDLE_* 舌口 + 23 条板边连接器焊盘
 38  hole_clearance           14 条 0.0001 mm：J170/J153 孔与焊盘相切
 10  starved_thermal          6 条 B.Cu、4 条 F.Cu 的 GND 焊盘只剩 1 根辐条
  4  through_hole_pad_without_hole   drill 0 的 Morse 桨焊盘
795 条违规 + 0 unconnected
```

  与第三批的 309 条 / 20 断点相比：新增 486 条全是铺铜/丝印的预期告警
  （丝印压焊盘、热焊盘、板边），换来 **GND 连通性 20 → 0**。
  `copper_edge_clearance` 的锚点是板框顶点、不是实际交点；实际铜在
  舌口附近贴近轮廓，源设计在这些边缘连接器处没有 0.5 mm 规则。

**丝印**：

- 图元来源：`*PARTDECAL*` 的 OPEN/CLOSED/CIRCLE（level 26/0/1）+
  `*LINES*` 的 level 26/29 板级线条 + **`*LINES*` 段里的 2 条 `COPPER`
  记录**（level 26/29 的填充形状，§C-17 补齐）+ 376 条 Ref.Des. +
  4 条自由文本。
- 层次规则有 ASCII 里嵌入的 CAM 文档作证（第 51011 行起）：
  `CAM_DOC_NAME Top Silkscreen` → `DOC_LAYER_NUMBERS 1 26`，
  `Bottom Silkscreen` → `4 29`。实测：**level 26 → 器件所在面**；
  **level 0/1 → 只在非镜像器件上归 F.SilkS**（底面孔件的 0/1 图元在
  GTO/GBO 都不出现）；level 20/23/27/29 → 不画；零长线段跳过。
- 数量：162 个 decal 图元、1497 个板级图元 {26: 754, 29: 743}（含 §C-17
  的 2 个 `COPPER` 填充形状）、4 条自由文本、376 个位号；15 个器件在源文件里
  没有 Ref.Des.（6 个 FIDUCIAL、7 个 MH3M、2 个 MH_80M——只有 Part Type
  文本，而 CAM job 不画 Part Type）。
- 双向覆盖率（40 px/mm，容差 0.10 mm）：

| 宽度 | GTO 源→KiCad | GTO KiCad→源 | GBO 源→KiCad | GBO KiCad→源 |
|---|---|---|---|---|
| 2 mil | 100.00% | 100.00% | 100.00% | 100.00% |
| 6 mil | 35.48% | 23.93% | 29.23% | 18.42% |
| 8 mil | 100.00% | 100.00% | 100.00% | 100.00% |
| 10 mil | 100.00% | 100.00% | 84.82% | 73.04% |

  （10 mil 这一行是 §C-17 补齐 `COPPER` 记录后的数字；补齐前是 GTO
  98.03% / 100.00%、GBO 29.47% / 46.88%。）

  - 2 mil 是 "psdr" 标志，8 mil 是板级线条/器件轮廓：两档双向 100%，
    说明坐标与层别都对。
  - 6 mil 是位号文本：KiCad 笔画字体 vs PADS Romansim，字形不同；
    6 mil 这一档的两向百分比不能当几何误差读。
  - GBO 10 mil 剩余的 84.82/73.04 由背面 4 条 10 mil 自由文本（`portablesdr.com`、
    `Serial No`、`HW V2.6.1 - 6/29/2016`、`Michael Colton - KE7HIA`）主导，
    与 6 mil 一样是 KiCad 笔画字体 vs PADS Romansim 的字形差，不是几何误差。
  - 补齐前 GTO 10 mil 的 1.97% 缺口（C151 左侧、板下缘附近）是 PADS 的
    `COPPER` 记录，不是 decal/LINES/TEXT 图元；根因与修法见 §C-17。
- 修了一个真 bug：PADS 把 decal 的 CIRCLE 写成一条 start == end 的 G75 圆弧，
  `gerbparse._arc_points` 原来把这种弧当零扫角，所有圆形丝印都没进对账栅格。
  修好后源 GTO drawup 从 9003 涨到 11663、GBO 10961 → 12956；KiCad 侧
  "多出来"的 10 mil 笔画随之对上（此前 1032/1121 条未匹配集中在若干
  r = 0.3 mm 的圆上）。

**复现**（生成器只依赖标准库；同一输入重跑逐字节相同）：

```
$ python tools/pads_asc_pcb.py Hardware/PSDR.asc --all \
      -o dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
$ kicad-cli pcb drc --severity-all --refill-zones \
      -o dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt \
      dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
$ kicad-cli pcb export gerbers -o <fab> --no-protel-ext --precision 6 --check-zones \
      -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask <board>
$ kicad-cli pcb export drill -o <fab> --format excellon --excellon-units mm \
      --excellon-zeros-format decimal --drill-origin absolute <board>
$ python tools/kicad_gerber_compare.py --pads <468dc41 原始 Gerber> \
      --fab <fab> --board PSDR_2.6.1_pcb_spike_full
```

最后一条重跑结果（§C-16 修复后）：**0 个源 flash 未覆盖、461/461 个钻孔对上**。

**判定**：铺铜、真实板框、丝印三件事完成。四层板现在是
4 层铜 / 12 个铺铜区 / 67 段板框 / 双向丝印对账通过（10 mil 档 GTO 双向
100%，GBO 余量为背面 4 条自由文本的字形差）/ 0 断点；
但它仍不是可投产的板：795 条 DRC（分类与处置见 §C-16，以源设计允许的
丝印压焊盘和紧间距为主）。生产包继续以上游 `468dc41` 的原始 Gerber 为准。

---

### C-15 导入嘉立创EDA Pro：KiCad 路线丢层/丢网/丢铺铜网络的根因与修复（2026-11-01）

工单没要求这一步，属于接管后用户提出的"能不能放进嘉立创EDA"。结论先写：
**能，但必须先在生成器和本地转换器上修三处缺陷**；修完后四层、278 网、
12 个铺铜区、391 器件都能在 EDA 里读到。当时宿主的 EDA 是 **3.2.203（V3）**，
低于本项目技能基线的 V4，属于已知限制（M1 已升到 4.1.60，见本节末尾的版本更新）。

**路线**：官方 `eda.sys_FileManager.importProjectByProjectFile` 只吃
`File` 对象，页面内的 KiCad 转换 worker 会把失败对象 stringify 成
`[object Object]`，没法定位。改为**本地跑 EDA 自带的转换器**
（`chameleon/3.2.50.42fc27da/js/convert-node-server.js`，`--cmd conversion`），
再用一个带 CORS 的本地 HTTP 服务喂给页面里的官方 API。转换器副本放在仓外
`PSDR-build-artifacts/eda-import/tools/convert-node-server-patched.js`。

**缺陷 1（仓库内，已修）：生成器写的铜层编号是 KiCad 5 的旧编号。**
`tools/pads_asc_pcb.py` 声明 `(version 20260206)`，却把 In1/In2/B.Cu 写成
layer id 1/2/31。转换器按版本走 `init3`（KiCad 9/10 编号：1=F.Mask、
2=B.Cu、31=F.CrtYd），于是 In2→Bottom、B.Cu→自定义层 "B.Cu"(id 76)、
In1→F.Mask 被当阻焊丢掉。改成 `(0 F.Cu)(4 In1.Cu)(6 In2.Cu)(2 B.Cu)`、
四个都写 `signal` 后，整板除这 3 行外逐字节不变：

```
nets 278; parts 391; pads 1194 (1132 netted, 62 not)
track segments 5034 (189 zero-length dropped); arcs 22; vias 419
outline 42 lines + 25 arcs 100.00x65.00 mm
pours 12 {F.Cu:7, In1.Cu:3, In2.Cu:1, B.Cu:1}
DRC 795 violations / 0 unconnected（与修改前同类同数，仅时间戳与两条报错顺序变化）
```

对照物是 pcbnew 10.0 自己写出的四层板 `probe/ki10_4layer.kicad_pcb`，
确认 KiCad 10 的规范编号就是 0/4/6/2。

**缺陷 2（转换器）：`parseNet` 用 shell 式分词器取网名，反斜杠被当转义。**
`AUDIO_AMP_\SHDN`、`\EARPHONE_INSERTED` 两个网因此变成 `undefined`，
276 网、7 个焊盘丢网。补丁只去掉包围引号、保留反斜杠原文。

**缺陷 3（转换器）：`parseCopperpour` 用 `netObj[net]` 按数字 ID 查网名，
但 KiCad 9/10 的 zone 写的是 `(net "GND")` 字符串**，查表得 `undefined`，
12 个铺铜的 `netName` 全空。EDA 读回直接报
`Copper pour boundary ie9344 has no readable net`。补丁：字符串直接做网名、
数字才查表。

**离线校验（修完后的 epro2）**：

```
837 docs {SCH 10, SCH_PAGE 10, DEVICE 541, SYMBOL 164, FOOTPRINT 100,
          INSTANCE 9, CONFIG 1, BOARD 1, PCB 1}
铜层 TOP/In1.Cu/In2.Cu/BOTTOM 均 use=true；In3..In30 未启用
PCB 文档：LINE 5024 + ARC 22 + VIA 419 + COMPONENT 391 + POUR 12 + PAD_NET 1870
PAD_NET 不同网名 279（含空网名）= 278 个真实网络，两个反斜杠网各 5/2 个焊盘
POLY 按层：3=787、4=757、11=67（板框 67 段）
12 个 POUR 的 (层, 网) 与源板 12 个 zone 一一对应
```

**线上导入结果**（新工程 `PSDR 2.6.1 (KiCad 4L final)`，
uuid `2fec79e66cba43fd9f0d848161f902a9`）：

| 项 | 读回命令 | 结果 |
|---|---|---|
| 铜层 | `pcb layers` | `copperLayerCount 4`，In1/In2 启用 |
| 网络 | `pcb nets` | 278，含 `\EARPHONE_INSERTED`、`AUDIO_AMP_\SHDN` |
| 器件 | `pcb list` | 391 |
| 铺铜边界 | `call pcb.pour.list` | 12 个，(层,网) 全对 |
| 铺铜铜皮 | `call pcb.pour.rebuild` → `pcb poured-list` | 12 个边界重建，10 个产出铜皮 |
| 板框 | `pcb outline-get` | `67` 条 layer 11 折线；`outlineFormat:"ambiguous:67-polylines:empty"` |
| 原理图 | `sch pages` | 10 页（root + p02..p10） |

**板框读回缺口**：EDA 把 KiCad 的 42 线 + 25 弧拆成 67 条 layer 11 折线，
`outline-get` 不会把它们拼成一条闭合轮廓，所以只回读成 AABB（`pcb dump`
明确标 `partial`）。但引擎本身认这条边界：DRC 报出 32 条
`Board Outline to SMD Pad/Track`，对象 id 就是 `ie94xx` 这些折线。
对比 PADS 路线：PADS 的 epru 里是**一条** `polyType:"BOARD_OUTLINE"`，
`outline-get` 同样回读失败（`outline:1 / segments:0 / format empty`）。
两条路线的这个 API 都是读回缺口，不是数据丢失。

**两个铺铜不出铜**：`+3V3_FLIP_FLOP`（In1，ie9349）和 `V_SUPPLY`
（F.Cu，ie9355）重建后 `poured fills 0`。原因是 eda 导入时
`keepIsland=false`（源 KiCad zone 写的是 `island_removal_mode 0`），
这两个小区被周边更高优先级的铜完全覆盖，孤岛被剔除。PADS 原始 POUR
记录里 `keepIsland=true`。要完全对齐，得在 epro2 里改这两个 POUR 的
`keepIsland` 后重导；本轮没做，如实记为差异。

**EDA 自带 DRC**（`pcb drc --json`，默认规则，不是源设计规则）：

```
passed false / total 507
Via Size 419（EDA 默认要求孔径 19.7~393.7 mil，源过孔 14 mil）
Board Outline to SMD Pad 20 / SMD Pad to Track 19 / TH Pad to Track 18
SMD Pad to TH Pad 14 / Board Outline to Track 12 / Device to TH Pad 4
Netlist Error 1（原理图↔PCB 网表差异；原理图是 2016 PDF 重建版）
```

这 507 条与 KiCad 的 795 条不是同一套规则，不能互相加减。

**复现命令**（仓外）：

```
node tools/convert-node-server-patched.js --cmd conversion --params \
  '{"decodingOptions":{"decodingType":"kicad",
    "decodingFilePath":".../PSDR_2.6.1_kicad_fixed.zip","projectName":"PSDR_2.6.1"},
    "encodingOptions":{"encodingType":"easyeda-pro-2",
    "savingDirPath":".../out","savingFileName":"PSDR_full_zip2"}}'
# 页面内：
# const r=await fetch('http://127.0.0.1:48765/out/PSDR_full_zip2.epro2');
# const f=new File([await r.arrayBuffer()],'PSDR_2.6.1.epro2');
# await eda.sys_FileManager.importProjectByProjectFile(f,'EasyEDA Pro',
#   {importOption:'ImportDocument'},
#   {operation:'Existing Project',existingProjectUuid:'<新工程 uuid>'});
```

后续 `pcb save` → `project export-source` 回导（1,109,579 B）复核：
12 个 POUR 带网、12 个 POURED 记录（其中 2 个 fills 0）、391 器件、
419 过孔、67 条 layer 11 折线，持久化无误。

**已知限制**：宿主 V3，技能基线要求 V4；中间工程
`PSDR 2.6.1 (KiCad 4L)`（铺铜无网的过渡版）和旧的降级工程
`PSDR 2.6.1 KiCad` 需要用户在 EDA 里手工删除——typed 接口没有删工程的 action。

**版本更新（2026-11-01 M1）**：宿主已从 3.2.203 升到 **4.1.60**。官方直链
`https://image.lceda.cn/files/lceda-pro-windows-x64-4.1.60.exe`（256,976,016 B，
`Get-AuthenticodeSignature` = `Valid`，签名主体「深圳嘉立创科技集团股份有限公司」，
签发者 GlobalSign EV CodeSigning）；单连接被 CDN 限到约 135 KB/s，改用 8 段
byte-range 并行下载后聚合约 1.3 MB/s。Inno Setup 安装器（不是 NSIS，`/S` 无效），
静默参数是 `//SILENT //NORESTART //SUPPRESSMSGBOXES`；`resources/app/version.txt`
由 `3.2.203.4bde4f6b` 变为 `4.1.60.198f38ab.e6f060`。`Documents/LCEDA-Pro/` 未被
触碰；**通道 A 的 connector 扩展升级后仍在线**（1.15.0），`hostCompatibility`
由 `block` 转 `ok`，通道 B 的 mcp-bridge 需要用户重新导入才在线。

#### C-15 补充（M1，2026-11-01）：零铜铺铜的真因是 EDA 优先级语义反向，不是 keepIsland

上一轮把原因写成"源 KiCad zone 的 `island_removal_mode 0`"，并计划把
两个 POUR 的 `keepIsland` 改成 true 后重导。M1 先验证"改 KiCad 区设置"
能否让转换器写出 keepIsland=true：**不能**。

- 用同一块板做两组对照，只把 12 个 zone 的 `(island_removal_mode 0)`
  改成 `1`（12 处），分别跑本地转换器
  （`convert-node-server-patched.js --cmd conversion`）：
  ```
  PSDR_full_zip2.epro2（mode 0）: 12 个 POUR keepIsland 全 false
  PSDR_island1.epro2（mode 1）: 12 个 POUR keepIsland 全 false
  ```
- 转换器源码里没有读 KiCad `island_removal_mode` 的分支；它只在解析
  PADS 的 `PLANEFLAGS` 时设置 `keepIsland`，KiCad 走默认 false。
  所以生成器改这个字段对 EDA 导入没有作用，改了反而会改变 KiCad 自己的
  填充（多保留孤岛）。
- 第一步先修**转换产物**（后面实测发现单靠它不够，见下条；该脚本已被下面第 9
  条的源驱动补丁取代并删除）：新增
  `tools/eda_epro2_keep_island.py`，把指定网（默认
  `+3V3_FLIP_FLOP` / `V_SUPPLY`，也可 `--all`）的 POUR `keepIsland`
  改成 true，其余记录逐字节复制。离线回读补丁后的 epro2：
  ```
  +3V3_FLIP_FLOP layer=15 keepIsland=True patched
  V_SUPPLY        layer=1  keepIsland=True patched
  其余 10 个 POUR 保持 False
  ```
- **现场验证（EDA 4.1.60，工程 `2fec79e6…`，PCB `cf6546e2…`，2026-11-01）**：
  1. 基线回读：12 个 POUR 全部 `preserveSilos=false`，`pouredCount=10`，
     缺 `ie9349`（`+3V3_FLIP_FLOP`，In1/层 15）与 `ie9355`（`V_SUPPLY`，F.Cu/层 1）。
  2. 逐个置 `preserveSilos=true`：请求属性回读一致（`requestedMismatches: []`），
     但 EDA 顺带把 `pourPriority` 6→7、12→13（工具按 `verified:false` +
     `sideEffects` 如实报告）。层内相对顺序没变：In1 是
     `ie9344=1 / ie9346=3 / ie9349=7`；F.Cu 原本最高是 `ie9353=10`。
  3. `pcb_pour_manage action=rebuild all=true`：原生返回 12 个对象，
     但只有 10 个有填充，`ie9349`/`ie9355` **仍然零铜皮**；再用通道 A 的
     `easyeda pcb poured-list` 独立回读，同样 10/12。
     ⇒ **单靠 keepIsland 解决不了**，上一轮的判断被证伪。（`preserveSilos=true`
     是否是必要条件没有单独拆开测：置 true 后仍 10/12，是在 true 的前提下
     改优先级才出铜。）
  4. 稳定性坑：EDA 的 `fillGeometryDigest` 在同一条操作链里会来回变——中途一次
     读到 5 个区的 digest 变化（`fillCount` 全不变），整条链走完后再读，只剩
     `ie9354` 由 `a3b878d9e2cda50a` 变成 `0c55a03042b16b26`，其余 9 个回到最初
     的值。⇒ **digest 不能当改动前后的判据**，只有 `fillCount` 稳定。
  5. 真因定位（离线几何 + 源侧证据）：**EDA 的 `pourPriority` 是"数值小者优先"，
     与 KiCad（大者优先）相反**。拿 `pcb pour list` 的 12 个边界多边形用
     shapely 求同层交叠：

     ```
     ie9349 +3V3_FLIP_FLOP In1  prio  7  被编号更大的邻区覆盖 0.0% / 被更小的覆盖 115.2%   ← 零填充
     ie9355 V_SUPPLY       F.Cu prio 13  被编号更大的邻区覆盖 0.0% / 被更小的覆盖 186.5%   ← 零填充
     ie9347 +3V3_CPU       F.Cu prio  4  被编号更大的邻区覆盖 100.0%                        ← 有 1 块填充
     ie9348 +3V3_CPU       F.Cu prio  5  被编号更大的邻区覆盖 100.0%                        ← 有 26 块填充
     ie9350 +5V_BOOST      F.Cu prio  7  被编号更大的邻区覆盖 100.0%                        ← 有 19 块填充
     ```

     有填充的恰好是编号小的，零填充的恰好是编号最大的两个。转换器把 12 个
     zone 按导入顺序编 1..12，于是最后两个区被整片判给了别网 —— 这也解释了
     为什么 `preserveSilos=true` 没用：被覆盖后连孤岛都不存在。
  6. 源侧反证（不是"本来就没铜"）：PADS 每个铺铜都有自己的 HATOUT 铜皮，
     `+3V3_FLIP_FLOP` 有 7 块、`V_SUPPLY` 有 2 块；POUROUT 记录尾部形如
     `-1 0.000000 <n>`（`+3V3 1`、`+3V3_CPU 2`、`BOOST_LOOP 2`、`V_SUPPLY 1`、
     `+5V_BOOST 6`、`GND 7`），`+3V3_FLIP_FLOP` 与 GND 大面一样没有尾部字段。
  7. KiCad 侧 12 个 zone **都没有写 `(priority N)`**（全 0），所以 KiCad 自己
     填得出这两块（`pcbnew` 重填充实测 `+3V3_FLIP_FLOP` 26.197 mm²/1 块、
     `V_SUPPLY` 26.750 mm²/1 块），一进 EDA 就归零。
  8. **现场实验已完成（EDA 4.1.60），12/12 达成**：
     - 请求 `ie9349.pourPriority = 0` → EDA 归一化成 **4**（工具如实报
       `requestedMismatches: expected 0 / actual 4`）→ 单独 rebuild
       → `ie9349` 出 **7 块铜皮**（digest `fnv1a64:5aa6cf3470b372e4`），
       与源 `POR69553698` 的 7 条 HATOUT 数量一致。
     - 请求 `ie9355.pourPriority = 1` → EDA 给 **3** → 单独 rebuild
       → **4 块铜皮**（源 `POR27151804` 是 2 条 HATOUT；EDA 的分解与源不等价，
       未逐块核过）。
     - `easyeda pcb poured-list` 独立回读 **12/12**；`pcb save` →
       `document.close` → `document.open` 重开后再读**仍是 12/12**（持久化成立）；
       其余 10 个区的 `fillCount` 与基线逐个相同
       （1/16/6/1/26/19/11/26/296/360）。
     - **代价（现场稳定后复测）**：EDA 自带 DRC 从 507 涨到 **513**，只多一类：
       `Copper Region(Filled) / Connection Error / No Connection` **6 条**，全是
       `+3V3_FLIP_FLOP` 在 In1 的孤岛铜（7 块中 1 块连上、6 块悬空）。源里这个
       铺铜本来就是 7 条独立 HATOUT，所以孤岛是源形态，不是新造的短路。
       中途一次读数里还出现过 7 条
       `Copper Region(Filled) to Copper Region(Filled) Clearance Error`，等这条
       操作链走完、宿主重启后再读已归零 —— EDA 的 DRC 在重建未 settle 时会漂，
       报数以"重开文档后复测"为准（与 §C-16 里 KiCad DRC 报项顺序不稳定同类）。
       EDA 跑的是它自己的默认规则（0.6 mm 一档，不是源的 8 mil），岛铜净间距
       仍要按源规则复核。
     - 桥接稳定性：`modify`/`rebuild` 多次超时进 `timed-out` 隔离；一次
       `rebuild all` 把客户端心跳打挂（`hostRestartRequired: true`），按
       `bridge_recover_client action=recover` → 重启宿主 → 全新客户端
       `readback` 走完恢复。那次超时的全量重建其实**已提交**（重启重开后通道 A
       回读仍 12/12）。恢复记录 `8a94a59d…`、`3c079efc…`、`79fdd1fe…`；
       在用的 mcp-bridge 是 2.4.0（本地缓存包 2.3.4）——"写一次掉一次"要当
       常态：**每次写入后先回读再决定，绝不重放写入**。
  9. **可复现的修法已进仓库**：`tools/eda_epro2_pour_source.py` 直接读
     `Hardware/PSDR.asc` 里每个 `POUROUT` 的优先级（尾部最后一个数，无尾部=0）
     与 `PLANEFLAGS` 的保留孤岛位，按 (网络, 层, 多边形面积) 配对写进转换后的
     `.epro2`。验收基准用 EDA 自己的 PADS 路线（它本就把这些数抄进 `order`）：
     12 条 `(net, layer, order, keepIsland)` **逐条相同**，且整个 `.epru` 只有
     那 12 行 POUR 变化。

     ```
     net              layer  文件原 order   源 order
     +3V3                15           1            1
     +3V3                 1           2            5
     +3V3_CPU            15           3            2
     +3V3_CPU             1           4            3
     +3V3_CPU             1           5            6
     +3V3_FLIP_FLOP      15           6            0   ← 现场零铜的那个
     +5V_BOOST            1           7            6
     BOOST_LOOP           1           8            2
     GND                 16           9            0
     GND                  1          10            7
     GND                  2          11            0
     V_SUPPLY             1          12            1   ← 现场零铜的那个
     逐条相同: True    改变的记录行数 12，全部是 POUR: True
     ```

     原先只翻 `keepIsland` 的 `tools/eda_epro2_keep_island.py` 已删除：它的
     诊断被上面第 3 条证伪，留着会误导。
- **当前状态**：M1 出口条件 **"EDA 12/12 有填充" 达成**并已保存；仓库侧的
  复现路径（`转换 → eda_epro2_pour_source.py → 导入`）属性已对平 PADS 路线
  基准，但**还没有走一次完整导入来实测 12/12**（要在 EDA 新建一次导入，
  且桥接不稳）——这一段如实记为未完成，见任务 #31。制造基线不变，仍是上游
  `468dc41` 的原始 Gerber（§C-16）。

---

### C-16 收尾：J170 安装孔修复、铺铜边界定量与 795 条 DRC 分类（2026-11-01）

本轮把 §C-13/§C-14 留下的三处尾巴做完：缺的 3.2 mm 安装孔、0.13 mm 铺铜
差异的定量、795 条 DRC 的逐类定性。交付物
`dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb` 已按修复后的生成器重写
（与修复前只差 5 行），Gerber/钻孔对账和 DRC 报告都按新版重跑。

**1. J170 孤儿焊盘：是生成器模型缺陷，已按通用规则修复**

源数据并不矛盾，矛盾在生成器的"按端子查同名 pad stack"模型：

- J170 的 decal 有四个 3.2 mm NPTH 安装孔，编号 `PAD 20/21/22/23`；
  四个角端子是 `21/22/23/24`，于是 `PAD 20` 没有端子、`T24` 没有同名焊盘；
- 原始钻孔在 J170 四个角上都有 3.2 mm 孔，且全板只有 J170 这一个 decal
  同时出现"孤儿焊盘 + 无焊盘端子"；PADS 只能把 `PAD 20` 放在 `T24` 上；
- 原生成器让 `T24` 落到 `PAD 0` 的默认焊盘（2.3 × 1.5 mm SMD），
  第 4 个安装孔就丢了。

`tools/pads_asc_pcb.py` 新增 `pad_stacks()`：把每个孤儿焊盘按编号差最小
配给一个无焊盘端子（数字编号才算，找不到就停）。这是通用规则，没有 J170
特例；其它 decal 没有孤儿焊盘，行为不变。重跑后与旧交付物只差这 5 行：

```
-		(pad "24" smd roundrect
-			(at -62.2000 -17.0500 -180.0000)
-			(size 2.3000 1.5000)
-			(layers "B.Cu" "B.Paste" "B.Mask")
-			(roundrect_rratio 0.2540)
+		(pad "24" np_thru_hole circle
+			(at -62.2000 -17.0500 -90.0000)
+			(size 3.2000 3.2000)
+			(drill 3.2000)
+			(layers "*.Cu")
```

（角度 −180 → −90 来自 `PAD 20` 的 `FINORI`；圆焊盘下无影响。）
焊盘总数仍 1194；B.Cu/B.Mask 各少一个兜底 flash（1014→1013、595→594），
F/B 两面从此完全对称。重跑对账：

```
$ python tools/kicad_gerber_compare.py --pads <468dc41 原始 Gerber> \
      --fab <由新版导出的 Gerber+钻孔> --board PSDR_2.6.1_pcb_spike_full
...
source hits 461, missing 0
RESULT: every source flash is covered and all drill hits match
```

DRC 仍是 795 条 / 0 unconnected，类别计数不变——新增的 NPTH 孔没有引入
新违规。把新旧报告按"类别 + 描述 + 对象"去重比对：794 个签名里 792 个
完全相同，另 2 个只是同一条违规的两个对象顺序互换（DRC 的报告顺序不稳定）。
同一输入重跑，`cmp` 逐字节相同。

**2. 铺铜边界：0.008 mm，不是 0.13 mm**

早先的 0.13 mm 是拿源 Gerber 的填充线**中心线** 0.635 mm 与 KiCad 的
**铜边** 0.500 mm 相比。按 0.254 mm 线宽重算源铜边：0.635 − 0.127 =
0.508 mm；KiCad 实测铜边 0.500 mm（GTL/GBL/G2 三层的原始 stroke 端点
范围 0.500..99.499 × 0.500..64.498 mm）。真实差异 **0.008 mm**，
小于 2 mil，不构成规则或工艺差异，未改板级设置。

（测量坑：`gerbparse.bbox()` 会把当前孔径宽度加到 G36/G37 区域描边上，
对 KiCad 的 zone 填充返回 −47.8..126.3 mm 的假范围；必须直接用原始
stroke 端点求范围。）

**3. 795 条 DRC 逐类定性**

判定口径：源 PADS 的规则在 `Hardware/PSDR.asc` 的 `RULES_SECTION`
（唯一一组 `CLEARANCE_RULE`）：铜间距 304800 = **8 mil (0.2032 mm)**，
孔间距 8 mil，铜到板框 762000 = **20 mil (0.508 mm)**；PADS 没有丝印 DRC，
`STMINSPOKES` 则是 4。KiCad 侧是默认 0.2 / 0.25 / 0.5 mm。

| 类别 | 条数 | 级别 | 定性 | 处置 |
|---|---|---|---|---|
| `lib_footprint_issues` | 199 | warning | 工程没有 `fp-lib-table`；封装数据内嵌在板上（391 个封装），KiCad 的去重计数不是按封装总数 | 不改 |
| `silk_overlap` | 199 | warning | PADS 无丝印 DRC；丝印与源 GTO/GBO 双向对账 100%，重叠来自源图 | 不改 |
| `silk_over_copper` | 199 | warning | 同上，每个封装至少一处位号/轮廓压开窗 | 不改（生产会裁丝印） |
| `silk_edge_clearance` | 55 | warning | 源图把文字/线条画到板边附近 | 不改 |
| `clearance` | 52 | error | 实际 0.1174..0.1986 mm，**全部小于源规则 0.2032**：源设计自身就不满足自己的规则；几何逐一来自源走线/焊盘 | 不改（保持源几何） |
| `copper_edge_clearance` | 39 | error | 全部是板边连接器：16 条 `PADDLE_*` 舌口 + ANT/VNA-IN 5、EARPHONE 7、VNA-OUT 5、USB 2、SPEAKER 1、M1/M2/M3 3；源 20 mil 规则同样被源设计违反 | 不改 |
| `hole_clearance` | 38 | error | 14 条 0.0001 mm 是 J170×9、J153×5 的 1.2 mm NPTH 与信号焊盘相切（源 8 mil 也不满足，PADS 允许）；其余 24 条 0.2042..0.2456 **≥ 源 8 mil**，只是严于 KiCad 默认 0.25 | 不改 |
| `starved_thermal` | 10 | error | 6 条 B.Cu + 4 条 F.Cu 的 GND 焊盘（0402/0603、microSD、U314、USB）重填后只剩 1 根辐条；源 PADS 用 `THERLINEWID 15 mil`/`THERSMDWID 10 mil` 的剖面线填充，KiCad zone 是单一 0.254/0.254 实心填充，辐条拓扑无法逐根复现；0 断点 | 不改，记为转换差异 |
| `through_hole_pad_without_hole` | 4 | error | CW1/CW2 的 4 个 Morse 桨焊盘，源设计是"多层铜 + 无钻孔"，这是 KiCad 连通性限制的既定绕法（§C-13） | 不改 |

合计 **652 warning + 143 error = 795，0 unconnected**。也就是说：
没有一条错误是"转换把几何做错了"——两类转换差异（热焊盘拓扑、零钻孔
桨焊盘）已知且不影响连通性，其余错误在源设计里本来就存在（PADS 规则
允许或源设计违反自己的规则）。

**4. 本轮重写/新增的文件**

```
dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb   M  仅 J170 pad 24 的 5 行
dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt     M  按新版重跑（795/0）
tools/pads_asc_pcb.py                            M  新增通用 pad_stacks()
docs/WO-psdr-takeover.md                         M  本文件（§C-13/14 勘误 + 本节）
md5(板) = 157f000bc9caa4eb67492a9a751d8f91
```

**5. 仍未闭合的缺口**

- ~~丝印：GTO 上约 1.4 mm 的实心三角标记来源未定位~~ —— **§C-17 已闭合**
  （PADS `COPPER` 记录，连同背面 800×190 mil 的序列号白块一起补上）；
- 嘉立创EDA：`+3V3_FLIP_FLOP`（In1）和 `V_SUPPLY`（F.Cu）两个铺铜重建后
  0 铜皮。**原先写的"根因是 KiCad `island_removal_mode 0` 与 PADS
  `keepIsland=true` 不一致"已在 M1 现场被证伪**：把这两个 POUR 的
  `preserveSilos/keepIsland` 置 true 后整体重建仍 10/12；真因是 EDA 的
  `pourPriority` 语义与 KiCad 相反（小者优先）加上转换器按导入顺序编号。
  M1 已在 EDA 4.1.60 里现场改优先级做到 **12/12 有填充、持久化回读通过**，
  代价是 EDA 自带 DRC 507→513（`+3V3_FLIP_FLOP` 的 6 块孤岛铜悬空，源里本就是
  7 条独立 HATOUT）；复现路径已进仓库
  （`tools/eda_epro2_pour_source.py`，属性逐条对平 EDA 自己的 PADS 路线），
  但完整"转换→打补丁→导入→实测 12/12"仍待走一次（§C-15 补充、任务 #31）；
- DRC 795 条按上表保留，生产仍以 `468dc41` 的原始 Gerber 为准。

**复现**：

```
$ C:/Users/ASUS/python-sdk/python3.13.2/python.exe tools/pads_asc_pcb.py \
      Hardware/PSDR.asc --all -o dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
$ kicad-cli pcb drc --severity-all --refill-zones \
      -o dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt \
      dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb
$ kicad-cli pcb export gerbers -o <fab> --no-protel-ext --precision 6 --check-zones \
      -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask <board>
$ kicad-cli pcb export drill -o <fab> --format excellon --excellon-units mm \
      --excellon-zeros-format decimal --drill-origin absolute <board>
$ python tools/kicad_gerber_compare.py --pads <468dc41 原始 Gerber> \
      --fab <fab> --board PSDR_2.6.1_pcb_spike_full
```

---

### C-17 M1：丝印 `COPPER` 记录补齐（2026-11-01）

§C-14/§C-16 留下的"1.4 mm 实心三角标记来源未定位"在 M1 里闭合。
缺口不是 decal、不是 `TEXT`，而是 `*LINES*` 段里的 **`COPPER` 记录**：
PADS 的板级铜皮形状也写在 `*LINES*` 里，piece 类型是 `COPCLS`，生成器的
`parse_board_silk` 只认 `LINES` + `OPEN/CLOSED/CIRCLE/TAG`，于是整条记录
被跳过。源文件里 level 26/29 的 `COPPER` 共 2 条：

```
3413:DRW4825552  COPPER  57912000 8763000 1 0          # level 29，背面
3421:DRW18244250 COPPER  85344000 4572000 1 0          # level 26，正面
```

| 记录 | 层 | 多边形（ASCII 绝对坐标，mil） | 换算到 KiCad（mm） |
|---|---|---|---|
| DRW4825552 | 29 | 锚点 (1520,230)，相对顶点 (0,0)(−800,0)(−800,−190)(0,−190) → 800×190 矩形 (720,40)–(1520,230) | x 18.288–38.608，y −1.016 – −5.842 |
| DRW18244250 | 26 | (2240,120) (2200,160) (2200,80) | (56.896,−3.048) (55.88,−4.064) (55.88,−2.032) |

先出现的 3413 不是大家一直在找的"三角"，而是 **800×190 mil 的背面序列号
白块**（就在 `Serial No` 文本左侧）：它此前也被一起丢掉，只是 GBO 侧
10 mil 缺口被大三角和自由文本掩盖，没有单独暴露。两条都是 `COPCLS`
填充形状，描边宽度 381000 = 10 mil。

**PADS 的画法**：这类铜皮的轮廓是**按线宽一半内缩后描边**，内部再以 9 mil
间距、10 mil 笔宽打剖面线（间距小于笔宽，并集就是实心）。证据是源 GTO 里
三角形的三条边正好比源多边形内缩 5 mil，GBO 矩形的剖面线端点也内缩 5 mil。
所以生成器不能按原多边形实心填充（那样四个角会多出半笔画），而应输出
**内缩半个线宽的多边形 + 10 mil 描边 + 实心填充**：

- `parse_board_silk` 接受 `COPPER` 记录与 `COPCLS` piece；
- 新增 `inset_polygon(pts, d)`：沿顶点角平分线内移 `d = width/2`；
- `emit_board_silk` 对 `COPCLS` 输出 `gr_poly`，`(stroke (width 0.254))` +
  `(fill solid)`。

**验证**（40 px/mm、0.10 mm 容差、双向）：

```
$ python tools/pads_asc_pcb.py Hardware/PSDR.asc --all -o <board>
silk  162 decal pieces, 1497 board pieces {26: 754, 29: 743}, 4 free texts, 376 refdes labels
$ kicad-cli pcb export gerbers ... -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask
$ python <diff_silk2.py>            # 源 GTO/GBO vs KiCad 丝印 Gerber
GTO 10 mil: src->ki 100.00%  ki->src 100.00%   (src 74099, ki 74297, src-only 0, ki-only 0)
GBO 10 mil: src->ki  84.82%  ki->src  73.04%   (src 265005, ki 308525, src-only 40216, ki-only 83171)
```

- 三角专用区域 (55.5,1.7)–(57.3,4.4) mm：**src-only 0 px、ki-only 0 px**；
- 矩形专用区域 (18.0,0.7)–(39.0,6.2) mm：src-only 0 px；ki-only 只剩 408 px，
  逐像素定位在 y 5.965–6.215 mm，是矩形上沿之外的字形像素，不属于矩形；
- GBO 10 mil 剩余 15.18%/26.96% 与 6 mil 档同一性质：背面 4 条 10 mil 自由
  文本（`portablesdr.com`、`Serial No`、`HW V2.6.1 - 6/29/2016`、
  `Michael Colton - KE7HIA`）的 KiCad 笔画字体 vs PADS Romansim 字形差；
- 另外两条 level 4 的 `COPPER`（DRW66110231、DRW17477132，带 `GND` 网名）
  是地平面补块，已被 B.Cu 的 GND 铺铜覆盖，栅格对账 src-only 0 px，故不单独
  发射，避免与铺铜重复。

**回归**：

```
$ kicad-cli pcb drc --severity-all --refill-zones -o dist/kicad/drc_...txt dist/kicad/...kicad_pcb
发现 795 条违规项
发现 0 个未连接的项目
```

- DRC 与修复前同为 **795 条 / 0 断点**，逐类计数完全相同；新增补块所在的
  (17.5,−0.5)–(39.0,−6.5) mm 区域在报告里 0 条。注意 KiCad 的
  `silk_overlap` 只报每个项目的一部分配对，两次重跑的具体配对会变
  （旧报告 R97/D100 的对数多、新报告 C106/C107 的多），因此这里只对
  计数与类别，不对到逐条；
- `kicad_gerber_compare.py`：**0 个源 flash 未覆盖、461/461 个钻孔对上**；
- 生成器确定性：同一输入连跑三次，`sha256 = 5029bd02…288cc` 三次相同；
- 新板替换 `dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb`（md5
  `478a4fac8dc4745fe9bfd082826c9062`）；UUID 归一化后与上一版只差 +14 行
  （2 个 `gr_poly`），无其它改动。未归一化时，插入点之后的 UUID 因发射
  序号整体 +2 而变化——UUID 是 `uuid5` over 发射序号的确定性值，不是
  `uuid4`。

**判定**：丝印缺口闭合；本节当时剩下的两项（EDA 两处零铜铺铜、一条命令复现
+ SHA256 清单）分别见 §C-15 补充与 §C-18。

---

### C-18 M1：一条命令复现 + SHA256 清单（2026-11-01）

`tools/reproduce_kicad.py` 把此前散在 §C-14/§C-16 的手工步骤收成一条命令：

```
$ python tools/reproduce_kicad.py --pads-gerbers <468dc41 的 PSDR261 Main Board>
$ python tools/reproduce_kicad.py --check          # 只验证，不覆盖工作副本
```

它依次执行：生成板 → `kicad-cli pcb drc --severity-all --refill-zones` →
导出 8 个 Gerber + Excellon 到 `dist/kicad/fab/` → （给了
`--pads-gerbers` 时）跑 `kicad_gerber_compare.py` → 写
`dist/kicad/SHA256SUMS`。`fab/` 是派生件，已加进 `.gitignore`，不入库；
板、对账报告与清单留在 `dist/kicad/`。

清单规则（文件头也写了）：

- **exact**：板文件按原样 sha256。生成器确定性已在 §C-17 证实，清单里记
  `5029bd02…288cc`。
- **normalized**：KiCad 的 Gerber/钻孔带 `%TF.CreationDate`、`G04 Created
  by KiCad … date …`、钻孔日期头和 `%TF.ProjectId`，每次运行都变；哈希前
  只删这几行，其余内容逐字节参与。8 个 Gerber + 1 个钻孔共 9 行。
- **DRC 报告不进清单**：KiCad 的 `silk_overlap` 同一输入两次运行会报出
  不同的配对顺序（计数与类别稳定），哈希不稳定；报告仍按 §C-16 入库。

验证：

```
$ python tools/reproduce_kicad.py --pads-gerbers ...   # 跑两次，第一次的清单先拷到仓外
$ cmp <第一次的 SHA256SUMS> dist/kicad/SHA256SUMS
# 无输出；两次生成的清单逐字节相同
$ python tools/reproduce_kicad.py --check
OK   PSDR_2.6.1_pcb_spike_full.kicad_pcb
OK   fab/PSDR_2.6.1_pcb_spike_full-B_Cu.gbr
...（10 个文件）
all files match the manifest
```

同时重跑的结果仍是 **795 条 DRC / 0 断点**、`0 个源 flash 未覆盖、
461/461 个钻孔对上`（`dist/kicad/gerber_compare.txt`）。

---

## 任务 D · 提交归档

待推清单（工单列的）与本轮实际状态：

```
Source/Makefile.linux        N  已在 96e06ce
Source/src/uart_hal_stub.c   N  已在 96e06ce
Source/src/{hal,main,misc,uart}.c  已在 96e06ce
docs/psdr-build-notes.md     已在 96e06ce
dist/kicad/                  N  本轮
dist/gerber/                 N  本轮（SolidWorks 大件未进仓，符合工单）
tools/                       N  本轮新增（工单没列，但转换与自证脚本是交付物的一部分）
docs/WO-psdr-takeover.md     M  本文件
```

2026-10-31 追加（原理图/网表，已提交为 `199d552` + `59ea7f4`）：

```
Hardware/PSDR.asc                              N  2.6.1 PADS Layout ASCII（源 468dc41）
Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf   N  2.6.1 原理图 PDF（源 468dc41）
tools/pads_asc_netlist.py                      N  网表提取器（标准库）
dist/netlist/PSDR_2.6.1_netlist.{csv,json}     N  391 器件 / 278 网 / 1132 引脚
tools/pads_asc_to_kicad.py                     N  KiCad 原理图生成器
tools/kicad_netlist_compare.py                 N  网表划分比对
tools/kicad_sch_geomcheck.py                   N  几何重合检查
dist/kicad/PSDR_2.6.1.kicad_sch                N  根图（A2，9 张层次图）
dist/kicad/PSDR_2.6.1-p02..p10.kicad_sch       N  子图 9 张，391 器件
dist/kicad/PSDR_2.6.1.kicad_sym                N  57 个符号
dist/kicad/PSDR_2.6.1.kicad_pro                N  工程文件
dist/kicad/sym-lib-table                       N  符号库表
docs/WO-psdr-takeover.md                       M  §C-10 二次修正 + §C-11/§C-12 新增
```

`Hardware/Enclosure/`（SolidWorks，未改）没有复制进 `dist/`，仓库里原样存在。

**不推上游 `MichaelRColton/PSDR`，不动 `PSDR_F7`，不碰射频逻辑。**

已推 `origin`（fork），单命令级代理，未改全局配置：

```
$ git -c ... push -u origin HEAD
To https://github.com/fe1iscurc0r/PSDR.git
   f30b11a..bb4d118  HEAD -> workorders/2026-10-30-psdr-takeover-linux-build-kicad
branch '...' set up to track 'origin/...'.
push rc=0

$ git fetch origin <branch> && git rev-parse HEAD^{tree} origin/<branch>^{tree}
c13cf4e8429d33acf9dcac786e6c7440923da69f   (local)
c13cf4e8429d33acf9dcac786e6c7440923da69f   (remote，tree 相同 = 内容逐字节一致)
ahead/behind = 0 0
```

2026-10-31 第二次推送（原理图 + 网表）：

```
$ git -c http.proxy=http://127.0.0.1:7890 -c https.proxy=... push -u origin HEAD
   61f1e20..59ea7f4  HEAD -> workorders/2026-10-30-psdr-takeover-linux-build-kicad

$ git fetch origin <branch> && git rev-parse HEAD^{tree} origin/<branch>^{tree}
2b6299b5d915821c714e85db1de4f30ac02578b8   (local)
2b6299b5d915821c714e85db1de4f30ac02578b8   (remote)
ahead/behind = 0 0
```

直连 `github.com:443` 本轮再次失败（`Failed to connect ... after 21071 ms`），
加 `-c http.proxy`/`-c https.proxy` 指向本机 7890 后一次成功——与 §D 末尾
记录的"api 通 ≠ git 直连通"一致，代理仍是单命令级，没有写进任何配置。

分支里的 `8d410f9` 是 `b8e60a8` 改写后的版本：原 message
body 误写"实物 12 层板中主控为 4 层"，实际是主控板 4 铜层；只改 message，树未动
（`git diff --stat backup/pre-msgfix HEAD` 为空）。

凭据坑（推之前连挂两次）：全局 `credential.helper` 指向
`C:/Program\ Files/Git/mingw64/bin/git-credential-manager.exe`，该文件不存在（GCM 实际在
`ucrt64/bin`）；而直接写带空格的绝对路径会让 git 的 shell 把它拆成 `C:/Program:`。
临时可用组合是"把 `ucrt64/bin` 加进 `PATH` + `-c credential.helper=manager`"。

**已永久修正**（备份 `~/.gitconfig.bak-20261031`）：用 `!` 开头的 shell 形式并加引号，
路径带空格也不会被拆，且不依赖 `PATH`：

```
[credential]
	helper =
	helper = !"C:/Program Files/Git/ucrt64/bin/git-credential-manager"
```

第一行空值用于清掉 system 级（`C:/Program Files/Git/etc/gitconfig`）里那条失效的
`manager`。改完不带任何 `-c` 覆盖实测：`git credential fill` 取到
`username=fe1iscurc0r`，`git push` 返回 `Everything up-to-date`、rc=0。凭据本身仍由
Windows 凭据管理器里的 `git:https://github.com` 提供，没有落地任何明文令牌。

2026-11-01 第三批（已提交为 `418f0a5` 并推 origin；本地/远端 tree 都是
`7117875038630437ce33e3a7baf4427a6c4dd156`，ahead/behind = 0 0）：

```
tools/pads_asc_decal.py                        N  decal/parttype/part 解析（283 行）
tools/pads_asc_route.py                        N  ROUTE 段 → 走线/弧/过孔（261 行）
tools/pads_asc_pcb.py                          N  全板 KiCad 10 发射器（456 行）
tools/kicad_gerber_compare.py                  N  KiCad plot ↔ 2.6.1 原始 Gerber 对账（196 行）
dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb N  4 层 / 278 网 / 5034 段 / 22 弧 / 419 过孔
dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt   N  DRC 309 违规 + 20 unconnected
dist/kicad/PSDR_2.6.1_spike_TX-Q_DRIVER_P.kicad_pcb  N  单网样例（C252/U4）
dist/kicad/drc_PSDR_2.6.1_spike_TX-Q_DRIVER_P.txt    N  样例 DRC：2 warning / 0 断点
docs/WO-psdr-takeover.md                       M  §C-13 新增 + C-0/SKIP-4/SKIP-5/制板口径更正
```

上游 PR #17 的正文写明「No footprints, hence no PCB. A board file is
deliberately excluded.」，所以 PCB 没有并进那个 PR 的 diff；改在该 PR 下补了
一条进度评论，指向 `418f0a5`，并列出板子的对账数字与三处缺口
（铺铜/板框/丝印）：

```
https://github.com/MichaelRColton/PSDR/pull/17#issuecomment-6553367174
```

评论的正文存在仓库外 `PSDR-build-artifacts/pr17-comment.md`，与贴出去的内容一致。

不提交的中间产物：上游 `468dc41` 的 2.6.1 原始 Gerber（对账基准）、本轮
KiCad Gerber/钻孔导出与实验板，都在 `D:\my git\PSDR-build-artifacts\` 下；
`dist/kicad/` 里上一轮的探针板与测试板已删除，只留下上面两块。

2026-11-01 第四批（铺铜、真实板框、丝印）：

```
tools/pads_asc_decal.py                        M  增加 GRAPHIC/LABEL 解析与图元列表（283 → 336 行）
tools/gerbparse.py                             M  修 G75 整圆弧（start == end 时零扫角）
tools/pads_asc_pcb.py                          M  发射板框/铺铜/丝印（456 → 873 行）
dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb M  + 67 段板框、12 个铺铜区、双向丝印
dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt   M  309 条 / 20 断点 → 795 条 / 0 断点
docs/WO-psdr-takeover.md                       M  §C-14 新增 + 状态/SKIP-1/SKIP-4/制板口径更正
```

`dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_prl` 是 KiCad 的本地 UI 状态，
不是交付物：没有提交，已从工作区删除。

已提交为 `03e22f7` 并推 `origin`（单命令级代理，未改配置）：

```
$ git push origin HEAD
   c858167..03e22f7  HEAD -> workorders/2026-10-30-psdr-takeover-linux-build-kicad
push rc=0

$ git fetch origin <branch> && git rev-parse HEAD^{tree} origin/<branch>^{tree}
8c75fe548b3ee2f56db346a536e10df036c92cd5   (local)
8c75fe548b3ee2f56db346a536e10df036c92cd5   (remote，tree 相同 = 逐字节一致)
ahead/behind = 0 0
```

2026-11-01 第五批（KiCad 10 铜层编号 + EDA 导入根因记录）：

```
tools/pads_asc_pcb.py                          M  内电层 1/2 → 4/6（KiCad 10 canonical），2 行
dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb M  仅 layer 声明 3 行；层数/网表/795 条 DRC/0 断点不变
dist/kicad/drc_PSDR_2.6.1_pcb_spike_full.txt   M  重跑时间戳与条目排序，795 条 / 0 断点不变
docs/WO-psdr-takeover.md                       M  §C-15 新增（+120 行）
```

已提交为 `108810b` 并推 `origin`（未碰 `upstream`）：

```
$ git push origin HEAD:refs/heads/workorders/2026-10-30-psdr-takeover-linux-build-kicad
   e456e40..108810b  HEAD -> workorders/2026-10-30-psdr-takeover-linux-build-kicad

$ git rev-parse HEAD^{tree} origin/<branch>^{tree}
7b3d746a9cc4d6a6c03709b671f186b77616bacb   (local)
7b3d746a9cc4d6a6c03709b671f186b77616bacb   (remote，tree 相同 = 逐字节一致)
ahead/behind = 0 0

$ git ls-remote upstream 'refs/heads/workorders/*'
（空）
```

§C-15 记录了 KiCad → 嘉立创EDA Pro 导入的三处根因（铜层编号、网络名反斜杠、
铺铜网络解析）；EDA 侧回读 4 铜层、278 网、391 器件、12 个铺铜边界与 67 段板框，
铺铜重建 12/12（10 个有填充、2 个 0 填充记为差异）。

---

### C-21 M4/A-3：八个层对的双向覆盖率（新工具 `tools/kicad_layer_coverage.py`）

方法：40 px/mm 栅格化，对侧先按 0.10 mm 膨胀再做差集，两个方向都报；
`G36/G37` 区域按多边形填充，CAM 侧统一减掉 +1000 mil（25.4 mm）平移。
跑在我们复现链产出的 `dist/kicad/fab` 与库内 CAM 包之间。

| 层对 | CAM 线段 | 我们线段/区域 | CAM→我们 | 我们→CAM |
|---|---|---|---|---|
| F.Cu ↔ `3 - top-art.GTL` | 47310 | 38221 / 57 | **100.00%** | 72.23% |
| In1.Cu ↔ `4 - L2.p.G1` | 39958 | 19076 / 8 | **100.00%** | 71.81% |
| In2.Cu ↔ `5 - L3.G2` | 49321 | 16680 / 1 | **100.00%** | 74.61% |
| B.Cu ↔ `6 - bot-art.GBL` | 47220 | 25988 / 50 | **100.00%** | 72.40% |
| F.Mask ↔ `2 - top-sm.GTS` | 4565 | 594 / 0 | **100.00%** | 13.92% |
| B.Mask ↔ `7 - bot-sm.GBS` | 5167 | 594 / 0 | **100.00%** | 12.75% |
| F.Silk ↔ `1 - top-ss.GTO` | 11663 | 11430 / 1 | 97.70% | 20.25% |
| B.Silk ↔ `8 - bot-ss.GBO` | 12956 | 12869 / 1 | 97.41% | 21.43% |

**能下的结论**：CAM 的四个铜层与两个阻焊层，100% 的图形像素都能在 0.1 mm 内被我们的板子解释；
丝印剩下 2.30%（顶面 89 个团块）与 2.59%（底面 160 个团块）没有解释，
但**最大团块只有 1.05 x 1.07 mm（顶）/ 1.05 x 1.18 mm（底）**，全是字符级笔段尺寸，
没有任何整块图元缺失——与 §C-17 记的位号字体（笔画字体 vs KiCad 描边字）差异同源。

**不能下的结论**：反向那几个低百分比（铜 72%、阻焊 12.7~13.9%、丝印 20~21%）**不是失败项**，
它量的是表示法而不是正确性——我们的铺铜是实心填充、PADS 是边界内缩 + 网格填充；
我们的阻焊是 594 个焊盘尺寸开口、CAM 是 4565/5167 条线段描出来的开口轮廓。
判等仍然只能用 §C-13/§C-16 那套 0.1 mil 的焊盘/钻孔逐位匹配，本表只回答"整层有没有漏东西"。

**过程里我自己写坏过一次，记下来免得后人重踩**：第一版把 `gerbparse` 的 `g.units` 又乘了一遍。
`gerbparse` 解析时已经按文件单位把坐标换算成**英寸**，再乘 units 等于把我们的图层缩了 25 倍，
跑出来 F.Silk 只有 0.22%、四个铜层 64~77%，与 §C-17 已实测的 100% 直接矛盾——
是那个矛盾把 bug 抓出来的，不是数字看起来"差不多"。修完才是上面这张表。

### C-20 M4/A-1：2.6.1 制造包逐层核对与锡膏母片实测（2026-11-02）

`Hardware/Gerbers/PSDR261 Main Board` 全 12 个文件结构（gerbparse，坐标已折成 mm）：

| 文件 | 出片者 | 光圈 | D03 闪光 | D02 线段 | 包围盒 (mm) |
|---|---|---|---|---|---|
| `3 - top-art.GTL` | PADS 9.5 | 30 | 659 | 46651 | 26.03,26.03..124.76,89.76 |
| `4 - L2.p.G1` | PADS 9.5 | 9 | 163 | 39795 | 同上 |
| `5 - L3.G2` | PADS 9.5 | 8 | 132 | 49189 | 同上 |
| `6 - bot-art.GBL` | PADS 9.5 | 27 | 602 | 46618 | 25.95,26.01..124.76,89.76 |
| `2 - top-sm.GTS` | PADS 9.5 | 26 | 242 | 4323 | 26.81,26.30..124.20,89.52 |
| `7 - bot-sm.GBS` | PADS 9.5 | 23 | 185 | 4982 | 25.95,27.75..124.23,89.32 |
| `1 - top-ss.GTO` | PADS 9.5 | 7 | 0 | 11663 | 25.40,25.40..124.49,90.40 |
| `8 - bot-ss.GBO` | PADS 9.5 | 8 | 0 | 12956 | 17.41,26.54..124.98,89.88 |
| **`top-paste.GTP`** | **gerbv 2.6A** | 26 | 194 | 3584 | 27.45,27.13..119.18,89.47 |
| **`bot-paste.GBP`** | **gerbv 2.6A** | 23 | 170 | 4270 | 25.95,27.75..124.23,88.86 |
| `9 - fabnotes.GBR` | PADS 9.5 | 1 | 0 | 670 | 25.40,25.40..125.40,90.40 |
| `0 - drillfile.TXT` | Excellon，非 RS-274X | -- | -- | -- | 钻孔已由 §C-13/§C-16 的 461/461 对账覆盖 |

**两层锡膏不是 PADS 出的，是 gerbv 2.6A 二次导出的**（文件头写明），这一点直接关系到
下单：它不是原始光绘，而是别人用查看器再导出来的东西。

**坐标框架对锡膏层同样成立**：+1000 mil 平移、不翻转（沿用 §C-13 已验证的约定），
拿源 decal 的焊盘中心（`transform(..., "rotate-then-mirror")`，Top 595 / Bottom 599，
与 KiCad 板里的 595/599 逐位相符）做最近邻配对：

```
top-paste.GTP   194 孔 | 距 Top 焊盘 ≤8 mil: 188 (96.9%)  中位 0.03 mil  最远 160.9 mil
bot-paste.GBP   170 孔 | 距 Bottom 焊盘 ≤8 mil: 170 (100%)  中位 0.03 mil  最远 0.05 mil
```

标签没反（做过 2×2：GTP 对 Bottom 只有 8/194，GBP 对 Top 只有 2/170）。
**6 个"远"孔全部落在 USB 座的 4 个固定片上**（`USB` pins 6/7/8/9，坐标
(80.7,931.1) (169.3,931.1) (169.3,565.0) (80.7,565.0) mil，逐位相符），
而 USB 在源里是底面件 ⇒ 顶面锡膏母片给底面件的屏蔽片开了孔。
这是实测事实；至于作者是有心双面开窗还是导错层，本机无法判（要看实物或原始工程）。

**两条必须记下的差异，不是通过项：**

1. **锡膏母片里没有一处 G36/G37 区域**（`G36` 出现 0 次），开口全靠 194+170 个闪光光圈
   加 3584/4270 条线段（线宽集中在 8.0/11.8/15.8 mil）。
2. 我们的参考板**不建模锡膏**（pad 里没有 `(paste ...)` 子层），但 KiCad 按默认规则照样
   能从焊盘生成：`F.Paste`/`B.Paste` 各 **574 个实心开口**。
   也就是说"我们的锡膏层"是 CAM 母片孔数的 **约 3 倍**。这两份**不等价**，
   所以下单开钢网只能用 CAM 包那两层，不能拿我们导出的顶替——
   这正是 §C-18 清单里把锡膏单列成"已知不覆盖"的原因，现在有了数字。

`9 - fabnotes.GBR`：1 个光圈、670 条线段、0 个闪光、无铜——纯文字/图框。
PADS 把文字画成线段，**本机无法把它读成文本**，所以制造说明的**内容审阅是 SKIP**
（要看 `TOP.png`/`BOTTOM.png` 或纸质 fab sheet），只核对到"它是独立一层、
不碰铜、不碰钻孔"。

### C-19 M4：SMT 贴装坐标表（2026-11-02）

工厂回流焊要的贴装表我们此前没有产出过。新工具 `tools/pads_asc_placement.py`
直接读 `*PART*`（经 `pads_asc_decal.parse_parts`）与 `*LINES*` 的 `BOARD` 记录，
不经过 KiCad 或 Gerber 插值，输出 `dist/fab/PSDR_2.6.1_placement.csv`。

约定（贴装表只有连约定一起才是对的，所以全写进工具文档字符串）：

- 38100 单位 = 1 mil；PADS 的 Y 向上（KiCad 的 Y 向下），本表**保留 PADS 方向**；
- 原点 = `BOARD` 多边形包围盒左下角，实测板框 **3937.00 x 2559.00 mil = 100.000 x 64.999 mm**，
  所以 `MidX = MidY = 0` 就是板角；
- `Side` 取 `*PART*` 的 mirror 位（`M` = Bottom），与 `psdr26.emn` 的 BOTTOM/TOP 标注一致
  （U304 是 `M`/BOTTOM，U16/U24/U30 是 `N`/TOP）；
- `Rotation` 是 PADS 存的 `ORI` 原值，不做底视翻转——底视换算是贴片机侧的事，
  原值 + `MirrorFlag` 两列都在表里，转换不丢信息。

对账两条，都是硬数：

1. **与 BOM**（`--bom-csv`，把 Ref Des 单元按 `C3,10,13-17` / `R97-99` 规则展开）：
   板上 391 件 = 采购件 332 + 单焊盘点位 42 + 螺钉孔/桨叶触点 11 + 基准点 6。
   展开后 BOM 340 行给出 323 个带号位 + 16 行是按名字列的单件
   （`USB`/`MICROSD`/`BOOT`/`ANT/VNA-IN`/`SPEAKER`/`EARPHONE`/`GPS_ANTENNA`/`RST`…）。
   结论：**每一个采购件都被 BOM 覆盖，BOM 之外的一律是基准点、螺钉孔、单焊盘点位**；
   另有 2 行 BOM 在本板上无对应件——`Battery connector`（线缆件）与 `Encoder`
   （编码器是另一块板），这是解释不是缺口。
2. **与已过 Gerber 验证的 KiCad 锚点**：391 个封装全比对，最大偏差 **0.0005 mm**
   （M6 的 73.9175 被表按 3 位小数四舍五入），其余逐位相符。
   板子本身的焊盘/钻孔已在 §C-13/§C-16 对过 2.6.1 CAM，所以这条链是**传递性地锚到制造数据**上的。

面别分布 Top 209 / Bottom 182。表里保留 `PadX_mil`/`PadY_mil` 原始整数，
便于以后按别的原点约定重算。

## 任务 E · 独立主线 `next`（2026-11-01）

### E-1 决定与依据

上游维护者 Jeff Benson 在 issue #7 明确邀请 fork 继续推进（2026-09-11 评论：
*"...please feel free to fork and help keep the project moving forward."*，
`https://github.com/MichaelRColton/PSDR/issues/7#issuecomment-5634997217`），
`LICENSE.md` 已是 MIT（Copyright (c) 2026 PSDR）。用户据此确认：

- 不再把“上游合入”当作前置条件；fork 作为独立开发线，`next` 为主线；
- 上游 `master` 是可选参考源，PR #17 保持 open，但不再阻塞任何工作；
- 仍然不推 upstream、不开新 issue；需要上游反馈时只用现有线程。

依据核对（2026-11-01）：`master` / `origin/master` / `upstream/master` 都是
`45acd0f`；上游 `PSDR_F7` 仍是 `ab2c8fd`、`PSDR_Rebuild` 仍是 `b9c0629`。

### E-2 分支拓扑

| ref | 作用 | 规则 |
|---|---|---|
| `master` | 上游镜像 | 只 fast-forward，不落自己的提交 |
| tag `fork-base/2026-10-30` | 临界转节点（annotated tag → `45acd0f`） | 标出分叉点，不动 |
| `next` | 我们的创作主线 | 从 `1d8e9ca` 起；所有工作最终汇入；不 force-push |
| `workorders/*` | 专题分支 | 完成后并入 `next`，保留历史 |
| `upstream-pr/*` | 只服务上游 PR | 不作主线来源 |

`fork-base/2026-10-30` 指向 clone 时的上游 `master`。F7 构建分支的基点是
`PSDR_Rebuild` 的 `b9c0629`，不是 `master`；并入 `next` 是一次真正的合并，
安排在 M2，不能当快进处理。

### E-3 里程碑

| 里程碑 | 内容 | 退出标准 |
|---|---|---|
| M0 建线（2026-11-01） | 推工单提交；打分叉 tag；建 `next`；写 `README.fork.md` | `origin/next` 与 tag 存在，tree 对账一致 |
| M1 转换闭环（2–4 周） | ~~1.4 mm 丝印三角~~（§C-17）、~~一条命令复现 + SHA256 清单~~（§C-18）、~~EDA 两处零铜铺铜~~（§C-15 补充：keepIsland 假设被证伪，真因是转换器丢优先级 + EDA `order` 小者优先；现场 12/12 已达成，复现工具 `tools/eda_epro2_pour_source.py` 已进仓库） | 重跑 md5 不变（达成）；EDA 12/12 有填充（达成，§E-9 在新主线上连读两次复测）；「完整转换→补丁→导入」自动化记 `unsupported`（宿主无 KiCad/`.epro2` 导入接口，§E-9） |
| M2 主线成型（1–2 个月） | 把 F7 构建线并入 `next`（目录隔离 `Source_F7/`），验证 F4/F7 构建与 KiCad 产物 | 两条固件线在同一主线可复现（达成，见 §E-7：两个 `make` 全 rc=0，产物与合并前逐字节相同）；冲突有记录（达成）；KiCad 产物在新主线上重跑复现链（达成，库内默认路径）；推送（达成，见 §E-8：`origin/next` = `1347d66`，tree 对账一致） |
| M3 硬件验证（硬件到位后） | RF bring-up、#6/#8/#9 | 每项有实测数据；无实物则 SKIP |
| M4 可制造/整机 | 以上游 `468dc41` Gerber 为生产基线 | 制造与整机验证记录 |

### E-4 M0 执行记录（2026-11-01）

工单分支先推送（单命令级代理，未改配置）：

```
$ git push origin HEAD:refs/heads/workorders/2026-10-30-psdr-takeover-linux-build-kicad
   108810b..1d8e9ca  HEAD -> workorders/2026-10-30-psdr-takeover-linux-build-kicad
push rc=0

$ git rev-parse HEAD^{tree} origin/<branch>^{tree}
afd777a5604ecaa1ad9fcf63dd5e824a53d86134   (local)
afd777a5604ecaa1ad9fcf63dd5e824a53d86134   (remote，tree 相同 = 逐字节一致)
ahead/behind = 0 0
```

分叉点与主线：

```
$ git tag -a fork-base/2026-10-30 45acd0f -m "Fork baseline: upstream master 45acd0f, ..."
$ git switch -c next 1d8e9ca
```

`README.fork.md` 写明独立 fork、MIT 归属（保留上游 `LICENSE.md`）、分支表、
已交付内容、未验证项与复现命令。

### E-5 M0 推送结果

`next` 与 tag 首次推送（同一单命令级代理）：

```
$ git push origin refs/heads/next refs/tags/fork-base/2026-10-30
 * [new branch]      next -> next
 * [new tag]         fork-base/2026-10-30 -> fork-base/2026-10-30
push rc=0

$ git rev-parse next^{tree} origin/next^{tree}
b2882d46c84b1e55f6b397594b73ba7cfd46f457   (local)
b2882d46c84b1e55f6b397594b73ba7cfd46f457   (remote，tree 相同 = 逐字节一致)
ahead/behind = 0 0

$ git ls-remote origin refs/heads/next 'refs/tags/fork-base/2026-10-30*'
a524e06cec7d7ac2d0be530916062a2f61282ecf  refs/heads/next
448528da85e0ca63144f0b03f15c8145d386d1d9  refs/tags/fork-base/2026-10-30
45acd0f5958cab4af5755e3da541cc4d3c6e2f12  refs/tags/fork-base/2026-10-30^{}

$ git ls-remote upstream 'refs/heads/next' 'refs/tags/fork-base/*'
（空）
```

推上去的 M0 提交是 `a524e06`（README.fork.md + 本节），父提交 `1d8e9ca`；
annotated tag 对象 `448528d` 剥开后指向上游 `45acd0f`。`master` 仍与上游
一致，upstream 未被写入。记录本节结果的提交随后推到同一分支。

### E-6 M1 落地与推送结果（2026-11-01）

三个提交推到 fork 的 `next`（单命令级代理，未改配置）：

```
$ git push origin HEAD:refs/heads/next
   9b050b3..a627c35  HEAD -> next
push rc=0

$ gh api repos/fe1iscurc0r/PSDR/git/ref/heads/next --jq .object.sha
a627c35458e553ef4ba87119b6dc5404c83c667e     ← 与本地 next 相同
$ git ls-remote upstream refs/heads/next
（空：upstream 未被写入）
```

| 提交 | 内容 | 验收 |
|---|---|---|
| `e4b5a06` | `fix(pcb)` 补 PADS `COPPER` 丝印（§C-17） | 10 mil 档 GTO 100%/100%、GBO 84.82%/73.04%；DRC 795/0 不变；0 flash 未覆盖、461/461 钻孔；重跑 sha256 不变 |
| `a627c35` | `feat(tools)` §C-18 复现链 + `SHA256SUMS`、§C-15 补充更正 EDA 零铜铺铜真因、README 过期 md5 更正 | 两次运行清单逐字节相同；`--check` 10 个文件全 OK |
| 本次 | §C-7 补充二（BOM 补丁＝上游 PR #18）+ 本节 | 见下 |

同日对外：`upstream-pr/bom-2.6.1-refdes-fix` @ `9c3ca93` → **PR #18**（未合并）；
`#14` 未再回帖（不在批准范围内）。

EDA 侧（§C-15 补充）：宿主从 3.2.203 升到 **4.1.60** 后，
`+3V3_FLIP_FLOP`/`V_SUPPLY` 两个铺铜靠改优先级做到 **12/12 出铜**并通过
`save → 关闭 → 重开 → 回读` 持久化验证；代价是 EDA 自带 DRC 507→**513**
（多的 6 条全是 `+3V3_FLIP_FLOP` 在 In1 的孤岛铜 `No Connection`；中途那次
读数里的 7 条铜区互相间距在宿主重启后复测归零，报数以重开后复测为准，见 §C-15），
且这份改法暂不可从仓库复现
（已另立任务）。

> 后注（同一天的 `786c412`）：可复现的那一半已经落地——`tools/eda_epro2_pour_source.py`
> 按 `Hardware/PSDR.asc` 的 `POUROUT` 尾部字段和 `PLANEFLAGS` 直接改 `.epro2` 里的
> `order`/`keepIsland`，12 条 `(net, layer, order, keepIsland)` 与 EDA 自己从 PADS 路由
> 出来的那份工程逐值相同。还缺的是「从转换开始跑一遍完整链并量到 12/12」这一步，
> 记在 §E-7 之后未完成任务里。

### E-7 M2 执行记录：F7 构建线并入 next（2026-11-02）

**先量代价，再决定怎么并。** 在 merge base `2c1530d`（2016-05-07，比 fork base `45acd0f` 老）上
比两条线对 `Source/` 的改动（对 `9de9b93` 改名**之前**的 F7 尖，带 `-M` 重命名检测）：
F7 那条线 **删 65 / 增 131 / 改 310**（另有 79 个树内改名，`--name-status` 共 585 行），
我们这条线改了 **6** 个，重叠 **5** 个（`Makefile.linux`、`Firmware_Build_Notes.md`、
`src/hal.c`、`src/main.c`、`src/misc.c`）。`git merge-tree --write-tree 786c412 2e19ad0`
复算改名之后再并的结果：**10 条 CONFLICT、涉及 8 个路径**，另有 7 次 auto-merge。
要紧的是 git 自己给出的三个 file-location 建议——它把我们这侧新增的
`Source/Makefile.linux`、`Source/Firmware_Build_Notes.md`、`Source/src/uart_hal_stub.c`
统统建议搬进 `Source_F7/`，再把 F4 那份 `Makefile.linux` 和 F7 那份判成 add/add。
照它的建议走，得到的就是一棵 F4 源码配 F7 构建脚本（或反之）的杂种树——这就是不能直接并的原因。

**做法：改名在前，合并在后。**

```
$ git checkout -b m2/f7-as-source-f7 9de9b93 && git mv Source Source_F7
2e19ad0 chore(merge-prep): 把 F7 构建线整体移到 Source_F7/，准备并入 next

$ git checkout next && git merge --no-ff m2/f7-as-source-f7
4dd2fca merge: 把 F7 构建线并入 next，用目录隔离而不是覆盖
 3156 files changed, 3098506 insertions(+)     ← 全是新增，Source/ 一行没动
```

`4dd2fca` 的两个父提交是 `786c412`（我们的 `next`）和 `2e19ad0`（改名后的 F7 线）。

冲突解决（8 个路径 10 条，逐条按「两侧各自保持自己那条线的字节」处理，不接受 git 的搬家建议）：

| 路径 | 冲突类型 | 取法 |
|---|---|---|
| `.gitignore` | content | 并集：两侧各加自己的构建目录 |
| `README.md` | content | `--ours`，以 `next` 上已交付的版本为准 |
| `LICENSE.md` | add/add | 同上 |
| `Hardware/BOMs/PSDR_2.0.0/PSDR2_BOMwithoutAmp.xlsx` | rename/delete + add/add | `--ours`（32,315 B）：这份就是上游 master `45acd0f` 的字节（`37c3da4` 引入且是其祖先），theirs 是 F7 线上 `2d3f7ee` 的旧版 26,838 B |
| `Source/src/misc.c` | modify/delete（F7 线把它删了）| 留 ours：F4 线必须要它，§B-2 那处 `#include "stm32f4xx_hal_conf.h"` 的修复就在里面 |
| `Source/Makefile.linux` → 建议搬到 `Source_F7/Makefile.linux` | file-location + add/add | 拒绝搬家：`Source/Makefile.linux` 保持 F4 那份，`Source_F7/Makefile.linux` 用 F7 那份 |
| `Source/Firmware_Build_Notes.md` → 建议搬到 `Source_F7/` | file-location | 同上，不搬；`Source_F7/` 里用的是 F7 线自己那份 |
| `Source/src/uart_hal_stub.c` → 建议搬到 `Source_F7/src/` | file-location | 同上；F7 线本来没有这个文件，HEAD 里 `Source_F7/src/uart_hal_stub.c` 确实不存在 |

auto-merge 过的两个源码路径（`hal.c`/`main.c`，两侧都改过）落成的仍是各自原字节：

```
$ git rev-parse HEAD:Source/src/hal.c HEAD:Source_F7/src/hal.c
82a2a8edda666f2cdf85056ae278d47ef54cc937   = 786c412:Source/src/hal.c（F4，未混）
3e4862232b488d30190e84743c9ea95950205027   = 2e19ad0:Source_F7/src/hal.c（F7，未混）
$ git rev-parse HEAD:Source/src/main.c HEAD:Source_F7/src/main.c
4339e617…   = ours（F4）      def78a44…   = theirs（F7）
```

**树是逐字节搬的，不是重写出来的：**

```
$ git diff --name-only 2e19ad0 HEAD -- Source_F7 | wc -l
0        # Source_F7/ 与改名前的 F7 线完全相同
$ git diff --name-only 786c412 HEAD -- Source | wc -l
0        # Source/ 仍是 M1 结束时的 F4 线，一个字节没被 F7 覆盖
```

**`Hardware/` 这次变了 97 个文件，方向是往前不是回退。** 分类是 56 个新增、
31 个纯改名（`R100`）、1 个 64% 相似改名、1 个「删除」（`Face Cover.SLDPRT` 其实是
搬进 `Hardware/Enclosure/Archive/`）、8 个内容修改。要紧的三处：

- `Hardware/PSDR.pcb` 2,058,120 → 1,899,112 B、`Hardware/PSDR.sch` 525,874 → 563,969 B、
  `Hardware/PSDR Schematic.pdf` 317,207 → 346,496 B。这三份在**上游 master `45acd0f`
  上最后一次改动是 2016-04-18 的 `1890b25`「PSDR 2.5 prototypes」**，而 2.6/2.6.1 的工作
  （`8ad6b3c`、`468dc41`）只在 F7/Rebuild 那条线上——`468dc41` 不是 `45acd0f` 的祖先。
  所以 F7 侧那份才是 2.6.1 的设计二进制，merge 是把主线缺的东西补进来。
  我们这侧自 merge base `2c1530d` 起没碰过这三个文件，所以 git 直接取 theirs，不报冲突。
- `Hardware/Gerbers/PSDR26 Main Board/`（14 个）和 `Hardware/Gerbers/PSDR261 Main Board/`
  （16 个）第一次出现在主线树里。§C-18 复现链默认 `--pads-gerbers` 指的就是后者，
  **合并前它在 `next` 上根本不存在**，M1 那两次跑是把上游 `468dc41` 的 Gerber 单独
  clone 到板外再显式指过去。
- 转换源 `Hardware/PSDR.asc` 两侧 blob 相同（`115cf190`，1,641,124 B），合并没动它。

合并后立刻用**库内**默认路径重跑一次复现链，确认 §C-16/§C-17 的对账基线没漂：

```
$ python tools/reproduce_kicad.py --check
...
OK   PSDR_2.6.1_pcb_spike_full.kicad_pcb
OK   fab/…-B_Cu.gbr … fab/…-In2_Cu.gbr
OK   fab/PSDR_2.6.1_pcb_spike_full.drl
all files match the manifest          # 10 个文件全 OK，rc=0

$ sha256sum "Hardware/Gerbers/PSDR261 Main Board/8 - bot-ss.GBO" \
            "../PSDR-build-artifacts/gerber261/Hardware/Gerbers/PSDR261 Main Board/8 - bot-ss.GBO"
0f7c904f65dd3e707c9228f49803eb07d3ca64541d5044b7d94408f9249fe271  (两个)
$ sha256sum "Hardware/Gerbers/PSDR261 Main Board/1 - top-ss.GTO" \
            "../PSDR-build-artifacts/gerber261/Hardware/Gerbers/PSDR261 Main Board/1 - top-ss.GTO"
b037b7f2e9a090eeed916207f42b0dd7dcca9687157232cdd51f279cd008026c  (两个)
```

**退出标准（两条固件线在同一主线可构建）——两条都过，且产物与合并前逐字节相同。**
WSL Ubuntu-24.04 + `arm-none-eabi-gcc 13.2.1`，两个 Makefile 只用树内相对路径，
所以改名不影响构建：

| 线 | 目录 | `make -f Makefile.linux -j` | text/data/bss | 锚点自证 |
|---|---|---|---|---|
| F4 | `Source/` | `F4_MAKE_RC=0` | 133644 / 2884 / 18152 | `anchor_check.py` 对 `Debug/PSDR.hex`：SP `0x20030000`、reset `0x080001B5` 双双 OK，`RESULT: PASS` |
| F7 | `Source_F7/` | `F7_MAKE_RC=0` | 103324 / 9144 / 17276 | 见下：向量锚点与作者 2018-06-21 的 `Source_F7/Debug/PSDR.hex`（上游 `457c270` 写入）对账 |

F7 的锚点对账结果第一次落到仓库里（之前只存在板外的
`../PSDR-build-artifacts/compare_vectors_out.txt`，任务 #20 的结论没有回写文档，这一条补上），
并把那次比对照成了可重跑的 `tools/anchor_check_f7.py`：

```
$ python tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex Source_F7/Debug/PSDR.hex
reference Source_F7/Debug/PSDR.hex
          base=0x08000000  SP=0x20050000  reset=0x080002F9  empty-slots=[7, 8, 9, 10, 13, 95]
built     Source_F7/build_linux_f7/PSDR.hex
          base=0x08000000  SP=0x20050000  reset=0x080001D5  empty-slots=[7, 8, 9, 10, 13, 95]
initial SP agree     : True
empty-slot pattern   : True
reset value agree    : False (not a gate)
words equal          : 7/118
RESULT: PASS
rc=0
```

判定与 F4 那条线同一口径：初始 SP 逐字节一致、空槽位模式一致，reset 向量的**取值**随
GCC/链接器布局移动——`docs/psdr-handoff/anchor_check.py` 把 reset 取值也当门（F4 上确实
相等），F7 上不能这么判，所以新脚本只把 SP 与空槽模式当门，reset 当观测值报出来。
`Makefile.linux` 的 `anchors` 目标在 F7 线上只 `echo` 参考路径、不含自动判定。
改名与合并没有移动任何一个字节（下面四对 sha256 全等）。

产物哈希与合并前留在板外的 artifact 一模一样（4 对全等）：

```
$ sha256sum ../PSDR-build-artifacts/PSDR-f7-head.hex Source_F7/build_linux_f7/PSDR.hex
5ce8588611ce4e6f5408d2858b8def5060ce45a417cc1779056829bc6bdbc43e  (两个)
$ sha256sum ../PSDR-build-artifacts/PSDR-f7-head.bin  Source_F7/build_linux_f7/PSDR.bin
f2c5874b52f23edba5d4ad68270e0b746c881c0d0263df2a4bfdc8e3d3ab4eec  (两个)
$ sha256sum ../PSDR-build-artifacts/PSDR.hex Source/build_linux/PSDR.hex
1c731aa599a49a8db4ec1ae591b37f9c47b093c88397430b69a66dff001a87a9  (两个)
$ sha256sum ../PSDR-build-artifacts/PSDR.bin Source/build_linux/PSDR.bin
1a824d1c1d47c0387f6c2cd6d5e09e5cbff991e1d1370a2ba87c67593829d9a7  (两个)
```

完整构建日志（含 newlib `_close`/`_write` 警告、`nineSmall` 符号尺寸警告这些本来就有的噪音）：
`../PSDR-build-artifacts/f7_build.log`、`f4_build.log`（板外，不入库）。

**上游自己的构建产物留在树里，这次没动。** `next` 上现在跟踪
`Debug/` 141、`TestingMakeFile/` 1530、`TestingMakeFile2/` 813 个文件。
构建产物本身的准确数是 **474** 个（`.o` 247、`.d` 109、`.lst` 107、`.hex` 3、
`.elf` 3、`.map` 3、`.bin` 2；根 `Debug/` 141 全是产物，`TestingMakeFile/` 174、
`TestingMakeFile2/` 159）——先前记的 364 是没把 `.d` 依赖文件算进去。
`TestingMakeFile*` 另有的 1284 份 `.c/.h/.s/.icf` 是 CubeMX 工程的源码，不是产物。
不在这次一并清理的理由：这两份 `Source*/Debug/PSDR.hex` 正是上面锚点自证的参考文件，
把它们从版本控制里撤掉是一次独立的决定，混进 merge 提交会让「树逐字节搬」这句自证失效。
已单独立项（#32，后以 `m2/untrack-build-artifacts` 分支 + PR 交付）。

`.gitignore` 这次只加了两条本次构建真正落地的目录（`Source/build_linux/`、
`Source_F7/build_linux_f7/`），加完 `git status --porcelain` 干净。

**补记：F7 构建线本身（任务 #18–#20）此前没写进本文档。** 那三步的结论只留在分支提交
信息 `9de9b93` 和板外日志里，正文里连 `0x20050000` 都没出现过，这里补齐要点：

- 基点：`PSDR_Rebuild` 的 `b9c0629`（不是 `master`），工作分支
  `workorders/2026-11-01-psdr-f7-linux-build`；那份 Makefile 当时叫
  `Source/Makefile.linux`（F7 分支上），M2 之后是 `Source_F7/Makefile.linux`。
  按 `.cproject` 的 Debug 配置转写，默认 `-O0`，`OPT=` 可覆盖，产物目录 `build_linux_f7`。
- 构建阻断 3 处（都是上游 Eclipse 配置里排除/漏掉的东西）：
  `stm32f7xx_hal_msp_template.c` 造成 MSP 符号重复定义 → 排除；
  `si5338.c`、`frequency_control.c` 缺 HAL 包含与 `handleI2C` 声明 → 补齐。
- 与作者 2018-06-21 的 `Source_F7/Debug/PSDR.hex` 对账：初始 SP 与空槽模式一致，
  reset 取值因链接器布局不同而移动。当时的四组对照（`compare_vectors_out.txt`）：
  参考 `reset=0x080002f9`；HEAD 线 `-O0` 与本文件在 `457c270` 上的 `-O0` 都是
  `0x080001d5`；`457c270` 的 `-Os` 是 `0x080001cd`——也就是优化档会移动 reset 取值，
  默认 `-O0` 给出的才是现在记录的这一组（尺寸 `103324/9144/17276`）。
- 上面这些现在都能在新主线上重跑：`make -f Makefile.linux -j` 与
  `python tools/anchor_check_f7.py`。

> **更正（2026-11-02 晚）**：`4dd2fca` 的提交信息里把 F7 线写成"CubeMX + FreeRTOS 重写"，
> 这个说法不准确——F7 树里 **没有任何 FreeRTOS**（`xTaskCreate` 全树 0 处），两条线都是裸机
> 超级循环，差别在 HAL 骨架、Si5338 频率合成与驱动分层。提交信息属历史不改，以
> `docs/PSDR-firmware-survey.md` §1 为准。

### E-8 M2 推送结果（2026-11-02 上午）

批准之后推送（单命令级代理，未改 git 配置）：

```
$ git -c http.proxy=http://127.0.0.1:7890 push origin refs/heads/next
   786c412..1347d66  next -> next
push rc=0

$ git -c http.proxy=http://127.0.0.1:7890 ls-remote origin refs/heads/next
1347d6641c415c90345e881f94ad4ca9589a4882  refs/heads/next

$ git rev-parse next^{tree} origin/next^{tree}
8824739cee03a0d6e1817bb5ec714e527d8be816   (local)
8824739cee03a0d6e1817bb5ec714e527d8be816   (remote，tree 相同 = 逐字节一致)
$ git rev-list --left-right --count origin/next...next
0 0

$ git -c http.proxy=http://127.0.0.1:7890 ls-remote upstream refs/heads/next 'refs/tags/fork-base/*'
（空：upstream 未被写入）
```

远端 `4dd2fca` 另用 GitHub API 复核过：能按该 sha 取到，`stats.additions = 3098506`
与本地 `git show --stat` 一致。commit 对象是内容寻址的，远端给出同一个 sha 就等于
给出同一对父提交——本地 `git cat-file -p 4dd2fca` 里那两行是
`parent 786c412…` 和 `parent 2e19ad0…`，也就是它到远端仍是一次真合并，没被压扁。
推送上去的两个提交是 `4dd2fca`（M2 合并）与 `1347d66`（§E-7 记录 +
`tools/anchor_check_f7.py` + README/.gitignore）。回滚点仍是 `786c412`：
`git push origin 786c412:refs/heads/next --force-with-lease` 即可退回，
不涉及别人在这条分支上的工作。

M2 退出标准全部达成，E-3 表里那一行可以收掉。剩下的独立事项：
#31（要在 EDA 宿主上跑一次完整「转换→补丁→导入→量 12/12」）和
#32（上游那 474 个构建产物要不要撤出版本控制）。

### E-9 M2 之后：现场铺铜在新主线上复测 + #31 的能力缺口（2026-11-02 上午）

E-8 之后又推了一个文档提交，`origin/next` 的现头是 `b0f1422`：

```
$ git -c http.proxy=http://127.0.0.1:7890 push origin refs/heads/next
   1347d66..b0f1422  next -> next
push rc=0
$ git rev-parse next^{tree} origin/next^{tree}
4ddccb12948de1607366382f4b261fda3b81530d   (两边相同)
$ git rev-list --left-right --count origin/next...next
0 0
```

中间两次 `ls-remote` 撞上 `schannel: failed to receive handshake`（git 传输通道的 TLS
抖动，不是凭据问题），所以改用 GitHub API 独立确认远端分支头：
`list_commits(sha="next")` 返回的第一条是 `b0f1422`，往下依次 `1347d66`、`4dd2fca`；
`list_branches` 在 `MichaelRColton/PSDR` 只列出 7 条分支、没有 `next`（上游仍未被写入）。

**现场铺铜复测**（EDA 4.1.60 + connector 1.15.0，文档 = PCB `PSDR_2.6.1`
`cf6546e2f1507a17`，就是 M1 那份 12/12 的文档；它的输入板子字节与合并后主线上
`--check` 通过的 `dist/kicad` 完全相同）：

```
$ easyeda pcb poured-list --doc cf6546e2f1507a17      # 连读两次，结果逐个相同
net                layer  铜皮块数
+3V3               In1      1
+3V3               TOP     16
+3V3_CPU           In1      6
+3V3_CPU           TOP      1
+3V3_CPU           TOP     26
+3V3_FLIP_FLOP     In1      7      ← M1 靠改优先级救回来的那个
+5V_BOOST          TOP     19
BOOST_LOOP         TOP     10      ← §C-15 基线记的是 11，见下
GND                In2     26
GND               TOP     296
GND               BOTTOM  360
V_SUPPLY           TOP      4      ← M1 靠改优先级救回来的第二个
non-empty pours: 12/12   total fills: 772
```

判读：**12/12 仍然成立**，`+3V3_FLIP_FLOP` 的 7 块孤岛铜也在（与源里 7 条 HATOUT 一致）。
唯一和 §C-15 基线不同的是 `BOOST_LOOP`：那次记 11 块，现在两次连续读都是 **10** 块。
差一块、且不是零铜那一类，所以不是优先级回归；最可能是宿主重启 + 铺铜重建后的
一次重新连通/分裂计数漂移（§C-15 里已经记过「EDA 的 DRC 与铺铜读数在未 settle 时会漂」）。
本轮没有为了追这一格去动写入——追它要做 `pour rebuild`，那是写操作，代价大于这一格的信息量。
原始回取留档：`../PSDR-build-artifacts/eda_poured_next_mainline.json`（板外）。

**#31 剩下的那半是能力缺口，不是没做。** 要把「转换→补丁→导入→量 12/12」全自动跑通，
需要两个宿主侧文件动作；把 typed 目录（167 个 action）和通道 B 的
`pcb_document_action` 枚举都翻过一遍，只有这些 import：

```
typed actions:   pcb.import_changes（原理图网表→PCB）、pcb.import_autoroute、
                 project.export / project.export_source、pcb.silk.import_svg
通道 B 的 import: import_changes / import_auto_route_json / import_auto_route_ses /
                 import_auto_layout_json
```

**没有** KiCad→EDA 的板子导入，也**没有**把打过补丁的 `.epro2` 导入回 EDA 的动作。
按 easyeda-agent 的硬红线，这两步不能用 GUI 自动化补，所以标 `unsupported`：
从仓库一键到 EDA 现场的链路，缺的是宿主接口，不是脚本。能做且已做的是两侧的可复现部分——
`tools/reproduce_kicad.py --check`（仓库内到 KiCad 产物）+
`tools/eda_epro2_pour_source.py`（`.epro2` 字节级补丁，12 条值与 EDA 自己的 PADS 路线逐条相同）
+ 本节这份现场 12/12 回读。人工在 EDA 里点这两下导入仍然是可行的，但那属于现场操作，
不能当复现链的证据。#31 据此改写口径：工具侧完成，端到端自动化记 `unsupported`。


### E-10 #32：把上游构建产物移出版本控制（`m2/untrack-build-artifacts`）

做法与边界：

- 只动索引，不动磁盘：`git rm --cached --pathspec-from-file`，474 个路径；
  文件仍在本地工作树里，历史里一个字节都没丢（`git log -- Diff 仍可取回）。
- 精确范围 = 根 `Debug/`（141，全是产物）+ `TestingMakeFile/` 174 + `TestingMakeFile2/` 159
  里的 `.o/.d/.lst/.map/.elf/.hex/.bin`。
- **不撤**的两份锚点参考：`Source/Debug/PSDR.hex`（F4，SP `0x20030000` /
  reset `0x080001B5`）与 `Source_F7/Debug/PSDR.hex`（F7，SP `0x20050000` /
  reset `0x080002F9`）——`git ls-files` 复测仍在册。
- `TestingMakeFile*` 里的 1284 份 `.c/.h/.s/.icf` 继续跟踪：那是 CubeMX 工程源码，
  不是产物；`.gitignore` 新块只按扩展名点掉产物。
- 根 `Debug/` 不需要新规则：本文件第 1 行 `/Debug` 早就在忽略它，只是这 141 个文件
  此前已被跟踪所以规则不生效；`git check-ignore -v` 两条都验过。
- 顺带查实：根 `Debug/PSDR.hex`（268,490 B）与两份参考 hex 都不同，但它的向量锚点是
  `SP=0x20050000 reset=0x080002F9`，即作者 F7 那批的又一次落盘；撤掉跟踪不丢证据，
  因为 `Source_F7/Debug/PSDR.hex` 仍在册。

验证：`git status --porcelain` 只有 474 条 `D` 加一条 `.gitignore` 的 `M`；
两条 `check-ignore` 命中；KiCad 复现链与两条固件线都不读这些路径。

**合并之后必须更正一句（2026-11-02，PR #1 已合并为 `4d4549f`）。**
我在分支上写的「只动索引不动磁盘」「文件仍在盘上」只在**提交那一刻**成立：`git rm --cached`
确实不碰盘上的文件。但任何检出这个提交的 `git checkout` / `git merge --ff-only`
都会把这些「新版本里不再跟踪」的路径**从工作树删掉**。实测就是这样的：

```
$ git merge --ff-only origin/next
 delete mode 100644 TestingMakeFile2/PSDR/build/usb_otg.lst
 delete mode 100644 TestingMakeFile2/PSDR/build/usb_otg.o
$ ls Debug
ls: cannot access 'Debug': No such file or directory          ← 盘上没了
$ git cat-file -s 568a079:Debug/PSDR.hex
268490                                                          ← 历史里完好
```

准确的口径应该是：**历史不丢字节，工作树会丢**（对任何人重新检出都一样）；
要拿回来用 `git checkout 568a079 -- Debug TestingMakeFile TestingMakeFile2`，
或者从 `568a079` 那棵树单独取文件。
影响面复核过：我们这几条链都不读这些路径，两份锚点参考
`Source/Debug/PSDR.hex`、`Source_F7/Debug/PSDR.hex` 仍在册且在盘上，
主线跟踪文件数 4008 → 3534（差 474），`git ls-files -o -i` 显示 531 个
忽略项仍在盘上（我们自己的构建目录等）。
这条更正同时说明：撤销这次变更不需要 revert，检出旧提交就能把文件拿回来——
`git revert 4d4549f` 也在，只是没必要。

### F 下一步规划（2026-11-02 定，按「不需要硬件就能验证」排序）

现状盘点：M0/M1/M2 都在 `next` 上；上游 `PR #17`（KiCad 原理图）与 `PR #18`
（BOM 位号修正）都还是 `OPEN`，上游最后一次合并是 2021-03-05 的 `#15`，
实质停摆。M2 之后 `next` 里第一次有了 2.6/2.6.1 的 CAM 与 PADS 资料，
所以下面 A 道才成立。

**A 道：可制造基线里不需要硬件的那一半（建议下一个就做这个）。**
库内 `Hardware/Gerbers/PSDR261 Main Board` 是完整的 15 文件包：
`0 - drillfile.TXT`、`1/8 GTO/GBO`、`2/7 GTS/GBS`、`3/6 GTL/GBL`、
`4 - L2.p.G1`、`5 - L3.G2`、`9 - fabnotes.GBR`、`top-paste.GTP`、`bot-paste.GBP`
加 TOP/BOTTOM 预览与原始 zip。要做三件，都能纯离线证：

1. **逐层核对制造包本身**：层类型/极性/单位/原点（这批 Gerber 带 +1000 mil 平移，
   §C-13 已钉死）与四层铜、两层阻焊、两层丝印、两层锡膏、钻孔一一对齐；
   现在 §C-13/§C-17 只核过铜、丝印、钻孔，**锡膏与 fabnotes 没核过**。
2. **SMT 贴片机坐标表**：从 `Hardware/PSDR.asc` 的 `*PART*` 记录出 mid-X/mid-Y、
   面别、角度、位号，和 PR #18 修好的 BOM 位号对账（391 个封装逐个能落）。
   工厂回流焊要的是这张表，我们目前没产出过。
3. **制造包 vs 我们复现的 `dist/kicad/fab` 逐层比对**：把 §C-18 那条命令的对账
   范围从「焊盘 + 钻孔」扩到全部 8 个铜/阻焊/丝印层，锡膏层另列（我们的
   板子没生成锡膏层，这是已知差项，要么补生成、要么如实记为不覆盖）。

   验收口径：每条都能给出「命中/未命中」的计数和残差位置，不许用综合分代替。

**B 道：M3 硬件相关，缺实物就 SKIP，不许假完成。**
现在能先做的是把「插上就能跑」的准备做完：电源/电流测点清单、显示屏与编码器
冒烟步骤、`#6/#8/#9` 那几条射频问题的**观测方法**（不是修法——按边界我不改射频逻辑），
写成一份带判据的检查表。真板到位再按表跑，跑不了的项目逐条记 SKIP 与原因。

**C 道：对外。**
`#17`/`#18` 无人回应是常态（上游 2021 年后没动过），不催、不重开新 issue（边界）；
`#14` 只在有实质新证据时补一条。有实质新证据的那件事是：`next` 现在能同时构建
F4/F7 两条固件线，并且 2.6.1 的 CAM 包进了主线——这直接影响「这个 fork 能不能
拿去下单」，值不值得写进 `#14` 由你定，我不擅自发。

**D 道：明确不做。**
不动上游 `PSDR_F7`/`PSDR_Rebuild` 分支；不修射频前端；不试图转换
`Hardware/Enclosure/` 的 SolidWorks 文件；不在云服务落盘源码；
EDA 侧不用 GUI 自动化补那个导入接口缺口（§E-9）。


## 任务 G · 上游 issue 逐项处置（2026-11-02）

按「我们已有的数据能不能推到可交付」过了一遍上游全部 11 条（6 开 5 关）。
用户定的边界：**先不碰固件源码**（#8/#9/#16 的固件改动不做，避免对着别人手写的
历史代码做 vibecoding），只做资料活；对外**能出 PR 就出 PR，回帖只在有硬证据时**。

| # | 处置 | 依据 |
|---|---|---|
| 14 | **本轮解决**（BOM 补 DNP 说明，PR 待你批准） | 网表逐件核到底，见 G-1 |
| 13 | 能给「替代件必须满足的约束」，**不替作者断言料号映射、不选替代件** | 见 G-2 |
| 16 / 6 | 不碰（射频前端） | 既有边界 |
| 9 / 8 | 不碰源码（本轮决定）；可另出诊断文档 | 既有边界 + 本轮决定 |
| 11 / 10 / 7 / 2 / 1 | 已关，无需动作；#10 的实质内容已由 §B + `docs/psdr-build-notes.md` 覆盖 | — |

### G-1 #14：四件 DNP 的网表证据与 BOM 改动

上游问的是「这四件是被删了、还是 BOM 该更新」，跟进者担心的是「要不要用 0 Ω 桥接」。
用 `tools/pads_asc_netlist.py` 从 `Hardware/PSDR.asc` 现取（391 件 / 278 网 / 1132 脚）：

```
C307  CAP_0603  pin1 = $$$2472（另一只脚只有 U314.8）  pin2 = GND
C320  CAP_0603  pin1 = GND                              pin2 = $$$2458（另一只脚只有 U314.14）
R72   RES_0603  pin1 = MIXER_LO2N（还有 C71.2, L41.1）  pin2 = MIXER_LO2P（还有 C73.2, L41.6）
R79   RES_0603  pin1 = MIXER_LO1N（还有 C78.2, L81.1）  pin2 = MIXER_LO1P（还有 C80.2, L81.6）
```

判定：**四件没有一件是串联元件**，所以拆掉都不会断通路，都不需要 0 Ω 桥——
`C307/C320` 是从 AD8302（U314，BOM 第 66 行 `AD8302` / `AD8302ARUZ-ND`）的两个脚到地的旁路；
`R72/R79` 是跨在混频器本振对（L41 / L81 的两个脚）上的桥接/阻尼电阻，
两侧网络本来就各自接在变压器绕组上，**装 0 Ω 反而会把 LO 的一对短掉**。
封装和铜都在板上（网表就是从板子里提出来的），所以是「按设计不装」，不是「被删」。

BOM 现状（这解释了为什么上游会问）：`Vendor Part #` 列写 `NA`，
而 `OPEN` / `DNS` 其实写在 **`Value` 列**——约定藏在错误的列里；
`Value` 旁边那个**无标题的列**（2.6.1 是 J，2.6 是 L）才是作者自己放备注的地方
（现存 9 行在用，含 "Buy but do not populate"）。所以本次只往备注列加字，不动任何既有单元格语义。

改动（两份 BOM，用 `bom_patch/patch_bom_cells.py`：按 Ref Des 定位、目标格必须为空才写、
回写源字体 Arial 与列宽，再用逐格 dump 对账）：

| 文件 | 格 | 内容（要点） |
|---|---|---|
| `PSDR2.6.1_BOM.xls` | `R26C10` (J) | C307/C320 是旁路到地，不在串联位置，无需 0 Ω |
| `PSDR2.6.1_BOM.xls` | `R64C10` (J) | R72/R79 跨 LO 对，**不要装 0 Ω**（会短接） |
| `PSDR2.6_BOM.xls` | `R26C12` (L) | 同上 |
| `PSDR2.6_BOM.xls` | `R62C12` (L) | 同上 |

逐格对账（相对 `next` 原基线）：2.6.1 共 4 处内容变化 = 新增 2 格备注 + PR #18 的两处位号
（`R6,14,268`→`R268`、`R97,-99`→`R97-99`）；2.6 共 3 处 = 新增 2 格 + `R97,-99`→`R97-99`。
黄色底 `bg=0xffff00` 与字体 `Arial/10` 保持，唯一副作用是列宽按 .xls 存储单位回写、
每列差 1–2 单位（PR #18 里已披露过同一现象）。

### G-2 #13：能说清的与不能替你拍的

能说清（都在仓库数据里）：#13 报不可得的两颗，`599-1068-1-ND` 是 U304，
`1465-1374-1-ND` 是 U16/U24/U30；**设计数据里两处名字都指向具体型号**——
封装名 `MMIC-AMP_HMC482ST` / `RF_DPDT_MASWSS0129TR` 与 PADS `*PARTTYPE*` 的
`MMIC-AMP-HMC482ST` / `RF_DPDT_MASWSS0129TR`；仓库里 `OctopartBOM.csv` 这两行的
`Manufacturer` / `MPN` 是**空的**（第 75、77 行只剩 DigiKey 号），这正好是 #13 的困境本身。
跟进者在 #13 里已找到 DigiKey 外的货源（SXB-2089Z；MASWSS0129TR-3000），
2025-10-30 又报 MASWSS0129 在欧洲也无货。

不能替你拍的：**选型本身**。那是射频决定，越界。能做的是给替代件列
「必须满足的约束」（下面 G-3 那表：脚数、偏置注入位置、控制脚由哪个 MCU 引脚驱动）。

**本节初稿写错过一次，更正如下。** 我当时写「检索不到 DigiKey 号到厂商料号的映射，
所以不填 `Mfg`/`Mfg Part #`」——那是没搜过自家文档与自家文件就下的结论：
映射**就写在这份 BOM 里**。U304 那行的超链接目标是

```
https://www.digikey.com/product-detail/en/rfmd/SXB-2089Z/599-1068-1-ND/937042
```

即 `599-1068-1-ND` = **RFMD `SXB-2089Z`**，封装名 `MMIC-AMP_HMC482ST` 是过期标签
（作者备注「DigiKey 号才算」正是这个意思）；这与 §C-7 第 3 条早已给出的结论一致。
这条链接为什么现场一度抓不到：BIFF8 把超链接放在**UTF-16 的流**里，
按 ASCII 直接 grep 二进制是零命中，得按 UTF-16 扫（本次就是这么找到的）。
所以下面 G-3 的判据改成：**U304 有表内权威，可以填；开关那行只有名字，不能填。**

### G-3 #13 的实际局面（2026-11-02 复核）

#13 报的两颗，**型号并不是未知，断的是供货**：

| BOM 行 | DigiKey 号 | 表内证据 | 结论 |
|---|---|---|---|
| Item 77 `U304` | `599-1068-1-ND` | 该行超链接直指 `rfmd/SXB-2089Z/.../937042` | 从始至终买的是 **RFMD SXB-2089Z**；#13 说的「DigiKey 外找到的 SXB-2089Z」是**同一颗**，不是替代 |
| Item 79 `U16,24,30` | `1465-1374-1-ND` | **该行没有超链接**（89 行只有 8 行有） | 型号只能靠 `Type`/`*PARTTYPE*` 名 `MASWSS0129TR`；#13 的 `MASWSS0129TR-3000` 是整盘包装码 ⇒ **换渠道不换料** |

结构性问题（值得单独一个 PR）：`Mfg` / `Mfg Part #` 两列 89 行里只有 5 行有值，
整张表按 DigiKey SKU 索引——SKU 一死就没有可搜的料号。嘉立创/立创商城按 MPN 索引，
下单前得把 MPN 补齐。

替代件必须满足的硬约束（全部取自设计数据，不是选型建议）：

```
U304            decal 3 脚：RFIN / GND / RFOUT
                偏置注入在输入网络：RF_AMP_IN = BIAS.1 + C13.2 + L11.1 + U304.1
                输出：RF_AMP_OUT = C305.2 + L19.1
U16/U24/U30     decal 13 脚；V1/V2 是控制，G1/G2 与 1/2/8/9/13 接地，4/6/10/12 是 RF 口（各经隔直电容）
                控制脚直接吃 MCU：U16 = PA0(U121.22)+PE6(U121.5)
                                  U24 = PC1(U121.16)+PA6(U121.30)
                                  U30 = PB2(U121.36)+PA7(U121.31)
```

顺带：这六根控制脚正是 #16 里 maintainer 说的「RF 开关需要配置」的那六根——
我们只把线找齐，没碰固件（按边界）。

PR #18 的正文按上面这套事实重写过：删掉「离线无法确认映射」那句错话，
改成「型号在表内，缺的是供货；U304 可填 MPN，开关那行不填；补 MPN 是另一个 PR」。

### G-4 国产化替代：**只在本树的提案，不报上游，且大概率不做实验**（2026-11-02）

用户决定：这条不上报上游，PR #18 里一个字不提；本树只留**提案**，并明确说明
**很可能没有时间去真实验板验证**。所以本节的作用是：把"哪些件理论上可换"算清楚
存下来，万一以后要做，不用重新推；不做也不欠谁结论。

判据不靠猜，用网表按连接性分（`tools/pads_asc_netlist.py` 现取，275 个无源件）：

```
             总数 | RF 侧 | 非 RF 侧
CAP          137 |    41 |    96
RES          104 |    30 |    74
IND/BEAD       3 |     2 |     1
其它 decal    31 |    --   |  --
非 RF 侧且只有两脚（去耦/上拉候选域）：188
```

RF 侧的界定：网络名命中 `RF_ / MIXER_ / FILTER_ / ANT / VNA / TX_ / RX_ / IF_ / LO_ / PA_ /
IMP_BRIDGE / AMP_SWITCH` 等前缀，**或**匿名网络（`$$$...`）连到射频 IC 的脚。
按这条规则，射频匹配网络、隔直电容、偏置磁珠与混频变压器全部落在不可换一侧。

三条硬约束（比"国产/进口"更重要）：

1. **封装必须逐字相同**。我们的生产基线是上游 `468dc41` 的 Gerber——改 footprint
   等于换板，前面所有 Gerber/钻孔/丝印对账结论都不再适用，也不能再说"按上游 CAM 下单"。
2. **射频路径不按"同值同封装"判等**。同一只 100 nF 在 0603 与 0402、不同介质（X5R/X7R/C0G）
   下 SRF 与 Q 差很多；混频器 LO 对上的电阻还牵涉幅相平衡。所以 41+30+2=73 个 RF 侧无源件
   留在"不动"这一栏。
3. **任何替代结论必须带实测**（增益/损耗、谐波、噪底、灵敏度、电流），
   没实测就只写"未验证"，不写"可用"。这是本项目一直在守的口径。

若将来真要试，做法上也有一条不越界的走法：只在 `experiments/*` 分支上、
只在上面那 188 个非 RF 两脚件里选，逐件替换 + 逐件记录，且**不动固件源码、不动射频前端**；
主线的 BOM 与制造文件保持上游原样，PR 也不带这类内容。

本节记录"提案存在但未执行"这一状态本身，上游不需要知道，也不需要任何人来批准一个
我们不打算做的实验。

### C-22 #37：岛铜间距到底按哪条规则、能证到什么程度（2026-11-02）

**先纠正我自己一直用的一句话**：我一直写"按源里的 8 mil 复核岛铜"，这是错的。
`Hardware/PSDR.asc` 的 `CLEARANCE_RULE`（唯一一组，单位 38100/mil）逐项读出来是：

```
TRACK_TO_TRACK / VIA_* / PAD_* / SMD_*   = 304800 / 38100 =  8 mil   （通用间距）
COPPER_TO_TRACK / VIA / PAD / SMD / COPPER = 457200 / 38100 = 12 mil  （铺铜到任何铜）
铜到板框                                      = 762000 / 38100 = 20 mil
```

所以对铺铜来说，源里该守的是 **12 mil**，不是 8 mil。而 EDA 工程实际用的是：

```
信号间距 clearanceMil        = 6 mil
线对线 clearanceTrackTrackMil = 4 mil
铺铜/内层 Plane lineClearance  = 0.254 mm = 10 mil   ← 比源的 12 mil 紧 2 mil
```

**现状实测（只读，跑了一遍 DRC）**：总 513 条，其中与铺铜区有关的只有那 6 条
`Copper Region(Filled) / Connection Error`（`+3V3_FLIP_FLOP` 的孤岛，源里本来就是 7 条 HATOUT）；
**没有任何** `Copper Region to Copper Region` 间距违规。§C-15 里记的"中途见过 4 条 In1 加
3 条 F.Cu 的铜区互相间距"，在今天的复测里不复现——再次印证那句"EDA 的 DRC 在重建未 settle
时会漂，报数以重开复测为准"。

**结论（这条按 `unsupported` 收，不是"已通过"）**：要按源的 12 mil 去复核铺铜几何，
现有接口做不到非破坏性地做——

- `easyeda pcb drc-rules-set` 对铺铜间距是**只升不降**，且文档明确要求随后
  `pcb pour-rebuild`；而 rebuild 会按新间距重排铜皮，**改掉我们 12/12 验证过的那份几何**；
- 用 GUI 改规则再跑 DRC 是硬红线禁止的（不是没有别的办法的问题）；
- 只升规则不 rebuild 也不会把既有铜重排，量出来的仍是旧几何，等于没量。

所以能确凿说的只有两条：**铺铜实际间距按 10 mil 生成（源要求 12 mil）**，以及
**在 EDA 自己的 6/10 mil 规则下，当前几何没有铜区互相间距违规**。
"岛铜符合源规则"这句话现在**不能写**。

真要收口，得接受一次 rebuild，做法（写在 §C-15 的设备上，用**工程副本**做）：
副本里把铺铜间距升到 12 → `pcb pour-rebuild` → DRC 读违规 → 与现在的 12/12 逐区比对
（7 块孤岛大概率会缩小或消失，那时要重新决定"孤岛是否该保留"）。
这一步会改变可制造几何，属设计决定，不该由自动化悄悄做掉。

### E-11 现场数据归档、EDA 导入 SOP、杂务（2026-11-02）

**为什么归档**：EDA 现场读数（12/12、DRC 513 构成）依赖一台开着 4.1.60、
且按手工步骤导入过两次的宿主，**当时那一刻的数据不可再生**。它们原来只躺在板外
`D:/my git/PSDR-build-artifacts/`，没备份也没入库。现在落进 `evidence/`：

```
evidence/README.md                        判读标准与三条必须知道的话
evidence/eda_poured_2026-11-02.json       12/12、772 块、+3V3_FLIP_FLOP 孤岛 7 块（不可重跑）
evidence/eda_drc_2026-11-02.json          总 513 = 73+14+419+6+1（不可重跑；507 基线原件未留，已注明）
evidence/firmware_builds_2026-11-02.json  两条固件线尺寸/锚点/hex+bin sha256（可重跑，留作合并前对照）
evidence/layer_coverage_2026-11-02.json   八层双向覆盖率（可重跑）
evidence/paste_check_2026-11-02.json      锡膏配对 + 层标签 2×2 + 6 个 USB 屏蔽片开口（可重跑）
evidence/bom_roundtrip_2026-11-02.json    PR #18 那份 .xls 重存的副作用核查
```

数字不是手打的：DRC 那份是从板外原始回读重新按分组求和算出来的（73+14+419+6+1=513，
正好等于 §C-15 记的 513，也自证了"多的 6 条是孤岛铜 No Connection"那句）；
构建那份现算 hex/bin sha256 并与合并前产物对比；覆盖率与锡膏两份是各自脚本重跑一遍
取回的，两次跑的数字逐位相同。**归档里也写了我自己错在哪**：那个 .xls 审计脚本的
notes/links 两个探针计数是坏的（notes 数成 1600=100×16、links 数成 0 与实测 8 条矛盾），
所以明确声明这两个字段不作证据，超链接存活只按 UTF-16 字节扫描说话。

**`docs/SOP-eda-import-2.6.1.md`**：把"重新导入一次 2.6.1 并拿到 12/12"写成显式清单，
关键是把**新板直接导入会得到 10/12、且那不是回归**写在最前面，并逐条列出哪些步骤
在宿主侧无接口、必须人工，同时重申不用 GUI 自动化顶替。验收给的是逐个铜皮块数的表，
不是"看起来有铜"。

**杂务**：删掉两条已并入的本地分支与一个遗留 worktree（都可按 sha 找回，
且这两个 sha 本来就写在 §E-7/§E-8 里）：

```
$ git worktree remove "D:/my git/PSDR-build-artifacts/m2_merge"
$ git branch -d m2/f7-as-source-f7 m2/untrack-build-artifacts
Deleted branch m2/f7-as-source-f7      (was 2e19ad0)
Deleted branch m2/untrack-build-artifacts (was dc084d1)
```

删之前先证过两条都是 `next` 的祖先（`git merge-base --is-ancestor` 两条都过），
worktree 干净。留着的是三个还有用的：主树、PR #18 的 `bom_pr`、PR #17 的 `pr-kicad-sch`。
远端 fork 上 `m2/untrack-build-artifacts` 与 `m2/f7-as-source-f7` 两个分支引用**没动**
（删远端是对外可见的动作，要删你说一句）。

**未收口**（写在这免得被 12/12 的漂亮数字盖住）：岛铜净间距仍只按 EDA 默认规则（0.6 mm 档）
量过，**没按源里的 8 mil 复核**——纯离线几何活，还没做。

### G-5 对外口径（用户 2026-11-02 定）

上游会看 PR（维护实际只剩我们和 maintainer 两人），所以 PR 正文只放可核对的证据，
不放意向。国产化/替代件这条线**不并入上游、不写进 PR**，在实测完成之前最多是个意见；
而实测本身依赖硬件与仪器，可能长期不发生——§G-4 保持"提案 + 明确标注大概率不做"。

## 任务 H · 需求边界修订（2026-11-03）

用户 2026-11-03 对 `docs/PSDR-scope-and-cost.md` 上一版拍了六条：VNA 不能砍（"我当时看中就是
VNA"）、GPS 可以更便宜、LC 带通组**要先验证**才允许向上游提、电容这轮不谈、CMOS 与继电器都行
但**要一个合并结论**、以及一个方向性疑问"短波段真的有火腿吗，不该是 UV 更合适吗"。
本轮全部按"只读 + 文档"处理，不改设计、不改固件源码。

### H-1 VNA 改判为保留项，成本地板随之上移

上一版"砍 VNA ≈$33"作废。改判不只因为用户偏好，网表本身也支持：VNA 不是外挂而是主链路。

```
ANT/VNA-IN.1 → C303 → U16.10/12 → (U304 放大器旁路) → C21 → U24 → C27 → U30 → C306 → RF_REF → VNA-OUT.1
RF_REF = C306.1 C322.1 R28.1 R321.2 REF.1 VNA-OUT.1(RF)     ← 桥的参考臂
RF_ANT = C309.1 DUT.1 R29.1 R308.2                          ← 桥的被测臂
U314(AD8302)：INPA ← C322，INPB ← C309                     ← 跨接两臂取幅度/相位
```

三级 GaAs DPDT 的分工也一并钉死（U16=放大器旁路、U24=阻抗桥插入/旁路、U30=射频口切换），
控制线全部来自 MCU：`AMP_SWITCH_A/B`、`IMP_BRIDGE_SWITCH_A/B`、`TX_RF_SWITCH_A/B`——
与 `Source_F7/src/main.c` 的 `signalPath()` 注释逐条对得上。所以砍 VNA 等于重做 RF 主链，
省下的 $33 会以改版代价还回来。**保留版地板 ≈ $225–235**（GPS −16.9、HMC1023→LC 组 −19、
1210 电容 −7、开关换型 ±2）；旧数字"$190–200"只在砍 VNA 时成立，已在文里写死作废。

### H-2 我自己的一处错误：CMOS 开关"板上有先例"这个论据不成立

追 MAX4525 时发现它是**低电压单电源件**，且本板把它接在 3.3 V 上：

```
# 逐引脚网络归属：临时内联脚本读 dist/netlist/PSDR_2.6.1_netlist.json
U4  pin 10 V+ -> +3V3      U18 pin 10 V+ -> +3V3      U86 pin 10 V+ -> +3V3_CPU

$ grep -n MAX4525 Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv
70:3,MAX4525CUB+-ND,Maxim Integrated,MAX4525CUB+,https://octopart.com/max4525cub%2B-maxim+integrated-42624946,...
```

手册（Maxim 19-1332 Rev 0）：单电源 **+2 V～+12 V**，Ron **200 Ω@+5 V / 500 Ω@+3 V**，
轨到轨信号，关断漏电 2 nA。500 Ω 串进 50 Ω 系统 = `20·log10(1+500/100)` ≈ **15.6 dB 插损**。

⇒ 替代提案 §4.1 路线 C 里"板上已有 CMOS，证明 CMOS 可用"这句**是错的**：I/Q 那些高阻电压节点
用 500 Ω 级开关成立，天线侧 50 Ω 节点不成立。两处都已就地更正（alternates §4.1 引用块 +
scope §7.1），并把"作者的 I/Q=CMOS / 天线侧=GaAs 是按阻抗分工"写进去。
教训还是同一条：**跨层核对要按物理锚点**——这次救场的是"开关的供电轨接的是几伏"这个锚点；
只看位号和封装名会得出方向相反的结论。

### H-3 LC 带通组：未验证，所以不提上游；但验证不需要改版

按用户的条件（"如果你验证过性能能够更好、动态范围更高的话"）如实回答：**没验证过**，
这里没硬件没仪器。因此本轮**不开**这条上游 issue（开上游 issue 本身也要逐次批准）。

意外收获（板子给的，不是推测）：外接滤波器插槽**已经在板上、也已经在 mux 档位里**。

```
U211/U298 = 74CBTLV3253，VCC=+3V3，1OE/2OE 接地，S0=FILTER_S0(U121.40/PE10)，S1=FILTER_S1(U121.55/PD8)
E_FILT_IF_P/N、E_FILT_RF_P/N 封装类型 = 0.1"_1PIN（四个直插焊盘）
FILTER_IN_P/N / FILTER_OUT_P/N ↔ U287(IIP/IIN/OQP/OQN)
```

⇒ 插一块 6 段 LC 小板就能和 HMC1023 同机 A/B，不动主射频设计。两个必须如实标注的缺口：
固件 `FILTER_S0/S1` 只出现三处、三处都写 `(1,0)`＝bypass（`recieve_with_filter:` 分支是空的），
所以外接档**当前从不被选中**；而 CBTLV3253 的真值表是数据缺口，得实测确认哪档导电。
固件冻结 ⇒ 不改代码，台架用跳线/断驱动，不能拿信号顶 MCU 的推挽输出。最小测量集（5 项，
含判据）写进 scope §6。

### H-4 短波 vs UV：找到一个代码级事实，两条边界都反直觉

`Source_F7/src/si5338.c:638-641`：

```c
frequency *= 2;              //because the flipflops will devide it back down by 2
if(frequency < 5000000) return;
if(frequency > 350000000) return;
```

⇒ 固件实际允许 **2.5–175 MHz**，越界**静默返回**（无错误路径）。两条后果：

1. README 承诺 0–35 MHz，但 **160 m（1.8–2.0 MHz）和 0.1–2.5 MHz 本来就调不到**。
   用户 2026-11-03 就此定了性：**发射端不算损失**——1.8 MHz 的 λ/2 要 83 m、λ/4 要 42 m，
   背包那 20 m 线只有 0.12λ，5 m 鞭 `Rr≈40(h/λ)²` 不到 1 Ω，白天还被 D 层吸收，
   "便携 + 160 m 发射"本来就不成立（同他买日版 705 的取舍）；**真正丢的是 0.1–2.5 MHz 的
   接收**（中波 DX、135 kHz WSPR、NDB），那是 SWL 价值。**措辞边界**：只写"固件不允许
   2.5 MHz 以下"，不写"硬件能做到但被代码挡了"——`SY100EP52V` 的最低输入频率和巴伦
   `WBC2-1TL` 的低频下限还没查完（分频件普遍有最低频率约束），硬件地板可能本来就在几 MHz。
   ⇒ 对上游的正确形态是"**README 0–35 MHz 与代码 2.5–175 MHz 不一致，且越界静默 `return`
   无错误路径**"，不是"请支持 160 m"。（是否真开这条 issue 仍逐次批准。）
2. **2 m（144–148 MHz）已在 LO 允许范围内**，而 70 cm（430 MHz）需要 LO > 350 MHz，
   现在必然调不到。所以"要不要做 UV"的瓶颈不在 LO，而在**前端选择性/预置滤波器、真正的 PA、
   以及 FM 模式（固件只有 AM/USB/LSB/CW，且固件冻结）**。

结论保持：本体留在 HF（差异化在"自带屏 + 瀑布 + 天线 VNA + 电池"这个组合），
VHF/UHF 走外置变频器 + 板上原始 I/Q 焊盘（RXI/TXI/RXQ/TXQ，均 `PAD_1MM`）。
另外核实：**全板 391 件里没有一颗信号继电器**，5 只 IRLML6401 全是电源域开关——
"继电器"这条路是新增件，不是恢复旧件。

合并结论（scope §7.3，按节点拍，不给通用答案）：**能慢的用继电器**（波段选择、桥的插入），
**不能慢的才用 RF 级低阻 CMOS**（T/R 全插、VNA 快扫）；通用逻辑 CMOS 只待在 I/Q 高阻节点。
天线侧三只 GaAs 的替代首选继电器（接受半插）、次选 RF 级低阻 CMOS，两者都要重新核
插损/隔离/时序、都要改板、都不并入上游（§G-4/§G-5 口径不变）。

### H-5 查"具体极限"：查出唯一射频增益件在 HF 本来就没增益（2026-11-03）

用户让查各频段真实极限，并批准"可以提 issues"。逐件结果与依据强度落在
`docs/PSDR-scope-and-cost.md` §8.2、`docs/PSDR-open-data-gaps.md` #3/#9/#10、
`docs/PSDR-alternates-proposal.md` §2.1。这里只记关键的两条与查法。

**一、器件极限**（公开检索，未上仪器）

| 件 | 结论 | 依据 |
|---|---|---|
| U304 `SXB-2089Z`（同族 SBB2089Z） | **50–850 MHz** ⇒ HF 全段无增益 | SIRENZA 手册标题即"50 - 850 MHz, Cascadable Active Bias InGaP/GaAs HBT MMIC Amplifier"；Qorvo 参数页 min 50 / max 850 MHz、20 dB、NF 2.7 dB、5 V/90 mA、SOT-89 |
| 封装名对应的 HMC482ST89 | **DC–5 GHz**，但要 **+6～+12 V** | 厂商转载页（P1dB +22 dBm、20 dB、SOT-89）⇒ 与本板 `+5V_AMP` 不符 ⇒ 名字是化石、电气按 5 V 件重设计过 |
| 巴伦 L39/L82 `WBC2-1TL` | 是 **Coilcraft WBC 系列**（不是 Mini-Circuits），族表 WBC1-1L **0.400–600 MHz** ⇒ 1.8 MHz 可用 | 华秋/立创参数条目 + elecfans 的 WBC 系列文章（WBC2-1TL 逐档仍待核） |
| U279/U280 `SY10EP52V` | **最低输入频率没查到**，仍是缺口 | 中英文检索只拿到同类 GaAs/SiGe 分频件"正弦波有下限、方波可到 DC"的旁证（HMC438/433/492） |

结构侧顺手钉死的一条（网表逐引脚打印）：两只 EP52 是**交叉耦合成正交 ÷2**——
`CLKA/CLKB`（Si5338 CLK0 经 C265/C267 交流耦合 + R268/R270/R271/R273/R274 偏置网络）进时钟脚，
`D`、`Q`、`\Q` 三组互相回接，出 `LO1P/LO1N/LO2P/LO2N`，供电 `+3V3_FLIP_FLOP`（经 Q246 P-MOSFET）。
所以"LO 频率 = 2× 调谐频率"是硬件拓扑，不是软件的随手乘法。

**二、固件侧**（纯读，`Source_F7/src/main.c`）

```
enum signalPaths (:811-820) 共 7 个状态，只有 0/2/3 有实现；
  1 recieve_with_filter、4 tramsmit_with_amp_with_filter、5 vna_reflected、6 vna_through 全是空桩
default: 分支被注释掉 (:937-940) ⇒ 非法值静默无操作
调用点只有 :1103（TX 用 transmit_no_amp_no_filter，:1104 的 with_amp 那行是注释）与 :1115（RX 用 no_filter）
三个已实现分支里 AMP_SWITCH_A 一律写 0（bypass），包括 :905 注释写着 "Amp relay set to on" 的那一支
F4 树没有 signalPath()，但 Source/src/main.c:958 `=1 //Route through amp`、:967 `=0 //Bypass amp`
```

⇒ **两条能对外说的结论**：① **射频端**当前不存在任何一级增益（器件带宽不符 + 开关从未置成插入，
两件事叠加），#16 标题"Enable Pre-Amp in Firmware"若只按字面在固件里打开，HF 也不会有 RF 增益。
**注意不要说过头**：混频之后的基带放大是有的（`U255/U272` 两只 MCP6N11 仪表放大器 +
`U15` MAX5388 数字电位器设增益），所以损失的是噪声系数/镜像抑制这一档，不是"整机不能工作"；
② **VNA 的两条路径在固件里是空的**——VNA 定为保留项之后，缺的是这两段状态与扫描流程，不是硬件。
另记：#16 楼里 2025-10-30 DM2NT 已在问 `MASWSS0129` 断供，作者答"缺件可以告诉我，我还有存货"——
断供的短期来源可能就在作者手里（只是信息，不构成我们的采购动作）。

**三、查重**（发东西之前必须做的）：`repo:MichaelRColton/PSDR` 全量 issue 12 条
（开着的 7 条：#19 我们那条、#16、#14、#13、#9、#8、#6）；#16 的 12 条回帖逐条读过，
**没有人提过 50–850 MHz 这条**，作者本人在 2021-12-07 只说过"RF 开关要配置、LPF IC 有一堆寄存器"、
"值得挂个外置前放试试"、"PSDR 几乎完全没有放大设计"。⇒ 这条是新增信息，不是重复劳动。

**当前未提交/未推送的改动**：`docs/PSDR-scope-and-cost.md`（§3/§4/§5/§6/§7/§8.1/§8.2/§9/§10）、
`docs/PSDR-alternates-proposal.md`（§4.1 路线 C 更正 + 新增 §2.1）、
`docs/PSDR-open-data-gaps.md`（#3 更新 + 新增 #9/#10）、`docs/README.md`（索引）、本 §H。
上游三条正文（#16 评论 / 空桩路径新 issue / 调谐范围新 issue）已起草，**先给用户过中文目再发**。

### H-6 待用户输入

- 群里那份"其他开源 HF SSB"文件还没拿到；scope §9 先只写了判据（纯收发前端普遍更便宜，
  但缺"屏 + 瀑布 + VNA + 电池"这个组合），文件到手再逐个核许可/成本/模式。
- GPS 三条路线（换国产模块 / 基础版不装只留焊盘 / 同厂降级 NEO）在 scope §5，
  **A 路线属国产化替代，不报上游**；C 路线可以上游谈。验收四项（首冻、灵敏度、PPS 精度、
  低压冷启动电流）都要仪器。
- 本轮全部文档改动清单见上一条 §H-5 末尾，**尚未提交/推送**，等点头。

## 任务 I · 维护者回归：两条实权回复与逐条复核（2026-11-03）

上游今天动了。两条都是 `OWNER`（MichaelRColton）本人回的，都会改变我们的做法，所以
**先把他的话当假设去验**，不把他的话当结论抄进文档。

### I-1 #7 结案：MIT 正式落地（许可证阻塞解除）

他 2026-11-03T01:47:22Z 关掉 #7："The MIT license is official — fully open (firmware,
software, and hardware) has always been my intent… Fork and build away."

按 ref 复核（不按他说的话）：

```
$ git show upstream/master:LICENSE.md | head -2
MIT License
Copyright (c) 2026 PSDR
$ git rev-parse next:LICENSE.md
aa9f66f0a9e0c0c2700d965a18222eee0dd9ffa6      ← 我们 next 上已是同一份 MIT
```

⇒ takeover 文档里"LICENSE.md 只有 TODO ⇒ 事实上保留所有权利"这条前置阻塞**已经消失**，
本 fork 的接手从"请求许可"变成"已授权的接手"。#7 线程本身就是我们 2026-08-19 发起的，
Jeff 2026-09-11 承诺加 MIT、Michael 今天落地——闭环。历史文档保留原样，只加"已于
2026-11-03 解除"的标注，不重写历史。

### I-2 #19 他的分支指引：一半对、一半是猜错

他说：master 是老的 F4；我们那份 `Source_F7/` 审阅"看起来来自 DMA 那条线"；
**`PSDR_F7` 才是该拿来做起点的那棵**（刷屏死循环已注释、`i2c.c` 结构不同）；
他已在命令行无头把它编出来，并准备以它为基线做 HMC1023 LPF 上电；
同时肯定我们两处产出：**HMC1023 `VDDBG`（脚 28 没有 5 V）是真板级 bug**、mux/bypass 映射正确。

逐条按 blob 核（本地已有这些 ref，**没有动上游任何分支**）：

| 他的说法 | 核验 | 结论 |
|---|---|---|
| `master` 是 F4 | `upstream/master:Source/src/main.c` = `190a0409`（F4 线） | 对 |
| 我们来自 **DMA** 线 | 我们 `Source_F7/src/main.c` = `def78a44`；`PSDR_F7_DMA` = `f5a41214`；**`PSDR_Rebuild` = `def78a44`** | **错**：我们是 `PSDR_Rebuild`（`i2c.c` 也逐 blob 相同 `619f2f5e`），不是 DMA |
| `PSDR_F7` 刷屏死循环已注释 | `PSDR_F7:Source/src/main.c:1020-1045` 直接进 setTextSize，唯一活动 `while(1)` 在 :1101 = 真主循环；`PSDR_Rebuild:…:1021-1032` 仍有 `fillScreen(BLACK/BLUE)` 陷阱 | 对 ⇒ **我们的 P0-1 是 PSDR_Rebuild 专属** |
| `PSDR_F7` 的 I2C 不一样 | 文件确实不同：`PSDR_F7`/`PSDR_F7_DMA` 共用 `c3e49239`（825 行），`PSDR_Rebuild` 拆成 `i2c.c` 138 行 + `frequency_control.c` + `si5338.c` | 结构对，但 **P0-2 没消失**：`PSDR_F7:Source/src/main.c:1031-1032` 就是那圈 `while(result != HAL_OK) result = HAL_I2C_IsDeviceReady(&handleI2C, (0x70 << 1), 100, 100);`——无上限重试还在，只是从 frequency_control.c 搬进 main.c |
| 分支布局他会整理 | — | 待他做；他动完之前我们不碰上游 |

分支时间线（顺手记下，免得下次又当"最新"猜）：`PSDR_F7` tip `ab2c8fd` **2018-07-31**；
`PSDR_F7_DMA` tip `457c270` 2018-06-21；`PSDR_Rebuild` tip `b9c0629` **2021-01-27**（Jeff 的 PR #12 合并）；
`DMA_Video`/`DMA_Video_Alt` 2016-01-13。⇒ 按提交日期 `PSDR_Rebuild` 更晚，按他的说法 `PSDR_F7`
是他的 F7 主线——**"哪棵为准"要他一句话**，不是我们能替他定的。

### I-3 新发现的代码事实：调谐上下限作者早就写死在 VFO 里

`Source_F7/src/main.c:1730-1731`（= `PSDR_Rebuild:Source/src/main.c:1730-1731`；
`PSDR_F7` 同一对夹取在 :1766-1767，**两棵 F7 树都有**）：

```c
if(vfoAFrequency < 2500000)   vfoAFrequency = 2500000;   //Currently, the code can only corectly drive down to 5MHz/2 = 2.5MHz
if(vfoAFrequency > 175000000) vfoAFrequency = 175000000; //Currently, the code can only correctly drive up to 350MHz/2 = 175MHz
```

⇒ **两处口径要更正（是我们自己写过头的地方）**：
1. `si5338.c:635-636` 那两个 `return` **在正常操作下不可达**——编码器路径先把 VFO 夹在 2.5–175 MHz。
   §H-4 与 scope §8.1 里"越界静默失败、用户无从得知"说过头了；准确说法是
   "**作者已在 UI 侧夹住范围并写了注释，`setFreq()` 里的 guard 只是第二道保险**"。
2. 这条新证据反而**加强**"2.5 MHz 是硬件下限"的读法：注释是作者本人写的
   "code can only correctly drive **down to** 5MHz/2 = 2.5MHz"，与 EP52 正交分频存在最低频率的猜测一致。
   真正的矛盾是"**README 的 0–35 MHz** vs **代码自带的 2.5–175 MHz**"，不是"代码有隐藏 bug"。
   ⇒ 第三条上游正文按此**重写**（从"静默失败请报错"降级为"文档与作者自己的注释哪个算数"），
   价值明显降低，**我倾向先不发**。

### I-4 我们已发出的东西有一处引用缺陷，得自己更正

今天发的 **#16 评论**与重复的 **#20/#21** 正文里，F7 侧行号用的是**我们 fork 的路径**
`Source_F7/src/main.c`——**上游没有这个目录**（上游叫 `Source/src/main.c`）。
其余引用是真的：`Hardware/BOMs/PSDR_2.6.1/OctopartBOM.csv:75`、`Hardware/PSDR.asc` 网表、
F4 的 `Source/src/main.c:958/967`。核对下来**结论在两棵 F7 树都成立**，只是行号要成对给：

| 事实 | `PSDR_Rebuild`（= 我们的 `Source_F7/`） | `PSDR_F7` |
|---|---|---|
| `enum signalPaths` 7 个状态 | main.c:811-820 | main.c:806-815 |
| 空桩 `tramsmit_with_amp_with_filter` / `vna_reflected` / `vna_through` | :928 / :931 / :934 | :923 / :926 / :929 |
| `//default:` 被注释 | :937-940 | :932-935 |
| `AMP_SWITCH_A = 0` 三处（bypass 图案） | :838 / :873 / :906 | :833 / :868 / :901 |
| `//Amp relay set to on` 后仍写 0 | :905-906 | :900-901 |
| TX 调用用 no-amp、with-amp 那行注释 | :1103-1104 | :1139-1140 |
| `FILTER_S0/S1` 三处都写 (1,0) | :856-857 / :891-892 / :924-925 | :851-852 / :886-887 / :919-920 |
| 无上限 `IsDeviceReady` 重试 | frequency_control.c:53-54 | **main.c:1031-1032** |
| VFO 2.5–175 MHz 夹取 | main.c:1730-1731 | main.c:1766-1767 |

待办（**对外动作，逐条等批准**）：
① **#20 与 #21 是同一份正文被表单建了两遍**（`created_at 01:25:20Z` / `01:25:34Z`，字节相同），
   关一条、留一条，并把留下那条的正文换成"按分支给行号"；
② 在 #16 补一条更正评论（同样按分支给行号，并说明 `Source_F7/` 是我们 fork 的镜像路径）；
③ 回 #19：谢他指基线 + 给出 I-2 的核验（**P0-1 确为 PSDR_Rebuild 专属；P0-2 在 PSDR_F7
   里仍在，位置 main.c:1031-1032**）+ 明确一问"哪棵为准"；
④ 调谐范围那条按 I-3 重写后再定发不发（倾向不发）。

### I-6 ①②③ 已执行（用户 2026-11-03 批准"你都放就行了"），逐条回查过

`mcp__github__*` 每次都回 `-32602 required property 'result'`（老假外壳错误），
所以每条都用**状态回查**判定，不看返回文本：

```
#21  issue_write update state=closed state_reason=duplicate duplicate_of=20
     -> issue_read: state=closed  state_reason=duplicate  closed_by=fe1iscurc0r
                   closed_at 2026-11-03T05:04:06Z                     只关了一次
#20  add_issue_comment（按分支成对给行号的更正）
     -> issue_read fields=comments: 0 -> 1   updated_at 05:05:08Z
#16  add_issue_comment（同一毛病的更正：Source_F7/ 是我们 fork 的路径）
     -> comments: 13 -> 14  updated_at 05:05:41Z
#19  add_issue_comment（三条核验 + 基线一问 + U287 表可提供）
     -> comments: 1 -> 2   updated_at 05:06:27Z
```

发出去的三条要点（都只给可核对证据、不附 PR、声明 AI 辅助）：
- **#20 / #16 更正**：F7 侧行号来自我们 fork 的 `Source_F7/`（上游无此目录，是 `Source/src/main.c`）；
  并给出两棵 F7 树的成对行号表（见 §I-4），**结论原样成立**：两棵都有 4 个空 case，
  两条 VNA 路径从未置过任何继电器状态。
- **#19 回复**：认下 P0-1 是 `PSDR_Rebuild` 专属；更正"我们不是 DMA 血统"（blob 证据）；
  **指出 P0-2 在 `PSDR_F7` 仍在**（`main.c:1031-1032`，只是从 `frequency_control.c` 搬过来）；
  一问"哪棵为准 + 有界重试在 `PSDR_F7` 原则上是否可接受"，二问"要不要把我们镜像改基到 `PSDR_F7`"，
  并把我们的判断摊开：**改基只有代价（M2 构建对账重跑、审阅结论重挂），除非两棵本就要合流**
  —— 用户 2026-11-03 的倾向是 **B（维持 `PSDR_Rebuild`）**，等他回话再定。

**顺手多验的一条（写下来免得下次重查）**：`LPF_POWER` / `HMC1023` 在 `PSDR_F7` 里同样**没有任何引用**
（`git grep -niE "lpf_power|hmc1023|lpf" upstream/PSDR_F7 -- Source/src Source/inc` 只命中一行
"helpful" —— **`lpf` 是 `helpful` 里的子串**，大小写不敏感的交替匹配会吃这种假阳性）。
⇒ #19 评论里"固件从不驱动 LPF 供电脚"这句对两棵 F7 树都成立。

### I-7 用户提示"2016 年有人打板焊装测过"→ 捞出作者的实测记录，并翻出我们两个错（2026-11-03）

**查法**（全部本地，可重跑）：

```
$ git log --all --format="%h|%ad|%an|%s" --date=short | grep -iE "dbm|measur|tested|works|assembl|prototype|..."
$ git merge-base --is-ancestor <sha> {next,upstream/master,upstream/PSDR_F7,upstream/PSDR_Rebuild}   # 逐条判在哪些血统里
$ git ls-tree -r --name-only next -- TestingMakeFile TestingMakeFile2 | grep -iE "makefile|\.ld$"
$ git grep -n "teardownPeripheralPower\|osKernelStart" ...
```

结果汇编成新文档 **`docs/PSDR-author-measurement-log.md`**（sha/日期/作者/血统/原话/数字/关联 issue/
证据强度全部逐条给）。最关键的四条：

1. **`2c1530d` 2016-05-07**：作者实测"能调 **2.5–175 MHz**"、灵敏度 "**-90dbm on 7MHz**、
   **-80-85dbm on 146.4MHz**"。⇒ ①与 §I-3 那对 VFO 夹取完全对上，**夹取是实测出来的**；
   ②我们此前说"第三层（射频验证过的整机）全空白"**过头了**，正确表述是"有作者一手实测自述、
   无原始数据与测量条件"。③立案：**2016 的 -90 dBm vs 2021 #16 的 -70 dBm 差 20 dB**，
   三个候选解释（板版本 / 配置 / 测量口径），且**没有条件不许写"退化了"**。
2. **`1890b25` 2016-04-18**："PSDR 2.5 prototypes **are assembled**"，并说想改的事项记在
   "**the notes section of the schematic**" ⇒ 库里那份 2.6.1 原理图 PDF 的 notes 区是**作者设计意图
   的第一手，我们还没挖**（WSL `pdftotext`，本机 Windows 侧无该工具）。
3. **`b78769a` 2019-05-24（我们的实质盲区）**：作者在 `PSDR_Rebuild` 血统里做了
   **CubeMX + FreeRTOS 重建**，落在 `TestingMakeFile/PSDR`、`TestingMakeFile/PSDRestore/PSDR`、
   `TestingMakeFile2/PSDR`（**带 `Makefile` 与 `STM32F746VGTx_FLASH.ld`，芯片正是 2.6.1 那颗**），
   `main.c:137 MX_FREERTOS_Init(); :140 osKernelStart();` 是真在起内核；他自述 **DMA 视频"基本完美"、
   radio 一行没移植**。⇒ survey 两处更正：①"全树没有任何 FreeRTOS"是**口径错**（我只 grep 了两棵应用树）；
   ②"不值得为此换到 FreeRTOS"收回，改成"对现有裸机树成立；要向下一代靠拢就先审那棵树"。
4. **`#9` 不缺代码**：`teardownPeripheralPower()` 在 `PSDR_F7` 与我们 `Source_F7/` 的 **`main.c:294`
   都有**，standby 入口 `:2161 HAL_PWR_EnterSTANDBYMode()` ⇒ #9 要的是"不用按 Reset 就能唤醒"，
   是唤醒源问题。与我们那条未对外说的硬证据正好对上：**PA0 既是 `PA0_WKUP` 又是 U16 的
   `AMP_SWITCH_A`**（待机时同一根脚同时决定"能不能醒"和"前放停在哪一挡"）。

**对第 2 步计划的改动**：验证"能不能无头编 F7"之前，先试 `TestingMakeFile2/PSDR/Makefile`
（库里现成、目标芯片正确）——若它能编，改基/演进的成本判断就有真实数字，
而"把我们手工的 `Makefile.linux` 移植到 `PSDR_F7`"未必是最优路径。

### I-8 改基代价实测：`Makefile.linux` 零改动就能编 `PSDR_F7`，锚点门原样通过（2026-11-03）

**这推翻了我在 §I-5 里给你的成本估算**（"改基要重跑整套对账、优势不大"）——实测下来移植是免费的，
所以"倾向 B"这个判断的前提不成立了。命令与输出都在下面，全部在板外 `/tmp` 跑，**仓库与上游 ref 未动**。

环境：WSL Ubuntu-24.04，`arm-none-eabi-gcc (15:13.2.rel1-2) 13.2.1`，`/usr/bin/make`。

```bash
# 1) 结构差异（Windows 侧）
$ git ls-tree --name-only upstream/PSDR_F7:Source/src | wc -l     # 17
$ git ls-tree -r --name-only next -- Source_F7/src   | wc -l      # 19（多 si5338.c + frequency_control.c）
$ for d in include system ldscripts DSP_Lib; do ...; done
  src 17↔19  include 16↔18  system 164↔164  ldscripts 3↔3  DSP_Lib 323↔323

# 2) 把我们的 Makefile.linux 直接放到 PSDR_F7 的 Source 上编
$ git archive --format=tar -o C:/Users/ASUS/f7src.tar upstream/PSDR_F7:Source
$ wsl bash /mnt/c/Users/ASUS/tmp_port_f7_test.sh
  === make rc=0
  === error lines: 0   fatal: 0   undefined-ref: 0
  text 114068  data 18488  bss 18260   (build_linux_f7/PSDR.elf / .hex / .bin)

# 3) 与 PSDR_F7 自己那份已提交的 hex 过我们现成的门
$ git show upstream/PSDR_F7:Source/Debug/PSDR.hex > C:/Users/ASUS/f7_PSDR_F7_ref.hex
$ python tools/anchor_check_f7.py <我们编出的 hex> <ref hex>
  reference  base=0x08000000 SP=0x20050000 reset=0x080002F9 empty-slots=[7,8,9,10,13,95]
  built      base=0x08000000 SP=0x20050000 reset=0x080001D5 empty-slots=[7,8,9,10,13,95]
  initial SP agree: True   empty-slot pattern: True   words equal: 7/118
  RESULT: PASS   (rc=0)
```

另外那棵 2019 的骨架也量了（`TestingMakeFile2/PSDR`）：Makefile 是 Windows 生成的，
**只需改 1 行**（`Makefile:213 cmd /c "mkdir $@"` → `mkdir -p $@`）就 `rc=0`、0 error、4 warning
（全是 newlib `_read/_write/_lseek` 未实现桩），产物 `text 22172 / data 20 / bss 18532`
⇒ 与他自述一致：**能编、DMA 骨架在、radio 一行没移植**。

**改基真正要重挂的东西**（都不难，但要一件件做完才允许说"改了基"）：

| 要重挂 | 现状 | 工作量 |
|---|---|---|
| Makefile | 零改动可用 | 0 |
| 锚点门 `tools/anchor_check_f7.py` | 原样 PASS | 0 |
| 我们那 6 行 include 修正 | `PSDR_F7` 没有 `si5338.c/frequency_control.c` ⇒ **这两只文件不存在，修正自动作废**（Si5338 在 `i2c.c` 825 行那份里） | 判定后删注 |
| survey 的行号引用 | 全部要换成 `PSDR_F7` 的行号 ⇒ §I-4 的对照表已经建好，可直接套 | 机械 |
| 尺寸注记（Makefile 头部第 25-30 行） | Rebuild 的 -O0 是 112344 B；`PSDR_F7` 是 text 114068 | 改数字 |
| P0-1 显示陷阱 | `PSDR_F7` **没有**这个陷阱（§I-2 已核） ⇒ 我们的 P0 清单少一条 | 更正 |
| hex 对账链 | 从"2018-06-21（DMA 期）"换成 `PSDR_F7:Source/Debug/PSDR.hex`（269,832 B，本次已用） | 重跑记录 |

⇒ **建议改为 A（把 `Source_F7/` 改基到 `PSDR_F7`）**，理由不是"跟他合流"这种偏好，而是实测：
构建免费、门免费、行号对照表已在手，而我们原本镜像的那棵**少一条他已修掉的 P0**、
又不是他现在做 HMC1023 的地方。要不要动，等你点头——这是主线内容变更，不擅自做。

（本节用的板外临时件已清理：`C:/Users/ASUS/tmp_*.sh`、`f7src.tar`、`f7_PSDR_F7_*.{hex,elf}`。）

### I-9 改基执行记录：`Source_F7/` 现镜像 `PSDR_F7`（分支 `m5/f7-rebase-psdr-f7`，2026-11-03）

用户批准"按 2→1→3 做"。第 2 步（文档提交推送）已完成，本条是第 1 步（改基）。**尚未并回 `next`、尚未推送**。

**做法**（全在本地分支，`next` 与所有上游 ref 未动）：

```
$ git checkout -q -b m5/f7-rebase-psdr-f7
$ git rm -rq --cached Source_F7 && rm -rf Source_F7 && mkdir Source_F7
$ git archive --format=tar upstream/PSDR_F7:Source | tar -x -C Source_F7
$ git checkout 4ce4540 -- Source_F7/Makefile.linux          # 我们的构建器原样挂回
$ git show 4ce4540:Source_F7/.gitignore > Source_F7/.gitignore
```

**换树的净效果**（`git diff --cached --name-status HEAD`）：**6 删 15 改**。
删除的 6 个 = `Debug/PSDR.hex`（改址保号）、`Firmware_Build_Notes.md`（Jeff 2021-01-18 的文件，
`PSDR_F7` 侧没有）、`include/{si5338,frequency_control}.h`、`src/{si5338,frequency_control}.c`；
修改的 15 个里真正有内容的是 `src/main.c`(+111/−89)、`src/i2c.c`、`src/spi.c`、
`src/Adafruit_*`、`include/*.h`、`.cproject`、`.settings/language.settings.xml`。

**差点丢锚点（记下来当规矩）**：`Source_F7/Debug/PSDR.hex` 是**被跟踪的**参考件（PR #1 特意保留的
两份 hex 之一），而 `Source_F7/.gitignore` 里的 `/Debug` 会把换树后解出来的同名文件挡在索引外 ⇒
直接提交等于**悄悄删掉 M2 对账链的参考**。处置：两份基线的 hex 改名带出处，落到
`dist/reference/`（不受 `/Debug` 影响），并写 `dist/reference/README.md` 记 sha256/blob/出处。

```
PSDR_hex_2017-01-15_aaa24f8_PSDR_F7.hex   269,832 B  sha256 d5f372a6…  blob e6fe1975…  ← 新基线官方参考
PSDR_hex_2018-06-21_457c270_DMA.hex       216,207 B  sha256 88cf1abb…  blob 73b11f70…  ← M2 用的历史参考
（git 把这次移动识别为 rename：Source_F7/Debug/PSDR.hex -> dist/reference/…_457c270_DMA.hex）
```

**改基后的复算**（从**已入库的树**跑的，不是临时 archive）：

```
$ cd Source_F7 && make -f Makefile.linux -j4
  rc=0   errors=0  fatal=0  undefined=0  warnings=26
  text 114068   data 18488   bss 18260     built PSDR.hex 372,928 B (sha256 5409836e…)
$ python tools/anchor_check_f7.py <built> dist/reference/PSDR_hex_2017-01-15_aaa24f8_PSDR_F7.hex
  SP=0x20050000 agree=True  empty-slots=[7,8,9,10,13,95] agree=True  words=7/118  RESULT: PASS
$ python tools/anchor_check_f7.py <built> dist/reference/PSDR_hex_2018-06-21_457c270_DMA.hex
  同上                                                      RESULT: PASS        ← 两条参考都过
```

**改基后我们在 F7 侧的自有内容**（`git diff --numstat upstream/PSDR_F7:Source HEAD:Source_F7`）：

```
1	0	.gitignore
0	6000	Debug/PSDR.hex        ← 有意不再跟踪构建产物（PR #1 政策），参考件已搬去 dist/reference/
120	0	Makefile.linux
```

⇒ **`.c/.h` 净改动 = 0**：旧镜像上那 6 行 include 修正随 `si5338.c`/`frequency_control.c`
一起消失（新基线不需要）。也从此可以准确说"我们没有改动固件源码"——上一版提交信息里
我还特意声明"这句以后不许写"，现在它换成了有依据的成立。

**清单变化**：P0-1（刷屏死循环）在新基线上不存在 ⇒ 从我们的缺陷清单移除，仅作 Rebuild 血统的历史记录；
P0-2 仍在，位置 `src/main.c:1031-1032`。survey 顶部加了"基线变更公告"，旧行号一律按 §I-4 对照表换算，
`README.fork.md`、`tools/anchor_check_f7.py` 的引用路径与数字同步更新。

**提交**：`29aa887`（改基本体 + dist/reference + Makefile 头部 + 工具 docstring + README.fork）。
**并回 `next` 与推送已完成**（见 §I-10 末：`next = 9aad812`）；F4 那侧不受影响。

### I-10 起草对外评论时自查出的两处 Makefile 头部假话（2026-11-03）

给 #19 写"我们的参数是照您分支的 `.cproject` 来的"之前，先去核了 `.cproject`，
结果发现**我自己在 §I-9 那次提交里写的头部有两句在新基线上不成立**：

| 头部原话 | `PSDR_F7` 的实测 |
|---|---|
| "Debug sourceEntries 只排除 `DSP_Lib/Examples` 与 `src/TinyGPS.c`" | 它排除 `Examples`，**没有排除 TinyGPS.c**（全文件 `TinyGPS` 出现 0 次） |
| "不像 F4 工程，**不排除任何 HAL 模块**" | 它的 Debug 排除 **42 个** `system/src/stm32f7-hal/*`（`.cproject:232`；含 `hal_dma.c`，但 `hal_i2c/uart/tim/spi/adc/dac/gpio/rcc` 都留着） |

根因是**把旧基线的注释直接搬进新基线的文件里**——那两句对 `PSDR_Rebuild` 是准确的（它的 Debug 排除
`Examples`+`TinyGPS.c`+9 个 HAL），对 `PSDR_F7` 不是。已改掉，并把三种口径都实测一遍：

```
PSDR_F7 @ ab2c8fd，GCC 13.2.1，make -f Makefile.linux -j4
  本 harness 的策略（全编 HAL，跳 TinyGPS.c）    rc=0 0err 26warn  text 114068 data 18488 bss 18260
  照分支原样（编译 TinyGPS.c，全编 HAL）        rc=0 0err 30warn  text 114064 data 18488 bss 18260
  照分支原样 + 它那 42 条 HAL 排除              rc=0 0err 30warn  text 114064 data 18488 bss 18260
```

⇒ `--gc-sections` 让三种口径收敛到同一量级，所以"全编 HAL"是便利而非隐性行为差异；
**但只说"尺寸相同"，不说"镜像逐字节相同"**（没验）。头部现在把这条写成明确的 (f) 项差异清单。
改完重跑：`rc=0`、0 error、`text 114068`，锚点门仍 **PASS**。

顺带把头部另一句也修了：原来写"本文件与编 Rebuild 那版逐字节相同"——改完注释就不成立了，
换成"规则未动，只改了注释块"。以及参数来源如实写成"**最初是从 `PSDR_Rebuild` 的 `.cproject` 抄的**，
在 `PSDR_F7` 上只对得上 `HSE_VALUE=26000000` 与 `--gc-sections` 两项"，不再声称逐参数一致。

**教训（写死）**：改基时**注释比代码更容易变成假话**——代码错了编不过，注释错了没人报警。
以后凡是"照 X 的构建配置"这类话，必须当场把 X 的配置文件 grep 一遍再落笔。

**落地**：`next` 已推到 `9aad812`（含 `29aa887` 改基、`239fe23` 记录、`9aad812` 头部更正；
远端 sha 与本地一致、ahead/behind 0/0、upstream 无 `next` 未被写入；回滚点 `4ce4540`）。
#19 的"改基后零成本 + 三种排除口径实测"评论也已发（回帖数 2→3 核实，链接三条 API 回 200）。

## 任务 J · 委派输入包（给无仓库上下文的执行方，2026-11-03）

用户要把耗时机械的活派给虚拟机里的另一个 agent（它接不到本仓库），要求"能派就派、回来我能验"。
所以这里出的不是提示词，是**可重跑的输入包生成器**：数据一律由脚本从库内派生，不手抄。

```
$ python tools/make_delegation_pack.py            rc=0（无 WARNING 即前提自洽）
ic_context: 36 files (netlist has 391 designators)
decal_raw : 23 distinct decals for the IC list
parts_census: 57 part types
bom_rows: 86 rows with a DigiKey number
$ du -sh delegation  ->  293K
打包件 C:/Users/ASUS/psdr_delegation_pack.zip  sha256 d9f9ee053c1ad239905e7e1ee78326202eaf245b195cdebd120834b5886d1bcc
```

内容：`ic_context/<位号>.md`（每脚→网络→同网其它引脚，被动件的值就编码在 `part_type` 里，
如 `CSM-X5R-22U-20P-10V-1210`）、`decal_raw/<封装>.txt`（**原样 `*PARTDECAL*` 块**，
不给我解码后的数字，免得执行方被我对口列名的猜测带偏）、`parts_census.csv`、`bom_rows.csv`，
外加答案 schema 与四条硬规则（无出处不作答、查不到写 `未证实`、第三方转述只当线索、
与前提矛盾要直说）。对应任务：A 生命周期普查 / B 立创 SMT / C 外围件 vs 手册公式 /
E 手册正本清单 / F 焊盘 vs 厂商推荐 footprint。

**两个自己抓到的位号错配**（差点把错问题派出去）：`U114` 我当 SSM2167，其实是 **AP3417C 降压**
（SSM2167 是 `U189`）；`MIC` 我当 MEMS 麦克风，其实只是 `PAD_1MM` 焊盘（麦克风是 `U32`）。
⇒ 生成器现在带 `EXPECT` 守卫：每位号断言 `part_type` 含指定子串，不符就 **rc=2 不出包**；
每个上下文文件顶部也写明"本问题假定该件是 X，若 part_type 不符请停止并报矛盾"。
另外重生成会**先清 `ic_context/*.md` 与 `decal_raw/*.txt`**——第一版残留过 `MIC.md`，
删了条目但文件还在，等于把已知的错问题继续派出去。

一处口径提醒（写进包内 README）：decal 名会**沿用/共用**——`U121` 的 `part_type` 是
`STM32F746_LQFP100`，但它用的 `*PARTDECAL*` 组名是 `STM32F429_LQFP100`（100 端）。
判"哪只脚属于哪只芯片"只能走 `_index.csv`，不许从封装名反推。

**验收口径**（等答案回来执行）：随机抽 10 行复算；封装类答案用 `tools/pads_asc_decal.py`
重新解码比对；手册类答案按给的页码/版本反查原文；**任一行不过，整批退回**，不挑能用的收。
外部断言在核完之前不进任何对外文本（尤其 #16 已经公开说过 U304 的带宽）。

### I-5 对主线计划的实际影响（要你拍板）

- 他要以 **`PSDR_F7`** 为基线做 HMC1023 上电，而我们 `next` 里那份是 **`PSDR_Rebuild`**。
  **(A) 把 `Source_F7/` 改基到 `PSDR_F7`**——跟他并行、以后合得上；代价是 M2 的构建对账要重跑，
  且 P0-1 消失、`docs/PSDR-firmware-survey.md` 的部分结论要重挂。
  **(B) 维持 `PSDR_Rebuild`**——我们自己的复现与 hex 对账链完整，只在文档里标注分支差异。
- 他**人回来了**（今天三条动作：关 #7、指 #19 基线、说正在起 HMC1023）⇒ HMC1023 那条我们
  **不抢跑**（`docs/PSDR-HMC1023-netlist.md` 的 SPI/校准时钟/VDDBG 全表正好是他现在要的）；
  LC 带通组、替代件、国产化继续 **fork-only 不上游**（§G-4/§G-5 口径不变）。
- 他说要整理分支布局 ⇒ **在他动完之前不往任何上游分支推东西**（我们本来也不推）。
- **用户 2026-11-03 的倾向已记：B（维持 `PSDR_Rebuild`）**——"除了改基的代价，感觉没有太大优势"。
  这条已在 #19 里摊开问他（见 §I-6），**他回话前不动 `Source_F7/`**；若他答"两棵要合流/以 F7 为准"，
  改基才有意义，届时 M2 的构建对账要整体重跑一遍再说话。

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

（这是 §C-14 之后的最终输出；`outline`/`pours`/`silk` 三行是第三批时还没有的。
第三批的输出块记的是 `outline 100.00 x 65.00 mm` 包络矩形。）

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
  `*LINES*` 的 level 26/29 板级线条 + 376 条 Ref.Des. + 4 条自由文本。
- 层次规则有 ASCII 里嵌入的 CAM 文档作证（第 51011 行起）：
  `CAM_DOC_NAME Top Silkscreen` → `DOC_LAYER_NUMBERS 1 26`，
  `Bottom Silkscreen` → `4 29`。实测：**level 26 → 器件所在面**；
  **level 0/1 → 只在非镜像器件上归 F.SilkS**（底面孔件的 0/1 图元在
  GTO/GBO 都不出现）；level 20/23/27/29 → 不画；零长线段跳过。
- 数量：162 个 decal 图元、1495 个板级图元 {26: 753, 29: 742}、4 条自由文本、
  376 个位号；15 个器件在源文件里没有 Ref.Des.（6 个 FIDUCIAL、7 个 MH3M、
  2 个 MH_80M——只有 Part Type 文本，而 CAM job 不画 Part Type）。
- 双向覆盖率（40 px/mm，容差 0.10 mm）：

| 宽度 | GTO 源→KiCad | GTO KiCad→源 | GBO 源→KiCad | GBO KiCad→源 |
|---|---|---|---|---|
| 2 mil | 100.00% | 100.00% | 100.00% | 100.00% |
| 6 mil | 35.48% | 23.93% | 29.23% | 18.42% |
| 8 mil | 100.00% | 100.00% | 100.00% | 100.00% |
| 10 mil | 98.03% | 100.00% | 29.47% | 46.88% |

  - 2 mil 是 "psdr" 标志，8 mil 是板级线条/器件轮廓：两档双向 100%，
    说明坐标与层别都对。
  - 6 mil 是位号文本：KiCad 笔画字体 vs PADS Romansim，字形不同；
    6 mil 这一档的两向百分比不能当几何误差读。
  - GBO 10 mil 的 29.47/46.88 由背面 4 条 10 mil 自由文本主导。GTO 10 mil
    的 1.97% 缺口是 **9 条笔画组成的一个约 1.4 mm 实心三角标记**
    （C151 左侧、板下缘附近）；它的来源未在 `PARTDECAL`/`LINES`/`TEXT`
    段中定位到（本轮逐段查过），如实记为已知缺口。
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
4 层铜 / 12 个铺铜区 / 67 段板框 / 双向丝印对账通过 / 0 断点；
但它仍不是可投产的板：795 条 DRC（分类与处置见 §C-16，以源设计允许的
丝印压焊盘和紧间距为主）、丝印还差一个约 1.4 mm 的三角标记（来源未定位）。
生产包继续以上游 `468dc41` 的原始 Gerber 为准。

---

### C-15 导入嘉立创EDA Pro：KiCad 路线丢层/丢网/丢铺铜网络的根因与修复（2026-11-01）

工单没要求这一步，属于接管后用户提出的"能不能放进嘉立创EDA"。结论先写：
**能，但必须先在生成器和本地转换器上修三处缺陷**；修完后四层、278 网、
12 个铺铜区、391 器件都能在 EDA 里读到。宿主的 EDA 是 **3.2.203（V3）**，
低于本项目技能基线的 V4，属于已知限制。

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

- 丝印：GTO 上约 1.4 mm 的实心三角标记（C151 左侧、板下缘）来源未定位，
  见 §C-14；
- 嘉立创EDA：`+3V3_FLIP_FLOP`（In1）和 `V_SUPPLY`（F.Cu）两个铺铜重建后
  0 铜皮，根因是 KiCad `island_removal_mode 0` 与 PADS `keepIsland=true`
  不一致，未改，见 §C-15；
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
| M1 转换闭环（2–4 周） | 1.4 mm 丝印三角、EDA 两处零铜铺铜、一条命令复现 + SHA256 清单 | 重跑 md5 不变；EDA 12/12 有填充 |
| M2 主线成型（1–2 个月） | 把 F7 构建线并入 `next`，验证 F4/F7 构建与 KiCad 产物 | 两条固件线在同一主线可复现；冲突有记录 |
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

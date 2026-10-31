# 施工记录 · PSDR 接手工单（2026-10-30）

分支：`workorders/2026-10-30-psdr-takeover-linux-build-kicad`
执行机：天选7P（Windows 11 26300）+ WSL2 Ubuntu 24.04（构建用）

> **当前状态：任务 A 通过验收；任务 B 通过（GC=1 与 GC=0 各一次完整构建，0 error、
> 365 warning、锚点 `_estack=0x20030000` / Reset `0x080001B5` 与 2016 上游 hex 一致，
> 尺寸对账见 §B-4）；任务 C 完成但带 5 项 SKIP（见 §C-8：4 铜层未覆盖；`.kicad_sch`
> 仍未产出，但它的前置缺口已补齐——2.6.1 的 PADS Layout ASCII 与 10 页原理图 PDF 已入库，
> 网表 391 器件 / 278 网 / 1132 引脚并通过四重校验，见 §C-11）；制板仍走 `dist/gerber/`；
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
实际走的是另一条有数据的通道：
`Hardware/BOMs/PSDR_2.6.1/psdr26.emn` + `.emp` 是 **PADS Layout 9.5 的 ASCII 导出**，
里面有板框、孔表和 391 个器件的贴装坐标。从它生成 KiCad 板子，再用
KiCad 自己的 plot 输出反解回来跟**原始 PADS Gerber** 对账，得到
亚微米级偏差（C-5）。`.kicad_sch` 与 SolidWorks 壳体**如实标 SKIP**（C-8）。

### C-1 交付物清单（真实 `ls`）

```
$ ls -la dist/kicad/
-rw-r--r-- 229724  PSDR_2.6.1-drc.json          # kicad-cli 10.0.6 DRC 报告（UTF-8, mm）
-rw-r--r-- 721924  PSDR_2.6.1.kicad_pcb         # 生成物
-rw-r--r--   2297  PSDR_2.6.1.kicad_prl         # KiCad 打开时自动创建
（无 .kicad_sch —— 见 C-8 SKIP-1）

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

### C-8 SKIP 清单（转不了的如实标，不假装成功）

| # | 项 | 原因（可复核） |
|---|---|---|
| SKIP-1 | `.kicad_sch` 图形化原理图 | **前置缺口已补齐，图形仍未生成**（原判据"唯一可读的 PDF 是 2014 旧版"已由 §C-10 推翻，此处是修正后的状态）。① 2.6.1 的 **10 页原理图 PDF** 与 **PADS Layout ASCII** 都在 `PSDR_Rebuild@468dc41`，本轮已复制进本分支（`Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`、`Hardware/PSDR.asc`）；② 从 `.asc` 已提取**完整网表**：391 器件 / 278 网 / 1132 连接引脚 / 41 未连接（全部可解释为 NC、基准点、安装孔），四重校验见 §C-11；③ `Hardware/PSDR.sch` 仍是 PADS Logic 二进制，开源工具读不了，但**不再阻塞网表**。⇒ 现在缺的只是"按 2.6.1 版面画的 `.kicad_sch`"，连接关系已有权威来源。 |
| SKIP-2 | `Hardware/Enclosure/` SolidWorks 壳体/装配 | `.SLDPRT`/`.SLDASM`，嘉立创EDA 无对应能力，工单也明确要求不要试图转换。 |
| SKIP-3 | `.sch`/`.pcb` 源文件 | 工单称 Eagle，实测是 **PADS Logic / PADS Layout 二进制**（`Hardware/README.md`："Schematics and Board layout files are for Mentorgraphics PADS"；头 `00 fe 0d 00` / `00 ff 26 20`）。KiCad 10.0.6 的 Eagle 插件报 `XML 解析错误：'not well-formed'` 却 **exit 0**（假成功）——因为它不是 Eagle XML。要转这两个二进制必须先有 PADS Logic/Layout 本体，本机没有；**但 2.6.1 的 PADS Layout ASCII（`Hardware/PSDR.asc`）已在库里，二进制不再阻塞网表**，只影响"图形原理图"（§C-11）。 |
| SKIP-4 | 铜走线 / 内层 / 网络 | `.emn` 无 `TRACE` 段 ⇒ 生成的 KiCad 板是 **2 个铜层（F.Cu/B.Cu）**，而真实板是 **4 层**（`In1_Cu`=L2 power、`In2_Cu`=L3，见 `dist/gerber/PSDR25_Main_Board/MANIFEST.txt`）。走线与电源层只能看原始 Gerber，不能看这块 KiCad 板。 |
| SKIP-5 | 器件真实焊盘形状 | `.emp` 无 pad stack（C-5）。 |

**制板用哪套**：给嘉立创EDA 下单/生产请直接用 `dist/gerber/` 的规范化 Gerber（含
真实 4 层铜）；`dist/kicad/` 只是可编辑的板框+贴装+孔位参考。

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
| `Hardware/PSDR Schematic.pdf` | `master` / 本分支 | 8 页，317,207 B | 2014-10-28 旧版（比 2.6.1 少 16 个位号） |
| `Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf` | 本分支新增（源 `468dc41`） | 10 页，346,496 B | `CreationDate` 2016-07-26；含 2.6.1 器件 |
| `Hardware/PSDR.sch` | 本分支 | PADS Logic 二进制，525,874 B | 2016-05-07 提交；开源工具读不了 |
| `Hardware/PSDR.asc` | 本分支新增（源 `468dc41`） | **PADS Layout ASCII 1.0**，1,641,124 B | `468dc41`，2.6.1 PCB complete |
| `Hardware/BOMs/PSDR_2.6.1/psdr26.emn`/`.emp` | 本分支 | PADS IDX ASCII | 只有 `BOARD_OUTLINE`/`DRILLED_HOLES`/`PLACEMENT`，无 `NETS` |

**结论：网表问题已解决**（§C-11）。剩下的只有"图形化原理图"（`.kicad_sch`）：
现在既不需要从 PDF 反推连接，也不需要逆 PADS 二进制——连接关系有权威来源，
图形照 2.6.1 PDF 的 10 页版面生成即可。

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
任务 C 的 `dist/gerber/` 用的是 2.5 主板的原始 Gerber（§C-8 SKIP-4）；
要出 2.6.1 生产包应改用它，这不在本工单的 C 阶段范围内，先记录。

本轮 PDF 侧的工具（poppler 24.02、PyMuPDF 1.28.2）和中间脚本留在
`D:\my git\PSDR-build-artifacts\sch_261\`、`sch_preview\`（不入仓）。

---

### C-12 由网表 + 2016 PDF 版面生成 KiCad 原理图（2026-10-31）

**先确认前提，避免做无用功**：上游 `468dc41` 上同时存在 2.6.1 的 PADS
Layout ASCII（`Hardware/PSDR.asc`）和 10 页原理图 PDF
（`Hardware/PSDR_2.6.1_Schematic_2016-07-31.pdf`），所以
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

2026-10-31 追加（原理图/网表，**尚未提交**；上面那次推送之后新增）：

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

# 施工记录 · PSDR 接手工单（2026-10-30）

分支：`workorders/2026-10-30-psdr-takeover-linux-build-kicad`
执行机：天选7P（Windows 11 26300）+ WSL2 Ubuntu 24.04（构建用）

> **当前状态：任务 A 通过验收；任务 B 通过（GC=1 与 GC=0 各一次完整构建，0 error、
> 365 warning、锚点 `_estack=0x20030000` / Reset `0x080001B5` 与 2016 上游 hex 一致，
> 尺寸对账见 §B-4）；任务 C 完成但带 5 项 SKIP（见 §C-8，`.kicad_sch` 与 4 铜层是硬缺口，
> 制板仍走 `dist/gerber/`）；任务 D 记录已写、本地提交已落，未推 `origin`。**
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

工单写的路径是 Eagle → KiCad。**这条路在本仓库里走不通**（Eagle 文件是二进制，
KiCad 10 的 Eagle 插件读不了，见 C-2）。实际走的是另一条有数据的通道：
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
| Eagle 二进制 `.sch`/`.pcb`，无 `.brd` | ✅ `file` 报 `data`；`kicad-cli` 导入报 `XML 解析错误：'not well-formed'`，**但 exit 0** | 放弃 Eagle 路线 |
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
  2.6.1 的制板文件（本仓库里没有，仓库里最新只到 2.5 main board）。

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
| SKIP-1 | `.kicad_sch` 原理图 | **仓库里不存在任何网表**。`psdr26.emn` 只有 4 个段 `BOARD_OUTLINE / DRILLED_HOLES / HEADER / PLACEMENT`（`grep -c '.NETS'` = 0），`.emp` 只有 57 个 body 多边形、无引脚数据（`_sections()` 返回空）；Eagle `.sch` 是二进制读不了；`find Hardware` 里没有任何 netlist 形状的文件。没有连接关系 ⇒ 原理图不可能重建，只能画符号。 |
| SKIP-2 | `Hardware/Enclosure/` SolidWorks 壳体/装配 | `.SLDPRT`/`.SLDASM`，嘉立创EDA 无对应能力，工单也明确要求不要试图转换。 |
| SKIP-3 | Eagle `.sch`/`.pcb` | 二进制（非 XML）格式；KiCad 10.0.6 Eagle 插件报 `XML 解析错误：'not well-formed'` 却 **exit 0**（假成功）。要转必须先有 Eagle 7/8 本体，本机没有。 |
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

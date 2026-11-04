# `Documentation/` 档案：库里那六份我们一直没读的作者材料

日期：2026-11-04。**这是一次补漏**：仓库根目录的 `Documentation/` 有 6 个文件，
我们此前所有文档（`docs/` 下 15 份 + `README.fork.md`）**一次都没提到过它们**——
`grep -rln "PSDR2 Guide|Assembly Instructions|Video Script|filter coeficient" docs README.fork.md` 是零命中。
本文逐份读出内容与"它确立什么 / 不确立什么"，并给出可复算的取文命令。

取证方式：`.pdf` 用本机 `pypdf`（`-layout` 提取，页码保留），`.xlsx` 用 `openpyxl(data_only=True)`，
`.docx` 解 `word/document.xml` 去标签。原始文本落在本机 `D:\my git\_psdr_history\`（仓外，可重跑）。

| 文件 | 大小 | sha256 前 12 | 进仓的提交（日期/作者） | 文件里的创建时间戳 |
|---|---|---|---|---|
| `Assembly Instructions.pdf` | 951,772 B | `e76ec61a7ca8` | `2a0a65c` 2016-11-17 Michael Colton | PDF `D:20161108224601-07'00'` |
| `PSDR2 Guide.pdf` | 309,043 B | `090b14534d1d` | `37c3da4` 2021-01-18 Jeffersonbenson | PDF `D:20140928202129-06'00'` |
| `Final Video Script.docx` | 14,602 B | `76e412734a3c` | `37c3da4` 2021-01-18 Jeffersonbenson | — |
| `PortableSDR Video Script.docx` | 15,328 B | `218484b3d803` | `37c3da4` 2021-01-18 Jeffersonbenson | — |
| `Stepping through filter coeficient population.xlsx`（文件名少一个 `l`，上游原样） | 130,567 B | `eaa42d4a1642` | `46c832e` 2014-10-15 Michael Colton | — |
| `BOM with space for parts.xlsx` | 16,073 B | `7705690a9f88` | `bec5351` 2017-01-19 Michael Colton | — |

**注意血统**：`PSDR2 Guide.pdf`、`Final/PortableSDR Video Script.docx` 是 **2021 年 Jeff 整理时补进去的**，
但里面的 PDF 时间戳是 2014-09-28 ⇒ "进仓时间"与"写作时间"是两回事，引用时别混。

---

## 1. `PSDR2 Guide.pdf`（1 页，2014-09-28 创建）——作者自己没写完的 VNA 说明页

它只讲 **VNA 这一小块**，而且是**半成品**：正文里留着作者写给自已的追问原句
（这是"这板子到底做到什么程度"的一手证据，比任何推测都硬）：

> "THEN WHAT HAPPENS?"
> "How can it be used for circuit analysis? etc. How about graphing it, math, etc."
> "The other port"
> "How about what pins on the microcontroller is it connected to?"
> "**Whre is it controlled in code?**"（拼写原样）
> "**TODO: What are C68 and 111 for again?**"

与我们已经核过的事实互相印证的两条（**这是独立来源，不是我们推的**）：

> "R29-30 are present to allow tuning of the center point and slope of the output (See page 18).
> **Set at 0 Ω, the output is 30mV/db and 10mV/Degree.**"
> "R25 and 26 are terminating resistors so signals into the VNA see a 50 Ω load."
> "This design follows the datasheet for the AD8302 (**Page 16**, see link below) with some modification."

⇒ AD8302 的 30 mV/dB、10 mV/° 我们先前只从原厂 Rev.B 式 8a/9 算得，这里作者的说法与之一致；
`C307/C320`（2.6.1 里的 DNP 旁路）与这里的 AD8302 脚位讨论可对照 `docs/PSDR-open-data-gaps.md` #5。

**但它讲的是 PSDR2，不是 2.6.1**：这一页的位号是 `U23 = AD8302`、`U24/U25/U26/U27 = RF_DPDT_MASWSS0129TR`，
而 2.6.1 网表里是 `U314 = AD8302`、DPDT 是 `U16/U24/U30`（三片不是四片）
⇒ **位号跨版本会漂**，这条与固件符号名≠网名是同一类坑；引用这份 PDF 的位号必须换算。
出现的网络名（可当 2014 年的设计意图清单）：`AMP_SWITCH_A/B`、`IMP_BRIDGE_SWITCH_A/B`、
`TX_RF_SWITCH_A/B`、`2M_MIXER_SWITCH_A/B`、`MAGNITUDE`、`PHASE`、`RF_REF`、`RF_ANT`、`VNA-OUT`、`ANT/VNA-IN`。
还有一句没落地的想法：**"It might make sense to put an inverter rather than run both lines to the micro"**
——这正是我们 2026-11 判定的"MASWSS 必须互补驱动"的同一件事，作者 2014 年就想到了但板子上仍走两根线。

## 2. `Assembly Instructions.pdf`（4 页，2016-11-08 创建）——PSDR2 的机械装配说明

内容是全机械装配（编码器板、旋钮顶丝、外壳、螺丝顺序），开头有防静电与"不要拧太紧"的告诫：

> "With all the screws on the PSDR, I recommend that you start them by setting them in the screw hole,
> and turning them **backwards until the screw pops into the thread** before screwing them in normally."

对我们的价值有两处：

1. **M3 上电前的机械前置**：`docs/PSDR-bringup-checklist.md` 是电气测点表，缺机械这一段——
   这份 PDF 正好补上（可给检查表加"装配/螺丝/顶丝"前置步，但那是另一次改动）。
2. **标题栏里留着没改的模板文本**：图纸框仍写
   "PROPRIETARY AND CONFIDENTIAL … IS THE SOLE PROPERTY OF **<INSERT COMPANY NAME HERE>**"
   ⇒ 2016 年的图纸框是带占位公司的模板；与 #7 那条"到底用什么许可"的十年悬案是同一件事的两个侧面。
   这只说明"当时没改"，**不**说明任何许可意图——许可按 #7 里 maintainer 2026-11-03 的原话为准。

页 1 的图纸框同时确认它挂在 **PSDR2 REV / SHEET 1 OF 1**，即这份装配说明也不是 2.6.1 的板。

## 3. 两份视频脚本（`.docx`，2021 年进仓）——项目的"对外宣称"原文

`Final Video Script.docx` 与 `PortableSDR Video Script.docx` 都是作者给宣传视频写的稿子，
里面是**项目自我定位的原始句子**，比二手转述好用：

> "The PortableSDR is a pocket sized, **two way shortwave radio**."
> "It includes what's called a **waterfall display**."（DM2NT 2021 年在 #16 里说"我不能没有瀑布显示"，同源审美）
> "The PortableSDR includes a **GPS receiver**, this combined with the shortwave transmitter means that
> in an emergency, the PortableSDR may be able to transmit your location…"
> "**The PortableSDR is an open source project. Everything about its design is freely available.**"
> "**I'm working on documentation that walks through how each part of the circuit works and why.**"
> "I plan on offering **kits** for people that are excited to build their own… I also hope to offer assembled units."
> "**I didn't design it as an emergency device**, if that's what you need, there are better tools."

⇒ "open source"这句话在这份稿子里就有了，比 #7 的 2017 开帖更早；但同一批稿子也承认文档没写完
（与 §1 那份半成品 PDF 完全吻合）。`BOM with space for parts.xlsx`（2017-01-19）是给装配者手填用的空白 BOM。

## 4. `Stepping through filter coeficient population.xlsx`（2014-10-15 进仓）——一张比固件更早的滤波系数走查表

机制事实（可复算）：`Sheet1` 是 **1155 行 × 19 列**，单元格里反复出现
`fftFilterCoeficient[N] | float | <数值>`；把全部 `N` 收下来是 **0…511，共 512 个不同下标**。
而固件里 `Source/src/main.c:52` 正是 `#define FFT_BUFFER_SIZE  512`，
`:63` 是 `float fftFilterCoeficient[FFT_BUFFER_SIZE];` ⇒ **这张表走查的就是这个数组**，
1155 行 = 同一张 512 点在"移动滤波下沿/上沿"过程中的多个版本。

值得记下的一点落差：表里的值是**浮点**（0.1289、−0.0003311、0.0165 … 像一条真实的窗/系数曲线），
而固件在 `:162-182` 只是把这段区间**填 1 或 0**（`fftFilterCoeficient[i] = 1 / = 0`）——
即出厂代码用的是二值掩码，作者 2014 年这张表里却是成形系数。
**这不构成 bug 判定**（可能是刻意的显示窗，也可能是没来得及实现），
但它与上游 **#6「S meter pinned on USB with filter bottom at 0」**（2017-01-06 开，至今 OPEN）
和我们的 **#20**（`recieve_with_filter` 等四个空 case）是同一条线上的三块料，
rev-B 做数字滤波/显示窗时这是唯一能直接复用的作者原稿。

---

## 这轮读出来的三条"该改的地方"

1. **`docs/PSDR-author-measurement-log.md` 缺这一整层材料**——那份文档编目的是 commit 里的作者原话，
   没覆盖 `Documentation/` 这 6 份二进制/Office 文件。本文先立独立档案，不改动那份（避免追溯性重写）。
2. **`docs/README.md` 里没有 `Documentation/` 的入口** ⇒ 本文已加一行，后续任何"作者说过什么"的
   检索都必须把它算进搜索范围。
3. **`PSDR2 Guide.pdf` 的位号与 2.6.1 不同一代** ⇒ 之前所有"作者没写 AD8302 周边为什么"的判断，
   现在多了一条出处（作者自己在 2014 页面上写的 "TODO: What are C68 and 111 for again?"）。

## 复算命令

```bash
# 六份文件的身份
cd "D:/my git/PSDR" && python -c "
import hashlib,os
for f in sorted(os.listdir('Documentation')):
    b=open('Documentation/'+f,'rb').read()
    print(f, len(b), hashlib.sha256(b).hexdigest()[:12])"
# PDF 文本（Windows 侧 pypdf/pdfminer/pymupdf 都在；本页提取用 pypdf -layout 等价物）
python -c "from pypdf import PdfReader; r=PdfReader('Documentation/PSDR2 Guide.pdf'); print(len(r.pages)); print(r.pages[0].extract_text()[:2000])"
# xlsx 结构
python -c "import openpyxl,re; ws=openpyxl.load_workbook('Documentation/Stepping through filter coeficient population.xlsx',data_only=True)['Sheet1'];
idx={int(m.group(1)) for row in ws.iter_rows(values_only=True) for v in row if isinstance(v,str) and (m:=re.match(r'fftFilterCoeficient\[(\d+)\]',v))};
print(len(idx), min(idx), max(idx), ws.max_row, ws.max_column)"
# docx 文本
python -c "import zipfile,re; x=zipfile.ZipFile('Documentation/Final Video Script.docx').read('word/document.xml').decode('utf-8','replace');
print(re.sub(r'<[^>]+>','',x.replace('</w:p>','\n'))[:2000])"
```

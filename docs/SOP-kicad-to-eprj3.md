# SOP：KiCad → eprj3 原生格式转换（免费打样通道）

日期：2026-11-07。面向"下一次有人想把这块板变成嘉立创EDA原生工程去用免费打样"。
与 `SOP-eda-import-2.6.1.md` 的区别：那份走**网页版导入 + connector typed 操作**；
这份走**官方转换器产出原生 `.eprj3` 文件夹工程**，用桌面客户端打开。
本文只描述 fork 内的操作与证据，不向上游 PSDR 发布。

红线照旧：不用 GUI 自动化做工程编辑；对转换产物的修复全部是**离线参数化脚本**
改记录流，改完有回读对账。桌面客户端没有 connector（`easyeda health` 的 windows 为空
是**正常现象**，不是故障），所以这条通道里客户端内的操作只能人工。

## 0. 一句话现状

转换本身**已经成功**，产物在 `D:/psdr_eprj3/PSDR_revB_poured/`（板框、12 块铺铜、
277 网都已修复并回读核验）。卡住的不是转换，是**桌面客户端加载这块 3.6 MB / 约 11,800
条记录的板极慢（13–30 分钟量级）**。判断"在干活还是死了"用 §5 的监视器，不要凭感觉重启。

## 1. 工具链与命令

| 项 | 值 |
|---|---|
| 转换器 | `easyeda/kicad-to-easyeda-eprj3` @ `a16545d`（2026-09-10 HEAD） |
| 输入 | `dist/kicad/PSDR_2.6.1_revB.kicad_pcb`（sha256 `aa24bda9…`，在 `SHA256SUMS` 的 `[exact-committed]` 行） |
| 宿主 | 嘉立创EDA专业版桌面 **V4.1.60** |
| 已知 bug 上游单 | [easyeda/kicad-to-easyeda-eprj3#2](https://github.com/easyeda/kicad-to-easyeda-eprj3/issues/2)（2026-11-07 提报，含本文全部数字） |

```bash
node scripts/convert-kicad.js convert <KiCad工程目录> <输出目录> --project-name PSDR_revB
```

输出是**文件夹工程**：`<名称>.eprj3`（JSON 索引）+ `pcb/PCB1.epcb2` + `sch/*.esch2`。
`.epcb2`/`.esch2` 是记录流文本（每行 `HEAD||BODY|`），可以直接离线解析/改写。

## 2. 两个已知转换器 bug（都已离线修复，勿再踩）

### 2.1 Edge.Cuts 圆弧 → 板框上的 giant circles

- 根因：`scripts/convert-kicad.js:1042` 的 `arcOutlinePath` 输出
  `[x1, y1, "ARC", sweep, x2, y2, …]`，把**扫角**放在 `ARC` 后；宿主把前两个数当**圆心**读，
  小圆角（弦长约 6.32 mm）渲染成大圆。板框还被拆成 50 条 `BOARD_OUTLINE` 碎片。
  转换器自带 example 有 0 个 `gr_arc`，此路径上游没测过。
- 修法（已做）：把 25 条 `gr_arc` 按 2° 步长折线化，与 42 条 `gr_line` 缝成**一条闭合
  `BOARD_OUTLINE` POLY**（1212 点）。回读：包围盒 99.9998 × 64.9986 mm 与源板一致，
  最大 sag 0.0007 mm。源几何存档 `D:/psdr_eprj3/outline_edgecuts.json`。

### 2.2 铺铜丢网 → 12 块无网孤岛铜

- 根因：`convertZone`（`:1175-1177`）只按**数字网号**查 `netNames[netArr[0]]`；
  我们的 zone 写的是名字串 `(net "GND")`，查不到 ⇒ `netName:""`。
  转换产物 12 块 POUR 全部 `netName:""`、`name:"POUR1"`、`keepIsland:false`——
  **看起来铺了铜，实际全是浮铜**。走线用数字网号所以没事，极具迷惑性。
- 修法（已做）：按同层 bbox 与源 `Hardware/PSDR.asc` 的 12 个 POUROUT 匹配，
  恢复 netName，**12/12 匹配误差 0.000 mil**（`D:/psdr_eprj3/pour_netmap.md`）。
  7 个网：F.Cu GND/+3V3/+3V3_CPU×2/+5V_BOOST/BOOST_LOOP/V_SUPPLY，
  In1 +3V3/+3V3_CPU/+3V3_FLIP_FLOP，In2 GND，B.Cu GND。
- 预防：以后生成 KiCad zone 时写数字网号 `(net N)`，或转换后必查 POUR.netName 非空。

## 3. 导入方式（"导入不进去"的根因）

- `.eprj3` 是**文件夹工程索引，不是可上传文件**。网页版"导入"对话框只收单文档
  （`.epcb2` 等），选 `.eprj3` 会失败——这不是文件坏了。
- 正确姿势：**桌面客户端 → 打开文件夹工程**，选 `D:/psdr_eprj3/PSDR_revB_poured/`。
- 只要 PCB 不要原理图时：`pcb/PCB1.epcb2` 是自包含的（57 个 FOOTPRINT + 57 个 DEVICE
  doc head 都在里面），可以单独走网页版导入。

## 4. 交付件清单（回读核验过）

`D:/psdr_eprj3/PSDR_revB_poured/pcb/PCB1.epcb2`：
**3,644,007 B，sha256 `e4e246e945f9fc761423ab0a7b14c568d191117fab4dad904233aea82ed22303`**

| 项 | 数 | 备注 |
|---|---|---|
| COMPONENT | 391 | 与网表一致 |
| NET | 277 | rev-B 并网后（VDDBG→LPF_5V） |
| PAD_NET | 1132 | 其中 145 个 `$$$NNNNN` 自动网名显示为 `##NNNNN`，**不是乱码** |
| POUR | 12 | 全部有网，无空 netName |
| BOARD_OUTLINE | 1 | 闭合 1212 点，99.9998 × 64.9986 mm |
| LINE / VIA | 6578 / 419 | 铜走线 5034 条，四层 |

电气缺口（`D:/psdr_eprj3/connectivity_report.md`）：唯一真实断点是 **LPF_5V 的
2.506 mm**（rev-B 并了网号但离线文件里物理铜没连；EDA 现场你已补 +155 mil，
离线这份还没补——走线归用户）。NRST 的 0.000 mm 跨层缺口判为焊盘桥接，不算断。

免费档：你已用 no-pour 变体实测**可以免费打样**，证明这个原生格式走券通道成立；
带铜版下单前仍要过一遍 DFM（4 处 <5 mil 线距是已知风险点）。

## 5. 加载慢：怎么判断它在干活

实测：Node `JSON.parse` 全部 11,800 条记录只要 **13–23 ms**，客户端却要 **13–30 min**
⇒ 瓶颈在客户端对象构建/渲染/DRC，不在文件解析。**改文件（压缩、舍入坐标）救不了**
（坐标舍入到 0.01 mil 只省 13.1% 体积，几何变化 0.0000 mil，已试）。

只读监视器：`D:/psdr_eprj3/watch_eda.ps1`

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:/psdr_eprj3/watch_eda.ps1 -Samples 5 -IntervalSec 5
```

判读：`WORKING-full-core`（单核吃满）+ 内存增长 + cache 持续写 = 在构建对象，**等**；
`IDLE` 且标题已变 = 加载完；长时间 `IDLE` 且标题还是"加载中"才考虑重启。
2026-11-07 15:30 现场读数：pid 28488，dCPU 4.1s/3s，WS 1033→1181 MB，cache 持续写，
`WORKING-full-core`，标题 `PSDR_revB_poured` ⇒ 当时仍在正常加载。

缓解（人工，客户端内）：关实时 DRC、少开层显示；加载期间不要反复开关工程。

## 6. 排障速查

| 症状 | 根因 | 处置 |
|---|---|---|
| 网页版导入选不中 `.eprj3` | 文件夹工程不是单文档 | 桌面客户端打开文件夹（§3） |
| 板框上有大圆/板框碎裂 | bug 2.1 | 用已修复的 `PSDR_revB_poured`，别用原始转换输出 |
| 铺铜全连不上/全是孤岛 | bug 2.2 | 同上；自查 POUR.netName 是否为空 |
| 网络名一半是 `##数字` | PADS 自动网名 `$$$NNNNN`，EDA 拒 `$` | 正常，145/277，不是损坏 |
| 加载十几分钟没动静 | 客户端对象构建慢 | §5 监视器判活，别杀进程 |
| `easyeda health` windows 为空 | 桌面客户端无 connector | 正常；本通道客户端内操作只能人工 |

## 7. 回滚点与复现

- 原始转换输出（未修复）：`D:/psdr_eprj3/PSDR_revB/` 与 `D:/my git/_eprj3_out/`。
- 修复前备份：`D:/psdr_eprj3/_backup_eprj3_out_203454/`。
- 复算铺铜匹配：`pour_netmap.md` 内附脚本口径（`"R"` 描述符 = `[x, y, w, h]`，y 向下，
  **不是**对角两点——这里踩过坑）。
- 板框源几何：`outline_edgecuts.json`（42 line + 25 arc，含圆心/半径）。
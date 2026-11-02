# SOP：把 2.6.1 的 KiCad 板导入嘉立创EDA专业版并拿到 12/12 铺铜

面向"下一次有人从仓库重新开始"。写这份东西的原因很具体：**照仓库现在的方式直接导入，
会得到 10/12 铺铜**，那**不是回归**，是已知行为（§C-15 补充）。少了这一步，下一个人一定会
误判成我们把铺铜改坏了。

红线照旧：不用 GUI 自动化做工程编辑（easyeda-agent 硬红线）。下面第 2 步与第 5 步是
**没有 typed 接口的两下人工动作**，本 SOP 不假装能自动，也不许用鼠标自动化顶替；
其余全部是命令行 + 可回读验证。

## 前置

| 项 | 要求 | 怎么确认 |
|---|---|---|
| 宿主 | 嘉立创EDA专业版 **4.1.60**（V4；V3 会 `hostCompatibility: block`） | `easyeda health` 看 `versionGate` |
| 连接器 | easyeda-agent connector **1.15.0** 已启用且允许外部交互 | `easyeda health` 的 `windows` 非空 |
| daemon | 60832 在听 | `netstat -ano \| grep 60832`（注意 `easyeda.exe` 是 **daemon**，不是 EDA 本体） |
| 板子 | `dist/kicad/PSDR_2.6.1_pcb_spike_full.kicad_pcb` 与清单一致 | `python tools/reproduce_kicad.py --check` |

## 1. 生成参考板（可自动）

```bash
python tools/reproduce_kicad.py            # 板 + DRC + fab + dist/kicad/SHA256SUMS
python tools/reproduce_kicad.py --check    # 只验不改
```

预期：`all files match the manifest`，板子 sha256 前缀 `5029bd02`（记录在 `SHA256SUMS`）。

## 2. 【人工】把它导进 EDA

编辑器里 `文件 → 导入 → KiCad`，选上面那个 `.kicad_pcb`。
**为什么这步是人工**：typed action 目录（167 个）和通道 B 的 `pcb_document_action` 都只有
`import_changes`（原理图网表→PCB）、`import_autoroute`、`silk.import_svg`，
**没有 KiCad 板导入接口**（§E-9 记为 `unsupported`）。

导入后确认身份：
```bash
easyeda doc ls --project <工程名>          # 找 PCB 文档 UUID（记下 <pcb-uuid>）
easyeda pcb layers --doc <pcb-uuid>        # 4 个铜层（F/In1/In2/B）
easyeda pcb nets   --doc <pcb-uuid> | head -1   # 278 网
easyeda pcb list   --doc <pcb-uuid> | wc -l     # 391 件
```

## 3. 导出原生工程

```bash
easyeda project export --project <工程名> -o out/PSDR_2.6.1_imported.epro2
```

## 4. 按源数据补铺铜优先级（可自动，关键一步）

```bash
python tools/eda_epro2_pour_source.py out/PSDR_2.6.1_imported.epro2 \
                                       out/PSDR_2.6.1_poursourced.epro2 \
                                       --asc Hardware/PSDR.asc
```

它在干什么：EDA 的 KiCad 导入器**丢掉了铺铜优先级**，把 12 个区按文件顺序编号 1..12；
而 EDA 判定重叠铺铜是 `order` **小者优先**（与 KiCad 相反），所以最后两个区
（`+3V3_FLIP_FLOP` 在 In1、`V_SUPPLY` 在 F.Cu）整片拿不到铜 ⇒ **10/12**。
这个脚本从 PADS ASCII 的 `POUROUT` 尾字段与 `PLANEFLAGS` 取回真实优先级与"保留孤岛"位，
只改命中的那 12 行 `POUR` 载荷，其余字节原样拷贝。
参照标准是 **EDA 自己从 PADS 路由出来的那份工程**：12 条 `(net, layer, order, keepIsland)` 逐值相同。

## 5. 【人工】把打过补丁的 `.epro2` 导回来

同样是宿主侧文件动作，无接口（§E-9）。导入后 `save → 关闭文档 → 重新打开`。

## 6. 验收（可自动，必须回读）

```bash
easyeda pcb poured-list --doc <pcb-uuid>
```

判据（不是"看起来有铜"，是逐个数字对得上）：

| 网络 | 层 | 铜皮块数 |
|---|---|---|
| `+3V3` | In1 / TOP | 1 / 16 |
| `+3V3_CPU` | In1 / TOP / TOP | 6 / 1 / 26 |
| **`+3V3_FLIP_FLOP`** | In1 | **7**（源里就是 7 条独立 HATOUT） |
| `+5V_BOOST` | TOP | 19 |
| `BOOST_LOOP` | TOP | **10**（§C-15 那次记的是 11，见下） |
| `GND` | In2 / TOP / BOTTOM | 26 / 296 / 360 |
| **`V_SUPPLY`** | TOP | **4** |

- **12/12 非空**，合计 772 块；连读两次逐个相同才算过（`evidence/eda_poured_2026-11-02.json`）。
- `BOOST_LOOP` 现在稳定读到 10 块，§C-15 记的是 11 块：差的是一块铜皮的分裂计数，
  不是零铜回归。追它要做 `pour rebuild`（写操作），本轮未做，只记录。
- EDA 自带 DRC 会 **507 → 513**：多的 6 条全是 `+3V3_FLIP_FLOP` 在 In1 的孤岛铜
  `No Connection`（源里那 7 条 HATOUT 本来就有 6 条孤岛）。中途读数会漂（曾见过 520/534），
  **报数以 `save → 重开 → 复测` 为准**。

## 7. 仍然没闭合的一条（别当成已完成）

岛铜之间的净间距现在只按 **EDA 默认规则（0.6 mm 档）**量过，
**没按源里的 8 mil 规则复核**。所以 12/12 只证明"铺铜算法与源优先级一致"，
不证明"岛铜间距符合设计规则"。这一步是纯离线的几何活，挂在待办里。

## 已知不可自动化的边界（汇总）

| 步骤 | 状态 | 出处 |
|---|---|---|
| KiCad 板 → EDA 导入 | 人工，接口缺失 → `unsupported` | §E-9 |
| 打过补丁的 `.epro2` → EDA 导入 | 人工，接口缺失 → `unsupported` | §E-9 |
| `preserveSilos` / `pourPriority` 写入 | 通道 B `pcb_document_action`（2.4.0）可写，超时进隔离需 `bridge_recover_client` | §C-15 补充 |
| GUI/CUA 自动化顶替上面两步 | **禁止**，不是兜底手段 | easyeda-agent 硬红线 |

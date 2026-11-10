# datasheets/ — 原厂 PDF 本地存档（fork-only）

取证口径：URL 直下 + `%PDF` 魔数 + sha256 与外包双下载记录（`delegation/answers/ANS_任务E_官方数据手册直链.md`）比对。
一致 ⇒ 原件级；不一致先查截断/换版，不直接升级。

| 文件 | 来源 URL | 版本 | sha256 | 状态 |
|---|---|---|---|---|
| hmc1023.pdf | https://www.analog.com/media/en/technical-documentation/data-sheets/hmc1023.pdf | v01.0113，34 页 | f80b95bf3a68358efa70b6b82aa448c66b33f2378e15d6a12c37ef18524e2cb2 | 2026-11-09 双下载一致（首次下载得到截断变体 bcd2d30a…，993,058 B，弃用；重下 1,997,914 B 与外包记录一致） |
| sn74cb3q3253.pdf | https://www.ti.com/lit/ds/symlink/sn74cb3q3253.pdf | SCDS145D（2003-10，修订至 2026-08），31 页 | 96d6c387bc61c2e8e567ab4f20c79479f6406fabd1daba9df33f89d08ea7f533 | 2026-11-09 下载即与外包记录一致 |
| GALI-4plus.pdf | https://www.minicircuits.com/pdfs/GALI-4%2B.pdf | REV. T（ECO-024667，260421），4 页 | 0ad8f527858b6b795b438068de8d2076a7c8e278940827f8f314f5892a3caaad | 2026-11-10 原件级（需浏览器 UA，裸 curl 403）；U304 进口备选依据 |
| ZDH3003_v1.2.3.pdf | https://www.cemaxrf.com/upload/pdf/202607/ZDH3003%E8%A7%84%E6%A0%BC%E4%B9%A6V1.2.3.pdf | V1.2.3（2024-03），7 页 | 0e42cf756b3561387891d63cfc4c5c5665ef840d2c1710315b2f893f7d35bdd2 | 2026-11-10 原件级；手册 5MHz–3GHz（官网表格写 DC，以手册为准） |
| ZDH3020_v1.2.3.pdf | https://www.cemaxrf.com/upload/pdf/202607/ZDH3020%E8%A7%84%E6%A0%BC%E4%B9%A6v1.2.3.pdf | V1.2.3（2024-03），7 页 | 57b3105094b73fff6963f9f438794024ca1ec4ffaf21436627ca069a7298c4cf | 2026-11-10 原件级；U304 国产首选依据（HF 段 22dB / NF≤1.7dB） |
| ZDH3157_v1.2.0.pdf | https://www.cemaxrf.com/upload/pdf/202610/ZDH3157%E8%A7%84%E6%A0%BC%E4%B9%A6V1.2.0.pdf | V1.2.0（2024-05），5 页 | 153c75c08fde4384ac59e49cdca6a54db2749fc734225c5dc2219e22285213c9 | 2026-11-10 原件级；**500MHz–3GHz ⇒ HF 不可用**，留档作排除证据 |
| ZDH5438_v1.2.0.pdf | https://www.cemaxrf.com/upload/pdf/202607/ZDH5438%E8%A7%84%E6%A0%BC%E4%B9%A6v1.2.0.pdf | V1.2.0（2023-12），8 页 | 63157e44afee898f6b2bbf16da996e58bf25310a1c7f352f4a175bfd6bdd13f6 | 2026-11-10 原件级；MASWSS0129 路线 B 候选（DC–6GHz DPDT，6 脚 DFN 非 pin 兼容） |
| Si5338.pdf | https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si5338.pdf | Rev. 1.6（2021-08-29），46 页 | d6857f2e224a5271c8899d8ebdbaa1e28e78542f316be2c64c3cacb49c2b5b6a | 2026-11-10 原件级（续传后与外包记录一致）；**p20 §3.3 VCO = 2.2–2.84 GHz**，纠正我方"超 2.8 上限"误读（D-09 关闭） |

用途：U287 HMC1023 寄存器映射（Table 15–22）与 U211/U298 实购 CB3Q3253 真值表的原件级依据；
2026-11-10 新增五份用于 U304 前放替代（#55）与 MASWSS0129 T/R 开关替代（#60），
结论见 `docs/PSDR-alternates-proposal.md` §2.2/§4.1 与 `docs/PSDR-research-2026-11-10.md`。
注意 netlist 名义型号是 CBTLV3253，实购是 CB3Q3253，两族真值表/Ron 不同，按 CB3Q 走
（见 `docs/PSDR-open-data-gaps.md` #6）。

仍缺原厂 PDF 的件（官网撤档/断链，见 ANS_任务E §2）：MASWSS0129、SXB-2089Z、SPU0410HR5H-PB、W3062A、
FAN4174/MC10EP52（Akamai 403）、RXM-GPS-RM-T（TE 文档控制器只回 HTML）。
2026-11-10 复核：`macom.com/DataSheets/MASWSS0129.pdf`（及 0143/0202 兄弟件）全部 404，
撤档确认；当时误存的三个 2742 B 错误页已删除。中电宏业官网表格的"DC 起步"与手册不符
（ZDH3003/3020 实为 5MHz、ZDH3157 实为 500MHz）——**一律以 PDF 手册为准**。
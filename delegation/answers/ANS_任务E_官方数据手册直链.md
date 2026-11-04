<!-- PROVENANCE / 取证口径（本 fork 添加，非原文一部分）
来源：外部执行方（另一账号）2026-11-03 交回的调研答案，经 IMA 知识库 psdr 文件夹取回。
状态：**外部断言**。已逐条核对的部分见 docs/PSDR-external-findings-2026-11-03.md
      （原厂 PDF sha256 对得上才升级）；未核对的性能/年份数字不得直接进对外文本。
-->

原始文件：ANS_任务E_官方数据手册直链.md（8156 字节，sha256 `7dd00b43b7dca359db60856c18140ab74e9c64067a4ba406f9f0964408ad8772`）

# PortableSDR 2.6.1 任务 E：官方数据手册 PDF 直链核实表

- 核实日期：2026-11-03
- 清单来源：ima psdr delegation pack（`_index.csv` 22 个 distinct part_type）+ `bom_rows.csv` 实购 MPN + W3062A 天线
- 规则：厂商域名直链优先，禁第三方汇总站/镜像；**sha256 由同一 URL 连续两次下载一致得出**（双下载均校验 %PDF 魔数 + %%EOF 完整性）；**版本/日期只认手册首页可见**；找不到官方 PDF 写"未找到"
- 本地留存：`E_datasheets/`（每型号 .1.pdf/.2.pdf 双下载对 + `meta/<型号>/p1.txt` 首页文本、`split/` 分页）

## 1. 已验证（20 项，双下载 sha256 一致）

| 厂商 | 完整型号 | URL | 文档编号/版本 | 封面日期 | 总页数 | sha256 |
|---|---|---|---|---|---|---|
| Texas Instruments | TPA0253DGQR | https://www.ti.com/lit/ds/symlink/tpa0253.pdf | SLOS280D | JANUARY 2000 – REVISED NOVEMBER 2002 | 14 | 668fed9414cc35bedc76277a79451723cc5492973c650c9e04bfb8a0687c8802 |
| Texas Instruments | SN74CB3Q3253DBQR | https://www.ti.com/lit/ds/symlink/sn74cb3q3253.pdf | SCDS145D | OCTOBER 2003 – REVISED AUGUST 2026 | 31 | 96d6c387bc61c2e8e567ab4f20c79479f6406fabd1daba9df33f89d08ea7f533 |
| Texas Instruments | SN74LVC1G3157DCKR | https://www.ti.com/lit/ds/symlink/sn74lvc1g3157.pdf | SCES424O | JANUARY 2003 – REVISED JUNE 2025 | 56 | 054575a791ba8da81e6d1c7b6c685203adade306cb8d27679cd7aba8f6fce3be |
| Texas Instruments | SN74CBTLV3253（netlist 名义型号） | https://www.ti.com/lit/ds/symlink/sn74cbtlv3253.pdf | SCDS039K | DECEMBER 1997 – REVISED JULY 2026 | 37 | d6fb46fe6b7ccc5e85a0e898ef912f6f1a6694720028ac81625f4f2608be03fb |
| Analog Devices | AD8302ARUZ | https://www.analog.com/media/en/technical-documentation/data-sheets/AD8302.pdf | Rev. B | ©2018 | 23 | cd52c37aedc301684968890140e6684ae3563c5b7222249cb81345f5aeb17fe8 |
| Analog Devices | AD8131ARMZ | https://www.analog.com/media/en/technical-documentation/data-sheets/AD8131.pdf | Rev. B | ©2005 | 20 | 162eca055bc98e1fd8967bd6fb78781e55ac69fb9e2ff4a96971b197dcd9f24e |
| Analog Devices | SSM2167-1RMZ-R7 | https://www.analog.com/media/en/technical-documentation/data-sheets/SSM2167.pdf | Rev. G | ©2001–2011 | 12 | 32b200c27cbe3c3ac5c58137436d3fb3a721677713c463053654e46951564517 |
| Analog Devices | ADP1613ARMZ-R7 | https://www.analog.com/media/en/technical-documentation/data-sheets/ADP1612_1613.pdf | Rev. D（ADP1612/ADP1613 合册） | ©2009–2012 | 28 | a5ef891354796c0323aec489b36ec402d97d1abdcf556774026c23550933ba7d |
| Analog Devices（原 Maxim） | MAX4525CUB+ | https://www.analog.com/media/en/technical-documentation/data-sheets/MAX4524-MAX4525.pdf | 19-1332; Rev 2 | 6/07 | 14 | a50b8877e18f87397a7c0fbd4dacd760d992579d386165e468ecdfedc6b886f6 |
| Analog Devices（原 Maxim） | MAX5388NAUB+ | https://www.analog.com/media/en/technical-documentation/data-sheets/MAX5386-MAX5388.pdf | 19-4599; Rev 3 | 9/14 | 13 | f1e409e6f3971fe752672ea2cf3f81cbcbbb786138ededb55c01defcb85076d9 |
| Analog Devices（原 Hittite） | HMC1023LP5E | https://www.analog.com/media/en/technical-documentation/data-sheets/hmc1023.pdf | v01.0113 | 首页未印日期 | 34 | f80b95bf3a68358efa70b6b82aa448c66b33f2378e15d6a12c37ef18524e2cb2 |
| Analog Devices（原 Hittite） | HMC482ST89（netlist 名义型号） | https://www.analog.com/media/en/technical-documentation/data-sheets/hmc482.pdf | v04.0710 | 首页未印日期 | 6 | af7aafdc93c682c0a1dce8196cc8060bd69b9b751d6c0c38dece16361f27ed7d |
| STMicroelectronics | STM32F746VGT6 | https://www.st.com/resource/en/datasheet/stm32f746vg.pdf | DS10916 Rev 5 | July 2025 | 230 | 23a9ec5dfd13ea2ec9d776f75a03e32d25a7bf49ef2d5438a36157e6d97c23fa |
| Diodes Incorporated | AP3417CKTR-G1 | https://www.diodes.com/assets/Datasheets/AP3417C.pdf | DS36516 Rev. 3-3 | July 2019 | 13 | bdd08bbcebc007e6c60654b4fb89dd53af7b70a70b917c055e30307776773a62 |
| Mini-Circuits | ADE2ASK+（手册名 ADE-2ASK） | https://www.minicircuits.com/pdfs/ADE-2ASK.pdf | REV. H | 首页未印日期 | 2 | 44a6c860d2432aab3d65f3e28c4a5c4a1adb31cc4b3e058a9e65add9db3edfd8 |
| Skyworks（原 Silicon Labs） | SI5338A-B-GM | https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si5338.pdf | Rev. 1.6 | August 29, 2021 | 46 | d6857f2e224a5271c8899d8ebdbaa1e28e78542f316be2c64c3cacb49c2b5b6a |
| Coilcraft | WBC2-1TLB（手册名 WBC 系列） | https://www.coilcraft.com/getmedia/f685d903-2563-4c96-8ba6-f82a58883aeb/wbc.pdf | Document 424-1 | Revised 06/14/22 | 5 | b6f1e900e8d105f2976d20eb2cea49a6a2b2151eca9a37b6916bb1b8b90fe329 |
| Microchip | MCP73871-2AAI/ML | https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP73871-Data-Sheet-DS20002090F.pdf | DS20002090F | ©2008–2022 | 36 | 56654f56a8ac83ada87a05903bdecee9372f7d223719436f3b6d6de2d70b254f |
| Microchip | MCP6N11-010E/SN | https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/25073A.pdf | DS25073A | ©2011 | 50 | b08e0d74003c4ec2c7b77906b24dd4b03a4c69b46872238e495d61cf67416b8b |
| Microchip（原 Micrel） | SY10EP52V（BOM 实购 MC10EP52DTG，见备注） | https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/SY10EP52V.pdf | M9999-092305, Rev.: F | September 2005 | 7 | 3096ce68310fd4a6a244d9f5f8e446016b5d1be216db1739fdcdb2ded5845035 |

## 2. 未闭环（7 项）

| 厂商 | 完整型号 | 状态 | 证据/原因 |
|---|---|---|---|
| onsemi | FAN4174IS5X | **sha256 无法校验** | 官方 URL 存在：https://www.onsemi.com/download/data-sheet/pdf/fan4174-d.pdf（新路径，onsemi 文档库同款模式）；旧路径 /pdf/datasheet/ 亦确认；**本机所有出口均被 Akamai 403**（curl/PowerShell/IPv6 均拒），无法双下载 |
| onsemi | MC10EP52DTG | **sha256 无法校验** | 同上，https://www.onsemi.com/download/data-sheet/pdf/mc10ep52-d.pdf，Akamai 403 |
| TE Connectivity（原 Linx） | RXM-GPS-RM-T | **未找到可下载直链** | te.com.cn 产品页确认官方文档名 `ENG_DS_RXM-GPS-RM-T_A.pdf`（RM Series GPS Receiver）；但 DDEController 各参数组合只返回 197KB 查看器 HTML，te.com 被 Akamai 403，取不到 PDF 字节 |
| MACOM | MASWSS0129TR | **未找到** | macom.com 现行站产品页/搜索/sitemap/cdn.macom.com 均 404，官网已无此撤档件手册；第三方镜像（chipdip/alldatasheet 等）按规则不计 |
| Qorvo（原 RFMD） | SXB-2089Z | **未找到** | https://www.qorvo.com/products/p/SXB-2089Z 已返回 "Page Not Found"（撤档）；qorvo.com 无独立 PDF 直链留存 |
| Knowles | SPU0410HR5H-PB | **未找到** | knowles.com 各文档路径均 404；sensor360 收录的文件名 `SPU0410HR5H-PB_revH-876884.pdf` 无对应官网 URL |
| Pulse Electronics（YAGEO） | W3062A | **未找到** | pulseelectronics.com/wp-content/... → 301 跳 yageogroup.com 后断链（000/301 循环）；官网迁移未带文档 |

## 3. 备注

1. **前提错位**（与 netlist/BOM 不一致处，仅记录不展开）：
   - `74CBTLV3253`（netlist part_type）BOM 实购 **SN74CB3Q3253DBQR**（CB3Q 系列，非 CBTLV）——两份手册均收录；
   - `SY10EP52V`（netlist part_type）BOM 实购 **MC10EP52DTG**（ON）——本次收录 Micrel SY10EP52V 手册（netlist 名义型号）；MC10EP52 官方手册在 onsemi（见上表第 2 行，被 Akamai 拦）；
   - `MMIC-AMP_HMC482ST`（netlist）BOM 实购 **SXB-2089Z**——HMC482 手册已收录；SXB-2089Z 官方手册未找到；
   - `STM32F746_LQFP100` 的 decal 名继承 `STM32F429_LQFP100`（pack README 已警示），器件实为 STM32F746VGT6。
2. 首批 20 项中 ADP1613ARMZ-R7、HMC1023LP5E 曾出现 1MB 整截断下载（首下 1048576 字节），重下两次确认完整（1307552 / 1997914 字节）后才计入；截断样本的哈希不作数。
3. 「封面日期」列只抄手册第 1 页可见字样；©年份属首页可见即采用；Hittite/Mini-Circuits 手册首页无日期列标注"首页未印日期"。
4. 总页数 = workbuddy-pdf split 实际分页数（STM32F746 手册 230 页为物理页数，印刷页码 1/248–248/248）。

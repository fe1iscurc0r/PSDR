# F7 构建的参考镜像（reference hex）

放这里的原因：`Source_F7/.gitignore` 里有 `/Debug`，构建产物与上游提交的 `Debug/PSDR.hex`
都不适合再躺在镜像目录里被忽略掉——**锚点门的参考件必须是可检出的、被跟踪的**。
2026-11-03 改基（`Source_F7/` 从 `PSDR_Rebuild` 换到 `PSDR_F7`）时，旧那份差点被删，
所以两份都固定到这里，各自标清来源。

| 文件 | 大小 | sha256 | git blob | 来源 |
|---|---|---|---|---|
| `PSDR_hex_2017-01-15_aaa24f8_PSDR_F7.hex` | 269,832 B | `d5f372a614df3b68f35305378d59a9a9a5a62d73bc3ae93bcc698e4395805d05` | `e6fe1975869a87ff8b7e541a077fe6d161c95260` | `upstream/PSDR_F7:Source/Debug/PSDR.hex`，该文件最后一次改动 `aaa24f8`（2017-01-15，Paul Warren "More compiler warnings"），分支 tip 是 `ab2c8fd`（2018-07-31）⇒ **改基后主线的官方参考** |
| `PSDR_hex_2018-06-21_457c270_DMA.hex` | 216,207 B | `88cf1abbbc107b87ab5e71bfddb64c82fe7ae5e5c3ea5778d5e0902df2ced60c` | `73b11f703ab604954b6e234c6c3723a1b357686f` | `upstream/PSDR_Rebuild:Source/Debug/PSDR.hex`（= `PSDR_F7_DMA` 同一 blob），最后一次改动 `457c270`（2018-06-21 "this DMA thing is killing me"）⇒ **M2 那次对账用的历史参考，留着以便复算** |

## 怎么复算（本地实测，2026-11-03）

```bash
# 构建（Linux/WSL 侧，arm-none-eabi-gcc 13.2.1）
cd Source_F7 && make -f Makefile.linux -j4
#   make rc=0；0 error；26 warning
#   arm-none-eabi-size build_linux_f7/PSDR.elf
#     text 114068   data 18488   bss 18260   dec 150816
#   产出 build_linux_f7/PSDR.hex，sha256 5409836ec6035eb9bbfbaa49f39429e371d96a54f10276dfb5141fbe1655ac30（372,928 B）

# 锚点门（两份参考各过一次，都 PASS）
python tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex \
    dist/reference/PSDR_hex_2017-01-15_aaa24f8_PSDR_F7.hex
python tools/anchor_check_f7.py Source_F7/build_linux_f7/PSDR.hex \
    dist/reference/PSDR_hex_2018-06-21_457c270_DMA.hex
```

门只看**与链接布局无关**的两个性质：初始 SP 与空向量槽图案；本次都是
`SP=0x20050000`、`empty-slots=[7, 8, 9, 10, 13, 95]` ⇒ **PASS**。
reset 值不作门（`0x080001D5` vs 参考 `0x080002F9`/旧参考另值），因为链接布局会变；
`words equal = 7/118` 反映的是 **2018/2017 老工具链产物 vs GCC 13.2.1 的必然差异**，
不是"编错了"——这条边界与 M2 记录一致（同一份源码在 GCC 13 下 `-O0 112,344 B`，
而那份 hex 是 76,837 B 的优化构建）。

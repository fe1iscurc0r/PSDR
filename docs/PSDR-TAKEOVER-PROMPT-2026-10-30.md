# 提示词 · 在本地开新仓并开工（PSDR 接手）

> 用途：把下面「提示词正文」整段丢给 Qoder。
> 完整施工细节在 fork 仓库内的工单文件里，提示词只负责开场和第一步。

---

## 提示词正文（复制这段）

你现在接手 **PSDR (PortableSDR)** 项目的开发，这是一个独立的 HF 全频段软件定义收发信机（0–35 MHz，STM32F429/F756 + 双 AD9834 DDS，MIT 许可，我们已获授权接手）。

上游自 2016 年后再无固件更新，**从未有过一次可链接的构建**。你的任务是让它能在现代 Linux + arm-none-eabi-gcc 上构建出来，并把 Eagle 格式的硬件文件转成 KiCad 供嘉立创EDA 导入。

## 第一步：完整克隆到本地新仓

本地仓库路径用你天选7 上的默认工作区即可（建议 `~/Projects/PSDR`，Windows 原生则 `D:\Projects\PSDR`）。**这是新建的独立工作目录，不要复用已有的任何旧目录。**

```bash
git clone https://github.com/fe1iscurc0r/PSDR.git
cd PSDR

# 上游原始仓库，保留关联以便日后比对/同步
git remote add upstream https://github.com/MichaelRColton/PSDR.git
git fetch upstream --prune
git fetch origin --prune

# 切到工作分支（工单已放在这个分支上）
git checkout workorders/2026-10-30-psdr-takeover-linux-build-kicad
git reset --hard origin/workorders/2026-10-30-psdr-takeover-linux-build-kicad
```

## 克隆的硬性要求

1. **必须完整克隆**。禁止 `--depth`、`--single-branch`、`--filter`，也不许用 tarball 代替。
2. **必须带全 7 个分支**：`PSDR_F7` 是 STM32F756 平台，而 **2.6.1 版硬件 BOM 用的正是 STM32F756** —— 只留 master 会缺最接近目标硬件的整条固件线。
3. **GitHub 连不上就配代理重试**（`git config --global http.proxy <你的代理>`），**绝不能因此降级成浅克隆或只拉 master**。仓库本身约 182 MB，耐心等。

## 宿主环境：选 WSL2（已实测，Windows 原生工具链不要用）

这台机器只有 Windows，最多装 WSL2 → **就用 WSL2 + Ubuntu**。

**不要直接用 Windows 原生 ARM 工具链**，三个理由：
1. Makefile 用了 `$(wildcard)` / `$(VPATH)` / `$(filter-out)` 等 GNU make 专有语法，
   必须另装 GNU make（MSYS2），否则 nmake 直接不认；
2. Windows 路径分隔符要和 Makefile 里的 `/` 混着处理；
3. **换来零收益** —— 锚点由链接脚本 + startup 汇编 + MCU 宏决定（`mem.ld`:
   `RAM ORIGIN=0x20000000` / `FLASH ORIGIN=0x08000000`），**不是编译器决定的**。

**好消息（已实测本仓库）**：无大小写地雷、无超长路径（最长 82 字符）、无 Windows 非法字符、
参与编译的 749 个源文件是纯裸机固件无 POSIX 依赖。所以 WSL2 上不会踩这些坑。

**WSL2 两个必踩的坑**：

1. **不要在 `/mnt/c/` 下编译** —— 跨文件系统访问极慢，749 个文件编译会卡死。
   ✅ 仓库放 WSL2 原生 ext4（`~/PSDR`），编完再拷回 Windows。
   验证：`stat -f -c %T .` 应输出 `ext2fs`/`ext4`，是 `drvfs`/`9p` 就换地方。

2. **用 Windows 版 Git 克隆会毁掉 Makefile** ——
   实测上游全部是 LF，但**仓库没有 `.gitattributes`**（无保护）。
   Git for Windows 默认 `core.autocrlf=true` 会转 CRLF，Makefile 靠 Tab 缩进，
   转完 `make` 报 `missing separator` 罢工。
   ✅ **推荐**：在 WSL2 里用 Linux 版 git 克隆（WSL2 内 git 默认 `autocrlf=false`，天然无此问题）。
   或用 Windows 版 git，但克隆**前**先 `git config --global core.autocrlf input`。

**具体怎么装**（WSL2 Ubuntu 内）：
```bash
sudo apt update && sudo apt install -y gcc-arm-none-eabi make git
```
装出来的 gcc 是 13.2.1，和验证时的版本完全一致。



编译 STM32 是**交叉编译**，工具链自包含。只要 `arm-none-eabi-gcc` + `make` + `git`（+ `python3` 跑锚点比对脚本）就够，**没有任何一项依赖 Ubuntu 特有功能** —— Kali、WSL2 Ubuntu、原生 Linux 都可以。

**别追 gcc 小版本**：真正要锁死的是二进制锚点（见下），它与编译器版本无关。gcc 版本不同只让 size 漂几字节。

⚠️ **三个坑**：

1. **Windows 换行符会毁掉 Makefile**（用 Git for Windows 克隆时必中）
   实测：上游全部文件是 LF，但**仓库里没有 `.gitattributes`** —— 没有保护。
   Git for Windows 默认 `core.autocrlf=true` 会把 LF 转 CRLF，Makefile 靠 Tab 缩进，
   转换后 `make` 直接报 `missing separator` 罢工。
   ✅ **克隆前**先设：`git config --global core.autocrlf input`
   （或在仓内 `git config core.autocrlf false && git checkout -- .`）

2. **WSL2 里不要在 `/mnt/c/` 下编译** —— 跨文件系统访问极慢，749 个文件编译会卡死。
   ✅ 仓库放 WSL2 原生 ext4 内（`~/PSDR`），编完再拷回 Windows。
   验证：`stat -f -c %T .` 应输出 `ext2fs`/`ext4`，若是 `drvfs`/`9p` 就换位置。

3. **Kali 的 PEP 668** 禁止系统级 `pip install`。本项目不需要 pip 装东西，
   临时要装就用 `python3 -m venv`。

**推荐分工**：编译验证放 Kali（真 Linux，无 CRLF 问题）；天选7 的 WSL2 当本地仓存代码。

## 克隆后验收（贴真实命令输出）

```bash
git rev-parse --is-shallow-repository   # 必须是 false
git branch -a | wc -l                    # 应 >= 15
git log --oneline -1 master              # 应为 45acd0f
git log --oneline -1                     # 应为 479ee18d2（工单 commit）
du -sh .git                              # 约 182M，偏差 >10% 要报告
git remote -v                            # origin=fork, upstream=MichaelRColton
git fsck --full                          # 不得有错误
```

## 然后读工单

克隆完成后，读这两个文件（就在你本地仓库里）：

```
docs/PSDR-TAKEOVER-WORKORDER-2026-10-30.md     ← 工单正文, 四个任务全在里面
docs/PSDR-TAKEOVER-EVALUATION-2026-10-30.md    ← 评估报告, 技术细节的出处
docs/psdr-handoff/Makefile.linux               ← 已验证可编译的构建脚本, 直接用
```

工单里的四个任务按顺序做：

- **A** 克隆与验收（就是上面这一步，做完即完成）
- **B** Linux 交叉编译复现 —— 修 4 处上游构建缺陷。**注意其中 3 个坑**：`hal.h` 的 `extern inline` 要求实现在 `.c` 里；`SysTick_Handler` 已存在于 `main.c:345`，别在 `stm32f4xx_it.c` 里新建否则重复定义；`uart.c` 是 SPL 时代代码，改完类型仍编译不过，需用新增的 `uart_hal_stub.c` 走 HAL。
- **C** Eagle → KiCad 转换 + Gerber 规范化命名，产出供嘉立创EDA 导入
- **D** 提交归档到本分支 + 写施工记录

## 构建验收硬指标

```bash
cd Source && make -f Makefile.linux
```

- `0 error`（warning 数百条属正常）
- `arm-none-eabi-size build_linux/PSDR.elf` → text 984908 / data 3004 / bss 18220
- **二进制锚点必须对上**：`arm-none-eabi-nm build_linux/PSDR.elf | grep _estack` → `0x20030000`；Reset 向量 `0x080001B5`。这两个值与上游 2016 年的 `Source/Debug/PSDR.hex` **逐字节一致**。

> 锚点对不上 = 构建配置错了，**不是"编译器版本差异"**。先自查再报。

## 纪律

- **不许写"已完成"而不贴真实命令和输出**。所有验收数字必须来自实际运行。
- **不许碰上游 `MichaelRColton/PSDR`**：不提 PR、不提 issue、不发评论。只在 `fe1iscurc0r/PSDR` 自己的分支上作业。
- **不要动 `PSDR_F7` 分支**——它与 master 差 15 万行，是另一套代码，混用会毁掉一切。
- **不要修射频逻辑**（前置放大器、低通滤波器、issue #6/#8/#9）。那需要实物硬件，不在本单范围。
- 遇到工单没覆盖的坑，记下来写进施工记录，不要自己绕过去。

开工前有疑问先问，别猜。

---

## 备注（给师傅看的，不必发给 Qoder）

- 工单在 fork 仓库里：`fe1iscurc0r/PSDR` @ `workorders/2026-10-30-psdr-takeover-linux-build-kicad`，commit `479ee18d2`
- 本地 scratchpad 也留了一份归档：`scratchpad/docs/工单-PSDR接手-天选7克隆与构建复现-2026-10-30.md`
- 如果你要的"本地开新仓"是指**另建一个全新的 GitHub 仓库**（而不是用现有 fork），说一声，我改指向

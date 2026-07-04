---
name: azf-hardware-skill
description: >-
  An Zhaofeng's hardware and server asset memory. Use whenever the user provides,
  asks about, verifies, deploys to, or updates information about servers,
  computers, GPUs, cameras, acquisition cards, storage devices, experiment
  instruments, network devices, or other hardware. Automatically supplement this
  skill when new hardware facts appear, but never record passwords, API keys,
  tokens, private keys, cookies, or other secrets.
---

# AZF Hardware Skill

Use this skill as An Zhaofeng's durable hardware and server inventory. Keep facts concise, current, and easy to verify.

## Maintenance Rules

- When the user provides new hardware, server, network, storage, or lab-equipment information, update this skill and its Chinese `README.md`.
- Record stable facts such as device name, model, location, IP/domain, operating system, CPU, memory, disk, GPU, role, and known limitations.
- Do not record passwords, API keys, tokens, private keys, cookies, recovery codes, or secret console links.
- If a fact is not yet verified, mark it as `待补充` instead of guessing.
- For Docker deployment layout and server operation conventions, use `azf-server-deploy` instead of this skill.

## Known Local Computer Conventions

### Windows software installation paths

- User-provided convention: besides default Windows install locations, most non-default software is installed under `E:\software`.
- Verified examples:
  - QQ: `E:\software\QQ\QQ.exe`
  - Next AI Draw.io: `E:\software\Next AI Draw.io\Next AI Draw.io.exe`
  - QQ Music: `E:\software\QQMusic\QQMusic.exe`
  - Tencent Meeting: `E:\software\TencentMeeting`
- When asked to open a local GUI application, check `E:\software` early instead of only searching `C:\Program Files` or Start Menu entries.

## Known Lab Instruments

### FrogTrace Zolix SGM1700 近红外光纤光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：卓立汉光 / Zolix SGM1700 近红外光纤光谱仪
- 光谱仪 S/N：型号下存在多台设备；`SGM26002` / `26002` 曾到货并拍摄实物照片，后续发生退换；2026-06-11 实际连接设备为 `SGM25003` / `25003`。2026-07-02 用户提供新铭牌照片显示同为 `26002`，铭牌日期为 `2026年06月16日`；Obsidian 旧附件中同 S/N 铭牌日期为 `2026年05月25日`。这两组照片按退换流程说明记录。2026-07-02 后续实机温控测试中，退换后的 `SGM26002` 被 dfield SDK 枚举到并完成 -10 C 降温/稳定性 CSV 记录。
- 有效波长范围：厂商官方 `898.7-1705.1 nm`
- 光谱范围要求：厂商文件标注 `900-1700 nm`
- 光栅：`150 g/mm @1250 nm`
- 波长准确度：厂商校准表允许值 `2 nm`，用户提供的官方图片中最大偏差 `0.66 nm`
- 当前状态：型号级信息保留；具体设备按 S/N 分开记录。2026-06-11 SGM25003 在 FrogTrace GUI 中完成 970 nm 采集；退换后的 `SGM26002` 已于 2026-07-02 实机连接并完成 -10 C 温度记录。`SGM25003` 和 `SGM26002` 的连接/采集/温控结果仍需按 S/N 分开引用。
- 重要限制：`800 nm` 不在 SGM1700 波段内；如果 SHG-FROG 二倍频信号在 800 nm 附近，应使用覆盖 800 nm 的可见光谱仪/Ocean/FX 入口
- FrogTrace 类型：`Zolix_IR`
- 自动选型依据：固定有效范围 `898.7-1705.1 nm`；目标中心波长低于 `898.7 nm` 时不应自动选择这台光谱仪
- 代码依据：`hardware/spectrometer_zolix.py` 默认 `898.7-1705.1 nm` 并线性重建波长轴；`64位/inc/dfield.h` 当前未公开逐像素波长标定数组函数
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\3_硬件信息\卓立汉光SGM1700近红外光谱仪.md`
- 相关实验记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\2_调试记录\20260529_Zolix在800nm插值空白问题.md`

### FrogTrace Ocean 光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：Ocean 光谱仪
- 当前状态：2026-06-01 通过安装驱动后已连接成功，并完成一次采集
- 驱动：已安装；驱动名称、版本、来源路径和具体步骤待补充
- 型号/序列号：待补充
- FrogTrace 类型：`Ocean`
- 波长范围：完整硬件范围待实机读取；FrogTrace 代码通过 SeaBreeze `Spectrometer.wavelengths()` 在连接后取得波长轴
- 历史数据窗口：项目数据里可见约 `339.456-500.339 nm`、`327.381-471.756 nm` 的采集/分析窗口；这些不等于完整硬件范围
- 自动选型依据：已连接时读取 `wavelengths()[0]` 和 `wavelengths()[-1]` 判断目标中心波长是否覆盖；未连接时不要仅凭历史窗口硬选
- 采集参数和数据路径：待补充
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\3_硬件信息\Ocean光谱仪.md`

### FrogTrace 可见光光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：可见光光谱仪
- 当前状态：2026-06-01 通过安装驱动后已连接成功，并完成一次采集
- 驱动：已安装；驱动名称、版本、来源路径和具体步骤待补充
- 型号/序列号：待补充
- FrogTrace 类型：`FX_Vis`
- 波长范围：完整硬件范围待实机读取；FrogTrace 代码通过 Ideaoptics SDK `GetWavelength()` 在连接后取得波长轴
- 历史数据窗口：项目配置里可见约 `533.466-752.979 nm`、`746.0940-852.1881 nm`、以及约 `645.249-1053.366 nm` 内的多个采集/分析窗口；这些不等于完整硬件范围
- 自动选型依据：已连接时读取 `GetWavelength()` 返回数组的首尾值判断目标中心波长是否覆盖；未连接时不要仅凭历史窗口硬选
- 采集参数和数据路径：待补充
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\3_硬件信息\可见光光谱仪.md`

## Known Servers

### 新云数据香港 CN2 云服务器

- 类型/线路：香港 CN2 云服务器
- 服务器地址：`103.56.112.21`
- 登录用户：`root`
- 密码：不记录
- 操作系统：Ubuntu 20.04.1 LTS，内核 `5.4.0-216-generic`，x86_64
- 系统提醒：Ubuntu 20.04 标准支持已在 2025-05-31 结束；后续应规划升级到 22.04/24.04 LTS 或启用 ESM
- CPU：2 vCPU，AMD EPYC 7551P 32-Core Processor
- 内存：约 1.4 GiB
- Swap：2.0 GiB
- 系统盘：`/`，ext4，约 39G，总体使用率约 75%
- 数据盘/部署盘：`/anzhaofeng`，ext4，约 40G，可用约 36G
- Docker：已安装，Docker `28.1.1`，Docker Compose `v2.35.1`
- 防火墙：UFW active；Docker 发布端口可能绕过普通 UFW 规则，公网服务需要额外注意访问控制
- 当前用途：Docker 自托管服务、n8n 自动化、已有 Portainer/openlist/pdf2zh/codexmanager 等服务
- n8n 记录：2026-05-31 已部署到 `/anzhaofeng/n8n`，公网入口暂为 `http://103.56.112.21:5678/`
- 记录来源：用户在 2026-05-31 提供的服务器截图，以及同日 SSH 实测


## 2026-06-11 FrogTrace 光谱仪按 S/N 拆分记录

- Ocean `USB2+U201510`：2026-06-11 已读取完整波长轴，339.45648-1063.004557 nm，2048 像素；GUI/SN 枚举仍待修。
- Ocean `USB4H11541`：GUI 日志/配置中出现，未完成实机确认，波长范围待读取。
- FX_Vis `FX4K261710`：2026-06-11 已读取完整波长轴，299.1692368-1094.6974945 nm，3648 像素；按 S/N 打开待验证。
- Zolix SGM1700 `SGM25003` / `25003`：2026-06-11 实际连接设备，dfield 信息 `Zolix,SGM1700,25003,20251124,V1.1`，完成 970 nm 采集；降温 CSV 未生成。
- Zolix SGM1700 `SGM26002` / `26002`：曾到货并拍摄实物照片，后续发生退换；2026-06-11 未连接确认，不能和 `SGM25003` 的采集结果混用；2026-07-02 退换后设备已实机连接并完成 -10 C 降温与稳定性记录。

## 2026-07-02 Zolix SGM26002 退换流程说明

- 用户提供新照片：Zolix SGM1700，序列号 `26002`，铭牌日期 `2026年06月16日`。
- Obsidian 旧设备卡片 `Zolix_SGM1700_SGM26002.md` 附件照片：同型号同序列号 `26002`，铭牌日期 `2026年05月25日`。
- 判断：该光谱仪已发生退换，因此同一 S/N 的两组铭牌日期按退换/重贴/重新流转说明记录；后续仍需避免把 `SGM26002` 的照片与 `SGM25003` 的实机连接、采集结果混用。

## 2026-07-02 Zolix SGM26002 温控实机测试

- 退换后的 `SGM26002` / `26002` 已被 dfield SDK 枚举到，`--list` 显示 `sn=SGM26002 normalized=SGM26002`。
- `--read-once` 可读取目标温度和实际探测器温度；SDK 温度范围为 `-10 C` 到 `25 C`。
- 本次 CSV 记录显示：从记录第一点 `25.0 C` 算起，约 `15.2 s` 首次达到 `-10 C` 以下；随后约 9 分钟稳定性记录中，实际探测器温度保持在约 `-10.4 C` 到 `-10.1 C`。
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\2_调试记录\20260702_Zolix_SGM26002降温过程实机测试.md`

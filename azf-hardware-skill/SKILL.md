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

## Known Lab Instruments

### FrogTrace Zolix SGM1700 近红外光纤光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：卓立汉光 / Zolix SGM1700 近红外光纤光谱仪
- 光谱仪 S/N：`SGM26002` / `26002`
- 有效波长范围：厂商官方 `898.7-1705.1 nm`
- 光谱范围要求：厂商文件标注 `900-1700 nm`
- 光栅：`150 g/mm @1250 nm`
- 波长准确度：厂商校准表允许值 `2 nm`，用户提供的官方图片中最大偏差 `0.66 nm`
- 当前状态：官方 GUI 能连接；FrogTrace GUI 的光谱仪单独测试链路曾采到 512 点光谱
- 重要限制：`800 nm` 不在 SGM1700 波段内；如果 SHG-FROG 二倍频信号在 800 nm 附近，应使用覆盖 800 nm 的可见光谱仪/Ocean/FX 入口
- FrogTrace 类型：`Zolix_IR`
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\3_硬件信息\卓立汉光SGM1700近红外光谱仪.md`
- 相关实验记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\2_调试记录\20260529_Zolix在800nm插值空白问题.md`

### FrogTrace Ocean 光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：Ocean 光谱仪
- 当前状态：2026-06-01 通过安装驱动后已连接成功，并完成一次采集
- 驱动：已安装；驱动名称、版本、来源路径和具体步骤待补充
- 型号/序列号：待补充
- 采集参数和数据路径：待补充
- 相关 Obsidian 记录：`E:\software\Obsidian\安钊锋的外置大脑\01-Project\20260527_FROG\20260527_FrogTrace\3_硬件信息\Ocean光谱仪.md`

### FrogTrace 可见光光谱仪

- 项目：FrogTrace / 20260527_FROG
- 类型：可见光光谱仪
- 当前状态：2026-06-01 通过安装驱动后已连接成功，并完成一次采集
- 驱动：已安装；驱动名称、版本、来源路径和具体步骤待补充
- 型号/序列号：待补充
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

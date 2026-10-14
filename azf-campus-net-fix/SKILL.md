---
name: azf-campus-net-fix
description: 安钊锋的校园网代理连通性诊断与适配 Skill。用于校园网环境下 Clash Verge 节点大面积超时、新订阅需要处理、优选 IP 失效、或需要判断「封锁发生在哪一层」的场景。它先做环境探测与网络画像，再按预先定义的策略矩阵实施，实施不了时诚实报告而不硬改配置。也可用于其它 Windows 电脑上的 Clash Verge 环境适配。
---

# AZF 校园网代理修复

## 定位

把本 Skill 当作 `scripts/campus-net-fix.py` 的**薄编排层**。确定性内核负责探测、画像、实测、生成脚本；本 Skill 只负责识别意图、选对命令、读退出码、按分层决定是否升级到 AI 诊断。

**不要替内核做它能做的事**：判定哪些入口是 Cloudflare 前置、哪些 IP 可达、哪些节点死了 —— 全部是实测得出，AI 猜测只会更慢更贵更不准。

## 什么时候用

- 校园网下 Clash Verge 节点大面积超时 / 全部 timeout
- 新增了机场订阅，需要让修复逻辑生效
- 之前能用的优选 IP 失效了
- 想知道「这个网络到底封在哪一层」

不适用：需要 portal 认证的网络（内核会判 D 并退出）、非 Clash Verge 客户端、macOS / Linux（v1 仅 Windows）。

## 分层：AI 只在该出现的地方出现

| 层 | 触发 | 动作 | AI 成本 |
|---|---|---|---|
| **L0** | 日常维护 | `run` —— 画像 → 实施 → 验证 | 0 |
| **L1** | `run` 退出码 4，或画像 verdict = X/B/C | 读画像 JSON 做诊断，判断是否出现新封锁形态 | 少量 |
| **L2** | 确认内核假设失效、需要改代码 | 交给 `azf-auto-dev-loop` | 按该 Skill 计费 |

**L0 是默认路径。** 不要因为「AI 更灵活」就把 L0 交给模型 —— 它 80 秒跑完、0 成本、结果可验证。

## 命令与退出码

```powershell
$py = "scripts\campus-net-fix.py"   # 相对本 Skill 目录
python $py doctor                   # 环境体检 + 漂移检测
python $py probe                    # 探测本机 Clash Verge 环境
python $py profile                  # 网络画像（约 80 秒）
python $py apply                    # 按画像实施（写全局扩展脚本）
python $py verify                   # 端到端验证（经用户 Clash 的代理端口）
python $py verify --simulate        # 端到端验证（不经用户 Clash，直接跑修复后的配置）
python $py run                      # profile → apply → verify（L0 入口）
python $py env client.install_dir   # 读已探明事实，避免重复探测
```

**`verify` 有两种模式，必须分清**：

| 模式 | 测什么 | 什么时候用 |
|---|---|---|
| 默认 | 经用户 Clash 的 `mixed-port` 发请求 —— 反映**用户当前实际状态** | 用户已经点过「刷新」之后 |
| `--simulate` | 把修复后的配置交给临时 mihomo 实例跑 —— 反映**修复本身是否有效** | `apply` 之后立刻验证，不必等用户去 GUI 操作 |

**判定顺序很重要**：如果用户还没刷新 Clash Verge，默认 `verify` 测的是**旧配置**，可能通过也可能失败，两种结果都不能说明修复有没有生效。此时应改用 `--simulate`，或先让用户刷新再跑默认模式。

**`apply` 之后 Clash Verge 不会自动重载**（实测：写入全局扩展脚本后运行时配置时间戳不变）。必须提醒用户在订阅卡片上右键 →「刷新」，或重启 Clash Verge。

退出码是**分层决策的接口**，必须读：

| 码 | 含义 | 你该做什么 |
|---|---|---|
| 0 | 成功 | 报告结果 |
| 3 | 环境缺失 / 漂移 | 先 `probe`；若 `probe` 失败，按下面「新机器适配」处理 |
| 4 | 画像不支持当前网络，或验证未通过 | 进 L1：读画像 JSON 诊断，不要反复重试 |
| 5 | 依赖缺失（Python / PyYAML / 内核） | 报告缺什么并给一行安装指引，**不要静默降级** |

加了 `--json` 后所有命令输出结构化数据，适合你自己解析。

## 硬性规则

1. **诚实降级**：画像不匹配任何已知策略（verdict = X/B/C/D）时，只输出报告与建议，**绝不硬改配置**。
2. **先备份再写**：`apply` 会自动把 `Script.js` 备份为 `Script.js.bak`；跨会话的大改动另存到 `E:\software\AI改前备份\<时间戳>_campus-net-fix_修改前备份_<harness>\`。
3. **不要手工编辑 `Script.js`**：它是 `apply` 的产物，下次运行会被覆盖。要改逻辑就改 `override.py` 的模板（那是 L2）。
4. **不要替内核改判**：v1 实测 `dialer-proxy` 对 REALITY 节点无效，但这是**当前 mihomo 版本的行为**，不是永久结论 —— 内核把它当探测项处理，你也不要写死。
5. **订阅 URL 含 token**：不要把 `profiles/*.yaml` 的内容贴进对话或提交到仓库。

## ⚠ 会叠加执行：必须检查订阅级扩展脚本

Clash Verge 的执行顺序是：

```
订阅原文 → 应用设置 → 全局扩展配置 → 全局扩展脚本 → 订阅扩展配置 → 订阅扩展脚本 → 应用设置回写
```

**全局脚本和订阅级脚本是串联的**，后跑的能看到前一个的输出。2026-10-14 踩过一次真实的坑：

- 全局脚本把 29 个节点的入口 IP 换成 Cloudflare **裸 IP**
- 订阅级那个**旧脚本**接着跑，它的判定是「server 不在硬编码的 CF 前置域名表里 → 判为死节点」
- 此时那 29 个节点已经是裸 IP，域名匹配全部失配；其余直连节点本来也不是 CF
- **结果：70 个节点全被判死，从所有代理组剔除，全部流量回退到 DIRECT**

排查这类问题的要点：

1. **症状特征**：节点列表还在（`proxies` 正常），但所有代理组只剩组名和 `DIRECT` —— 这是「有人把节点从组里剔光了」而不是「节点本身没了」。
2. **必查**：`profiles.yaml` 里当前订阅的 `option.script` 指向哪个文件，以及那个文件（`profiles/<uid>.js`）到底是不是空模板。
3. **单一职责**：全局脚本做了某件事，订阅级脚本就不要再做同一件事。`apply` 只写全局脚本；发现订阅级脚本也在改同一批字段时，应先清空它（备份到 `AI改前备份`）。
4. **验证靠实际产物**：不要只测自己的脚本。要读 Clash Verge 生成的 `clash-verge.yaml`，确认代理组的**成员数**合理 —— 自己跑脚本永远复现不出别人的脚本造成的问题。

## 新机器适配（这是 AI 唯一必要的入口）

内核的探测是确定性的，但**环境变了它可能找不到东西**。遇到 `probe` 失败（退出码 5）时按顺序做：

1. **找安装目录**：Clash Verge 的 GUI 进程路径可读（内核进程由 SYSTEM 服务启动，**读不到**，别去猜）。若 GUI 没运行，就在常见位置找 `clash-verge.exe`，或直接问用户。
2. **确认数据目录**：Rev 的数据目录是 `%APPDATA%\io.github.clash-verge-rev.clash-verge-rev`。原版 Clash Verge 用不同的应用 ID —— 产品名都叫 "Clash Verge"，**不要用产品名区分**，用数据目录名。
3. **验证每一项**：路径必须真的存在、内核必须真的能跑 `-v`、`profiles.yaml` 必须真的能解析。验证不过就当没探到。
4. **显式覆盖**：可以用 `probe --install-dir <P> --data-dir <P>` 把定位结果固化进机器档案。
5. **确认能力而非版本**：判断是否支持全局扩展脚本，看 `profiles.yaml` 里有没有 `uid: Script` / `type: script` 条目，**不要按版本号猜**。

机器档案落在 `data/env.<主机名>.json`，按主机名分文件，多机并存不冲突。

## 必须知道的实测事实

这些是本 Skill 存在的理由，也是排查时的先验知识：

- **TUN 模式会污染一切本地测量**。开启后所有 UDP/53 返回同一个 fake-ip，被丢包的 IP 也「连得上」。内核用 `IP_UNICAST_IF` 把所有探测 socket 绑到物理网卡来绕过，并在画像里做**通道自检**。如果 `channel.raw_channel_ok` 是 false，**画像结论一律不可信**，不要拿它做判断。
- **「知名被封 SNI 被拦」≠「节点不可用」**。`www.google.com` 的 SNI 在任何网络（含手机热点）都会被拦，那是国家级过滤。策略相关的判据是**节点自己的 SNI**（`layers.sni_node`）与优选 IP 实测（`cf_preferred.working`）。
- **服务端 doh 端点不能硬编码**。实测同一个校园网里 `223.5.5.5` 被丢包而 `223.6.6.6` 正常，换个网络可能正好相反 —— 候选池实测。
- **`dialer-proxy` 链式代理对 REALITY / Hysteria2 节点无效**（链式机制本身可用，两个 CF 节点互链成功）。所以直连型 REALITY 节点在 IP 被封时救不回来。
- **一元机场这类没有 CF 前置节点的订阅**：换不了入口 IP，只能靠可达性剔组。

## 换校园网之后

`CF_IPS` 是**本网络实测结果**，写在生成的 `Script.js` 里。换网络后必须重跑：

```powershell
python $py run      # profile 会重扫优选 IP，apply 会用新结果重写脚本
```

`CF_FRONTED` 域名名单与启发式兜底是通用的，但**可达 IP 集合一定不通用**。

## 交付物位置

| 内容 | 路径 |
|---|---|
| 内核 | `scripts/campus-net-fix.py` + `scripts/campus_net_fix/` |
| 机器档案 | `data/env.<主机名>.json` |
| 网络画像 | `data/profile.<主机名>.json` |
| 生成的脚本 | `data/Script.latest.js`（实际生效的是 Clash Verge 的 `profiles/Script.js`） |
| 测试 | `python scripts/tests/test_all.py`（37 项）、`node scripts/tests/test_script_js.js` |

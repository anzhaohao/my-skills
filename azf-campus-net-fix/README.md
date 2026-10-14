# AZF 校园网代理修复

## 这个 skill 解决什么问题

校园网对境外 IP 做封锁时，Clash Verge 里的节点会大面积超时。这个 skill 负责：

1. **诊断** —— 判断封锁发生在哪一层（IP 层 / SNI 层 / 协议端口层 / portal 认证），而不是一上来就乱改配置
2. **修复** —— 如果是「IP 层黑名单且机场节点套了 Cloudflare」，就把入口 IP 换成当前网络实测可达的优选 IP
3. **善后** —— 把实测确认连不通的节点从代理组里剔除，避免误选
4. **诚实** —— 判断不了或修不了的时候，给报告和建议，不硬改

## 什么时候应该触发

- 校园网下节点全部 / 大面积超时
- 新加了机场订阅，希望修复逻辑自动生效
- 之前能用的优选 IP 失效了
- 想知道「这个网络到底封在哪一层」

**不适用**：需要 portal 认证的网络、非 Clash Verge 客户端、macOS / Linux（v1 只做 Windows）。

## 怎么用

### 前提

| 要求 | 说明 |
|---|---|
| 操作系统 | **Windows**（v1 只做 Windows；网卡探测与绑定用了 Windows API） |
| 客户端 | **Clash Verge**（Rev 分支，2.x）。原版 Clash Verge 理论上也能跑，但未验证 |
| Python | **Python 3.9+**。PyYAML 已内置在 `scripts/vendor/`，**不需要 pip 安装任何东西** |

### 安装

把整个 `azf-campus-net-fix` 文件夹放到你的 agent 技能目录里，例如：

```
C:\Users\<你>\.claude\skills\azf-campus-net-fix\      # Claude Code
C:\Users\<你>\.codex\skills\azf-campus-net-fix\       # Codex
C:\Users\<你>\.dsh\skills\azf-campus-net-fix\         # DSH
```

没有技能目录也可以直接用命令行，不装技能照样能跑（`scripts\campus-net-fix.py` 是独立的）。

### 首次使用

```powershell
cd <技能目录>\scripts
python campus-net-fix.py probe      # 探测本机 Clash Verge 环境，写出机器档案
python campus-net-fix.py run        # 画像 → 修复 → 验证
```

跑完 `run` 之后，去 Clash Verge 的订阅卡片上**右键 →「刷新」**（或重启 Clash Verge）让配置生效。

### 日常命令

```powershell
python scripts\campus-net-fix.py doctor            # 体检：环境还在不在、有没有漂移
python scripts\campus-net-fix.py run               # 日常：画像 → 修复 → 验证（约 80 秒）
python scripts\campus-net-fix.py verify --simulate # 不改你的 Clash，直接验证修复后的配置能不能用
```

> ⚠️ **Clash Verge 不会自动重载全局扩展脚本**（实测：写入后运行时配置的时间戳不变）。所以：
> - 想看「修复本身有没有用」→ 用 `verify --simulate`（不需要你操作 GUI）
> - 想看「我的 Clash 现在到底通不通」→ 先点刷新，再跑 `verify`

### 两种验证模式的差别

| 命令 | 测的是什么 | 什么时候用 |
|---|---|---|
| `verify` | 经你 Clash 的 7897 端口发请求 —— 反映**你当前的实际状态** | 点过刷新之后 |
| `verify --simulate` | 把修复后的配置交给一个临时 mihomo 实例跑 —— 反映**修复本身是否有效** | `apply` 之后立刻确认 |

没刷新就跑默认 `verify`，测的是**旧配置**，结果通过与否都不能说明修复生效没有。

### 退出码的含义

| 码 | 意思 | 怎么办 |
|---|---|---|
| 0 | 成功 | 完事 |
| 3 | 环境找不到 / 变了 | 先跑 `probe` |
| 4 | 这个网络形态超出内置策略 | 把画像 JSON 交给 AI 诊断 |
| 5 | 缺 Python / PyYAML / 内核 | 按提示装 |

## 三层分工（为什么不是全都交给 AI）

| 层 | 谁来做 | 为什么 |
|---|---|---|
| L0 日常维护 | **确定性内核** | 80 秒、0 模型成本、结果可复现可验证 |
| L1 新封锁形态诊断 | **AI** | 要从证据反推，这是模型擅长的 |
| L2 改内核代码 | **AI + `azf-auto-dev-loop`** | 需要独立评估与自动返工 |

一句话：**机械的活交给脚本，判断的活交给 AI。**

## ⚠ 一个必须知道的坑：扩展脚本会叠加执行

Clash Verge 的执行顺序是：

```
订阅原文 → 应用设置 → 全局扩展配置 → 全局扩展脚本 → 订阅扩展配置 → 订阅扩展脚本 → 应用设置回写
```

**全局脚本和订阅级脚本是串联的** —— 后跑的那个能看到前一个的改动。2026-10-14 踩过一次：

1. 全局脚本把 29 个节点的入口 IP 换成 Cloudflare **裸 IP**
2. 订阅级还留着一个**旧脚本**，它的判定是「server 不在硬编码的域名表里 → 判为死节点」
3. 此时那 29 个节点已经是裸 IP，域名全部失配；其余直连节点本来也不是 CF
4. **70 个节点全被判死并踢出所有代理组 → 所有流量回退到 DIRECT**

**症状特征**：节点列表还在（`proxies` 正常），但代理组里只剩组名和 `DIRECT`。

**怎么排查**：看 `profiles.yaml` 里当前订阅的 `option.script` 指向哪个文件，再看 `profiles/<那个文件>` 是不是空模板。清空前先备份到 `E:\software\AI改前备份\`。

**原则**：全局脚本做了某件事，订阅级脚本就别再做同一件事。

## 当前保存的关键事实

这些都是 2026-10-14 在本校园网实测得到的，排查时可以直接用：

- **TUN 模式会污染测量**：开启后所有 UDP/53 返回同一个 fake-ip（`198.18.0.75`），早就确认被丢包的 IP 也「连得上」。内核用 `IP_UNICAST_IF` 把探测 socket 绑到物理网卡绕过 —— 实测绑定后本地地址从 `198.18.0.1` 变回 `192.168.1.110`，结果才与真实封锁一致。
- **「Google 的 SNI 被拦」不等于「节点不能用」**：那是国家级过滤，手机热点上一样有。真正相关的判据是**节点自己的 SNI**。
- **DNS 服务器可用性因网络而异**：这个校园网里 `223.5.5.5` 和 `8.8.8.8` 被丢包，`119.29.29.29` / `223.6.6.6` / `114.114.114.114` 正常。所以不能硬编码。
- **校园网放行 QUIC (UDP 443)**：实测 QUIC Version Negotiation 能收到回应。
- **WireGuard 端口是否被封不可观测**：没有对端时 WireGuard 对非法握手静默丢弃，所以画像里这一项老实标 `untested`，不编。
- **`dialer-proxy` 链式代理救不了 REALITY 节点**：链式机制本身是好的（两个 CF 节点互链 108ms 成功），但 REALITY 握手会失败；Hysteria2 的 UDP 中继也走不通。所以直连型 REALITY 节点在 IP 被封时没救。
- **一元机场这类没有 CF 前置节点的订阅**：换不了入口 IP，只能靠可达性剔组；实测它 19 个节点当前全部不可达。

## 换电脑 / 换校园网

- **换电脑**：把 `probe` 重跑一遍即可。内核的网卡/进程/路径探测全部走 Python 标准库（ctypes），不依赖 PowerShell，不依赖 psutil，不需要管理员权限。遇到找不到的情况，用 `probe --install-dir <P> --data-dir <P>` 显式指定。
- **换校园网**：必须重跑 `run`。优选 IP 集合是**本网络实测结果**，一定不通用；域名名单和启发式规则才是通用的。

## 目录结构

```
azf-campus-net-fix/
├── SKILL.md                    # 给 agent 的指令
├── README.md                   # 本文件
├── data/                       # 机器档案与画像（按主机名分文件）
│   ├── env.<主机名>.json
│   ├── profile.<主机名>.json
│   └── Script.latest.js        # 生成的脚本副本
└── scripts/
    ├── campus-net-fix.py       # CLI 入口
    ├── campus_net_fix/         # 确定性内核
    │   ├── cli.py              # 命令与退出码
    │   ├── netif.py            # 物理网卡探测 + 绕过 TUN 的绑定
    │   ├── clashverge.py       # Clash Verge 适配层
    │   ├── envprobe.py         # 环境探测 / 漂移体检
    │   ├── profiling.py        # 网络画像（通用性核心）
    │   ├── strategy.py         # 策略矩阵
    │   ├── cfip.py             # Cloudflare 优选 IP 实测
    │   ├── reach.py            # 节点可达性实测
    │   ├── override.py         # 生成并写入扩展脚本
    │   ├── verify.py           # 端到端验证
    │   └── vendor/yaml/        # 内置 PyYAML（免 pip）
    └── tests/
        ├── test_all.py         # 37 项单元 / 集成测试
        └── test_script_js.js   # 跨语言一致性测试（Node）
```

## 自检

```powershell
python scripts\tests\test_all.py           # 37 项，约 1 秒
python scripts\tests\test_all.py --e2e     # 追加经真实代理的端到端验证
node scripts\tests\test_script_js.js       # 需要先 apply --dry-run 和 dump
```

## 最近维护

2026-10-14：新建。把当天一次性排查出的临时脚本沉淀为可移植技能。相比临时版本的关键改进：

- **TUN 污染问题**（最重要）：临时版没有意识到 TUN 会污染测量，导致画像完全失真。现在用 `IP_UNICAST_IF` 绑定物理网卡，并加了通道自检。
- **判定逻辑修正**：临时版可能因「知名被封 SNI 被拦」把可行方案误判为不可行。现在区分「节点 SNI」与「通用知名 SNI」。
- **去 shell 化**：不再调 PowerShell 管理探测进程（改为持有 Popen 句柄），换机器后不依赖 shell。
- **内置 PyYAML**：不需要 pip、不需要联网。
- **策略矩阵化**：从「一种修法」变成「画像 → 策略」的映射，不支持的形态诚实报告。
- **可移植的网卡探测**：ctypes 直调 Windows API，不依赖 psutil。

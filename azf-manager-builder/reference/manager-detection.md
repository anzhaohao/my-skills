# 管理器识别清单（部署/接手项目时先扫这个）

目标：在 1 分钟内判断"这个项目现在是谁在保证进程活着"，避免做重复或没必要的管理器。

## 一、已有真正的管理器 → 只报告，不要另建

| 特征 | 例子（本机实况） |
|---|---|
| `manager\` 目录 / `*Manager.exe` | `20260922-codex-router\local\manager\CodexRouterManager.exe` |
| Windows 服务注册（nssm / WinSW） | `*.xml` 配置 + 注册过的服务名（`sc query`） |
| 进程管理器配置 | `pm2.config.js`、`ecosystem.config.js`、`supervisord.conf`、`Procfile` + 常驻 runner |
| 容器托管且带重启策略 | `20260720-ai-website-cloner-template\docker-compose.yml`（有 `restart: unless-stopped`/`always`） |
| 计划任务里直接指向该项目的常驻进程 | 计划任务动作里含该项目的 exe/脚本，且触发器是登录/开机 |

## 二、"看起来有托管"但不是 → 这就是要建管理器的场景

| 特征 | 例子（本机实况） | 为什么不算 |
|---|---|---|
| 无窗口启动器 `.bat` / `.vbs` | `20260828-ctxedkbh-paper-workbench\启动桌面版-无控制台.bat`、`web\autostart.vbs` | 只启动一次；进程崩了、卡死了都不会被拉起；无端口健康检查；无状态视图 |
| 启动脚本 `.ps1` | `20260812-DeepSight\scripts\start.ps1`、`20260825-backend-model-effort-probe\scripts\start-probe.ps1` | 同上，人工重启 |
| 计划任务跑一次性/周任务 | `20260715-ai-paper-weekly\scripts\run-scheduled.ps1` | 不是常驻进程守护 |
| 项目内的看门狗模块 | `20260820-hana-dsh++\features\dsh-watchdog\manager.js` | 只管它自己插件内的任务，不管本机常驻进程 |

## 三、绝不算作管理器的噪音（要主动排除）

- `.venv\Scripts\activate.bat`、`deactivate.bat`、`pydoc.bat`（虚拟环境自带）
- `.vscode\launch.json`（编辑器调试配置）
- `node_modules\**`（依赖自带脚本，如 `why-is-node-running.ps1`）
- 一次性 `run_*.ps1` / `test_*.ps1` / `build_*.bat` 辅助脚本
- `data\plugins\*.yml`（插件市场清单）

## 四、扫描命令（浅层 2 级足够，避免扫进 node_modules）

```powershell
$root = 'D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab'
$patterns = @('*Manager*.exe','*manager*.ps1','*manager*','*start*.ps1','*run*.ps1','*launch*',
              'pm2*','ecosystem.config*','docker-compose*','Procfile','*.vbs','supervisord*','*service*.xml','*.bat')
Get-ChildItem $root -Directory | ForEach-Object {
  $hits = Get-ChildItem $_.FullName -Recurse -Depth 2 -File -ErrorAction SilentlyContinue |
    Where-Object { $n = $_.Name; $patterns | Where-Object { $n -like $_ } }
  if ($hits) { "--- $($_.Name) ---"; $hits | ForEach-Object { '    ' + $_.FullName.Replace($_.FullName.Split('\')[-1],'') } }
}
```

补充检查（有则说明已被系统级托管）：

```powershell
Get-ScheduledTask | Where-Object { $_.Actions.Execute -match '<项目关键字>' } |
  Select-Object TaskName, State
sc.exe query type= service state= all | Select-String '<项目关键字>'
```

## 五、判定输出模板（问用户前先给出这段）

```
扫描结果：<已托管 / 只有启动器 / 没有任何托管>
长驻进程：<有，哪些：exe/脚本 + 端口> | <无>
建议：<无需管理器，继续> | <建议建一个 .exe 管理器，是否现在做？>
会生成：<项目>\manager\（Manager.exe + manager.json + build 脚本 + README）
回滚：现有启动脚本不动；旧计划任务停用但保留；<具体命令>
```

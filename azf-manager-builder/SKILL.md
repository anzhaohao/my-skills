---
name: azf-manager-builder
description: >-
  Build or maintain a zero-dependency Windows single-file tray manager
  (.exe supervisor) for An Zhaofeng's local projects that only ship
  command-line start scripts. Use when deploying, taking over, or repairing a
  project that has long-running processes (gateway, daemon, local API, watcher,
  tunnel, dev server) but no process manager; when he asks for 开机自启 /
  别老手动重启 / 托管 / 守护 / 管理器 / 托盘; or when the deployment check in
  `azf-personal-habits` reports a long-running project without a manager. NOT
  for one-shot scripts, pure CLI tools, Docker-managed stacks, Windows service
  (SCM) requirements, or projects that already work under a real manager.
---

# AZF Manager Builder

Turn "only starts from a command line" into "always running, self-healing, tray-controlled".

## What gets produced

| Artifact | Purpose |
|---|---|
| `<Project>\manager\<Name>Manager.exe` | single-file, windowless, tray supervisor (built with the in-box .NET Framework `csc`, no SDK / no NuGet) |
| `manager.json` (or `manager.ini`) | declares the child processes, their ports, env file, guards, tray URL |
| `build-manager.ps1` | rebuild the exe from source |
| `make-icon.py` | optional: PNG → multi-size `.ico` for the tray |
| `README.md` inside `manager\` | how to run, tray menu, CLI, rollback |
| Scheduled task `<Name>Manager` | logon-triggered autostart (registered only after the smoke test passes) |

Capabilities that define "the same as CodexRouterManager": N supervised children, port-level health checks every 5 s, restart with backoff that resets once healthy, orphan port reclamation at startup, single-instance mutex, status JSON, rotating log, tray states/menu, script-friendly CLI (`--status`, `--stop`, `--restart <child|all>`, `--headless`, `--fix-*`), pluggable self-healing guards.

## Step 0 — Detect before anything else

Run the checklist in `reference/manager-detection.md` against the project. It separates:

- **already managed** — `manager\` dir or `*Manager.exe`, nssm/winsw config, pm2/`ecosystem.config.js`, `supervisord.conf`, `docker-compose.yml` with a restart policy, a scheduled task pointing at the project → do nothing except report it;
- **looks managed but is not** — a `.bat`/`.ps1`/`.vbs` launcher or an "无控制台" shortcut that merely starts the process once, with no health check and no restart → this is the target case;
- **noise, never count as a manager** — `.venv\Scripts\activate.bat`, `.vscode\launch.json`, `node_modules\**`, one-shot `run_*.ps1` / `test_*.ps1` helpers.

Also decide whether the project actually has long-running processes. If it does not (one-shot script, CLI tool, static site), say so in one line and stop — no manager is needed.

## Step 1 — Ask first (mandatory)

Never build a manager unasked, and never touch the supervised project's own source. Present in one short block:

1. what was found (managed / launcher-only / nothing),
2. which processes would be supervised and on which ports,
3. what would be created (the table above) and where,
4. the rollback path (the existing start scripts stay untouched; the old scheduled tasks stay installed but disabled).

Then wait for An Zhaofeng's confirmation.

## Step 2 — Scaffold: copy-adapt the existing manager (one exe per project)

Chosen shape (2026-09-24, An Zhaofeng's decision): **one manager exe per project** — identical tray UX everywhere, but each project keeps its own process and fails independently. Do not build a shared/global manager for several projects, and do not build a template framework: copy the working implementation and adapt it.

Baseline to copy (reference implementation):
`D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260922-codex-router\local\manager\`
(`Manager.cs`, `build-manager.ps1`, `make-icon.py`, `README.md`, and `icon.png` / `icon.ico` if wanted).

Then change every project-specific value:

| Where | What to change |
|---|---|
| `Config.Load` defaults | child exe paths (python/node), script paths, `.env` path, log dir, status file |
| `Config` ports | router / face / gateway ports → this project's ports |
| `Supervisor` constructor | the children: name, exe, args, ports (one or more), plus their env |
| Project-specific guards | delete the tunnel-bearer / catalog guards, or replace them with this project's own `file-prefix` / `run-script` guards |
| Tray identity | window/tooltip title and `icon.png` — give every project a **distinct** icon, otherwise the tray icons are indistinguishable |
| **Unique identity** | exe name (`<X>Manager.exe`), singleton mutex name, scheduled task name, status file path, log file path — two managers that share a mutex or task name will fight each other |
| `build-manager.ps1` | output exe name; keep `/target:winexe` + the in-box .NET Framework `csc` compile |

Rules while scaffolding:

- Secrets stay in `.env` or environment variables; never in the manager config, never in logs.
- Child processes run with `CreateNoWindow`; the manager itself is compiled `/target:winexe`.
- Guards are declarative and idempotent: `file-prefix` (keep a file in a required shape) and `run-script` (run a maintenance script after a child start and/or every N seconds). A guard must only act when the content actually differs.
- `.ps1` files written for this stack must be **UTF-8 with BOM** (see hardening rule 1).

## Step 3 — Verify with real drills (mandatory evidence)

Do not report success from a green process list. Collect:

1. `--status` output and `manager-status.json` with every child `running=true` and `portsUp=true`;
2. kill one child process → assert the ports come back within ~20 s (record the elapsed time);
3. assert `MainWindowHandle = 0` (proves there is no console window);
4. exercise the CLI: `--restart <child>`, `--fix-*` (if guards exist);
5. the project's own functional regression (its API/model/page answers as before);
6. tray state and the log file tail.

Then say what was verified, with numbers.

## Step 4 — Hand off

- Add the manager + rollback commands to the project's `README` / `PROGRESS.md`.
- Register the scheduled task only after step 3 passes; keep the previous start mechanism installed but disabled.
- Tell An Zhaofeng: tray menu entries, the CLI contract, where the status file and logs live, and the exact rollback commands.
- Remind about a Git commit for the project.

## Hardening rules (all mandatory)

Full trap-by-trap detail: `reference/hardening-checklist.md`.

1. `.ps1` must be UTF-8 **with BOM**; editing tools silently strip it and PowerShell 5.1 then mis-decodes Chinese into syntax errors.
2. The restart backoff counter must reset to zero once a child is alive **and** its ports are up, otherwise a few restarts push every later restart into the 300 s tier.
3. Health = port listening, not process alive. A hung child that still holds no port must be restarted.
4. Reclaim ports at startup and hold a single-instance mutex.
5. Prove "no window" with `MainWindowHandle = 0` instead of assuming it.
6. Status JSON + rotating log + tray colour states + balloon on state transitions.
7. Scheduled task: logon trigger + delay, restart on failure, no execution time limit; keep the old tasks disabled-but-present for rollback.
8. Guards must be idempotent and must not fight other writers (act only when the content differs; never rewrite unconditionally on a timer).
9. Fix the CLI contract and make project scripts call it (`--restart <child>`) instead of manipulating scheduled tasks.
10. When killing processes by command-line pattern, exclude the current PID — a self-match kills the running command itself.
11. Secrets live in `.env`/environment only; scrub them before logging.
12. After any change, re-run the kill drill and write the evidence into `PROGRESS.md`.

## Do not

- Do not build one global manager for several projects: the chosen shape is **one exe per project** (per-project isolation, identical tray UX), and two projects must never share a mutex, task name, status file or exe name.
- Do not build a generic template / scaffolder framework: copy the reference implementation and adapt the values.
- Do not install this as a Windows service (session 0 has no desktop: no tray, no computer-use tools).
- Do not modify the supervised project's source to make supervision easier.
- Do not build a manager when Docker, a real service manager, or an existing manager already owns the lifecycle.
- Do not leave the tray app as the only way to start the stack: scripts must be able to use the CLI.

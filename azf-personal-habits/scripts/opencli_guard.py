#!/usr/bin/env python3
"""Fail-fast readiness and bounded-output wrapper for OpenCLI on Windows."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


EXIT_OPENCLI_MISSING = 2
EXIT_EDGE_MISSING = 3
EXIT_BRIDGE_NOT_READY = 4
EXIT_OPENCLI_FAILED = 5
EXIT_OPENCLI_TIMEOUT = 6

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
STARTF_USESHOWWINDOW = getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
SW_SHOWMINIMIZED = 2


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def decode_browser_output(data: bytes) -> tuple[str, str]:
    candidates: list[tuple[int, int, str, str]] = []
    for preference, encoding in enumerate(("utf-8", "gb18030")):
        text = data.decode(encoding, errors="replace")
        replacement_count = text.count("\ufffd")
        candidates.append((replacement_count, preference, encoding, text))
    _, _, encoding, text = min(candidates, key=lambda item: (item[0], item[1]))
    return text, encoding


def find_opencli_base() -> list[str]:
    appdata = Path(os.environ.get("APPDATA", ""))
    npm_root = appdata / "npm"
    main_js = npm_root / "node_modules" / "@jackwener" / "opencli" / "dist" / "src" / "main.js"
    node = npm_root / "node.exe"
    if not node.exists():
        node_path = shutil.which("node.exe") or shutil.which("node")
        node = Path(node_path) if node_path else node
    if main_js.exists() and node.exists():
        return [str(node), str(main_js)]

    launcher = shutil.which("opencli.cmd") or shutil.which("opencli")
    if launcher and not launcher.lower().endswith((".cmd", ".bat", ".ps1")):
        return [launcher]
    raise FileNotFoundError("OpenCLI executable or Node entrypoint was not found")


def run_opencli(args: list[str], timeout: float = 12.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*find_opencli_base(), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        creationflags=CREATE_NO_WINDOW,
    )


def parse_status(output: str) -> dict[str, Any]:
    daemon_match = re.search(r"^Daemon:\s+running(?:\s+\(PID\s+(\d+)\))?", output, re.MULTILINE)
    extension_match = re.search(
        r"^Extension:\s+connected(?:\s+\(v([^\)]+)\))?", output, re.MULTILINE
    )
    daemon_version = re.search(r"^Version:\s+v?([^\s]+)", output, re.MULTILINE)
    port_match = re.search(r"^Port:\s+(\d+)", output, re.MULTILINE)
    return {
        "daemon_running": bool(daemon_match),
        "daemon_pid": int(daemon_match.group(1)) if daemon_match and daemon_match.group(1) else None,
        "daemon_version": daemon_version.group(1) if daemon_version else None,
        "connected": bool(extension_match),
        "extension_version": extension_match.group(1) if extension_match else None,
        "port": int(port_match.group(1)) if port_match else None,
    }


def get_status() -> tuple[dict[str, Any], str]:
    result = run_opencli(["daemon", "status"], timeout=10.0)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return parse_status(output), output


def find_edge() -> Path | None:
    candidates: list[Path] = []
    for env_name in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        root = os.environ.get(env_name)
        if root:
            candidates.append(Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe")

    if sys.platform == "win32":
        try:
            import winreg

            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for key_name in (
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
                ):
                    try:
                        with winreg.OpenKey(hive, key_name) as key:
                            value, _ = winreg.QueryValueEx(key, None)
                            candidates.append(Path(value))
                    except OSError:
                        pass
        except ImportError:
            pass

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    edge_path = shutil.which("msedge.exe") or shutil.which("msedge")
    return Path(edge_path) if edge_path else None


def edge_is_running() -> bool:
    if sys.platform != "win32":
        return False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq msedge.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            timeout=8.0,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )
        return b"msedge.exe" in result.stdout.lower()
    except (OSError, subprocess.TimeoutExpired):
        return False


def start_edge(edge: Path, profile: str) -> None:
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_SHOWMINIMIZED
    subprocess.Popen(
        [
            str(edge),
            f"--profile-directory={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--start-minimized",
            "about:blank",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )


def wait_for_connection(timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_status: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            last_status, _ = get_status()
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            last_status = {}
        if last_status.get("connected"):
            return last_status
        time.sleep(0.75)
    return last_status


def ensure_ready(profile: str, timeout: float, restart_timeout: float, launch_edge: bool) -> tuple[int, dict[str, Any]]:
    started = time.monotonic()
    events: list[str] = []
    edge_started = False
    try:
        status, _ = get_status()
    except FileNotFoundError as error:
        return EXIT_OPENCLI_MISSING, {"ok": False, "connected": False, "error": str(error), "events": events}
    except (subprocess.TimeoutExpired, OSError) as error:
        status = {}
        events.append(f"status_error:{type(error).__name__}")

    if status.get("connected"):
        events.append("bridge_already_connected")
        return 0, {
            "ok": True,
            **status,
            "edge_started": False,
            "events": events,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }

    if not status.get("daemon_running"):
        events.append("daemon_restart_requested")
        try:
            run_opencli(["daemon", "restart"], timeout=15.0)
        except (subprocess.TimeoutExpired, OSError):
            events.append("daemon_restart_failed")

    if launch_edge and not edge_is_running():
        edge = find_edge()
        if not edge:
            return EXIT_EDGE_MISSING, {
                "ok": False,
                "connected": False,
                "error": "Microsoft Edge executable was not found",
                "events": events,
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            }
        start_edge(edge, profile)
        edge_started = True
        events.append("edge_started_minimized")
    elif edge_is_running():
        events.append("edge_already_running")
    else:
        events.append("edge_launch_disabled")

    status = wait_for_connection(timeout)
    if not status.get("connected"):
        events.append("daemon_restart_after_disconnect")
        try:
            run_opencli(["daemon", "restart"], timeout=15.0)
        except (subprocess.TimeoutExpired, OSError):
            events.append("daemon_restart_failed")
        status = wait_for_connection(restart_timeout)

    ok = bool(status.get("connected"))
    if ok:
        events.append("bridge_connected")
    else:
        events.append("bridge_not_ready_fail_fast")
    return (0 if ok else EXIT_BRIDGE_NOT_READY), {
        "ok": ok,
        **status,
        "edge_started": edge_started,
        "events": events,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
    }


def trim_value(value: Any, max_items: int, max_string_chars: int, budget: list[int], depth: int = 0) -> Any:
    if budget[0] <= 0:
        return "[output budget exhausted]"
    if depth > 8:
        return "[nested content omitted]"
    if isinstance(value, str):
        take = min(len(value), max_string_chars, max(0, budget[0]))
        budget[0] -= take
        suffix = "…[truncated]" if take < len(value) else ""
        return value[:take] + suffix
    if isinstance(value, list):
        kept = [trim_value(item, max_items, max_string_chars, budget, depth + 1) for item in value[:max_items]]
        if len(value) > max_items:
            kept.append(f"[{len(value) - max_items} more items omitted]")
        return kept
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 64 or budget[0] <= 0:
                output["_truncated"] = "additional fields omitted"
                break
            budget[0] -= min(len(str(key)) + 4, budget[0])
            output[str(key)] = trim_value(item, max_items, max_string_chars, budget, depth + 1)
        return output
    return value


def run_bounded(args: argparse.Namespace) -> int:
    code, readiness = ensure_ready(
        profile=args.profile,
        timeout=args.ready_timeout,
        restart_timeout=args.restart_timeout,
        launch_edge=not args.no_launch_edge,
    )
    if code != 0:
        print(json.dumps({"ok": False, "stage": "preflight", "preflight": readiness}, ensure_ascii=False))
        return code

    opencli_args = list(args.opencli_args)
    if opencli_args and opencli_args[0] == "--":
        opencli_args.pop(0)
    if not opencli_args:
        print(json.dumps({"ok": False, "stage": "arguments", "error": "No OpenCLI arguments supplied"}, ensure_ascii=False))
        return EXIT_OPENCLI_FAILED

    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            [*find_opencli_base(), *opencli_args],
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            creationflags=CREATE_NO_WINDOW,
        )
        try:
            process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3.0)

        stdout_size = stdout_file.tell()
        stderr_size = stderr_file.tell()
        stdout_file.seek(0)
        stderr_file.seek(0)
        capture_limit = max(args.max_output_chars * 6, 65536)
        stdout_bytes = stdout_file.read(capture_limit + 1)
        stderr_bytes = stderr_file.read(min(capture_limit, 65536) + 1)

    stdout_text, stdout_encoding = decode_browser_output(stdout_bytes)
    stderr_text, stderr_encoding = decode_browser_output(stderr_bytes)
    source_was_capped = stdout_size > capture_limit
    parsed: Any
    parsed_json = False
    if not source_was_capped:
        try:
            parsed = json.loads(stdout_text)
            parsed_json = True
        except json.JSONDecodeError:
            parsed = stdout_text
    else:
        parsed = stdout_text

    budget = [max(1000, args.max_output_chars - 2500)]
    cleaned = trim_value(parsed, args.max_items, args.max_string_chars, budget)
    payload = {
        "ok": (not timed_out and process.returncode == 0),
        "stage": "opencli",
        "preflight": readiness,
        "command": opencli_args,
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stdout_bytes": stdout_size,
        "stderr_bytes": stderr_size,
        "stdout_encoding": stdout_encoding,
        "stderr_encoding": stderr_encoding,
        "source_was_capped": source_was_capped,
        "parsed_json": parsed_json,
        "data": cleaned,
        "stderr": stderr_text[:2000] + ("…[truncated]" if len(stderr_text) > 2000 else ""),
    }
    rendered = json.dumps(payload, ensure_ascii=False)
    if len(rendered) > args.max_output_chars:
        preview_chars = max(500, args.max_output_chars // 3)
        payload = {
            "ok": payload["ok"],
            "stage": "opencli",
            "preflight": readiness,
            "command": opencli_args,
            "exit_code": process.returncode,
            "timed_out": timed_out,
            "elapsed_ms": payload["elapsed_ms"],
            "stdout_bytes": stdout_size,
            "stderr_bytes": stderr_size,
            "stdout_encoding": stdout_encoding,
            "source_was_capped": source_was_capped,
            "guard_truncated": True,
            "data_preview": stdout_text[:preview_chars] + "…[guard output truncated]",
        }
        rendered = json.dumps(payload, ensure_ascii=False)
    print(rendered)
    if timed_out:
        return EXIT_OPENCLI_TIMEOUT
    return 0 if process.returncode == 0 else EXIT_OPENCLI_FAILED


def add_preflight_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", default="Default", help="Edge profile directory name")
    parser.add_argument("--ready-timeout", type=float, default=12.0, help="Seconds to wait after Edge is available")
    parser.add_argument("--restart-timeout", type=float, default=8.0, help="Seconds to wait after one daemon restart")
    parser.add_argument("--no-launch-edge", action="store_true", help="Fail without starting Edge")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="P0 readiness and bounded-output guard for OpenCLI browser commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Ensure Edge and Browser Bridge are connected")
    add_preflight_options(preflight)
    preflight.add_argument("--json", action="store_true", help="Emit structured JSON")

    run_parser = subparsers.add_parser("run", help="Run an OpenCLI command after preflight with bounded output")
    add_preflight_options(run_parser)
    run_parser.add_argument("--timeout", type=float, default=60.0, help="OpenCLI command timeout in seconds")
    run_parser.add_argument("--max-output-chars", type=int, default=12000)
    run_parser.add_argument("--max-items", type=int, default=5)
    run_parser.add_argument("--max-string-chars", type=int, default=1600)
    run_parser.add_argument("opencli_args", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args()
    if args.command == "run":
        return run_bounded(args)

    code, result = ensure_ready(
        profile=args.profile,
        timeout=args.ready_timeout,
        restart_timeout=args.restart_timeout,
        launch_edge=not args.no_launch_edge,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result.get("connected"):
            print(
                "OpenCLI ready: Edge/Browser Bridge connected"
                f" (extension v{result.get('extension_version') or 'unknown'})"
            )
        else:
            print(f"OpenCLI not ready: {result.get('error') or 'Browser Bridge did not connect'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

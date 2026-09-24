#!/usr/bin/env python3
"""Cell-lct local configuration page server (zero dependencies).

Serves a small local web page on 127.0.0.1 that reads and writes
~/.cell-lct/config.json, shows secret status, stores the Xiaomiao API key
with Windows DPAPI (never plaintext on disk), and can run diagnostics.

Run:
    python config-ui/server.py [--port 8765] [--open-browser] [--home <dir>]

The launcher (open-config.cmd) starts this and opens the browser for you.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import webbrowser
import ctypes
import ctypes.wintypes as wt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Keep in sync with runtime/powershell/resolve-config.ps1 defaults.
DEFAULTS = {
    "image_edit_provider": "codex-agent",
    "vectorize_provider": "xiaomiao",
    "xiaomiao_base_url": "https://xiaomiao-ai.com",
    "output_root": "",
    "credit_gate_enabled": True,
    "setup_run_doctor": True,
    "skill_install": {"preferred_destination": ""},
}

IMAGE_EDIT_PROVIDERS = ["codex-agent", "dsh-image-gen", "openai-compatible", "custom"]
VECTORIZE_PROVIDERS = ["xiaomiao"]

INDEX_HTML = (Path(__file__).resolve().parent / "index.html").read_text(encoding="utf-8")

# --------------------------------------------------------------------------- DPAPI

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

def _blob(data: bytes) -> DATA_BLOB:
    buf = ctypes.create_string_buffer(data, len(data))
    return DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))

def _from_blob(blob: DATA_BLOB) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        if blob.pbData:
            ctypes.windll.kernel32.LocalFree(blob.pbData)

def dpapi_encrypt(plain: bytes) -> bytes:
    blob_in = _blob(plain)
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)  # CRYPTPROTECT_UI_FORBIDDEN
    ):
        raise RuntimeError("CryptProtectData failed")
    return _from_blob(blob_out)

def dpapi_decrypt(cipher: bytes) -> bytes:
    blob_in = _blob(cipher)
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0x01, ctypes.byref(blob_out)
    ):
        raise RuntimeError("CryptUnprotectData failed")
    return _from_blob(blob_out)

# --------------------------------------------------------------------------- config

class ConfigStore:
    def __init__(self, home: Path):
        self.home = home
        self.config_path = home / "config.json"
        self.secret_path = home / "secrets" / "xiaomiao-api-key.dpapi"
        self.legacy_secret_path = Path(os.environ.get("USERPROFILE", "")) / ".codex" / "secrets" / "xiaomiao-api-key.dpapi"

    def read(self) -> dict:
        if not self.config_path.is_file():
            return json.loads(json.dumps(DEFAULTS))
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return json.loads(json.dumps(DEFAULTS))
        merged = json.loads(json.dumps(DEFAULTS))
        for key in merged:
            if key in data and data[key] is not None:
                merged[key] = data[key]
        if isinstance(merged.get("skill_install"), dict):
            si = merged["skill_install"]
            si["preferred_destination"] = str(si.get("preferred_destination", ""))
        return merged

    def write(self, payload: dict) -> None:
        allowed = set(DEFAULTS)
        clean = {}
        for key, value in payload.items():
            if key not in allowed or value is None:
                continue
            if key == "skill_install":
                if isinstance(value, dict) and isinstance(value.get("preferred_destination"), str):
                    clean[key] = {"preferred_destination": value["preferred_destination"]}
                continue
            if key in ("credit_gate_enabled", "setup_run_doctor"):
                clean[key] = bool(value)
                continue
            clean[key] = value
        self.home.mkdir(parents=True, exist_ok=True)
        tmp = self.config_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.config_path)

    def _secret_path(self, name: str) -> Path:
        return self.home / "secrets" / f"{name}-api-key.dpapi"

    def secret_status(self, name: str = "xiaomiao") -> dict:
        path = self._secret_path(name)
        if name == "xiaomiao" and not path.is_file() and self.legacy_secret_path.is_file():
            return {"name": name, "configured": True, "source": "legacy-codex", "path": str(self.legacy_secret_path)}
        if path.is_file():
            return {"name": name, "configured": True, "source": "default", "path": str(path)}
        return {"name": name, "configured": False, "source": "missing", "path": str(path)}

    def store_secret(self, key: str, name: str = "xiaomiao") -> dict:
        import re
        if name == "xiaomiao":
            if not re.fullmatch(r"img_live_[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", key):
                raise ValueError("key format does not match the Xiaomiao API-key pattern")
        else:
            if len(key.strip()) < 8 or " " in key.strip():
                raise ValueError("key must be at least 8 characters without spaces")
        path = self._secret_path(name)
        (self.home / "secrets").mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".dpapi.tmp")
        tmp.write_bytes(dpapi_encrypt(key.strip().encode("utf-8")))
        tmp.replace(path)
        try:
            identity = subprocess.run(
                ["icacls.exe", str(path), "/inheritance:r", "/grant:r", f"{os.environ.get('USERNAME', '')}:(F)"],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            identity = None
        return {"name": name, "configured": True, "source": "default", "path": str(path), "icacls_ok": bool(identity and identity.returncode == 0)}

    def remove_secret(self, name: str = "xiaomiao") -> dict:
        path = self._secret_path(name)
        if path.is_file():
            path.unlink()
        return self.secret_status(name)

# --------------------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    store: ConfigStore = None  # type: ignore[assignment]

    def log_message(self, fmt, *args):  # keep console quiet
        pass

    def _send(self, code: int, body: bytes, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, code: int = 200) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _secret_name(self, body: dict) -> str:
        name = str(body.get("name", "xiaomiao"))
        if name not in ("xiaomiao", "openai-compatible"):
            raise ValueError("unknown secret name")
        return name

    def do_GET(self) -> None:
        from urllib.parse import urlparse, parse_qs
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path == "/api/config":
            self._json({"ok": True, "config": self.store.read(), "home": str(self.store.home)})
            return
        if self.path.startswith("/api/secret/status"):
            query = parse_qs(urlparse(self.path).query)
            name = str(query.get("name", ["xiaomiao"])[0])
            self._json({"ok": True, **self.store.secret_status(name)})
            return
        if self.path == "/api/doctor":
            self._json({"ok": True, "doctor": self._run_doctor()})
            return
        self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self) -> None:
        body = self._read_body()
        if self.path == "/api/config":
            try:
                self.store.write(body.get("config", {}))
                self._json({"ok": True, "config": self.store.read()})
            except OSError as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return
        if self.path == "/api/secret":
            try:
                result = self.store.store_secret(str(body.get("key", "")), self._secret_name(body))
                self._json({"ok": True, **result})
            except ValueError as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            except (OSError, RuntimeError) as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return
        if self.path == "/api/secret/remove":
            try:
                self._json({"ok": True, **self.store.remove_secret(self._secret_name(body))})
            except ValueError as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        self._json({"ok": False, "error": "not found"}, 404)

    def _run_doctor(self) -> dict:
        powershell = os.environ.get("PSModulePath") and "powershell.exe" or "powershell.exe"
        doctor = Path(__file__).resolve().parent.parent / "installers" / "doctor.ps1"
        if not doctor.is_file():
            return {"error": f"doctor.ps1 not found at {doctor}"}
        try:
            proc = subprocess.run(
                [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(doctor), "-Json", "-SkipIllustrator", "-SkipApi"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
            )
            try:
                return json.loads(proc.stdout.strip())
            except json.JSONDecodeError:
                return {"error": proc.stdout.strip() or proc.stderr.strip(), "exit": proc.returncode}
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Cell-lct config page server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--home", default="", help="Override the Cell-lct home (default ~/.cell-lct)")
    args = parser.parse_args()

    home = Path(args.home).expanduser() if args.home else Path.home() / ".cell-lct"
    Handler.store = ConfigStore(home)

    server = None
    port = args.port
    for _ in range(20):
        try:
            server = ThreadingHTTPServer((args.host, port), Handler)
            break
        except OSError:
            port += 1
    if server is None:
        print(f"CONFIG_UI_ERROR|no free port from {args.port}", file=sys.stderr, flush=True)
        return 1

    url = f"http://{args.host}:{port}/"
    print(f"CONFIG_UI_OK|url={url}|home={home}", flush=True)
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

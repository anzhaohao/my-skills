#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create and publish group-meeting PPT folders under the two-root model.

WORK      = <PPT_MASTER>\\output\\<YYYYMMDD>-<topic>
DELIVERY  = <TARGET_ROOT>\\<YYYYMMDD>-<topic>

Everything generated while making the deck stays in WORK.  DELIVERY is for the
final .pptx only; `check` fails as soon as anything else appears there.

Usage:
    python workspace.py prepare --date 20261030 --topic "FROG啁啾不稳定性" `
        --target "D:\\Postgraduate_JilinUniversity\\03_Sundries\\00_组会"
    python workspace.py prepare ... --confirm
    python workspace.py publish --work "<WORK>" --pptx "<WORK>\\exports\\xxx_final.pptx"
    python workspace.py check --delivery "<DELIVERY>" --expect-one
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

PPT_MASTER = Path(r"D:\Postgraduate_JilinUniversity\03_Sundries\02_DevLab\20260429-ppt-master")
DEFAULT_WORK_ROOT = PPT_MASTER / "output"

WORK_SUBDIRS = ("svg_output", "images", "validation", "exports", "sources", "scripts")
ILLEGAL_CHARS = set('\\/:*?"<>|')
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def die(message: str) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def validate_date(value: str) -> str:
    if len(value) != 8 or not value.isdigit():
        die("--date must be exactly 8 digits, e.g. 20261030")
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        die(f"--date is not a real calendar date: {value}")
    return value


def validate_topic(value: str) -> str:
    topic = value.strip()
    if not topic:
        die("--topic must not be empty")
    bad = sorted({ch for ch in topic if ch in ILLEGAL_CHARS or ord(ch) < 32})
    if bad:
        die(f"--topic contains illegal characters: {''.join(bad)!r}")
    if topic in {".", ".."} or topic.rstrip(" .") != topic:
        die("--topic must not be '.'/'..' or end with a space/dot")
    if topic.split(".")[0].upper() in RESERVED_NAMES:
        die(f"--topic is a reserved Windows name: {topic}")
    if len(topic) > 120:
        die("--topic is too long (max 120 characters)")
    return topic


def resolve_existing_dir(value: str, label: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        die(f"{label} must be an absolute path: {value}")
    path = path.resolve()
    if not path.is_dir():
        die(f"{label} does not exist or is not a directory: {path}")
    return path


def project_name(date: str, topic: str) -> str:
    return f"{date}-{topic}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_office_lock(entry: Path) -> bool:
    """PowerPoint/WPS create `~$name.pptx` while the deck is open."""
    return entry.is_file() and entry.name.startswith("~$")


def non_pptx_entries(directory: Path) -> list[str]:
    return sorted(
        entry.name
        for entry in directory.iterdir()
        if not (entry.is_file() and entry.suffix.lower() == ".pptx") and not is_office_lock(entry)
    )


def read_meta(work: Path) -> dict:
    meta_path = work / "project.json"
    if not meta_path.is_file():
        die(f"missing {meta_path}; run `prepare --confirm` first")
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {meta_path}: {exc}")


def cmd_prepare(args: argparse.Namespace) -> int:
    date = validate_date(args.date)
    topic = validate_topic(args.topic)
    name = project_name(date, topic)

    target_root = resolve_existing_dir(args.target, "--target")
    work_root = Path(args.work_root).expanduser()
    if not work_root.is_absolute():
        die(f"--work-root must be an absolute path: {args.work_root}")
    work_root = work_root.resolve()

    work = work_root / name
    delivery = target_root / name

    print(f"WORK     = {work}")
    print(f"DELIVERY = {delivery}")

    if not args.confirm:
        print("dry run: nothing created. Re-run with --confirm after the user approves.")
        return 0

    for sub in WORK_SUBDIRS:
        (work / sub).mkdir(parents=True, exist_ok=True)
    delivery.mkdir(parents=True, exist_ok=True)

    meta_path = work / "project.json"
    expected = {
        "date": date,
        "topic": topic,
        "work_dir": str(work),
        "delivery_dir": str(delivery),
        "delivery_folder": name,
    }
    if meta_path.exists():
        old = read_meta(work)
        old_delivery = old.get("delivery_dir")
        if old_delivery and Path(old_delivery).resolve() != delivery.resolve():
            die(f"existing project.json points to a different delivery dir: {old_delivery}")
        print(f"reused: {meta_path}")
    else:
        payload = dict(expected, created=datetime.now().astimezone().isoformat(timespec="seconds"))
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"created: {meta_path}")

    strays = non_pptx_entries(delivery)
    if strays:
        print("warning: DELIVERY currently holds non-pptx entries:")
        for entry in strays:
            print(f"  - {entry}")
        print("         move them into WORK before publishing.")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    work = resolve_existing_dir(args.work, "--work")
    meta = read_meta(work)
    delivery = Path(meta.get("delivery_dir", "")).expanduser()
    if not delivery:
        die("project.json has no delivery_dir")
    if not delivery.is_dir():
        die(f"DELIVERY does not exist: {delivery}")

    source = Path(args.pptx).expanduser()
    if not source.is_file():
        die(f"--pptx does not exist: {source}")
    source = source.resolve()
    if source.suffix.lower() != ".pptx":
        die(f"--pptx must be a .pptx file: {source}")

    strays = non_pptx_entries(delivery)
    if strays:
        die("DELIVERY contains non-pptx entries, refusing to publish: " + ", ".join(strays))

    name = args.name or source.name
    if not name.lower().endswith(".pptx") or Path(name).name != name:
        die("--name must be a bare .pptx filename")
    destination = delivery / name
    if destination.exists() and not args.force:
        die(f"destination exists: {destination} (pass --force to overwrite)")

    shutil.copy2(source, destination)
    if sha256(source) != sha256(destination):
        die(f"copy verification failed: {destination}")
    print(f"published: {destination}")
    print(f"sha256:    {sha256(destination)}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    delivery = resolve_existing_dir(args.delivery, "--delivery")
    entries = list(delivery.iterdir())
    bad = non_pptx_entries(delivery)
    pptx = sorted(
        p.name
        for p in entries
        if p.is_file() and p.suffix.lower() == ".pptx" and not is_office_lock(p)
    )

    if bad:
        print("FAIL: DELIVERY contains non-pptx entries:", file=sys.stderr)
        for entry in bad:
            print(f"  - {entry}", file=sys.stderr)
        return 1
    if not pptx:
        print("FAIL: DELIVERY contains no .pptx", file=sys.stderr)
        return 1
    if args.expect_one and len(pptx) != 1:
        print(f"FAIL: expected exactly 1 .pptx, found {len(pptx)}: {', '.join(pptx)}", file=sys.stderr)
        return 1

    locks = sorted(p.name for p in entries if is_office_lock(p))
    if locks:
        print(f"note: ignoring Office lock file(s): {', '.join(locks)}")
    print(f"OK: {delivery}")
    for entry in pptx:
        print(f"  - {entry}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Two-root workspace helper for azf-zuhui-ppt.")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="show or create WORK and DELIVERY")
    prepare.add_argument("--date", required=True, help="meeting date, YYYYMMDD")
    prepare.add_argument("--topic", required=True, help="short topic used in the folder name")
    prepare.add_argument("--target", required=True, help="confirmed target root (must already exist)")
    prepare.add_argument("--work-root", default=str(DEFAULT_WORK_ROOT), help="parent of WORK")
    prepare.add_argument("--confirm", action="store_true", help="actually create the directories")
    prepare.set_defaults(func=cmd_prepare)

    publish = sub.add_parser("publish", help="copy the final .pptx into DELIVERY")
    publish.add_argument("--work", required=True)
    publish.add_argument("--pptx", required=True)
    publish.add_argument("--name", default="", help="filename inside DELIVERY (default: source name)")
    publish.add_argument("--force", action="store_true", help="overwrite an existing file of the same name")
    publish.set_defaults(func=cmd_publish)

    check = sub.add_parser("check", help="fail if DELIVERY contains anything but .pptx")
    check.add_argument("--delivery", required=True)
    check.add_argument("--expect-one", action="store_true", help="require exactly one .pptx")
    check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

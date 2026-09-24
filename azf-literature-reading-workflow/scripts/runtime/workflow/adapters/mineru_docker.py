from __future__ import annotations

"""本地 Docker MinerU 适配器。

2026-09 起 MinerU 发布 4.0，CLI 与产物结构都是破坏性变更：

- 3.x：``mineru -p <pdf> -o <dir> --backend pipeline``
- 4.x：``mineru-kit parse <pdf> -o <dir> -f zip --tier standard``

其中 ``flash/basic/standard/advanced`` 四档质量取代了原来的
``pipeline/vlm/hybrid`` 后端选择。本适配器统一调用 4.x 命令，并把产物
交给 ``workflow.services.mineru4_bundle`` 还原成工作流既有的 3.x 目录契约。
"""

import json
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz

DEFAULT_MINERU_IMAGE = "mineru:4.0.2-vllm0.21.0"
DEFAULT_MINERU_TIER = "standard"
MINERU_TIERS = ("flash", "basic", "standard", "advanced")


def docker_status() -> dict:
    docker = shutil.which("docker")
    if not docker:
        return {"available": False, "reason": "docker executable not found"}
    try:
        version = subprocess.run([docker, "--version"], capture_output=True, text=True, check=False)
        ps = subprocess.run([docker, "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=False)
    except OSError as exc:
        return {"available": False, "reason": str(exc)}
    if ps.returncode != 0:
        return {"available": False, "version": version.stdout.strip(), "reason": (ps.stderr or ps.stdout).strip()}
    return {"available": True, "version": version.stdout.strip(), "containers": ps.stdout.splitlines()}


def mineru_image_available(image: str = DEFAULT_MINERU_IMAGE) -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    result = subprocess.run([docker, "images", "-q", image], capture_output=True, text=True, check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def build_mineru_docker_command(
    image: str,
    input_dir: Path,
    output_dir: Path,
    *,
    tier: str = DEFAULT_MINERU_TIER,
    use_gpu: bool = True,
    pdf_name: str = "paper.pdf",
) -> list[str]:
    """Build the 4.x ``docker run`` invocation for one staged PDF."""
    command = ["docker", "run", "--rm"]
    if use_gpu:
        command.extend(["--gpus", "all"])
    command.extend(
        [
            "-v",
            f"{input_dir.resolve()}:/input",
            "-v",
            f"{output_dir.resolve()}:/output",
            image,
            "mineru-kit",
            "parse",
            f"/input/{pdf_name}",
            "-o",
            "/output",
            "-f",
            "zip",
            "--tier",
            tier,
        ]
    )
    return command


def run_mineru_docker(
    pdf_path: Path,
    output_dir: Path,
    image: str = DEFAULT_MINERU_IMAGE,
    *,
    tier: str = DEFAULT_MINERU_TIER,
    use_gpu: bool = True,
) -> subprocess.CompletedProcess:
    """Run MinerU 4.x in Docker and publish the legacy ``<stem>/auto/`` bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = hashlib.sha1(str(pdf_path.resolve()).encode("utf-8")).hexdigest()[:12]
    temp_base = Path(os.environ.get("LITERATURE_WORKFLOW_TMP", tempfile.gettempdir())).expanduser().resolve()
    staging_root = temp_base / "azf-literature-workflow" / "docker-staging" / run_id
    input_dir = staging_root / "input"
    staged_output = staging_root / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    staged_output.mkdir(parents=True, exist_ok=True)
    staged_pdf = input_dir / "paper.pdf"
    shutil.copy2(pdf_path, staged_pdf)
    command = build_mineru_docker_command(
        image, input_dir, staged_output, tier=tier, use_gpu=use_gpu, pdf_name=staged_pdf.name
    )
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if result.returncode == 0:
            from workflow.services.mineru4_bundle import publish_mineru4_bundle

            auto_dir = publish_mineru4_bundle(staged_output, output_dir, staged_pdf)
            if auto_dir is not None:
                shutil.copytree(staged_output, output_dir, dirs_exist_ok=True)
        return result
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def pymupdf_preview_parse(pdf_path: Path, markdown_path: Path, raw_output_path: Path) -> None:
    doc = fitz.open(pdf_path)
    pages = []
    markdown_parts = [
        "# PyMuPDF Preview Parse",
        "",
        "> [!warning] 这不是正式 MinerU 输出",
        "> Docker MinerU 当前不可用。本文件仅用于本地预览、工作区联调和后续人工核对；不得视为通过 MinerU 解析质量门。",
        "",
    ]
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        pages.append({"page": index, "chars": len(text)})
        markdown_parts.append(f"## Page {index}")
        markdown_parts.append("")
        markdown_parts.append(text.strip() or "[no selectable text detected]")
        markdown_parts.append("")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(markdown_parts), encoding="utf-8")
    raw_output_path.write_text(
        json.dumps(
            {
                "parser": "pymupdf_preview",
                "accepted_as_mineru": False,
                "source_pdf": str(pdf_path),
                "pages": pages,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

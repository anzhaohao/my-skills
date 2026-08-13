from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from workflow.models.paper import PaperWorkspace
from workflow.services.artifact_runs import latest_successful_state_dir
from workflow.services.zotero_links import extract_frontmatter_value


DEFAULT_ENDPOINT = "http://127.0.0.1:23119/zotero-research-db/v1/artifacts/import"
DEFAULT_TOKEN_ENV = "ZOTERO_RESEARCH_DB_TOKEN"
DEFAULT_TOKEN_FILE = Path.home() / ".config" / "azf-literature-reading-workflow" / "zotero-research-db-token"
ZOTERO_KEY_PROPERTY = "Zotero条目键"


class ZoteroArtifactDeliveryError(RuntimeError):
    """Raised when a validated workflow artifact cannot be delivered safely."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_local_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ZoteroArtifactDeliveryError("Zotero 产物端点必须是本机 HTTP 回环地址")
    if parsed.path != "/zotero-research-db/v1/artifacts/import":
        raise ZoteroArtifactDeliveryError("Zotero 产物端点路径不符合插件 v1 契约")
    return endpoint


def load_delivery_token(
    *,
    environment_name: str = DEFAULT_TOKEN_ENV,
    token_file: Path = DEFAULT_TOKEN_FILE,
    environ: dict[str, str] | None = None,
) -> str:
    environment = os.environ if environ is None else environ
    token = environment.get(environment_name, "").strip()
    if token:
        return token
    try:
        token = token_file.expanduser().read_text(encoding="utf-8-sig").strip()
    except FileNotFoundError:
        token = ""
    except OSError as exc:
        raise ZoteroArtifactDeliveryError(f"无法读取 Zotero 本机令牌文件：{token_file}") from exc
    if not token:
        raise ZoteroArtifactDeliveryError(
            f"缺少 Zotero 本机令牌；请设置环境变量 {environment_name}，"
            f"或写入仅本机可读文件 {token_file.expanduser()}"
        )
    return token


def _load_passed_quality_report(state_dir: Path) -> dict[str, Any]:
    quality_path = state_dir / "quality-report.json"
    if not quality_path.is_file():
        raise ZoteroArtifactDeliveryError(f"latest_successful 缺少质量报告：{quality_path}")
    try:
        quality = json.loads(quality_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ZoteroArtifactDeliveryError(f"无法读取 latest_successful 质量报告：{quality_path}") from exc
    if not isinstance(quality, dict) or quality.get("overall_status") != "pass":
        raise ZoteroArtifactDeliveryError("latest_successful 的质量报告不是 pass，拒绝交付")
    return quality


def _read_zotero_item_key(overview_note: Path) -> str:
    if not overview_note.is_file():
        raise ZoteroArtifactDeliveryError(f"找不到论文总览笔记：{overview_note}")
    value = extract_frontmatter_value(
        overview_note.read_text(encoding="utf-8-sig", errors="replace"),
        ZOTERO_KEY_PROPERTY,
    ).strip()
    if not value:
        raise ZoteroArtifactDeliveryError("论文总览缺少 Zotero条目键，无法确定导入父条目")
    return value


def _artifact(path: Path, role: str) -> dict[str, str]:
    if not path.is_file():
        raise ZoteroArtifactDeliveryError(f"缺少待交付产物：{path}")
    if path.suffix.casefold() != ".md":
        raise ZoteroArtifactDeliveryError(f"只允许交付 Markdown 产物：{path}")
    return {
        "role": role,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "title": path.name,
    }


def build_artifact_import_request(
    workspace_root: Path,
    artifact_root: Path,
    *,
    library_id: int = 1,
) -> dict[str, Any]:
    workspace_root = workspace_root.expanduser().resolve()
    successful_state = latest_successful_state_dir(artifact_root, workspace_root)
    if successful_state is None:
        raise ZoteroArtifactDeliveryError(
            "工作区尚无 validate-pilot 提升后的 latest_successful 运行，拒绝交付"
        )
    _load_passed_quality_report(successful_state)
    run_id = successful_state.parent.name
    workspace = PaperWorkspace.from_root(
        workspace_root,
        state_path=successful_state,
        artifact_root=artifact_root,
        artifact_id=run_id,
    )
    parent_item_key = _read_zotero_item_key(workspace.overview_note)
    artifacts = []
    if workspace.source_language == "en":
        artifacts.append(_artifact(workspace.mineru_source_path(), "mineru-original"))
    artifacts.append(_artifact(workspace.chinese_fulltext_path(), "translation"))
    return {
        "libraryID": library_id,
        "parentItemKey": parent_item_key,
        "workflowRunID": run_id,
        "artifacts": artifacts,
    }


def post_artifact_import_request(
    endpoint: str,
    token: str,
    payload: dict[str, Any],
    *,
    timeout: float = 30.0,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    endpoint = validate_local_endpoint(endpoint)
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-ZRDB-Token": token,
        },
    )
    try:
        with opener(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            raw = response.read().decode("utf-8-sig")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8-sig", errors="replace")
        raise ZoteroArtifactDeliveryError(
            f"Zotero 端点返回 HTTP {exc.code}：{detail[:500]}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ZoteroArtifactDeliveryError(f"无法连接 Zotero 本机端点：{exc}") from exc
    if status < 200 or status >= 300:
        raise ZoteroArtifactDeliveryError(f"Zotero 端点返回 HTTP {status}")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ZoteroArtifactDeliveryError("Zotero 端点返回了无效 JSON") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise ZoteroArtifactDeliveryError(f"Zotero 端点拒绝产物：{result}")
    return result


def validate_delivery_response(
    payload: dict[str, Any],
    response: dict[str, Any],
) -> None:
    expected_roles = {str(entry["role"]) for entry in payload.get("artifacts", [])}
    returned = response.get("artifacts")
    if not isinstance(returned, list):
        raise ZoteroArtifactDeliveryError("Zotero 响应缺少 artifacts 结果，不能归档工作区")
    accepted_roles = {
        str(entry.get("role"))
        for entry in returned
        if isinstance(entry, dict) and entry.get("status") in {"imported", "unchanged"}
    }
    if accepted_roles != expected_roles:
        raise ZoteroArtifactDeliveryError(
            f"Zotero 未确认全部产物，不能归档工作区：expected={sorted(expected_roles)}, "
            f"accepted={sorted(accepted_roles)}"
        )


def retirement_target(
    workspace_root: Path,
    artifact_root: Path,
    workflow_run_id: str,
) -> Path:
    return (
        artifact_root.expanduser().resolve()
        / workflow_run_id
        / "zotero-delivered-workspace"
        / workspace_root.expanduser().resolve().name
    )


def retire_delivered_workspace(
    workspace_root: Path,
    artifact_root: Path,
    payload: dict[str, Any],
    response: dict[str, Any],
) -> Path:
    validate_delivery_response(payload, response)
    source = workspace_root.expanduser().resolve()
    artifact_root = artifact_root.expanduser().resolve()
    if not source.is_dir():
        raise ZoteroArtifactDeliveryError(f"待归档工作区不存在：{source}")
    try:
        source.relative_to(artifact_root)
    except ValueError:
        pass
    else:
        raise ZoteroArtifactDeliveryError("工作区已经位于 artifact_root 内，拒绝重复归档")
    target = retirement_target(source, artifact_root, str(payload["workflowRunID"]))
    try:
        target.relative_to(artifact_root)
    except ValueError as exc:
        raise ZoteroArtifactDeliveryError("工作区归档目标越出 artifact_root") from exc
    if target.exists():
        raise ZoteroArtifactDeliveryError(f"工作区归档目标已存在，拒绝覆盖：{target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        moved = Path(shutil.move(str(source), str(target))).resolve()
    except OSError as exc:
        raise ZoteroArtifactDeliveryError(f"工作区已入库但归档失败：{exc}") from exc
    audit = {
        "schema_version": 1,
        "backend": "zotero",
        "retired_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_workspace": str(source),
        "archived_workspace": str(moved),
        "parent_item_key": payload["parentItemKey"],
        "workflow_run_id": payload["workflowRunID"],
        "artifacts": response["artifacts"],
    }
    audit_path = artifact_root / str(payload["workflowRunID"]) / "zotero-delivery.json"
    audit_path.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return moved

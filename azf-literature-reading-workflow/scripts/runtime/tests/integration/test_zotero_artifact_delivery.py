from __future__ import annotations

import io
import json
from argparse import Namespace
from pathlib import Path
from urllib.error import HTTPError

import pytest

from workflow.commands import deliver_zotero_artifacts
from workflow.services.zotero_artifact_delivery import (
    ZoteroArtifactDeliveryError,
    build_artifact_import_request,
    load_delivery_token,
    post_artifact_import_request,
    retire_delivered_workspace,
    sha256_file,
    validate_local_endpoint,
)


def _make_validated_workspace(tmp_path: Path, *, source_language: str = "en") -> tuple[Path, Path]:
    workspace = tmp_path / "paper-root" / "Paper A"
    reading = workspace / "阅读工作台"
    source = workspace / "附件" / "原文"
    reading.mkdir(parents=True)
    source.mkdir(parents=True)
    (reading / "【总览】测试论文.md").write_text(
        "---\n"
        "中文短标题: \"测试论文\"\n"
        f"原文语言: {source_language}\n"
        "Zotero条目键: \"ABCD1234\"\n"
        "---\n",
        encoding="utf-8",
    )
    if source_language == "en":
        (source / "【MinerU原文】测试论文.md").write_text("# English\n", encoding="utf-8")
    (reading / "【中译】测试论文.md").write_text("# 中文\n", encoding="utf-8")

    artifact_root = tmp_path / "artifacts"
    state = artifact_root / "run-001" / "state"
    state.mkdir(parents=True)
    (state / "quality-report.json").write_text(
        json.dumps({"overall_status": "pass"}),
        encoding="utf-8",
    )
    paper_key = "workspace:paper a"
    (artifact_root / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "papers": {
                    paper_key: {
                        "paper_workspace": str(workspace.resolve()),
                        "latest_successful": "run-001",
                    }
                },
                "lookup": {paper_key: paper_key},
            }
        ),
        encoding="utf-8",
    )
    return workspace, artifact_root


class _Response:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_request_discovers_both_markdown_artifacts_and_hashes_them(tmp_path: Path) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path)

    payload = build_artifact_import_request(workspace, artifact_root)

    assert payload["libraryID"] == 1
    assert payload["parentItemKey"] == "ABCD1234"
    assert payload["workflowRunID"] == "run-001"
    assert [entry["role"] for entry in payload["artifacts"]] == ["mineru-original", "translation"]
    for entry in payload["artifacts"]:
        path = Path(entry["path"])
        assert entry["sha256"] == sha256_file(path)
        assert entry["title"] == path.name


def test_chinese_source_delivers_only_merged_chinese_artifact(tmp_path: Path) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path, source_language="zh")
    payload = build_artifact_import_request(workspace, artifact_root)
    assert [entry["role"] for entry in payload["artifacts"]] == ["translation"]


def test_missing_latest_successful_is_rejected(tmp_path: Path) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path)
    index = json.loads((artifact_root / "index.json").read_text(encoding="utf-8"))
    index["papers"]["workspace:paper a"].pop("latest_successful")
    (artifact_root / "index.json").write_text(json.dumps(index), encoding="utf-8")

    with pytest.raises(ZoteroArtifactDeliveryError, match="latest_successful"):
        build_artifact_import_request(workspace, artifact_root)


def test_dry_run_does_not_post(tmp_path: Path, monkeypatch, capsys) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path)
    monkeypatch.setattr(
        deliver_zotero_artifacts,
        "post_artifact_import_request",
        lambda *_args, **_kwargs: pytest.fail("dry-run must not send a request"),
    )
    args = Namespace(
        workspace=str(workspace),
        resolved_locations={"artifact_root": artifact_root},
        library_id=1,
        apply=False,
        endpoint="http://127.0.0.1:23119/zotero-research-db/v1/artifacts/import",
        token_env="ZOTERO_RESEARCH_DB_TOKEN",
        token_file=None,
        timeout=30.0,
        retire_workspace=False,
    )

    assert deliver_zotero_artifacts.run(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "dry-run"


def test_http_success_and_unchanged_response() -> None:
    captured = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["token"] = request.headers["X-zrdb-token"]
        captured["timeout"] = timeout
        return _Response({"ok": True, "artifacts": [{"status": "unchanged"}]})

    payload = {"libraryID": 1, "parentItemKey": "ABCD1234", "workflowRunID": "run", "artifacts": []}
    result = post_artifact_import_request(
        "http://127.0.0.1:23119/zotero-research-db/v1/artifacts/import",
        "secret",
        payload,
        timeout=5,
        opener=opener,
    )

    assert result["artifacts"][0]["status"] == "unchanged"
    assert captured == {"body": payload, "token": "secret", "timeout": 5}


def test_http_401_is_reported_without_hiding_status() -> None:
    def opener(_request, timeout):
        raise HTTPError(
            "http://127.0.0.1:23119/zotero-research-db/v1/artifacts/import",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":"unauthorized"}'),
        )

    with pytest.raises(ZoteroArtifactDeliveryError, match="HTTP 401"):
        post_artifact_import_request(
            "http://127.0.0.1:23119/zotero-research-db/v1/artifacts/import",
            "bad",
            {},
            opener=opener,
        )


def test_token_precedence_and_external_endpoint_rejection(tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("file-token\n", encoding="utf-8")
    assert load_delivery_token(token_file=token_file, environ={}) == "file-token"
    assert load_delivery_token(token_file=token_file, environ={"ZOTERO_RESEARCH_DB_TOKEN": "env-token"}) == "env-token"
    with pytest.raises(ZoteroArtifactDeliveryError, match="回环"):
        validate_local_endpoint("https://example.com/zotero-research-db/v1/artifacts/import")


def test_zotero_only_backend_retires_workspace_after_complete_response(tmp_path: Path) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path)
    payload = build_artifact_import_request(workspace, artifact_root)
    response = {
        "ok": True,
        "artifacts": [
            {"role": "mineru-original", "status": "imported"},
            {"role": "translation", "status": "unchanged"},
        ],
    }

    archived = retire_delivered_workspace(workspace, artifact_root, payload, response)

    assert not workspace.exists()
    assert archived.is_dir()
    audit = json.loads((artifact_root / "run-001" / "zotero-delivery.json").read_text(encoding="utf-8"))
    assert audit["backend"] == "zotero"
    assert audit["parent_item_key"] == "ABCD1234"


def test_workspace_is_not_retired_after_partial_response(tmp_path: Path) -> None:
    workspace, artifact_root = _make_validated_workspace(tmp_path)
    payload = build_artifact_import_request(workspace, artifact_root)

    with pytest.raises(ZoteroArtifactDeliveryError, match="未确认全部产物"):
        retire_delivered_workspace(
            workspace,
            artifact_root,
            payload,
            {"ok": True, "artifacts": [{"role": "translation", "status": "imported"}]},
        )
    assert workspace.is_dir()

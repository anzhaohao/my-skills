import json
from argparse import Namespace
from datetime import datetime
from pathlib import Path

import pytest

from workflow.models.paper import PaperWorkspace
from workflow.services.artifact_runs import (
    doi_slug,
    initialize_run,
    load_index,
    make_artifact_id,
    mark_run_failed,
    promote_run,
    resolve_run_from_args,
)


def _overview(workspace: Path, doi: str = "10.1234/ABC:DEF", zotero_key: str = "ITEM123") -> None:
    reading = workspace / "阅读工作台"
    reading.mkdir(parents=True)
    (reading / "【总览】测试.md").write_text(
        f"---\nDOI: \"{doi}\"\nZotero条目键: \"{zotero_key}\"\n---\n",
        encoding="utf-8",
    )


def test_doi_slug_and_multiple_runs_are_windows_safe() -> None:
    assert doi_slug("HTTPS://doi.org/10.1234/ABC:DEF") == "10.1234_abc_def"
    assert doi_slug(None, "ABCD1234") == "no-doi__zotero-abcd1234"
    first = make_artifact_id("10.1234/ABC", when=datetime(2026, 7, 18, 10, 0, 0))
    second = make_artifact_id("10.1234/ABC", when=datetime(2026, 7, 18, 10, 0, 1))
    assert first != second
    assert first.endswith("__10.1234_abc")


def test_failed_attempt_does_not_replace_latest_successful(tmp_path: Path) -> None:
    workspace = tmp_path / "vault" / "Paper"
    _overview(workspace)
    artifact_root = tmp_path / "output"
    paper_root = workspace.parent

    successful = initialize_run(
        artifact_root,
        workspace,
        artifact_id="20260718_100000__10.1234_abc_def",
        doi="10.1234/ABC:DEF",
        zotero_key="ITEM123",
        paper_root=paper_root,
    )
    promote_run(artifact_root, successful, quality_status="pass")
    failed = initialize_run(
        artifact_root,
        workspace,
        artifact_id="20260718_100001__10.1234_abc_def",
        doi="10.1234/ABC:DEF",
        zotero_key="ITEM123",
        paper_root=paper_root,
    )
    mark_run_failed(artifact_root, failed, "test failure")

    entry = next(iter(load_index(artifact_root)["papers"].values()))
    assert entry["latest_attempt"] == failed.artifact_id
    assert entry["latest_successful"] == successful.artifact_id


def test_successful_run_is_readable_but_not_mutated_in_place(tmp_path: Path) -> None:
    workspace = tmp_path / "vault" / "Paper"
    _overview(workspace)
    artifact_root = tmp_path / "output"
    run = initialize_run(
        artifact_root,
        workspace,
        artifact_id="20260718_100000__10.1234_abc_def",
        doi="10.1234/ABC:DEF",
        zotero_key="ITEM123",
        paper_root=workspace.parent,
    )
    promote_run(artifact_root, run, quality_status="pass")
    args = Namespace(
        workspace=str(workspace),
        artifact_id=run.artifact_id,
        resolved_locations={"artifact_root": artifact_root, "paper_root": workspace.parent},
    )

    with pytest.raises(RuntimeError, match="already successful and immutable"):
        resolve_run_from_args(args, require_writable=True)
    paper, resolved = resolve_run_from_args(args, require_writable=False)
    assert paper.artifact_id == resolved.artifact_id == run.artifact_id

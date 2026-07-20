from pathlib import Path

from workflow.services.cache_paths import cleanup_legacy_workspace_transients, cleanup_workspace_cache, workspace_cache_root
from workflow.validators.workspace_cleanliness import validate_workspace_cleanliness


def test_cache_is_external_and_cleanup_removes_legacy_transients(tmp_path: Path) -> None:
    workspace = tmp_path / "vault" / "Paper"
    (workspace / "附件" / "原文" / "_mineru_output").mkdir(parents=True)
    (workspace / "附件" / "原文" / "MinerU原始输出.json").write_text("{}", encoding="utf-8")
    (workspace / "_figure_skill_output").mkdir()
    cache_base = tmp_path / "cache"
    cache = workspace_cache_root(workspace, cache_base)
    cache.mkdir(parents=True)
    (cache / "temp.bin").write_bytes(b"x")

    assert not validate_workspace_cleanliness(workspace) == []
    cleanup_workspace_cache(workspace, cache_base)
    cleanup_legacy_workspace_transients(workspace)

    assert not cache.exists()
    assert validate_workspace_cleanliness(workspace) == []
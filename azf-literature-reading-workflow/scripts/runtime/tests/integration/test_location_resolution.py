import json
from pathlib import Path

import pytest
import yaml

from workflow.cli import main
from workflow.services.location_resolution import (
    BASE_FILE,
    CARD_FOLDER,
    CONCEPT_MARKER_KEY,
    CONCEPT_MARKER_VALUE,
    INDEX_FOLDER,
    INDEX_NOTE,
    confirm_manifest,
    load_confirmed_locations,
    resolve_locations,
    vault_relative,
    write_pending_manifest,
)


def _make_vault(tmp_path: Path, concept_relative: Path, *, marker: bool = True, base_relative: str | None = None) -> dict[str, Path]:
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    paper_root = vault / "02-Brain Cells" / "0_论文精读"
    paper_root.mkdir(parents=True)
    concept_root = vault / concept_relative
    (concept_root / CARD_FOLDER).mkdir(parents=True)
    index_dir = concept_root / INDEX_FOLDER
    index_dir.mkdir(parents=True)
    marker_lines = (
        f"系统角色: 中央扫盲班\n{CONCEPT_MARKER_KEY}: {CONCEPT_MARKER_VALUE}\n"
        if marker
        else ""
    )
    (index_dir / INDEX_NOTE).write_text(
        f"---\n类型: 概念库入口\n{marker_lines}---\n\n![[{BASE_FILE}]]\n",
        encoding="utf-8",
    )
    folder = base_relative or vault_relative(concept_root / CARD_FOLDER, vault)
    (index_dir / BASE_FILE).write_text(
        f'filters:\n  and:\n    - file.folder == "{folder}"\n',
        encoding="utf-8",
    )
    template = vault / "05-Junk Drawer" / "2_模板" / "2.1 Templater" / "概念卡模板.md"
    template.parent.mkdir(parents=True)
    template.write_text("---\n类型: 概念卡\n---\n", encoding="utf-8")
    return {
        "vault_root": vault,
        "paper_root": paper_root,
        "concept_library_root": concept_root,
        "template_path": template,
    }


def test_resolver_discovers_moved_concept_library_and_reports_stale_base(tmp_path: Path) -> None:
    paths = _make_vault(
        tmp_path,
        Path("02-Brain Cells/99_Mind Palace/1_扫盲班"),
        base_relative="02-Brain Cells/3_信息图鉴/1_扫盲班/概念卡",
    )
    registry = tmp_path / "locations.yaml"
    stale = paths["vault_root"] / "02-Brain Cells" / "99_扫盲班"
    registry.write_text(
        yaml.safe_dump(
            {
                "locations": {
                    "vault_root": str(paths["vault_root"]),
                    "paper_root": str(paths["paper_root"]),
                    "concept_library_root": str(stale),
                    "template_path": str(paths["template_path"]),
                }
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = resolve_locations(registry_path=registry)

    assert result.ready_for_confirmation is True
    assert result.locations["concept_library_root"] == paths["concept_library_root"].resolve()
    assert result.sources["concept_library_root"] == "role-marker-discovery"
    assert any("registry path is stale" in warning for warning in result.warnings)
    assert any("Base folder filter is stale" in warning for warning in result.warnings)

    manifest = tmp_path / "manifest.json"
    write_pending_manifest(result, manifest, registry)
    confirmed = confirm_manifest(manifest, registry)
    assert confirmed["repairs"]
    index_text = (paths["concept_library_root"] / INDEX_FOLDER / INDEX_NOTE).read_text(encoding="utf-8")
    base_text = (paths["concept_library_root"] / INDEX_FOLDER / BASE_FILE).read_text(encoding="utf-8")
    assert CONCEPT_MARKER_VALUE in index_text
    assert 'file.folder == "02-Brain Cells/99_Mind Palace/1_扫盲班/概念卡"' in base_text


def test_multiple_unmarked_concept_libraries_require_explicit_choice(tmp_path: Path) -> None:
    paths = _make_vault(tmp_path, Path("02-Brain Cells/A/扫盲班"), marker=False)
    second = paths["vault_root"] / "02-Brain Cells" / "B" / "扫盲班"
    (second / CARD_FOLDER).mkdir(parents=True)
    (second / INDEX_FOLDER).mkdir(parents=True)
    (second / INDEX_FOLDER / INDEX_NOTE).write_text("---\n类型: 概念库入口\n---\n", encoding="utf-8")

    result = resolve_locations(vault_root=paths["vault_root"], registry_path=tmp_path / "missing.yaml")

    assert result.ready_for_confirmation is False
    assert any("multiple candidates" in error for error in result.errors)


def test_confirmed_manifest_rejects_folder_move(tmp_path: Path) -> None:
    paths = _make_vault(tmp_path, Path("02-Brain Cells/99_Mind Palace/1_扫盲班"))
    resolution = resolve_locations(
        vault_root=paths["vault_root"],
        paper_root=paths["paper_root"],
        concept_library_root=paths["concept_library_root"],
        template_path=paths["template_path"],
        registry_path=tmp_path / "registry.yaml",
    )
    manifest = tmp_path / "manifest.json"
    registry = tmp_path / "registry.yaml"
    write_pending_manifest(resolution, manifest, registry)
    confirm_manifest(manifest, registry)
    load_confirmed_locations(manifest)

    moved = paths["concept_library_root"].parent / "2_扫盲班"
    paths["concept_library_root"].rename(moved)

    with pytest.raises(RuntimeError, match="concept_library_root is unavailable"):
        load_confirmed_locations(manifest)


def test_mutating_cli_rejects_pending_manifest(tmp_path: Path, capsys) -> None:
    paths = _make_vault(tmp_path, Path("02-Brain Cells/99_Mind Palace/1_扫盲班"))
    resolution = resolve_locations(
        vault_root=paths["vault_root"],
        paper_root=paths["paper_root"],
        concept_library_root=paths["concept_library_root"],
        template_path=paths["template_path"],
        registry_path=tmp_path / "registry.yaml",
    )
    manifest = tmp_path / "manifest.json"
    write_pending_manifest(resolution, manifest, tmp_path / "registry.yaml")
    workspace = paths["paper_root"] / "Paper A"

    code = main(
        [
            "generate-deep-reading",
            "--workspace",
            str(workspace),
            "--title-zh",
            "测试论文",
            "--no-dry-run",
            "--location-manifest",
            str(manifest),
        ]
    )

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert "has not been confirmed" in payload["reason"]
    assert not workspace.exists()
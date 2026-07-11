from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml

INDEX_FOLDER = "入口和索引"
INDEX_NOTE = "扫盲班总览.md"
BASE_FILE = "扫盲班索引.base"
CARD_FOLDER = "概念卡"
CONCEPT_MARKER_KEY = "系统标识"
CONCEPT_MARKER_VALUE = "azf-literature-concept-library-v1"
CONCEPT_ROLE_KEY = "系统角色"
CONCEPT_ROLE_VALUE = "中央扫盲班"

DEFAULT_VAULT_ROOT = Path("E:/software/Obsidian/安钊锋的外置大脑")
DEFAULT_PAPER_RELATIVE = Path("02-Brain Cells/0_论文精读")
DEFAULT_CONCEPT_RELATIVE = Path("02-Brain Cells/99_Mind Palace/1_扫盲班")
DEFAULT_TEMPLATE_RELATIVE = Path("05-Junk Drawer/2_模板/2.1 Templater/概念卡模板.md")
ROLE_NAMES = ("vault_root", "paper_root", "concept_library_root", "template_path")


def default_config_dir() -> Path:
    return Path.home() / ".config" / "azf-literature-reading-workflow"


def default_registry_path() -> Path:
    return default_config_dir() / "locations.yaml"


def default_manifest_path() -> Path:
    return default_config_dir() / "location-manifest.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _resolved(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def vault_relative(path: Path, vault_root: Path) -> str:
    return path.resolve().relative_to(vault_root.resolve()).as_posix()


def _path_fingerprint(locations: dict[str, Path]) -> str:
    payload = "\n".join(f"{name}={locations[name].resolve()}" for name in ROLE_NAMES)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_registry(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    locations = data.get("locations", {}) if isinstance(data, dict) else {}
    return {name: str(value) for name, value in locations.items() if name in ROLE_NAMES and value}


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _find_vault_ancestor(path: Path) -> Path | None:
    current = path if path.is_dir() else path.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".obsidian").is_dir():
            return candidate.resolve()
    return None


def _discover_concept_libraries(vault_root: Path) -> tuple[list[Path], list[Path]]:
    marked: list[Path] = []
    structural: list[Path] = []
    for index_note in vault_root.rglob(INDEX_NOTE):
        if index_note.parent.name != INDEX_FOLDER:
            continue
        root = index_note.parent.parent.resolve()
        if not (root / CARD_FOLDER).is_dir():
            continue
        frontmatter = _read_frontmatter(index_note)
        if frontmatter.get(CONCEPT_MARKER_KEY) == CONCEPT_MARKER_VALUE:
            marked.append(root)
        else:
            structural.append(root)
    return sorted(set(marked)), sorted(set(structural))


def _discover_named_directories(vault_root: Path, name: str) -> list[Path]:
    return sorted({path.resolve() for path in vault_root.rglob(name) if path.is_dir()})


def _discover_concept_name_candidates(vault_root: Path) -> list[Path]:
    keywords = ["扫盲班"]
    excluded_names = {INDEX_FOLDER, CARD_FOLDER}
    excluded_parts = {"Attachments", "0_论文精读"}
    candidates: set[Path] = set()
    for path in vault_root.rglob("*"):
        if not path.is_dir() or path.name in excluded_names:
            continue
        relative_parts = set(path.relative_to(vault_root).parts)
        if relative_parts & excluded_parts:
            continue
        if any(keyword in path.name for keyword in keywords):
            candidates.add(path.resolve())

    # If both a container and its child match (for example 99_???/1_???),
    # keep the leaf folder that is more likely to contain the cards.
    leaves = []
    for candidate in sorted(candidates):
        if not any(other != candidate and other.is_relative_to(candidate) for other in candidates):
            leaves.append(candidate)
    return leaves


def _discover_named_files(vault_root: Path, name: str) -> list[Path]:
    return sorted({path.resolve() for path in vault_root.rglob(name) if path.is_file()})


@dataclass(slots=True)
class LocationResolution:
    locations: dict[str, Path]
    sources: dict[str, str]
    candidates: dict[str, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    resolved_at: str = field(default_factory=_now)

    @property
    def fingerprint(self) -> str:
        return _path_fingerprint(self.locations) if all(name in self.locations for name in ROLE_NAMES) else ""

    @property
    def ready_for_confirmation(self) -> bool:
        return not self.errors and bool(self.fingerprint)

    def to_manifest(self, registry_path: Path) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "status": "pending_confirmation",
            "resolved_at": self.resolved_at,
            "confirmed_at": None,
            "registry_path": str(registry_path.resolve()),
            "locations": {name: str(path.resolve()) for name, path in self.locations.items()},
            "sources": self.sources,
            "candidates": self.candidates,
            "warnings": self.warnings,
            "errors": self.errors,
            "fingerprint": self.fingerprint,
            "ready_for_confirmation": self.ready_for_confirmation,
        }


def _select_role(
    *,
    role: str,
    explicit: str | Path | None,
    registry: dict[str, str],
    fallback: Path,
    discover: Callable[[], tuple[list[Path], str] | list[Path]],
    expect_file: bool,
    sources: dict[str, str],
    candidates: dict[str, list[str]],
    warnings: list[str],
    errors: list[str],
) -> Path | None:
    def valid(path: Path) -> bool:
        return path.is_file() if expect_file else path.is_dir()

    if explicit:
        path = _resolved(explicit)
        sources[role] = "user-explicit"
        if not valid(path):
            errors.append(f"explicit {role} does not exist: {path}")
        return path

    registered = registry.get(role)
    if registered:
        path = _resolved(registered)
        if valid(path):
            sources[role] = "approved-registry"
            return path
        warnings.append(f"approved registry path is stale for {role}: {path}")

    discovered_result = discover()
    if isinstance(discovered_result, tuple):
        discovered, discovery_source = discovered_result
    else:
        discovered, discovery_source = discovered_result, "structure-discovery"
    discovered = sorted(set(path.resolve() for path in discovered if valid(path)))
    candidates[role] = [str(path) for path in discovered]
    if len(discovered) == 1:
        sources[role] = discovery_source
        return discovered[0]
    if len(discovered) > 1:
        errors.append(f"multiple candidates found for {role}; explicit confirmation is required")
        return None

    fallback = fallback.resolve()
    if valid(fallback):
        sources[role] = "fallback-default"
        warnings.append(f"{role} used fallback default because no approved or discoverable candidate was found")
        return fallback

    errors.append(f"unable to resolve {role}")
    return None


def resolve_locations(
    *,
    vault_root: str | Path | None = None,
    paper_root: str | Path | None = None,
    concept_library_root: str | Path | None = None,
    template_path: str | Path | None = None,
    registry_path: str | Path | None = None,
) -> LocationResolution:
    registry_file = _resolved(registry_path or default_registry_path())
    registry = _read_registry(registry_file)
    sources: dict[str, str] = {}
    candidates: dict[str, list[str]] = {}
    warnings: list[str] = []
    errors: list[str] = []
    locations: dict[str, Path] = {}

    explicit_children = [value for value in [paper_root, concept_library_root, template_path] if value]
    inferred_vaults = sorted({candidate for value in explicit_children if (candidate := _find_vault_ancestor(_resolved(value)))})

    if vault_root:
        vault = _resolved(vault_root)
        sources["vault_root"] = "user-explicit"
    elif len(inferred_vaults) == 1:
        vault = inferred_vaults[0]
        sources["vault_root"] = "inferred-from-explicit-child"
    elif registry.get("vault_root") and _resolved(registry["vault_root"]).is_dir():
        vault = _resolved(registry["vault_root"])
        sources["vault_root"] = "approved-registry"
    else:
        vault = DEFAULT_VAULT_ROOT.resolve()
        sources["vault_root"] = "fallback-default"
        if registry.get("vault_root"):
            warnings.append(f"approved registry path is stale for vault_root: {_resolved(registry['vault_root'])}")

    locations["vault_root"] = vault
    if not vault.is_dir() or not (vault / ".obsidian").is_dir():
        errors.append(f"vault_root is not an Obsidian vault: {vault}")
        return LocationResolution(locations, sources, candidates, warnings, errors)

    def concept_discovery() -> tuple[list[Path], str]:
        marked, structural = _discover_concept_libraries(vault)
        if marked:
            return marked, "role-marker-discovery"
        if structural:
            return structural, "structure-discovery"
        return _discover_concept_name_candidates(vault), "name-discovery"

    resolved_paper = _select_role(
        role="paper_root",
        explicit=paper_root,
        registry=registry,
        fallback=vault / DEFAULT_PAPER_RELATIVE,
        discover=lambda: _discover_named_directories(vault, "0_论文精读"),
        expect_file=False,
        sources=sources,
        candidates=candidates,
        warnings=warnings,
        errors=errors,
    )
    resolved_concept = _select_role(
        role="concept_library_root",
        explicit=concept_library_root,
        registry=registry,
        fallback=vault / DEFAULT_CONCEPT_RELATIVE,
        discover=concept_discovery,
        expect_file=False,
        sources=sources,
        candidates=candidates,
        warnings=warnings,
        errors=errors,
    )
    resolved_template = _select_role(
        role="template_path",
        explicit=template_path,
        registry=registry,
        fallback=vault / DEFAULT_TEMPLATE_RELATIVE,
        discover=lambda: _discover_named_files(vault, "概念卡模板.md"),
        expect_file=True,
        sources=sources,
        candidates=candidates,
        warnings=warnings,
        errors=errors,
    )

    for role, path in [
        ("paper_root", resolved_paper),
        ("concept_library_root", resolved_concept),
        ("template_path", resolved_template),
    ]:
        if path is None:
            continue
        locations[role] = path
        try:
            path.resolve().relative_to(vault)
        except ValueError:
            errors.append(f"{role} is outside vault_root: {path}")

    if resolved_concept:
        index_note = resolved_concept / INDEX_FOLDER / INDEX_NOTE
        base_file = resolved_concept / INDEX_FOLDER / BASE_FILE
        if index_note.is_file():
            marker = _read_frontmatter(index_note)
            if marker.get(CONCEPT_MARKER_KEY) != CONCEPT_MARKER_VALUE:
                warnings.append(f"central concept library marker is missing from {index_note}")
        else:
            warnings.append(f"central concept library index note is missing: {index_note}")
        if base_file.is_file():
            expected_folder = vault_relative(resolved_concept / CARD_FOLDER, vault)
            base_text = base_file.read_text(encoding="utf-8-sig", errors="replace")
            if f'file.folder == "{expected_folder}"' not in base_text:
                warnings.append(f"Base folder filter is stale: expected {expected_folder} in {base_file}")
        else:
            warnings.append(f"central concept Base file is missing: {base_file}")

    return LocationResolution(locations, sources, candidates, warnings, errors)


def write_pending_manifest(resolution: LocationResolution, manifest_path: str | Path, registry_path: str | Path) -> Path:
    manifest = _resolved(manifest_path)
    registry = _resolved(registry_path)
    payload = resolution.to_manifest(registry)
    _write_text_atomic(manifest, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return manifest


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = _resolved(path)
    data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid location manifest: {manifest}")
    return data


def _manifest_locations(data: dict[str, Any]) -> dict[str, Path]:
    raw = data.get("locations", {})
    if not isinstance(raw, dict):
        raise RuntimeError("location manifest has no locations mapping")
    locations = {name: _resolved(raw[name]) for name in ROLE_NAMES if raw.get(name)}
    if set(locations) != set(ROLE_NAMES):
        missing = sorted(set(ROLE_NAMES) - set(locations))
        raise RuntimeError(f"location manifest is missing roles: {missing}")
    return locations


def validate_manifest(data: dict[str, Any], *, require_confirmed: bool) -> dict[str, Path]:
    if require_confirmed and data.get("status") != "confirmed":
        raise RuntimeError("location manifest has not been confirmed in the second round")
    locations = _manifest_locations(data)
    if data.get("fingerprint") != _path_fingerprint(locations):
        raise RuntimeError("location manifest fingerprint mismatch")
    vault = locations["vault_root"]
    if not vault.is_dir() or not (vault / ".obsidian").is_dir():
        raise RuntimeError(f"confirmed vault_root is unavailable: {vault}")
    for role in ["paper_root", "concept_library_root"]:
        if not locations[role].is_dir():
            raise RuntimeError(f"confirmed {role} is unavailable: {locations[role]}")
    if not locations["template_path"].is_file():
        raise RuntimeError(f"confirmed template_path is unavailable: {locations['template_path']}")
    for role in ["paper_root", "concept_library_root", "template_path"]:
        try:
            locations[role].relative_to(vault)
        except ValueError as exc:
            raise RuntimeError(f"confirmed {role} moved outside vault_root: {locations[role]}") from exc
    return locations


def repair_concept_location_metadata(locations: dict[str, Path]) -> list[str]:
    repairs: list[str] = []
    vault = locations["vault_root"]
    concept_root = locations["concept_library_root"]
    index_note = concept_root / INDEX_FOLDER / INDEX_NOTE
    base_file = concept_root / INDEX_FOLDER / BASE_FILE

    if index_note.is_file():
        text = index_note.read_text(encoding="utf-8-sig", errors="replace")
        frontmatter = _read_frontmatter(index_note)
        if (
            frontmatter.get(CONCEPT_ROLE_KEY) != CONCEPT_ROLE_VALUE
            or frontmatter.get(CONCEPT_MARKER_KEY) != CONCEPT_MARKER_VALUE
        ):
            frontmatter[CONCEPT_ROLE_KEY] = CONCEPT_ROLE_VALUE
            frontmatter[CONCEPT_MARKER_KEY] = CONCEPT_MARKER_VALUE
            body = text
            if text.startswith("---"):
                parts = text.split("---", 2)
                body = parts[2].lstrip("\r\n") if len(parts) == 3 else ""
            rendered = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
            _write_text_atomic(index_note, f"---\n{rendered}\n---\n\n{body.rstrip()}\n")
            repairs.append(f"updated central concept role marker: {index_note}")

    if base_file.is_file():
        expected = vault_relative(concept_root / CARD_FOLDER, vault)
        text = base_file.read_text(encoding="utf-8-sig", errors="replace")
        pattern = re.compile(r'file\.folder\s*==\s*"[^"]+"')
        replacement = f'file.folder == "{expected}"'
        updated, count = pattern.subn(replacement, text, count=1)
        if count and updated != text:
            _write_text_atomic(base_file, updated)
            repairs.append(f"updated Base folder filter: {base_file}")
    return repairs


def confirm_manifest(manifest_path: str | Path, registry_path: str | Path | None = None) -> dict[str, Any]:
    manifest = _resolved(manifest_path)
    data = load_manifest(manifest)
    if data.get("errors"):
        raise RuntimeError("location manifest contains unresolved errors")
    locations = validate_manifest(data, require_confirmed=False)
    repairs = repair_concept_location_metadata(locations)
    registry = _resolved(registry_path or data.get("registry_path") or default_registry_path())
    confirmed_at = _now()
    data["status"] = "confirmed"
    data["confirmed_at"] = confirmed_at
    data["registry_path"] = str(registry)
    data["fingerprint"] = _path_fingerprint(locations)
    data["repairs"] = repairs
    if repairs:
        data["warnings"] = [
            warning
            for warning in data.get("warnings", [])
            if "role marker is missing" not in warning and "Base folder filter is stale" not in warning
        ]
    _write_text_atomic(manifest, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    registry_payload = {
        "schema_version": 1,
        "approved_at": confirmed_at,
        "locations": {name: str(path) for name, path in locations.items()},
    }
    _write_text_atomic(registry, yaml.safe_dump(registry_payload, allow_unicode=True, sort_keys=False))
    return data


def load_confirmed_locations(manifest_path: str | Path | None = None) -> dict[str, Path]:
    manifest = _resolved(manifest_path or default_manifest_path())
    return validate_manifest(load_manifest(manifest), require_confirmed=True)


def ensure_workspace_under_paper_root(workspace: str | Path, paper_root: Path) -> Path:
    resolved = _resolved(workspace)
    try:
        resolved.relative_to(paper_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"workspace is outside confirmed paper_root: {resolved}") from exc
    return resolved
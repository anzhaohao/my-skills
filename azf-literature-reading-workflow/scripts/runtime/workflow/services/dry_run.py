from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PlannedChange:
    action: str
    path: str
    reason: str
    will_overwrite: bool = False


@dataclass(slots=True)
class DryRunPlan:
    dry_run: bool = True
    changes: list[PlannedChange] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_change(self, action: str, path: Path, reason: str, will_overwrite: bool = False) -> None:
        self.changes.append(PlannedChange(action, str(path), reason, will_overwrite))

    def add_warning(self, warning: str) -> None:
        if warning not in self.warnings:
            self.warnings.append(warning)

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "changes": [asdict(change) for change in self.changes],
            "warnings": self.warnings,
        }


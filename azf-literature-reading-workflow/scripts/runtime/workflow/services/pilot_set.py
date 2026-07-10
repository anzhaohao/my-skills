from __future__ import annotations

from pathlib import Path


REQUIRED_CATEGORIES = {"normal", "two_column", "formula_heavy", "figure_table_heavy", "ocr_challenging"}


def validate_pilot_categories(category_map: dict[str, Path]) -> list[str]:
    missing = REQUIRED_CATEGORIES - set(category_map)
    issues = [f"missing pilot category: {item}" for item in sorted(missing)]
    for category, path in category_map.items():
        if not path.exists():
            issues.append(f"pilot workspace missing for {category}: {path}")
    return issues


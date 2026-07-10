from pathlib import Path

from workflow.services.pilot_set import validate_pilot_categories


def test_pilot_category_validator_reports_missing(tmp_path: Path) -> None:
    issues = validate_pilot_categories({"normal": tmp_path})
    assert any("two_column" in issue for issue in issues)


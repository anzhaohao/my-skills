from pathlib import Path

from workflow.validators.layout_sanity import simple_layout_sanity


def test_layout_sanity_flags_short_text(tmp_path: Path) -> None:
    parsed = tmp_path / "MinerU英文全文.md"
    parsed.write_text("too short", encoding="utf-8")
    status, notes = simple_layout_sanity(parsed)
    assert status == "suspect"
    assert notes


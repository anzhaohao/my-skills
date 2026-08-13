from pathlib import Path

from workflow.services.wikilinks import (
    path_qualified_wikilink_targets,
    short_wikilink,
    shorten_wikilink_targets,
    wikilink_targets,
)


def test_short_wikilink_uses_filename_only() -> None:
    link = short_wikilink(Path("附件/原文/【原文】测试论文.pdf"), "原文PDF")

    assert link == "[[【原文】测试论文.pdf|原文PDF]]"


def test_shorten_wikilinks_preserves_alias_and_anchor() -> None:
    source = "![[../附件/图片/Fig-01.png|图 1|650]] [[附件/原文/原文.pdf#page=2|原文]]"

    updated = shorten_wikilink_targets(source)

    assert updated == "![[Fig-01.png|图 1|650]] [[原文.pdf#page=2|原文]]"
    assert path_qualified_wikilink_targets(updated) == []
    assert wikilink_targets(updated) == ["Fig-01.png", "原文.pdf#page=2"]

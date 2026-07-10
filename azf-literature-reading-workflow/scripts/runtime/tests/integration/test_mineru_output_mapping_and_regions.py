from __future__ import annotations

import json
from pathlib import Path

from workflow.services.mineru_outputs import attach_mineru_outputs, find_mineru_auto_dir
from workflow.services.mineru_visual_crops import extract_regions


def test_attach_mineru_outputs_keeps_raw_and_images_outside_vault(tmp_path: Path) -> None:
    auto = tmp_path / "cache" / "paper" / "auto"
    auto.mkdir(parents=True)
    (auto / "paper.md").write_text("# parsed", encoding="utf-8")
    (auto / "paper_middle.json").write_text("{}", encoding="utf-8")
    (auto / "paper_content_list.json").write_text("[]", encoding="utf-8")
    (auto / "paper_content_list_v2.json").write_text("[]", encoding="utf-8")
    (auto / "images").mkdir()
    (auto / "images" / "fig.jpg").write_bytes(b"fake")

    source = tmp_path / "workspace" / "附件" / "原文"
    assert find_mineru_auto_dir(tmp_path / "cache") == auto
    mapped = attach_mineru_outputs(tmp_path / "cache", source)

    assert Path(mapped["markdown"] or "").name == "MinerU英文全文.md"
    assert Path(mapped["raw_output"] or "") == auto / "paper_middle.json"
    assert Path(mapped["images_dir"] or "") == auto / "images"
    assert not (source / "MinerU原始输出.json").exists()
    assert not (source / "MinerU_images").exists()


def test_extract_regions_prefers_mineru_visual_body_blocks(tmp_path: Path) -> None:
    raw = tmp_path / "MinerU原始输出.json"
    raw.write_text(
        json.dumps(
            {
                "pdf_info": [
                    {
                        "page_idx": 0,
                        "para_blocks": [
                            {"type": "image", "bbox": [1, 2, 3, 4]},
                            {"type": "image_body", "bbox": [10, 20, 110, 120]},
                            {"type": "table_body", "bbox": [30, 40, 130, 140]},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    regions = extract_regions(raw)

    assert [item.source_type for item in regions] == ["figure", "table"]
    assert [item.page_index for item in regions] == [0, 0]
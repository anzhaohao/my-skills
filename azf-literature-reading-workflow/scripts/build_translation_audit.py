from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sentence-count", type=int, required=True)
    parser.add_argument("--accounted-sentence-count", type=int, required=True)
    parser.add_argument("--omitted", action="append", default=[])
    parser.add_argument("--added-explanation", action="append", default=[])
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"source missing: {source}")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    passed = (
        args.source_sentence_count > 0
        and args.source_sentence_count == args.accounted_sentence_count
        and not args.omitted
        and not args.added_explanation
    )
    payload = {
        "mode": "faithful_sentence_by_sentence",
        "status": "pass" if passed else "fail",
        "source_sha256": digest,
        "source_sentence_count": args.source_sentence_count,
        "accounted_sentence_count": args.accounted_sentence_count,
        "omitted_source_sentences": args.omitted,
        "added_explanatory_passages": args.added_explanation,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
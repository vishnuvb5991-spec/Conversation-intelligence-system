"""Evaluate transcript accuracy and meeting-record quality from JSONL annotations.

Each line may contain: meeting_id, reference_transcript, hypothesis_transcript,
reference_rttm, hypothesis_rttm, reference_record, hypothesis_record.
RTTM paths are optional and may be relative to the manifest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


RUBRIC = """Score each dimension from 1 to 5 using these anchors:
1 = materially incorrect or missing; 2 = major omissions/errors; 3 = usable with clear gaps;
4 = accurate with only minor gaps; 5 = accurate, complete, and concise.
Dimensions: factuality, decision_coverage, action_item_quality, and completeness.
Only compare the hypothesis to the reference. Never reward unsupported claims.
Return JSON with integer scores, one short explanation per dimension, and an overall note."""


def _annotation(path: Path, uri: str):
    from pyannote.core import Annotation, Segment

    annotation = Annotation(uri=uri)
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] != "SPEAKER" or len(fields) < 8:
            continue
        start, duration = float(fields[3]), float(fields[4])
        annotation[Segment(start, start + duration)] = fields[7]
    return annotation


def _llm_judge(reference: dict[str, Any], hypothesis: dict[str, Any]) -> dict[str, Any] | None:
    import os
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": json.dumps({"reference": reference, "hypothesis": hypothesis}, ensure_ascii=False)},
        ],
    )
    return json.loads(response.choices[0].message.content or "{}")


def evaluate(path: Path, *, judge: bool) -> dict[str, Any]:
    import jiwer

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Manifest contains no evaluation rows.")
    wer_values: list[float] = []
    der_values: list[float] = []
    rubric_scores: dict[str, list[float]] = {key: [] for key in ("factuality", "decision_coverage", "action_item_quality", "completeness")}
    records = []

    for index, row in enumerate(rows, start=1):
        item: dict[str, Any] = {"meeting_id": row.get("meeting_id", str(index))}
        reference_transcript, hypothesis_transcript = row.get("reference_transcript"), row.get("hypothesis_transcript")
        if reference_transcript is not None and hypothesis_transcript is not None:
            item["wer"] = jiwer.wer(reference_transcript, hypothesis_transcript)
            wer_values.append(item["wer"])

        reference_rttm, hypothesis_rttm = row.get("reference_rttm"), row.get("hypothesis_rttm")
        if reference_rttm and hypothesis_rttm:
            from pyannote.metrics.diarization import DiarizationErrorRate
            base = path.parent
            reference = _annotation((base / reference_rttm).resolve(), item["meeting_id"])
            hypothesis = _annotation((base / hypothesis_rttm).resolve(), item["meeting_id"])
            item["der"] = DiarizationErrorRate()(reference, hypothesis)
            der_values.append(item["der"])

        if judge and row.get("reference_record") and row.get("hypothesis_record"):
            item["llm_judge"] = _llm_judge(row["reference_record"], row["hypothesis_record"])
            if item["llm_judge"]:
                for key in rubric_scores:
                    value = item["llm_judge"].get(key)
                    if isinstance(value, (int, float)):
                        rubric_scores[key].append(float(value))
        records.append(item)

    summary = {
        "meetings": len(rows),
        "mean_wer": mean(wer_values) if wer_values else None,
        "mean_der": mean(der_values) if der_values else None,
        "mean_llm_judge_scores": {key: mean(scores) if scores else None for key, scores in rubric_scores.items()},
    }
    return {"summary": summary, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Score conversation intelligence against human annotations.")
    parser.add_argument("manifest", type=Path, help="JSONL with human references and system outputs")
    parser.add_argument("--judge", action="store_true", help="Run the anchored OpenAI meeting-record rubric")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    result = evaluate(args.manifest, judge=args.judge)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()

import json
from pathlib import Path
from backend.repository import SearchRepository


def reciprocal_rank(expected: set[str], returned: list[str]) -> float:
    for index, item in enumerate(returned, 1):
        if item in expected:
            return 1 / index
    return 0.0


def main() -> None:
    repository = SearchRepository()
    cases = [json.loads(line) for line in Path("evals/questions.jsonl").read_text().splitlines() if line]
    recalls, mrrs = [], []
    for case in cases:
        results = repository.search(case["question"], case.get("sources", []), limit=10)
        returned = [result.document_id for result in results]
        expected = set(case["expected_document_ids"])
        recalls.append(len(expected & set(returned)) / len(expected))
        mrrs.append(reciprocal_rank(expected, returned))
    print(json.dumps({"cases": len(cases), "context_recall_at_10": round(sum(recalls) / len(recalls), 3), "mrr": round(sum(mrrs) / len(mrrs), 3)}, indent=2))


if __name__ == "__main__":
    main()

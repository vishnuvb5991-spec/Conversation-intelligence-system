import argparse
import json
from pathlib import Path
from .chunking import chunk_document
from .repository import SearchRepository
from .schemas import Document
from .seed import SEED_DOCUMENTS


def read_jsonl(path: Path) -> list[Document]:
    """Accept EnterpriseRAG-Bench exports after mapping common text fields."""
    documents = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        text = raw.get("text") or raw.get("content") or raw.get("body")
        if not text:
            raise ValueError(f"No text/content/body field on line {line_number}")
        documents.append(Document(
            id=str(raw.get("id", line_number)), source=raw.get("source", raw.get("source_type", "Unknown")),
            title=raw.get("title", "Untitled"), text=text, author=raw.get("author"), url=raw.get("url"),
            metadata=raw.get("metadata", {}),
        ))
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Index EnterpriseRAG-Bench or seed company documents")
    parser.add_argument("--input", type=Path, help="JSONL export with id, source, title, and text/content/body")
    args = parser.parse_args()
    documents = read_jsonl(args.input) if args.input else SEED_DOCUMENTS
    repository = SearchRepository()
    repository.ensure_collection()
    chunks = [chunk for document in documents for chunk in chunk_document(document)]
    repository.upsert(chunks)
    print(f"Indexed {len(documents)} documents as {len(chunks)} chunks")


if __name__ == "__main__":
    main()

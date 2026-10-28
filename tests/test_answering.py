from backend.answering import GroundedAnswerer
from backend.schemas import SearchResult


def test_fallback_answers_are_cited(monkeypatch):
    monkeypatch.setattr("backend.answering.settings.openai_api_key", None)
    result = SearchResult(
        id="chunk-1", document_id="document-1", source="Slack", title="Launch update",
        excerpt="The launch is planned for November 4.", score=0.9, author="Maya", chunk_index=0,
    )
    answer, citations, grounded, mode = GroundedAnswerer().answer("When is launch?", [result])
    assert "[1]" in answer
    assert citations[0].id == "chunk-1"
    assert grounded is True
    assert mode == "local-fallback"

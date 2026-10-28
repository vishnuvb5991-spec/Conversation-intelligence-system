from backend.chunking import chunk_document
from backend.schemas import Document


def test_chunking_preserves_source_and_overlap():
    document = Document(id="one", source="Slack", title="Test", text=" ".join(f"word{index}" for index in range(25)))
    chunks = chunk_document(document, size=10, overlap=2)
    assert len(chunks) == 3
    assert chunks[0].source == "Slack"
    assert "word8" in chunks[0].text and "word8" in chunks[1].text

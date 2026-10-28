from .schemas import Chunk, Document


def chunk_document(document: Document, size: int = 900, overlap: int = 120) -> list[Chunk]:
    """Split on word boundaries while retaining source and permission metadata."""
    words = document.text.split()
    if not words:
        return []
    chunks, start, index = [], 0, 0
    while start < len(words):
        selected = words[start:start + size]
        chunks.append(Chunk(
            id=f"{document.id}:{index}", document_id=document.id, source=document.source,
            title=document.title, text=" ".join(selected), author=document.author,
            url=document.url, chunk_index=index, metadata=document.metadata,
        ))
        if start + size >= len(words):
            break
        start += max(1, size - overlap)
        index += 1
    return chunks

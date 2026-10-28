import uuid
from qdrant_client import QdrantClient, models
from .config import settings
from .embeddings import Embedder
from .schemas import Chunk, SearchResult


class SearchRepository:
    def __init__(self, client: QdrantClient | None = None, embedder: Embedder | None = None):
        self.client = client or QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self.embedder = embedder or Embedder()

    def ensure_collection(self) -> None:
        if self.client.collection_exists(settings.qdrant_collection):
            return
        self.client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config={"dense": models.VectorParams(size=settings.dense_dimensions, distance=models.Distance.COSINE)},
            sparse_vectors_config={"sparse": models.SparseVectorParams()},
        )

    def upsert(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        dense = self.embedder.embed([chunk.text for chunk in chunks])
        self.client.upsert(settings.qdrant_collection, points=[models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.id)),
            vector={"dense": dense[index], "sparse": models.SparseVector(**self.embedder.sparse(chunk.text))},
            payload=chunk.model_dump(),
        ) for index, chunk in enumerate(chunks)])

    def count(self) -> int:
        return self.client.count(settings.qdrant_collection, exact=True).count

    def search(self, query: str, sources: list[str], limit: int) -> list[SearchResult]:
        query_filter = models.Filter(must=[models.FieldCondition(key="source", match=models.MatchAny(any=sources))]) if sources else None
        dense, sparse = self.embedder.embed([query])[0], self.embedder.sparse(query)
        points = self.client.query_points(
            collection_name=settings.qdrant_collection,
            prefetch=[
                models.Prefetch(query=dense, using="dense", filter=query_filter, limit=limit * 3),
                models.Prefetch(query=models.SparseVector(**sparse), using="sparse", filter=query_filter, limit=limit * 3),
            ], query=models.FusionQuery(fusion=models.Fusion.RRF), limit=limit,
        ).points
        return [SearchResult(
            id=str(point.id), score=round(point.score, 4), document_id=point.payload["document_id"],
            source=point.payload["source"], title=point.payload["title"], excerpt=point.payload["text"],
            author=point.payload.get("author"), url=point.payload.get("url"), chunk_index=point.payload["chunk_index"],
        ) for point in points]

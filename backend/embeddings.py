import hashlib
import math
import re
from openai import OpenAI
from .config import settings


class Embedder:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.client:
            response = self.client.embeddings.create(model=settings.embedding_model, input=texts, dimensions=settings.dense_dimensions)
            return [item.embedding for item in response.data]
        return [self._deterministic_embedding(text) for text in texts]

    @staticmethod
    def sparse(text: str) -> dict[str, list[int] | list[float]]:
        counts: dict[int, int] = {}
        for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
            index = int(hashlib.sha1(token.encode()).hexdigest()[:8], 16) % 1_000_000
            counts[index] = counts.get(index, 0) + 1
        return {"indices": list(counts), "values": [float(value) for value in counts.values()]}

    @staticmethod
    def _deterministic_embedding(text: str) -> list[float]:
        values = [0.0] * settings.dense_dimensions
        for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % settings.dense_dimensions
            values[index] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

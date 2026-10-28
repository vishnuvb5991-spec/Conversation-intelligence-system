from cohere import ClientV2
from .config import settings
from .schemas import SearchResult


def rerank(query: str, results: list[SearchResult]) -> list[SearchResult]:
    if not settings.cohere_api_key or len(results) < 2:
        return results
    client = ClientV2(api_key=settings.cohere_api_key)
    try:
        response = client.rerank(model="rerank-v3.5", query=query, documents=[result.excerpt for result in results], top_n=len(results))
        return [results[item.index].model_copy(update={"score": round(item.relevance_score, 4)}) for item in response.results]
    except Exception:
        return results

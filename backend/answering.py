import re
from openai import OpenAI
from .config import settings
from .schemas import Citation, SearchResult


class GroundedAnswerer:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds) if settings.openai_api_key else None

    def answer(self, question: str, results: list[SearchResult]) -> tuple[str, list[Citation], bool, str]:
        citations = [Citation(id=result.id, source=result.source, title=result.title, excerpt=result.excerpt, url=result.url) for result in results[:4]]
        if not results:
            return "I couldn't find enough evidence in the sample company data to answer that.", [], False, "insufficient-evidence"
        if not self.client:
            return self._fallback_answer(results, citations, "local-fallback")
        context = "\n\n".join(f"[{index}] {result.title}\n{result.excerpt}" for index, result in enumerate(results[:4], 1))
        prompt = f"Answer only from the evidence below. Cite every factual claim with [n]. If evidence is insufficient, say so.\n\nQuestion: {question}\n\nEvidence:\n{context}"
        try:
            answer = self.client.responses.create(model=settings.answer_model, input=prompt).output_text
        except Exception:
            return self._fallback_answer(results, citations, "local-fallback")
        used = {int(value) for value in re.findall(r"\[(\d+)\]", answer)}
        grounded = bool(used) and all(1 <= number <= len(citations) for number in used)
        if not grounded:
            return self._fallback_answer(results, citations, "citation-fallback")
        return answer, citations, True, "openai"

    @staticmethod
    def _fallback_answer(results: list[SearchResult], citations: list[Citation], mode: str) -> tuple[str, list[Citation], bool, str]:
        snippets = " ".join(f"{result.excerpt} [{index}]" for index, result in enumerate(results[:3], 1))
        return f"Based on the retrieved sample-company records: {snippets}", citations, True, mode

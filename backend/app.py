from collections import defaultdict, deque
from contextlib import asynccontextmanager
from time import monotonic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .answering import GroundedAnswerer
from .repository import SearchRepository
from .rerank import rerank
from .schemas import AnswerResponse, SearchRequest
from .chunking import chunk_document
from .config import settings
from .seed import SEED_DOCUMENTS

repository = SearchRepository()
answerer = GroundedAnswerer()
request_windows: dict[str, deque[float]] = defaultdict(deque)
startup_error: str | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global startup_error
    try:
        repository.ensure_collection()
        if settings.auto_seed_demo and repository.count() == 0:
            chunks = [chunk for document in SEED_DOCUMENTS for chunk in chunk_document(document, settings.chunk_size, settings.chunk_overlap)]
            repository.upsert(chunks)
    except Exception as error:
        startup_error = type(error).__name__
    yield


app = FastAPI(title="Relay Enterprise Search", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok" if startup_error is None else "degraded", "demo": settings.public_demo, "search_ready": startup_error is None}


def enforce_rate_limit(request: Request) -> None:
    address = request.client.host if request.client else "unknown"
    now = monotonic()
    window = request_windows[address]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Demo request limit reached. Please try again in a minute.")
    window.append(now)


@app.post("/api/search", response_model=AnswerResponse)
def search(request: SearchRequest, raw_request: Request) -> AnswerResponse:
    enforce_rate_limit(raw_request)
    if startup_error is not None:
        raise HTTPException(status_code=503, detail="The demo search service is waking up. Please retry in a moment.")
    try:
        results = rerank(request.query, repository.search(request.query, request.sources, request.limit))
    except Exception as error:
        raise HTTPException(status_code=503, detail="The demo search service is temporarily unavailable. Please retry shortly.") from error
    answer, citations, grounded, mode = answerer.answer(request.query, results)
    notice = "Using a deterministic demo fallback while the hosted AI provider is unavailable." if mode.endswith("fallback") else None
    return AnswerResponse(answer=answer, citations=citations, results=results, grounded=grounded, mode=mode, notice=notice)


app.mount("/", StaticFiles(directory="dist", html=True), name="ui")

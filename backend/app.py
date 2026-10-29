from __future__ import annotations

import base64
import asyncio
from binascii import Error as Base64Error
from contextlib import asynccontextmanager
from hmac import compare_digest
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.staticfiles import StaticFiles

from .config import settings
from .pipeline import process_meeting
from .schemas import MeetingRecord

MAX_AUDIO_BYTES = settings.max_audio_mb * 1024 * 1024
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".flac", ".ogg"}
meetings: dict[str, MeetingRecord] = {}
request_windows: dict[str, deque[float]] = defaultdict(deque)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.require_access_auth and not (settings.relay_access_username and settings.relay_access_password):
        raise RuntimeError("Access authentication is enabled but credentials are missing")
    yield


app = FastAPI(title="Converse Intelligence", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def protect_app(request: Request, call_next):
    if settings.require_access_auth and request.url.path != "/health":
        authorization = request.headers.get("authorization", "")
        username = password = ""
        if authorization.startswith("Basic "):
            try:
                username, _, password = base64.b64decode(authorization[6:], validate=True).decode().partition(":")
            except (Base64Error, UnicodeDecodeError):
                pass
        if not (compare_digest(username, settings.relay_access_username or "") and compare_digest(password, settings.relay_access_password or "")):
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Converse Intelligence"'})

    response = await call_next(request)
    response.headers.update({
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    })
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def enforce_rate_limit(request: Request) -> None:
    address = request.client.host if request.client else "unknown"
    now = monotonic()
    window = request_windows[address]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Upload limit reached. Try again in a minute.")
    window.append(now)


@app.get("/api/meetings", response_model=list[MeetingRecord])
def list_meetings() -> list[MeetingRecord]:
    return list(reversed(meetings.values()))


@app.get("/api/meetings/{meeting_id}", response_model=MeetingRecord)
def get_meeting(meeting_id: str) -> MeetingRecord:
    meeting = meetings.get(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found. Process an audio file to create one.")
    return meeting


@app.post("/api/meetings", response_model=MeetingRecord)
async def create_meeting(request: Request, audio: UploadFile = File(...)) -> MeetingRecord:
    enforce_rate_limit(request)
    extension = Path(audio.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Upload WAV, MP3, M4A, MP4, WebM, FLAC, or OGG audio.")

    contents = await audio.read(MAX_AUDIO_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded audio file is empty.")
    if len(contents) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail=f"Audio uploads are limited to {settings.max_audio_mb} MB.")

    meeting_id = str(uuid4())
    safe_name = Path(audio.filename or "meeting").name[:120]
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(prefix="conversation-", suffix=extension, delete=False) as temporary_audio:
            temporary_audio.write(contents)
            temporary_path = Path(temporary_audio.name)
        meeting = await asyncio.to_thread(process_meeting, meeting_id, safe_name, contents, audio.content_type or "application/octet-stream", str(temporary_path))
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Meeting processing failed ({type(error).__name__}). Check provider configuration and try again.") from error
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)

    meetings[meeting_id] = meeting
    while len(meetings) > 20:
        del meetings[next(iter(meetings))]
    return meeting


app.mount("/", StaticFiles(directory="dist", html=True), name="ui")

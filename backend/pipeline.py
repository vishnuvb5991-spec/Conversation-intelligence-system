from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import settings
from .schemas import ActionItem, Decision, MeetingRecord, TranscriptTurn


def _deepgram_transcribe(audio: bytes, content_type: str) -> dict[str, Any]:
    if not settings.deepgram_api_key:
        raise ValueError("Add DEEPGRAM_API_KEY in the server environment to transcribe meeting audio.")
    query = urlencode({"model": "nova-3", "smart_format": "true", "punctuate": "true", "utterances": "true"})
    request = Request(
        f"https://api.deepgram.com/v1/listen?{query}",
        data=audio,
        headers={"Authorization": f"Token {settings.deepgram_api_key}", "Content-Type": content_type},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read())
    except HTTPError as error:
        detail = error.read(512).decode("utf-8", "replace")
        raise ValueError(f"Deepgram transcription failed (HTTP {error.code}): {detail}") from error
    except (URLError, TimeoutError) as error:
        raise ValueError("Deepgram could not be reached. Check the service and retry.") from error


def _diarize(audio_path: str) -> list[tuple[float, float, str]]:
    if not settings.diarization_enabled:
        return []
    if not settings.hf_token:
        return []
    try:
        from pyannote.audio import Pipeline
    except ImportError as error:
        raise ValueError("Install requirements-diarization.txt to use pyannote speaker diarization.") from error

    pipeline = Pipeline.from_pretrained(settings.diarization_model, token=settings.hf_token)
    result = pipeline(audio_path)
    annotation = getattr(result, "speaker_diarization", result)
    segments = []
    for segment, _, speaker in annotation.itertracks(yield_label=True):
        segments.append((float(segment.start), float(segment.end), str(speaker)))
    return segments


def _overlap_speaker(start: float, end: float, segments: list[tuple[float, float, str]]) -> str | None:
    midpoint = (start + end) / 2
    matching = [(max(0.0, min(end, seg_end) - max(start, seg_start)), speaker) for seg_start, seg_end, speaker in segments]
    if not matching:
        return None
    overlap, speaker = max(matching)
    if overlap > 0 or any(seg_start <= midpoint <= seg_end and label == speaker for seg_start, seg_end, label in segments):
        return speaker
    return None


def _turns_from_words(words: list[dict[str, Any]], diarization: list[tuple[float, float, str]]) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    current: dict[str, Any] | None = None
    for word in words:
        text = str(word.get("punctuated_word") or word.get("word") or "").strip()
        if not text:
            continue
        start, end = float(word.get("start", 0)), float(word.get("end", 0))
        speaker = _overlap_speaker(start, end, diarization)
        confidence = word.get("confidence")
        pause = start - current["end"] if current else 0
        boundary = current is None or speaker != current["speaker"] or pause > 0.8 or bool(re.search(r"[.!?]$", current["text"]))
        if boundary:
            if current:
                turns.append(TranscriptTurn(**current))
            current = {"start": start, "end": end, "speaker": speaker, "text": text, "confidence": confidence}
        else:
            current["end"] = end
            current["text"] += f" {text}"
            if confidence is not None:
                current["confidence"] = min(float(current["confidence"]), float(confidence)) if current["confidence"] is not None else float(confidence)
    if current:
        turns.append(TranscriptTurn(**current))
    return turns


def _summarize(transcript: str, turns: list[TranscriptTurn]) -> dict[str, Any]:
    if not settings.openai_api_key:
        excerpt = re.split(r"(?<=[.!?])\s+", transcript.strip())
        return {
            "summary": [sentence[:350] for sentence in excerpt[:3] if sentence],
            "decisions": [],
            "action_items": [],
            "open_questions": [],
        }

    from openai import OpenAI

    speaker_transcript = "\n".join(f"{turn.speaker or 'Speaker unknown'}: {turn.text}" for turn in turns)
    prompt = (
        "Extract a concise, evidence-grounded meeting record as JSON. Do not invent owners, dates, decisions, or tasks. "
        "Use null when owner or due_date is not explicit. Return keys summary (array of short strings), "
        "decisions (array of {decision,evidence}), action_items (array of {task,owner,due_date,evidence}), "
        "open_questions (array of strings). Keep evidence as a short exact quote from the transcript.\n\n"
        f"Transcript:\n{speaker_transcript or transcript}"
    )
    response = OpenAI(api_key=settings.openai_api_key, timeout=45).chat.completions.create(
        model=settings.openai_summary_model,
        messages=[{"role": "system", "content": "You create accurate, cautious meeting records."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def process_meeting(meeting_id: str, filename: str, audio: bytes, content_type: str, audio_path: str) -> MeetingRecord:
    response = _deepgram_transcribe(audio, content_type)
    result = response.get("results", {})
    channel = (result.get("channels") or [{}])[0]
    alternative = (channel.get("alternatives") or [{}])[0]
    transcript = str(alternative.get("transcript") or "").strip()
    if not transcript:
        raise ValueError("Deepgram returned no speech transcript for this file.")
    words = alternative.get("words") or []
    warnings: list[str] = []
    diarization: list[tuple[float, float, str]] = []
    if settings.diarization_enabled and settings.hf_token:
        diarization = _diarize(audio_path)
    else:
        warnings.append("Speaker labels are unavailable. Configure HF_TOKEN and accept the pyannote Community-1 model terms to enable diarization.")

    turns = _turns_from_words(words, diarization)
    if not turns:
        utterances = result.get("utterances") or []
        turns = [TranscriptTurn(start=float(item.get("start", 0)), end=float(item.get("end", 0)), text=str(item.get("transcript", ""))) for item in utterances]

    try:
        record = _summarize(transcript, turns)
    except Exception as error:
        warnings.append(f"Structured summary is unavailable ({type(error).__name__}); transcript and diarization were retained.")
        record = {"summary": [transcript[:350]], "decisions": [], "action_items": [], "open_questions": []}

    duration = float((response.get("metadata") or {}).get("duration") or max((turn.end for turn in turns), default=0))
    return MeetingRecord(
        id=meeting_id,
        title=filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
        created_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration,
        language=alternative.get("languages", [None])[0] if alternative.get("languages") else alternative.get("detected_language"),
        transcript=transcript,
        turns=turns,
        summary=record.get("summary") or [],
        decisions=[Decision(**item) for item in record.get("decisions", []) if isinstance(item, dict) and item.get("decision")],
        action_items=[ActionItem(**item) for item in record.get("action_items", []) if isinstance(item, dict) and item.get("task")],
        open_questions=[str(item) for item in record.get("open_questions", [])],
        providers={"transcription": "Deepgram Nova-3", "diarization": "pyannote Community-1" if diarization else "not configured", "summary": "OpenAI" if settings.openai_api_key else "transcript-only fallback"},
        warnings=warnings,
    )

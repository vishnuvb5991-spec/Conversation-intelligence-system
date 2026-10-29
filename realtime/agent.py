"""Optional LiveKit room worker for live note-taking and spoken summaries."""
from __future__ import annotations

import json
import logging
import os
import time

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext
from livekit.plugins import deepgram, elevenlabs, openai

logger = logging.getLogger("conversation-intelligence.realtime")
turn_started_at: float | None = None
first_output_reported = False


def configure_phoenix() -> None:
    endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
    if not endpoint:
        return
    from phoenix.otel import register
    from openinference.instrumentation.openai import OpenAIInstrumentor

    provider = register(project_name="conversation-intelligence", endpoint=endpoint)
    OpenAIInstrumentor().instrument(tracer_provider=provider)


class MeetingNotesAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=(
            "You are a quiet meeting-notes assistant in a live meeting room. Listen carefully, "
            "attribute comments to the available speaker labels, and do not interrupt. Respond "
            "only when directly asked or when someone asks for a recap. Keep spoken responses "
            "brief. Distinguish proposals from confirmed decisions and never invent action owners or dates."
        ))


async def entrypoint(ctx: JobContext) -> None:
    global turn_started_at, first_output_reported
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", enable_diarization=True),
        llm=openai.LLM(model=os.getenv("REALTIME_LLM_MODEL", "gpt-4o-mini")),
        tts=elevenlabs.TTS(
            model=os.getenv("ELEVENLABS_TTS_MODEL", "eleven_v3_conversational"),
            voice_id=os.environ["ELEVENLABS_VOICE_ID"],
        ),
    )

    @session.on("user_state_changed")
    def on_user_state_changed(event) -> None:
        global turn_started_at, first_output_reported
        if str(event.new_state) == "speaking":
            turn_started_at = time.perf_counter()
            first_output_reported = False

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event) -> None:
        if not event.is_final:
            return
        words = len((event.transcript or "").split())
        logger.info(json.dumps({"metric": "transcript_words", "words": words, "speaker": event.speaker_id, "language": event.language}))

    @session.on("agent_state_changed")
    def on_agent_state_changed(event) -> None:
        global first_output_reported
        if str(event.new_state) == "speaking" and turn_started_at and not first_output_reported:
            first_output_reported = True
            logger.info(json.dumps({"metric": "time_to_first_output_seconds", "value": round(time.perf_counter() - turn_started_at, 3)}))

    @session.on("metrics_collected")
    def on_metrics_collected(event) -> None:
        metric = event.metrics
        # LiveKit reports model timing for streamed LLM/TTS work. TTS ttfb is the
        # time-to-first-audio measurement; ttft is the LLM time-to-first-token.
        values = {name: getattr(metric, name, None) for name in ("ttft", "ttfb", "audio_duration", "duration", "request_duration")}
        values = {key: round(value, 4) if isinstance(value, (float, int)) else value for key, value in values.items() if value is not None}
        if values:
            logger.info(json.dumps({"metric": "provider_timing", "type": type(metric).__name__, **values}))

    await session.start(room=ctx.room, agent=MeetingNotesAgent())
    await session.generate_reply(instructions="Join quietly and introduce yourself in one short sentence as the meeting notes assistant.")


if __name__ == "__main__":
    configure_phoenix()
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

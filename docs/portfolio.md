# Conversation intelligence portfolio kit

## Portfolio description

**Converse — conversation intelligence** turns meeting recordings into speaker-attributed transcripts, concise summaries, decisions, and action items. The batch pipeline uses Deepgram Nova-3 and pyannote Community-1, with an optional LiveKit real-time voice agent and Eleven v3 Conversational speech.

**Stack:** FastAPI, Deepgram, pyannote.audio, OpenAI, LiveKit Agents/Cloud, ElevenLabs, Docker, Render, Vite, Arize Phoenix.

- Live demo: [Conversation intelligence](https://relay-enterprise-search.onrender.com)
- GitHub: `https://github.com/vishnuvb5991-spec/relay-enterprise-search`

## Resume bullets

- Built an audio-to-record pipeline that combines Deepgram Nova-3 word timing with pyannote Community-1 speaker segments to produce speaker-attributed meeting transcripts.
- Generated evidence-linked summaries, decisions, open questions, and action items with owner/date extraction that avoids inventing details absent from the conversation.
- Added WER, DER, an anchored LLM-judge rubric, and optional LiveKit timing metrics for first token, first audio, and response latency.

## Two-minute demo script

1. Upload a short meeting recording and explain that the audio file is temporary.
2. Show the speaker-labeled, timestamped transcript.
3. Walk through the summary and separate decisions from next actions.
4. Show the transcript quote that supports an action item.
5. Explain WER for transcription, DER for speaker attribution, and the anchored rubric for record quality.
6. Describe the optional LiveKit worker and its first-token/first-audio timing metrics.

## Interview prompts

| Question | Concise answer |
| --- | --- |
| How do you prevent invented action items? | The extraction prompt requires short transcript evidence and uses null for owners or due dates that are not stated. |
| How is diarization evaluated? | DER compares reference and hypothesis speaker-time annotations; WER separately measures transcript word errors. |
| Why keep AMI recordings out of Git? | The corpus is real recorded speech with human annotations; evaluation data stays local and follows its access terms. |
| What would change for production? | Add durable encrypted record storage, retention controls, consent/notice flows, tenant isolation, and monitored worker queues. |

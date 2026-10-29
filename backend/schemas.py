from pydantic import BaseModel, Field


class TranscriptTurn(BaseModel):
    start: float
    end: float
    speaker: str | None = None
    text: str
    confidence: float | None = None


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    due_date: str | None = None
    evidence: str | None = None


class Decision(BaseModel):
    decision: str
    evidence: str | None = None


class MeetingRecord(BaseModel):
    id: str
    title: str
    created_at: str
    duration_seconds: float
    language: str | None = None
    transcript: str
    turns: list[TranscriptTurn] = Field(default_factory=list)
    summary: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    providers: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    deepgram_api_key: str | None = None
    hf_token: str | None = None
    openai_api_key: str | None = None
    openai_summary_model: str = "gpt-4.1-mini"
    require_access_auth: bool = False
    relay_access_username: str | None = None
    relay_access_password: str | None = None
    max_audio_mb: int = 50
    rate_limit_per_minute: int = 5
    diarization_enabled: bool = True
    diarization_model: str = "pyannote/speaker-diarization-community-1"


settings = Settings()

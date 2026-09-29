"""Validated orchestrator and DSH runtime configuration."""

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings loaded once during application startup."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field("127.0.0.1", validation_alias="AGENT_HOST")
    port: int = Field(8080, ge=1, le=65535, validation_alias="AGENT_PORT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    gemini_api_key: SecretStr = Field(validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-3.6-flash", validation_alias="GEMINI_MODEL")
    mcp_url: str = Field("http://127.0.0.1:8000/mcp", validation_alias="MCP_URL")
    database_url: SecretStr | None = Field(None, validation_alias="DATABASE_URL")
    dsh_bin: str = Field("dsh", validation_alias="DSH_BIN")
    dsh_document_home: Path = Field(
        Path("/data/dsh/documenter"), validation_alias="DSH_DOCUMENT_HOME"
    )
    dsh_knowledge_home: Path = Field(
        Path("/data/dsh/knowledge"), validation_alias="DSH_KNOWLEDGE_HOME"
    )
    dsh_working_dir: Path = Field(Path("/app"), validation_alias="DSH_WORKING_DIR")
    dsh_max_tokens: int = Field(
        16_384, ge=1_024, le=65_536, validation_alias="DSH_MAX_TOKENS"
    )
    dsh_request_timeout_seconds: float = Field(
        600, ge=10, le=3_600, validation_alias="DSH_REQUEST_TIMEOUT_SECONDS"
    )

    @field_validator("gemini_api_key")
    @classmethod
    def validate_api_key(cls, value: SecretStr) -> SecretStr:
        if value.get_secret_value() in {"", "replace_me"}:
            raise ValueError("GEMINI_API_KEY must be configured")
        return value

    @field_validator("mcp_url")
    @classmethod
    def validate_mcp_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("MCP_URL must be an HTTP(S) URL")
        return value

    @field_validator("gemini_model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("GEMINI_MODEL may not be empty")
        return value

from pathlib import Path

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field("127.0.0.1", validation_alias="AGENT_HOST")
    port: int = Field(8080, ge=1, le=65535, validation_alias="AGENT_PORT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    gemini_api_key: SecretStr = Field(min_length=1, validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        "gemini-3.6-flash", min_length=1, validation_alias="GEMINI_MODEL"
    )
    mcp_url: AnyHttpUrl = Field(
        "http://127.0.0.1:8000/mcp", validation_alias="MCP_URL"
    )
    dsh_bin: str = Field("/usr/local/bin/dsh", validation_alias="DSH_BIN")
    dsh_home: Path = Field(Path(".dsh"), validation_alias="DSH_HOME")
    dsh_workspace: Path = Field(Path("."), validation_alias="DSH_WORKSPACE")
    dsh_max_tokens: int = Field(16_384, gt=0, validation_alias="DSH_MAX_TOKENS")
    dsh_timeout: float = Field(
        600, gt=0, validation_alias="DSH_REQUEST_TIMEOUT_SECONDS"
    )

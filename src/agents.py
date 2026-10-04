import asyncio
import hashlib

from deepseek_harness import DeepSeekHarness, RunResult

from config import Settings


class DshAgent:
    def __init__(self, role: str, system_prompt: str, settings: Settings) -> None:
        home = settings.dsh_home / role
        home.mkdir(parents=True, exist_ok=True)
        self._role = role
        self._lock = asyncio.Lock()
        self._harness = DeepSeekHarness(
            provider="google",
            model=settings.gemini_model,
            max_tokens=settings.dsh_max_tokens,
            cwd=str(settings.dsh_workspace.resolve()),
            dsh_bin=settings.dsh_bin,
            profile="project-docs",
            dsh_home=str(home.resolve()),
            env={
                "GEMINI_API_KEY": settings.gemini_api_key.get_secret_value(),
                "GEMINI_MODEL": settings.gemini_model,
                "MCP_URL": str(settings.mcp_url),
                "DSH_SYSTEM_PROMPT": system_prompt,
            },
            request_timeout_seconds=settings.dsh_timeout,
        )

    async def start(self) -> None:
        await asyncio.to_thread(self._harness.start)

    async def close(self) -> None:
        await asyncio.to_thread(self._harness.close)

    async def run(self, prompt: str, thread_id: str, project_id: str) -> RunResult:
        session_id = self._session_id(thread_id, project_id)
        async with self._lock:
            result = await asyncio.to_thread(
                self._harness.run, prompt, session_id=session_id
            )
        if not result.final_response.strip():
            raise RuntimeError(f"{self._role} agent completed without a final response")
        return result

    def _session_id(self, thread_id: str, project_id: str) -> str:
        digest = hashlib.sha256(f"{project_id}\0{thread_id}".encode()).hexdigest()[:24]
        return f"{self._role}-{digest}"

"""DeepSeek Harness adapter used by LangGraph nodes."""

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from config import Settings


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Provider-neutral result of one DSH agent turn."""

    answer: str
    finish_reason: str | None
    session_id: str


class AgentRunner(Protocol):
    """Async capability consumed by workflow nodes."""

    async def run(self, prompt: str, thread_id: str, project_id: str) -> AgentResult:
        """Run one turn in a stable role session."""


class DshAgentRunner:
    """Serialize turns through one long-lived synchronous DSH SDK runtime."""

    def __init__(
        self, role: str, system_prompt: str, home: Path, settings: Settings
    ) -> None:
        from deepseek_harness import DeepSeekHarness

        home.mkdir(parents=True, exist_ok=True)
        settings.dsh_working_dir.mkdir(parents=True, exist_ok=True)
        self._role = role
        self._lock = asyncio.Lock()
        self._harness = DeepSeekHarness(
            provider="google",
            model=settings.gemini_model,
            max_tokens=settings.dsh_max_tokens,
            cwd=str(settings.dsh_working_dir),
            runtime_cwd=str(settings.dsh_working_dir),
            dsh_bin=settings.dsh_bin,
            profile="project-docs",
            dsh_home=str(home.resolve()),
            env={
                "GEMINI_API_KEY": settings.gemini_api_key.get_secret_value(),
                "GEMINI_MODEL": settings.gemini_model,
                "MCP_URL": settings.mcp_url,
                "DSH_SYSTEM_PROMPT": system_prompt,
            },
            request_timeout_seconds=settings.dsh_request_timeout_seconds,
        )

    async def start(self) -> None:
        """Start the child runtime and validate provider and MCP readiness."""
        await asyncio.to_thread(self._harness.start)

    async def close(self) -> None:
        """Flush and stop the owned child runtime."""
        await asyncio.to_thread(self._harness.close)

    async def run(self, prompt: str, thread_id: str, project_id: str) -> AgentResult:
        """Run one role-scoped turn without blocking the FastAPI event loop."""
        session_id = self._session_id(thread_id, project_id)
        async with self._lock:
            result = await asyncio.to_thread(
                self._harness.run, prompt, session_id=session_id
            )
        if not result.final_response.strip():
            raise RuntimeError(f"{self._role} agent completed without a final response")
        return AgentResult(
            answer=result.final_response,
            finish_reason=result.finish_reason,
            session_id=result.session_id,
        )

    def _session_id(self, thread_id: str, project_id: str) -> str:
        digest = hashlib.sha256(f"{project_id}\0{thread_id}".encode()).hexdigest()[:24]
        return f"{self._role}-{digest}"


class AgentRuntime:
    """Own exactly the documenter and knowledge DSH runtimes."""

    def __init__(self, documenter: DshAgentRunner, knowledge: DshAgentRunner) -> None:
        self.documenter = documenter
        self.knowledge = knowledge
        self._started = False

    async def start(self) -> None:
        """Start both runtimes and roll back if either fails."""
        try:
            await asyncio.gather(self.documenter.start(), self.knowledge.start())
        except BaseException:
            await asyncio.gather(
                self.documenter.close(),
                self.knowledge.close(),
                return_exceptions=True,
            )
            raise
        self._started = True

    async def close(self) -> None:
        """Stop both runtimes; all errors are allowed to settle."""
        await asyncio.gather(
            self.documenter.close(),
            self.knowledge.close(),
            return_exceptions=True,
        )
        self._started = False

    @property
    def ready(self) -> bool:
        return self._started

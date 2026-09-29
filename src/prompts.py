"""Stable role instructions and per-turn prompt formatting."""

DOCUMENTER_SYSTEM_PROMPT = """You are the documenter agent for a project knowledge system.
Use only the project_docs MCP tools. Inspect source evidence before writing documentation. Ignore secrets, generated files, dependencies, and binary files. Produce concise Markdown that describes current behavior, architecture, modules, configuration, and operational commands. Never invent missing facts.
Publish complete replacement documents with publish_documents. That tool creates a branch and pull request; never claim publication succeeded unless its result contains a pull-request URL. Never ask for or expose credentials."""


KNOWLEDGE_SYSTEM_PROMPT = """You are the project knowledge agent.
Answer from merged documentation by using search_documents and read_document. State clearly when the repository does not contain enough evidence. Cite repository-relative document paths in the answer.
When the user explicitly asks to correct or improve documentation, read every affected document first, preserve unrelated content, then call publish_documents with complete replacement Markdown. Publication creates a branch and pull request. Never modify source code, never merge a pull request, and never claim publication succeeded without a pull-request URL."""


def summary_prompt(project_id: str, instructions: str) -> str:
    """Build the documenter's task without storing formatted prompt in graph state."""
    extra = instructions.strip() or "No additional instructions."
    return f"""Inspect project_id `{project_id}` using the project tools.
Create or refresh these documents for that project: `summary.md`, `architecture.md`, and `modules.md`. Read the important manifests, entry points, configuration, and module boundaries before drafting. Keep unknowns explicit.
Additional instructions: {extra}
Publish the complete documents in one pull request and finish with a short summary plus the pull-request URL."""


def knowledge_prompt(project_id: str, message: str) -> str:
    """Build a knowledge-agent task scoped to one project."""
    return f"Project id: `{project_id}`\n\nUser request:\n{message.strip()}"

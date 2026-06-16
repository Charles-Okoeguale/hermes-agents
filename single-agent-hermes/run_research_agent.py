"""Entry point — runs the Hermes research agent.

web_search and web_extract are Hermes built-ins (backed by TAVILY_API_KEY).
save_note is our one custom tool, registered via .hermes/plugins/research/.

Run:  python run_research_agent.py "your research question"
"""

import os
import sys

from dotenv import load_dotenv

# Load .env before anything else so keys are available when Hermes initialises.
load_dotenv()

# Project-local plugins (./.hermes/plugins) are opt-in; enable them before import.
os.environ.setdefault("HERMES_ENABLE_PROJECT_PLUGINS", "true")

from run_agent import AIAgent  # noqa: E402 — must come after env vars are set
from hermes_state import SessionDB  # noqa: E402 — Hermes' SQLite session store

SYSTEM_PROMPT = (
    "You are a research assistant. When asked a question, use web_search to find "
    "sources, use web_extract to read the most relevant ones in full, then write "
    "a clear cited summary. Always finish by calling save_note to record your "
    "findings, including the source URLs."
)


def main():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = "What are the headline new features in Python 3.13?"

    agent = AIAgent(
        model=os.getenv("HERMES_MODEL", "anthropic/claude-sonnet-4.6"),
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        quiet_mode=False,
        # Pass Hermes' SQLite session store so the conversation persists to
        # ~/.hermes/state.db. Without this, AIAgent runs stateless — the bare
        # library class defaults session_db=None and skips all persistence.
        session_db=SessionDB(),
    )
    result = agent.run_conversation(
        user_message=question,
        system_message=SYSTEM_PROMPT,
        task_id="research-1",
    )
    print("\n=== FINAL ANSWER ===\n")
    print(result["final_response"])


if __name__ == "__main__":
    main()



















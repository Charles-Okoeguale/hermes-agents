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

# Name of our project plugin (folder ./.hermes/plugins/research/) and the
# toolset it registers save_note under.
PLUGIN_NAME = "research"

SYSTEM_PROMPT = (
    "You are a research assistant. When asked a question, use web_search to find "
    "sources, use web_extract to read the most relevant ones in full, then write "
    "a clear cited summary. Always finish by calling save_note to record your "
    "findings, including the source URLs."
)


def _activate_research_plugin():
    """Make the save_note custom tool live before the agent starts.

    Hermes discovers project plugins (./.hermes/plugins/) only when
    HERMES_ENABLE_PROJECT_PLUGINS is set AND the plugin is on the
    `plugins.enabled` allow-list in $HERMES_HOME/config.yaml — plugins are
    opt-in by design. The bare AIAgent library class never runs the CLI's
    `hermes plugins enable` step, so we do the equivalent here in code:
    add `research` to the allow-list, then trigger discovery. Without this,
    save_note is found but loads disabled and is never offered to the model.
    """
    from hermes_cli.config import load_config, save_config
    from hermes_cli.plugins import discover_plugins

    cfg = load_config()
    plugins_cfg = cfg.get("plugins") if isinstance(cfg.get("plugins"), dict) else {}
    enabled = set(plugins_cfg.get("enabled") or [])
    if PLUGIN_NAME not in enabled:
        enabled.add(PLUGIN_NAME)
        plugins_cfg["enabled"] = sorted(enabled)
        cfg["plugins"] = plugins_cfg
        save_config(cfg)
    discover_plugins(force=True)


def main():
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = "What are the headline new features in Python 3.13?"

    # Register save_note (our custom tool) into the `research` toolset.
    _activate_research_plugin()

    agent = AIAgent(
        model=os.getenv("HERMES_MODEL", "anthropic/claude-sonnet-4-6"),
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        quiet_mode=False,
        # Leave enabled_toolsets unset (None) so the agent gets the FULL default
        # tool set — the built-in web_search/web_extract PLUS our save_note,
        # which _activate_research_plugin() registered above. Passing
        # enabled_toolsets=["research"] would filter the set down to ONLY
        # save_note and strip the web tools, breaking the research step.
        # Pass Hermes' SQLite session store so the conversation persists to
        # $HERMES_HOME/state.db. Without this, AIAgent runs stateless — the bare
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



















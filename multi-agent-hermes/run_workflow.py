import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from run_agent import AIAgent

RESEARCHER_PROMPT = """You are a Researcher agent. Your job is a three-step pipeline:

STEP 1 — RESEARCH
Use web_search to gather facts on the topic the user gives you. Run 2-3 searches
to get enough material. Use web_extract on the most relevant URLs to read them in full.

STEP 2 — SAVE TO MEMORY
Call the memory tool (action: "add", target: "memory") with a concise summary of
your key findings so they persist across future sessions. Keep it under 150 words.

STEP 3 — DELEGATE TO WRITER
Call delegate_task with:
  goal: "You are a Writer agent. Write a well-structured, engaging article on
         <topic>, based on the research findings below. Do NOT use any tools and do
         NOT try to save files — you have no file or save tools. Simply WRITE the
         full article as your text response.

         Return your response in EXACTLY this format and nothing else:
           TITLE: <the article title on one line>
           <a blank line>
           <the full article body in markdown>

         Research findings to base the article on:
         <paste your key findings and source URLs here>"
  toolsets: ["skills"]

That is your final step. Once delegate_task returns the Writer's article, you are done —
report briefly that the Writer produced the article. Do NOT try to save files yourself;
the surrounding program persists the article to disk from the Writer's output.
"""


def _extract_writer_article(result: dict) -> str:
    """Pull the Writer's article text out of the conversation result.

    The Writer runs as a delegated child; its article comes back inside the
    ``delegate_task`` tool result in the message history. We search the history
    (most recent first) for that tool result and return the longest text block
    we find, falling back to the Researcher's final response.
    """
    messages = result.get("messages") or []

    def _text_of(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(item.get("text") or item.get("content") or "")
                else:
                    parts.append(str(item))
            return "\n".join(p for p in parts if p)
        if isinstance(content, dict):
            return content.get("text") or json.dumps(content)
        return str(content or "")

    def _unwrap_delegate(text: str) -> str:
        """delegate_task returns JSON like {"results":[{"summary": "<article>"}]}.
        Parse it so we get the real (unescaped) article text, not a JSON blob
        full of literal \\n sequences. Returns the original text if it isn't that
        shape."""
        stripped = text.lstrip()
        if not stripped.startswith("{"):
            return text
        try:
            data = json.loads(stripped)
        except (ValueError, TypeError):
            return text
        results = data.get("results") if isinstance(data, dict) else None
        if isinstance(results, list) and results:
            summary = results[0].get("summary") if isinstance(results[0], dict) else None
            if isinstance(summary, str) and summary.strip():
                return summary
        return text

    candidates = []
    for msg in messages:
        role = msg.get("role")
        if role not in ("tool", "user"):
            continue
        text = _unwrap_delegate(_text_of(msg.get("content")))
        if not text:
            continue
        # The Writer's article begins with the TITLE: marker we asked it to use.
        if "TITLE:" in text or "delegate" in str(msg.get("name", "")).lower():
            candidates.append(text)

    # Pick the candidate that actually carries the article (has TITLE: and is long).
    titled = [c for c in candidates if "TITLE:" in c]
    if titled:
        return max(titled, key=len)
    if candidates:
        return max(candidates, key=len)
    return result.get("final_response", "") or ""


def _parse_title_and_body(article: str) -> tuple[str, str]:
    """Split the Writer's 'TITLE: ...' header from the markdown body.

    Also strips a leading '# <title>' heading from the body if present, so the
    saved file doesn't show the title twice (we add one '# title' ourselves).
    """
    article = article.strip()
    m = re.search(r"TITLE:\s*(.+)", article)
    if m:
        title = m.group(1).strip().splitlines()[0].strip()
        body = article[m.end():].strip()
    else:
        # No TITLE marker — use the first markdown heading or first line.
        first = next((ln.strip() for ln in article.splitlines() if ln.strip()), "article")
        title = first.lstrip("# ").strip() or "article"
        body = article

    title = title or "article"

    # Drop a duplicate leading "# <same title>" heading from the body.
    body_lines = body.splitlines()
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    if body_lines and body_lines[0].lstrip("# ").strip() == title:
        body_lines.pop(0)
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
    body = "\n".join(body_lines).strip()

    return (title, body or article)


def _save_article(title: str, content: str) -> Path:
    """Deterministically write the article to ./output (mounted in Docker)."""
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:60] or "article"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{stamp}_{safe_title}.md"
    out_path.write_text(f"# {title}\n\n{content}\n")
    return out_path


def main():
    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = "The current state of open-source LLMs in 2025"

    print(f"\n=== RESEARCHER → WRITER WORKFLOW ===")
    print(f"Topic: {topic}\n")

    agent = AIAgent(
        model=os.getenv("HERMES_MODEL", "anthropic/claude-sonnet-4-6"),
        provider="anthropic",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        quiet_mode=False,
    )

    result = agent.run_conversation(
        user_message=topic,
        system_message=RESEARCHER_PROMPT,
        task_id="researcher-1",
    )

    print("\n=== WORKFLOW COMPLETE ===\n")
    print(result.get("final_response", ""))

    # Deterministic save: the Writer returned the article text via delegate_task;
    # we persist it here in code so an article ALWAYS lands in ./output, regardless
    # of which tool the LLM chose internally.
    article = _extract_writer_article(result)
    if article.strip():
        title, body = _parse_title_and_body(article)
        out_path = _save_article(title, body)
        print(f"\n📄 Article saved to: {out_path}")
    else:
        print("\n⚠️  No article text found in the Writer's output — nothing saved.")


if __name__ == "__main__":
    main()

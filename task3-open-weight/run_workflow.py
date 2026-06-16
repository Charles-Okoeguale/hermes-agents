import os
import sys
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("HERMES_ENABLE_PROJECT_PLUGINS", "true")

from run_agent import AIAgent

RESEARCHER_PROMPT = """You are a Researcher agent. Your job is a four-step pipeline.
You MUST complete ALL four steps. The task is NOT complete until STEP 4 succeeds.

STEP 1 — RESEARCH
Use web_search to gather facts on the topic the user gives you. Run 2-3 searches
to get enough material. Use web_extract on the most relevant URLs to read them in full.

STEP 2 — SAVE TO MEMORY
Call the memory tool (action: "add", target: "memory") with a concise summary of
your key findings so they persist across future sessions. Keep it under 200 words.

STEP 3 — DELEGATE TO WRITER
Call delegate_task with:
  goal: "Write a well-structured article on <topic>. Here are the research findings:
         <paste your key findings and source URLs here>"
  toolsets: []

STEP 4 — SAVE THE ARTICLE (MANDATORY — DO NOT SKIP)
After delegate_task returns the finished article, you MUST call the `save_article`
tool with the article title and the full article text the Writer produced.

CRITICAL RULES FOR STEP 4:
- You MUST use `save_article`. This is the ONLY correct way to save the article.
- DO NOT use `write_file`. DO NOT use `terminal`. DO NOT use any other tool to save.
- `save_article` is the only tool that writes to the output folder the user can see.
- If you use write_file instead of save_article, the article will be LOST and you
  will have FAILED the task.
- The task is NOT complete until `save_article` returns success.

Do not skip any step. Do not write the article yourself — the Writer writes it,
you save it with save_article.
"""


def main():
    topic = " ".join(sys.argv[1:]).strip()
    if not topic:
        topic = "The current state of open-source LLMs in 2025"

    model = os.getenv("HERMES_MODEL")
    provider = os.getenv("HERMES_PROVIDER")
    api_key = os.getenv("HERMES_API_KEY")
    base_url = os.getenv("HERMES_BASE_URL")  # required for local Ollama

    if not model or not provider or not api_key:
        print("ERROR: HERMES_MODEL, HERMES_PROVIDER, and HERMES_API_KEY must all be set.")
        sys.exit(1)

    print(f"\n=== RESEARCHER → WRITER WORKFLOW ===")
    print(f"Model:    {model}")
    print(f"Provider: {provider}")
    if base_url:
        print(f"Base URL: {base_url}")
    print(f"Topic:    {topic}\n")

    agent = AIAgent(
        model=model,
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        quiet_mode=False,
    )

    result = agent.run_conversation(
        user_message=topic,
        system_message=RESEARCHER_PROMPT,
        task_id="researcher-1",
    )

    print("\n=== WORKFLOW COMPLETE ===\n")
    print(result["final_response"])


if __name__ == "__main__":
    main()

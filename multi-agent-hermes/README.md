# Multi-Agent Hermes: Researcher → Writer Workflow

A 2-agent collaborative pipeline built on Hermes Agent. A Researcher agent gathers information from the web, saves a summary to long-term memory, then hands off to a Writer agent that produces a polished article.

## How it works

```
User gives a topic
       ↓
 Researcher Agent (parent)
  ├── web_search   (Hermes built-in, x2-3)
  ├── web_extract  (Hermes built-in, reads pages in full)
  ├── memory       (Hermes built-in, persists findings to $HERMES_HOME/memories/MEMORY.md)
  └── delegate_task (Hermes built-in) ──► Writer Agent (child, isolated context)
                                            └── writes the article and RETURNS it as text
       ↓
 run_workflow.py captures the Writer's returned article and writes it to
 output/<date>_<title>.md   (deterministic — done in plain Python, not by the LLM)
```

**The handoff (2 agents).** The Researcher uses `delegate_task` — a Hermes built-in — to spawn the Writer as a *separate child agent* with its own conversation loop and isolated context. The Writer gets the research findings inside its `goal` string and returns the finished article as its text response. This is a genuine two-agent collaboration: the child runs its own agent loop and never shares the parent's history.

**Why the program saves the file, not the agent.** A delegated child agent does not inherit project-plugin tools, and the parent's LLM cannot be relied on to consistently pick a specific save tool over the built-in `write_file`. To make the deliverable deterministic, `run_workflow.py` extracts the Writer's returned article from the conversation result and writes it to `output/` in code — so an article **always** lands in the mounted output folder, every run.

**Long-term memory** is handled by Hermes's built-in `memory` tool. The Researcher appends a summary of each session's findings to `$HERMES_HOME/memories/MEMORY.md`. On the next run, Hermes loads that file into the Researcher's system prompt automatically, so knowledge compounds across runs. In Docker, `$HERMES_HOME` is pinned to `/app/.hermes_home` and mounted as a host volume, so memory survives `docker compose down`.

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and TAVILY_API_KEY in .env
```

## Run locally

```bash
source .venv/bin/activate
python run_workflow.py "Your topic here"
```

Articles are saved to `output/`.

## Run with Docker (recommended)

From a fresh clone, three steps — in this order:

```bash
# 1. Create your .env from the template (the repo does NOT ship a .env)
cp .env.example .env

# 2. Open .env and paste in your real keys:
#      ANTHROPIC_API_KEY=sk-ant-...   (must have API credits)
#      TAVILY_API_KEY=tvly-...        (free at https://tavily.com)

# 3. Build and run on any topic you like
docker compose run --rm workflow "any topic here"
```

> **Note:** Step 1 is required. `docker-compose.yml` reads keys from `.env`, so
> running step 3 before creating `.env` fails with `env file .env not found`.
> The `.env` file is gitignored on purpose — secrets are never committed.

The first run builds the image (clones Hermes Agent from GitHub — give it a minute).
The finished article is written to `output/<date>_<title>.md`, and the Researcher's
findings are appended to `.hermes_home/memories/MEMORY.md`, which persists across runs.

You can also use `docker compose up --build` to run the default topic set in the
`command:` line of `docker-compose.yml`.

## Requirements

- Python 3.11-3.13
- `ANTHROPIC_API_KEY` — for the LLM (Claude)
- `TAVILY_API_KEY` — for web search ([get one free at tavily.com](https://tavily.com))

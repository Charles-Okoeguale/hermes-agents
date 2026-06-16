# Hermes Research Agent

A single, tool-using AI agent built on [Hermes Agent](https://github.com/NousResearch/hermes-agent)
(by Nous Research). Give it a research question and it will **search the web**,
**read the most relevant pages**, and **save a cited summary** as a markdown note.

This project demonstrates Hermes fundamentals: the agent loop, custom tool definition,
built-in tools, and session memory — all provided by Hermes.

## What it does

```
You ask a question
  → the agent calls web_search (Hermes built-in) to find sources
  → it calls web_extract (Hermes built-in) to read the most relevant pages in full
  → it writes a summary and calls save_note (custom tool) to record it with source URLs
  → it returns the answer
```

The agent decides *when* to call each tool. We never script the order — we just
describe the tools and let the model reason.

## Tools

`web_search` and `web_extract` are **Hermes built-ins** — they load automatically with no extra code. `web_search` is backed by Tavily (`TAVILY_API_KEY`).

The one **custom tool** lives in [`.hermes/plugins/research/`](.hermes/plugins/research/):

| Tool | What it does |
|------|--------------|
| `save_note` | Writes a cited markdown note to `notes/` |

A custom tool is three pieces, kept in separate files so each has one job:

- **`schemas.py`** — the plain-English description the LLM reads (the "menu").
- **`tools.py`** — the handler that does the actual work and returns a JSON string.
- **`__init__.py`** — `register(ctx)`, which wires the schema to its handler.
- **`plugin.yaml`** — the manifest declaring what tools the plugin provides.

## Run with Docker (recommended)

Docker avoids the local Python-version and dependency setup entirely — the image
pins Python 3.12 and clones Hermes Agent for you (with retries, so a flaky network
doesn't break the build). From a fresh clone, three steps in order:

```bash
# 1. Create your .env from the template (the repo does NOT ship a .env)
cp .env.example .env

# 2. Open .env and paste in your real keys:
#      ANTHROPIC_API_KEY=sk-ant-...   (must have API credits)
#      TAVILY_API_KEY=tvly-...        (free at https://tavily.com)

# 3. Build and run on any research question you like
docker compose run --rm agent "What are the headline new features in Python 3.13?"
```

> **Note:** Step 1 is required. `docker-compose.yml` reads keys from `.env`, so
> running step 3 before creating `.env` fails with `env file .env not found`.
> The `.env` file is gitignored on purpose — secrets are never committed.

The first run builds the image (clones Hermes Agent from GitHub — give it a minute).
The cited note is written to `notes/<title>.md` on your host, and the conversation
is persisted to `.hermes_home/state.db` (the Hermes SQLite session store), which is
mounted as a host volume so it survives across runs.

You can also run `docker compose up --build` to run the default question in the
`command:` line of `docker-compose.yml`.

## Run locally (without Docker)

Prefer running on your own machine instead? Run these from inside the
`single-agent-hermes/` folder, in order.

1. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

   > **Python version:** Hermes requires Python **3.11–3.13** (not 3.14). Check with
   > `python3 --version`. If your default is 3.14, create the venv with 3.12 explicitly:
   > `python3.12 -m venv .venv` (then activate as above).

   Keep this venv active for every step below and whenever you run the agent.

2. **Install the dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   This pulls in Hermes Agent (the agent loop, LLM connection, memory, and the
   `web_search`/`web_extract` built-in tools) and everything it needs.

   > If this step fails mid-download (pip clones Hermes from GitHub, which can stall on a flaky network), skip the local setup and use the Docker path above — it clones Hermes with retries.

3. **Add your keys**

   ```bash
   cp .env.example .env
   # then edit .env and fill in ANTHROPIC_API_KEY and TAVILY_API_KEY
   ```

   Get a free Tavily search key at https://tavily.com.

That's it — you can now run the agent. (If you'd rather install Hermes globally as a
CLI instead of as a project library, run
`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash` and use the
`hermes model` command to pick a model — but for pulling and running *this* project,
the three steps above are all you need.)

With the venv still active, run the agent:

```bash
python run_research_agent.py "What are the headline new features in Python 3.13?"
```

The agent will work through the question and drop a summary in `notes/`.

## How this maps to Hermes' architecture

- **Agent loop** → Hermes' `AIAgent` class (we don't write the loop).
- **Tool definition** → `register(ctx)` in the plugin's `__init__.py` wires schema to handler.
- **Built-in tools** → `web_search` and `web_extract` load automatically; no registration needed.
- **Session memory** → Hermes' built-in SQLite session storage (automatic).

See [`COMPARISON.md`](COMPARISON.md) for the one-page Hermes vs. LangChain writeup.

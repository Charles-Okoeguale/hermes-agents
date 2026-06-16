# Task 3 — Open-Weight Models on the Same Workflow

The identical Researcher → Writer workflow from Task 2, running on two open-weight models
with no Anthropic dependency. Same Hermes framework, same tools, same system prompt —
only the model and provider change.

## Models

| Service | Model | Provider | Runs on |
|---------|-------|----------|---------|
| `workflow-ollama` | `llama3.2` (3B, default) | Ollama | Local (Docker sidecar, CPU) |
| `workflow-openrouter` | `openai/gpt-oss-120b:free` (default) | OpenRouter | Cloud (hosted API) |

Both models are open-weight and self-hostable. They are configurable via `.env` — see `.env.example`.

## Prerequisites

- **Docker Desktop** installed and running (this project is Docker-only — nothing to install locally).
- **A few GB free disk** for the Llama 3.2 model (~2 GB) the Ollama service downloads on first run.
- API keys (see Setup): a **Tavily** key for web search, and an **OpenRouter** key for the cloud run.
  Ollama needs no key.

## Setup (required before any run)

From a fresh clone, do this first — `docker compose` reads keys from `.env`, and the file is
**not** shipped (it's gitignored so secrets are never committed):

```bash
cp .env.example .env
```

Then open `.env` and fill in:

- `TAVILY_API_KEY` — free at <https://tavily.com> (needed by both runs for web search)
- `OPENROUTER_API_KEY` — free at <https://openrouter.ai> (needed by the OpenRouter run)

> If you skip `cp .env.example .env`, every `docker compose` command fails with
> `env file .env not found`. Even the Ollama-only run requires the `.env` file to exist
> (though Ollama itself needs no API key).

## Run with Docker

This project is Docker-only — the command below builds the image, starts the local
Ollama model, and runs both models on the same workflow. Run it from the project root
after completing Setup above.

```bash
docker compose up --build
```

- On first run, the Ollama service pulls the `llama3.2` model (~2 GB) before the workflow
  starts — this can take a while on a slow connection. Subsequent runs reuse the cached model.
- Ollama inference runs **CPU-only** under Docker on macOS (no GPU passthrough), so the local
  run is slow — expect several minutes per call. See Performance Observations below.
- Articles land in `output/` — the OpenRouter run saves to `output/openrouter/`.
- **Expect `output/ollama/` to be empty.** The default Llama 3.2 (3B) model is too small to
  drive the tool-calling workflow and saves no article — this is a documented finding, not a
  bug. See **Performance Observations** below for why, and use a larger Ollama model to change it.

## Run one model at a time

```bash
# Ollama only
docker compose up --build workflow-ollama

# OpenRouter only
docker compose up --build workflow-openrouter
```

## Change the topic

```bash
docker compose run --rm workflow-ollama "quantum computing breakthroughs 2025"
docker compose run --rm workflow-openrouter "quantum computing breakthroughs 2025"
```

(`--rm` removes the one-off container after it finishes so stopped containers don't pile up.)

## Change the model

Edit `.env`:

```bash
# Use a different Ollama model (must be available at https://ollama.com/library)
OLLAMA_MODEL=mistral

# Use a different OpenRouter model (see https://openrouter.ai/models)
# Must be a model whose free endpoint supports tool calling.
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

---

## Performance Observations

These notes come from **actual runs** of this workflow on the same topic
("The current state of open-source LLMs in 2025"), not estimates. The two open-weight
models below were both run through the identical Researcher → Writer pipeline. Claude
Sonnet figures are included as a baseline from the equivalent Task 2 workflow.

Test environment: Apple Silicon Mac, Docker Desktop. Ollama ran **CPU-only** inside Docker
(Docker on macOS does not pass through the GPU), which is the single biggest factor in the
Ollama timings below.

### Speed (measured)

| Model | Where | Time | Notes |
|-------|-------|------|-------|
| Claude Sonnet 4.6 | Anthropic (baseline) | ~45–60 s total | Multiple tool calls, full pipeline |
| gpt-oss-120b | OpenRouter (cloud) | **535 s (8.9 min) total over 7 API calls** | Slowest single call ~109 s (the delegated Writer step); network-bound on the free tier |
| Llama 3.2 (3B) | Ollama (local, CPU) | **917 s (15.3 min) for a *single* API call** | CPU-only; would be far faster with GPU |

The Ollama number is the headline finding on speed: a single inference took **over 15
minutes** on CPU (877 s of that was raw model inference). Native Ollama on Apple Silicon
(using the Metal GPU) would be dramatically faster, but Docker-on-Mac has no GPU
passthrough — so the Dockerised local path is slow by nature, independent of the model's
quality.

### Output quality & tool use (measured)

This is where the gap between models was starkest.

**Claude Sonnet 4.6 (baseline)** — executed the full pipeline reliably: searched, saved to
memory, delegated to the Writer, and saved the article. Coherent, well-cited output.

**gpt-oss-120b (OpenRouter)** — **handled the agentic workflow correctly.** Verified from the
run log, it drove the full multi-step pipeline over 7 API calls: it researched, called
`memory` (add) to persist findings, called `delegate_task` to hand off to the Writer (a
109 s call), and then called `save_article` to write the finished piece. The delegated
Writer produced a well-structured, 7-section article with a real References list (Red Hat
Developer, n8n Blog, Medium — with working URLs), saved to `output/openrouter/`. This model
was a genuine success — a free, open-weight model driving the entire multi-agent pipeline
end to end.

**Llama 3.2 3B (Ollama, local)** — **could not drive the agentic workflow at all.** Verified
from the run log:
- It made **one** API call, produced a plain text reply, and stopped — it never called a
  single tool (no `web_search`, no `delegate_task`, no `save_article`).
- It did not understand it *had* tools to fetch real data — it replied that its *"knowledge
  cutoff is 2022"* and offered a stale overview instead of searching.
- The content was **out of date and partly wrong**: it described 2022-era models (LLaMA, T5,
  BART, RoBERTa) and mis-attributed several of them. No article was saved to `output/ollama/`.

This is the key lesson of the exercise: **a small (3B) open-weight model is not capable of
driving a multi-step, tool-calling agent workflow.** It can generate text, but it cannot
reliably emit tool calls or follow a multi-step plan. Model *size and capability* — not the
framework — is the limiting factor.

### Key takeaway: capability is the bottleneck, not Hermes

Hermes ran identically for all three models — same loop, same tools, same prompt. What
differed entirely was the **model's ability to follow a multi-step, tool-using plan**:

- **Capable models (Claude, gpt-oss-120b)** drove the whole pipeline correctly.
- **A small model (Llama 3.2 3B)** ignored the tools and the plan, and hallucinated.

So an agent is only ever as capable as its model. The harness gives the model hands; the
model still has to know how to use them. A larger local model (e.g. `llama3.1:8b`,
`qwen2.5:7b`) would likely fare better at tool-calling than the 3B — that's the natural next
test, though it needs a larger download and slower CPU run.

### Cost (measured / known)

| Model | Cost per run |
|-------|--------------|
| Claude Sonnet 4.6 | Paid API tokens (most expensive) |
| gpt-oss-120b (OpenRouter) | **Free** (`:free` tier) — but rate-limited and shared |
| Llama 3.2 (Ollama, local) | **$0.00** — runs entirely on your own hardware |

Local Ollama has no API cost and keeps all data on-machine (important for sensitive data),
but pays for it in speed on CPU and — at the 3B size — in capability. The OpenRouter free
tier was capable *and* free for this task, but free endpoints are rate-limited and not
guaranteed available (we hit `404 no tool-use endpoint` and `429 rate-limited` on several
free models before settling on `gpt-oss-120b:free`).

### Recommendation

- **For reliability and quality:** a capable model (Claude, or a large open-weight model).
- **For a free cloud option that still drives the workflow:** `gpt-oss-120b:free` on
  OpenRouter worked well here — with the caveat that free endpoints are rate-limited.
- **For zero cost / full data privacy:** local Ollama — but use a **larger** model than 3B
  for agentic tool-calling, and expect slow CPU inference unless you run native (GPU).

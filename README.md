# Hermes Agents

Three self-contained projects built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. Each folder is independent — its own `.env`, its own dependencies, its own README with setup and run instructions.

## Projects

### [single-agent-hermes/](single-agent-hermes/)
**Task 1.** A single tool-using research agent. Give it a question — it searches the web, reads the relevant pages, and saves a cited summary. Also includes a one-page Hermes vs. LangChain comparison.

### [multi-agent-hermes/](multi-agent-hermes/)
**Task 2.** A two-agent Researcher → Writer pipeline. The Researcher gathers and saves findings to long-term memory, then delegates to a Writer agent that produces the article. Dockerised. Runs on Claude (Anthropic).

### [task3-open-weight/](task3-open-weight/)
**Task 3.** The same Researcher → Writer workflow running on two open-weight models with no Anthropic dependency: Llama 3.2 via Ollama (local) and gpt-oss-120b via OpenRouter (cloud). Includes real performance data comparing both models against Claude.

## Structure

```
hermis/
├── single-agent-hermes/    Task 1  (includes COMPARISON.md — Hermes vs. LangChain)
├── multi-agent-hermes/     Task 2
└── task3-open-weight/      Task 3
```

Each project has its own README — open that for setup and run instructions.
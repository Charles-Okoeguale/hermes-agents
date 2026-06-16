# Hermes Agents vs. LangChain Agents

A comparison of two frameworks for building AI agents, across six areas: architecture, tool definition, state management, compounding value, multi-agent support, and deployment.

---

## Background: What are these two things?

Hermes Agents (by Nous Research) is an open-source Python framework. You install it, plug in any LLM like Claude, Llama, Mistral, or 200+ models via OpenRouter add your own custom tools, and it runs the agent loop for you. Think of it as a ready-made robot body - you supply the brain.

LangChain Agents (specifically LangGraph, which is LangChain's modern agent runtime) is also an open-source Python framework. But instead of giving you a ready-made loop, it gives you the parts to build your own loop as a graph of connected nodes and edges that you wire together yourself.

Both frameworks do the same fundamental job: take an LLM, give it tools, and run the think, act, observe loop until the job is done.

---

## 1. Architecture - how the agent is structured

Hermes gives you one pre-built agent class called AIAgent. You create it, give it a question, and it handles everything: calling the LLM, deciding which tool to run, running it, reading the result, and looping until done. You do not design the loop - you configure it. The same AIAgent works whether you are running a CLI script, an API server, or a chat interface, one class, many uses.

Hermes is like buying a car. It already drives. You just choose the engine (the LLM) and where to go (the task).

LangGraph makes you build the agent as a graph. You create nodes (each node is a step: call the LLM, run a tool, check a condition) and edges (the arrows connecting them: after this node, go to that one). You define the flow explicitly. This gives you full control over what happens when, but you write more code to get there.

LangGraph is like getting car parts and an instruction manual. You assemble the car yourself. More flexible, more setup.

Hermes is opinionated and fast to run. LangGraph is flexible and fully controllable. If you need a custom loop shape (e.g. two agents debating, or a human approval step mid-task), LangGraph gives you that control. If you just need an agent running quickly, Hermes is faster.

---

## 2. Tool Definition - how you give the agent new abilities

In Hermes, a tool is three separate pieces kept in separate files. A schema is a plain Python dict that describes the tool to the LLM (name, what it does, what arguments it takes), the LLM only ever sees this, not your actual code. A handler is a normal Python function that does the actual work and returns a string (returning a JSON string is the recommended pattern so the agent can read structured results, but it is not strictly required). Registration is a register(ctx) call that wires the schema to the handler. There is no decorator, the schema and the function are intentionally kept apart. Tools live in a plugin folder (.hermes/plugins/your-plugin/) and are auto-discovered at startup.

You write the tool's job description (schema) separately from the tool's actual code (handler). More files, but very clear separation of what the AI sees vs. what the code does.

LangChain uses a @tool decorator directly on the function. The function name becomes the tool name, the docstring becomes the description, and the type hints become the argument schema, all in one place. You write one function with a decorator and a docstring, then pass it to the agent.

LangChain's @tool is quicker to write. Hermes' plugin/schema/handler split is more explicit and organised, especially useful when you have many tools or want the tool descriptions carefully crafted independently of the code.

---

## 3. State Management - how the agent remembers things

Hermes handles memory through two separate systems. First, every conversation is saved to a SQLite database (a local file-based database at ~/.hermes/state.db) with full-text search built in, so sessions survive restarts. When a conversation gets too long to fit in the LLM's context window, Hermes compresses that session automatically, summarising older turns while keeping the important parts. Second, there are bounded long-lived markdown files in ~/.hermes/memories/ (MEMORY.md, capped at about 2,200 characters / 800 tokens, and USER.md, capped at about 1,375 characters / 500 tokens). These markdown files do not auto-compact: when a write would exceed the limit, the memory tool returns an error and the agent must consolidate or remove entries itself before retrying. So session history is compressed automatically, but the long-lived memory files have hard limits the agent has to manage deliberately.

Hermes keeps a searchable notebook of sessions automatically, and keeps a small set of long-lived note files that it has to tidy up itself once they fill, rather than letting them grow forever.

LangGraph makes state management explicit and configurable. You define a State object (a typed schema) that represents exactly what the agent needs to remember, and you choose a checkpointer (the thing that saves state), in-memory for testing, SQLite or PostgreSQL for production (note: the SQLite checkpointer requires a separate install via pip install langgraph-checkpoint-sqlite). Every node in the graph reads from and writes to this shared state object, so all parts of the workflow can see the same information.

LangGraph gives you a shared whiteboard that all parts of the agent can read and write to. You design the whiteboard yourself and choose where it is stored. More setup, but you control exactly what is remembered.

Hermes is low-config persistent memory, sessions and compression are built in and require no setup. LangGraph is full control over what you store and where - but you have to set it up yourself.

---

## 4. Compounding Value - how the agent improves over time

This is a key differentiator that LangGraph does not match at the architectural level.

Hermes is built around a closed learning loop. When the agent solves a task, it can write a reusable Markdown skill file that captures the procedure, pitfalls, and verification steps for that type of task. On future runs, the agent reads those saved skills and uses them - getting faster and more accurate the longer it operates. This is what Nous Research calls compounding value: the agent's capabilities grow with use, without any manual prompt tuning from you.

In independent benchmarking (attributed to TokenMix.ai), agents with 20 or more self-created skills completed similar future tasks about 40% faster than a fresh instance with no prior skills. This is a domain-specific gain measured in time and tokens on repeated task categories, not a general capability boost that transfers across unrelated tasks.

LangGraph does not have a built-in equivalent. State persists across sessions via checkpointers, but the agent does not automatically write reusable skill documents from its experience. Any improvement over time requires you to engineer it deliberately, fine-tuning the model, updating prompts, or building your own skill storage layer.

Hermes gets smarter the more you use it, automatically. With LangGraph, making the agent improve over time is your responsibility to build.

---

## 5. Multi-Agent Support - how the framework handles more than one agent

This matters because the next stage of this project is a two-agent workflow.

Hermes can run more than one agent through a delegate_task tool: a parent agent spawns throwaway child agents that each run in their own isolated context with their own toolset, do their work independently, and return only a final summary to the parent (an orchestrator-worker pattern). The children cannot talk to each other or share state directly. True peer collaboration is still being built out by Nous Research, so today this is best described as delegation rather than full multi-agent cooperation.

LangGraph was designed for multi-agent systems from the start. Agents are nodes in a shared graph that can hand off to one another and read and write the same shared state, so building patterns like a researcher handing off to a writer, or a supervisor coordinating several workers, is a core use case rather than an add-on.

Hermes does delegation (parent spawns isolated workers). LangGraph does true multi-agent graphs (agents share state and hand off directly). For a collaborative two-agent handoff with shared memory, LangGraph is the more natural fit, though Hermes' delegation can achieve a parent-to-worker split.

---

## 6. Deployment - how you run it in production

Hermes is self-hosted. You run it yourself on your own machine, a VPS (a rented cloud server), or in Docker. There is no managed cloud product; you own the infrastructure and the maintenance. This ties directly into the goal of running on your own open-weight models without depending on a paid hosted service.

LangGraph offers both. You can self-host it (a free Lite tier, an Enterprise tier, or a standalone server you run on your own infrastructure), or use the managed LangGraph Platform (Cloud SaaS, or Bring Your Own Cloud where it runs in your own cloud account but they handle provisioning).

Hermes is self-host only. LangGraph gives you the choice of self-hosting or letting them host it for you.

---

## Summary Table

| | Hermes Agents | LangChain / LangGraph |
|---|---|---|
| Architecture | One pre-built AIAgent loop you configure | A graph of nodes and edges you assemble yourself |
| Tool definition | Separate schema + handler + register(ctx) in a plugin folder | @tool decorator on a function with a docstring |
| State management | Built-in SQLite sessions with auto-compression - low config (has limits) | Explicit State schema + pluggable checkpointer you set up |
| Compounding value | Built-in skill learning loop - agent improves automatically with use | No built-in equivalent - you engineer improvement yourself |
| Multi-agent support | Delegation - parent spawns isolated workers (no shared state) | Native multi-agent graphs - agents share state and hand off directly |
| Deployment | Self-host only (your machine, VPS, or Docker) | Self-host or managed LangGraph Platform |
| Speed to get running | Fast - less to build | Slower - more to assemble |
| Flexibility | Less - the loop is Hermes' | More - you control the flow |
| Best for | Getting a solid, self-improving agent running quickly | Custom control flow, multi-agent graphs, production fine-tuning |

---



Use Hermes when you want an agent up and running quickly, with memory, tooling, and self-improvement handled for you, and you are happy following Hermes' conventions.

Use LangChain / LangGraph when you need full control over how the agent thinks, branches, and remembers, especially for complex multi-agent systems or production deployments where you need to tune every part of the pipeline.




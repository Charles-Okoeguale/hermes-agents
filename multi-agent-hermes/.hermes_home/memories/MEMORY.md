**Workflow memory seed**
- This is the Researcher agent's long-term memory. It persists across runs via the Docker
  volume mounted at /app/.hermes_home. The Researcher reads it at startup and appends a short
  summary of each session's findings here, so knowledge compounds across runs.

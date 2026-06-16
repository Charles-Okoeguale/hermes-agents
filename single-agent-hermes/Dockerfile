FROM python:3.12-slim

WORKDIR /app

# git is needed to fetch hermes-agent from GitHub.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Make git resilient to flaky networks: larger buffer + abort only on truly
# stalled transfers. Large repo clones over TLS otherwise fail with
# "fetch-pack: invalid index-pack output" / "early EOF" on transient drops.
RUN git config --global http.postBuffer 524288000 \
    && git config --global http.lowSpeedLimit 1000 \
    && git config --global http.lowSpeedTime 60

COPY requirements.txt .

# Clone hermes-agent ourselves with --depth 1 (small, fast) and retry on transient
# network failures, then pip-install from the local checkout. This is far more
# reliable than letting pip do a full git clone, which kept failing mid-transfer.
RUN for i in 1 2 3 4 5; do \
        git clone --depth 1 https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent && break; \
        echo "git clone attempt $i failed, retrying in 10s..."; rm -rf /tmp/hermes-agent; sleep 10; \
    done; \
    test -d /tmp/hermes-agent/.git || { echo "FATAL: could not clone hermes-agent after 5 attempts"; exit 1; }

# Install hermes from the local clone, plus python-dotenv (the only other dep).
# Installing the clone directly avoids letting pip do its own flaky git fetch.
RUN pip install --no-cache-dir --retries 5 /tmp/hermes-agent python-dotenv \
    && rm -rf /tmp/hermes-agent

# Copy the project in — this includes .hermes/plugins/research/ (our custom tool).
COPY . .

# The save_note custom tool writes cited notes here.
RUN mkdir -p /app/notes

# Pin Hermes home to a known path so the SQLite session store (state.db) is
# mountable as a volume and persists across runs. Hermes reads HERMES_HOME first,
# falling back to ~/.hermes — see hermes_constants.get_hermes_home().
ENV HERMES_HOME=/app/.hermes_home
RUN mkdir -p /app/.hermes_home

# Opt into project-local plugins so .hermes/plugins/research/ (save_note) loads.
# run_research_agent.py also sets this via os.environ.setdefault as a fallback.
ENV HERMES_ENABLE_PROJECT_PLUGINS=true

ENTRYPOINT ["python", "run_research_agent.py"]
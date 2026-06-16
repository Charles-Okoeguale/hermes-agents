FROM python:3.12-slim

WORKDIR /app

# Install git so pip can pull hermes-agent from GitHub (see requirements.txt)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Make git resilient to the flaky/large TLS transfers that fail under Docker-on-Mac
# ("RPC failed; curl 56 ... early EOF" on big clones). Force HTTP/1.1, a large
# post buffer, and no low-speed abort so a slow-but-alive transfer is not killed.
RUN git config --global http.version HTTP/1.1 && \
    git config --global http.postBuffer 1048576000 && \
    git config --global http.lowSpeedLimit 0 && \
    git config --global http.lowSpeedTime 999999

COPY requirements.txt .
# Retry the install a few times — the clone can still drop mid-transfer; a retry
# almost always succeeds because git resumes against a warm connection.
RUN for i in 1 2 3 4 5; do \
        pip install --no-cache-dir -r requirements.txt && break; \
        echo "pip install attempt $i failed; retrying..."; \
        sleep 5; \
    done

COPY . .

# Place the plugins.enabled allow-list at the container's Hermes home so our
# standalone `save_article` plugin actually loads (plugins are opt-in).
RUN mkdir -p /root/.hermes && cp /app/hermes-config.yaml /root/.hermes/config.yaml

RUN mkdir -p /app/output

ENV HERMES_ENABLE_PROJECT_PLUGINS=true
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "run_workflow.py"]

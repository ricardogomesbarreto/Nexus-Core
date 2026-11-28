FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl postgresql python3-psycopg python3-tk xauth xvfb && rm -rf /var/lib/apt/lists/*
# Only the CPU runtime is needed in the bounded desktop trial.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -fsSL --retry 3 https://github.com/ollama/ollama/releases/download/v0.11.10/ollama-linux-amd64.tgz | tar -xz -C /usr --exclude='*cuda*' --exclude='*rocm*'
WORKDIR /app
COPY . .
ENV NEXUS_DATABASE_PASSWORD=local-disposable NEXUS_RESOURCE_PROFILE=eco PYTHONPATH=/app
CMD ["bash","tests/acceptance/run_4gb.sh"]

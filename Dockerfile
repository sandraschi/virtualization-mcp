# Glama build image. Must build AND start headless on stock Debian slim.
# Deliberately NO VirtualBox install: kernel modules cannot load in a build
# sandbox, and apt-key / lsb_release are gone from modern Debian (both broke
# the previous Dockerfile). The server degrades gracefully without a
# hypervisor. Fixed 2026-10-06 after Glama "Build failed" (Sep 22), which
# traced to: missing requirements.txt in COPY, `apt-key` removed, missing
# lsb_release, and `python -m virtualization-mcp` (hyphen is not importable).
FROM python:3.13-slim

WORKDIR /app

# Project metadata first for layer caching (all three exist at repo root)
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package; runtime deps come from pyproject (requires-python >=3.12)
RUN pip install --no-cache-dir -e .

# Non-root runtime user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

ENV PYTHONPATH=/app/src
ENV DEBUG=false

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import virtualization_mcp" || exit 1

# MCP stdio server (src/virtualization_mcp/__main__.py)
CMD ["python", "-m", "virtualization_mcp"]

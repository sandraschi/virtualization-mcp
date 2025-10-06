# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install VirtualBox (for Linux containers)
# Note: This is a simplified version - in production you might want to use a different approach
RUN wget -q https://www.virtualbox.org/download/oracle_vbox_2016.asc -O- | apt-key add - \
    && echo "deb [arch=amd64] http://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" >> /etc/apt/sources.list.d/virtualbox.list \
    && apt-get update \
    && apt-get install -y virtualbox-7.0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml ./
COPY README.md ./

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 virtualization-mcp && chown -R virtualization-mcp:virtualization-mcp /app
USER virtualization-mcp

# Expose port (if needed for HTTP mode)
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV VBOX_INSTALL_PATH=/usr/bin
ENV DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import virtualization-mcp; print('VBoxMCP is healthy')" || exit 1

# Default command
CMD ["python", "-m", "virtualization-mcp"]

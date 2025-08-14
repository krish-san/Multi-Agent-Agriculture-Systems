# My AgentWeaver container
FROM python:3.11-slim

WORKDIR /app

# My Python setup
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# System dependencies I need
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install my Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy my source code
COPY src/ ./src/
COPY *.py ./

# Security - run as non-root user
RUN useradd -m -u 1000 agentweaver && \
    chown -R agentweaver:agentweaver /app
USER agentweaver

# My API port
EXPOSE 8000

# Health check for my container
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import src; print('OK')" || exit 1

# Run my server
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]

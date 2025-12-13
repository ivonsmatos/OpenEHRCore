FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY openehrcore_agent/ ./openehrcore_agent/
COPY config.example.yaml ./config.yaml

# Expose MLLP port
EXPOSE 2575

# Expose DICOM port (optional)
EXPOSE 4242

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 2575)); s.close()" || exit 1

# Run agent
CMD ["python", "-m", "openehrcore_agent"]

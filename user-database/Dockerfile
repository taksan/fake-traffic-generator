FROM python:3.11-slim

# Install tini and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends tini curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create data directory
RUN mkdir -p /data

EXPOSE 8500

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["python", "app.py"]

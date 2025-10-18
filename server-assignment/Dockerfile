FROM python:3.11.3-alpine

# Install tini
RUN apk add --no-cache tini

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create log directory
RUN mkdir -p /var/log/server-assignment

# Expose API port
EXPOSE 8100

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Run the API server
CMD ["python", "-u", "app.py"]

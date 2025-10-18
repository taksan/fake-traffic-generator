FROM python:3.11.3-alpine

# Install tini
RUN apk add --no-cache tini

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY *.py .

RUN apk add --no-cache netcat-openbsd

# Expose API port
EXPOSE 8000

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["/sbin/tini", "--"]

# Run the API server when the container starts
CMD ["python", "-u", "api.py"]

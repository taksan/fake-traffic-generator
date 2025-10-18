# Fake Traffic Generator

A comprehensive traffic generation system for testing and demonstrating monitoring stack capabilities. This system generates realistic web application traffic with user flows, geographic distribution, and DDoS simulation capabilities.

## Overview

The fake traffic generator consists of three main services:

1. **Traffic Generator** - Generates realistic web application logs with user flows
2. **User Database** - Manages up to 100 users for log generation
3. **Server Assignment** - Provides geographic server assignment based on user location

## Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f traffic-generator

# Stop services
docker-compose down
```

The services will be available at:
- Traffic Generator API: http://localhost:8000
- User Database API: http://localhost:8500
- Server Assignment API: http://localhost:8100

You can customize the port mappings by creating a `.env` file (see `.env.example`).

## Logging

All services use the **GELF (Graylog Extended Log Format)** logging driver to send structured logs to a log aggregation system (e.g., Promtail/Loki or Logstash/Elasticsearch).

- **Protocol**: GELF over UDP
- **Port**: 12201
- **Target**: `host.docker.internal:12201` (reaches the host's port 12201)
- **Format**: JSON logs wrapped in GELF messages

The GELF configuration is defined using a YAML anchor in `docker-compose.yml` for easy reuse across all services.

## Services

### Traffic Generator
- **Port**: 8000
- **Purpose**: Generates realistic web application traffic and logs
- **Log Format**: JSON with structured fields to stdout
- **User Management**: Fetches users from User Database service
- **User Flows**: Simulates realistic user journeys
  - Purchase flows
  - Browse-only sessions
  - Profile management
  - Support interactions
  - Abandoned carts
  - 30% random traffic, 70% flow-based
- **Geographic Distribution**: 
  - Europe: 20%
  - Asia: 20%
  - South America: 20%
  - Africa: 20%
  - Australia/Oceania: 10%
  - North America: 10%
- **Log Rate**: ~1-5 logs per second (configurable via API)
- **API Documentation**: http://localhost:8000/docs

### User Database
- **Port**: 8500
- **Purpose**: Manages up to 100 users for log generation
- **Storage**: Persistent JSON file in Docker volume
- **Logging**: GELF logging to port 12201
- **Endpoints**:
  - `GET /user/random` - Get or create a user
  - `GET /users` - List all users
  - `GET /health` - Health check
  - `POST /users/reset` - Reset all users
- **Documentation**: See [user-database/README.md](user-database/README.md)

### Server Assignment
- **Port**: 8100
- **Purpose**: Assigns users to geographic servers based on location
- **Features**: GeoJSON-based server mapping
- **Logging**: GELF logging to port 12201

## Log Structure

Each generated log entry contains:

```json
{
  "timestamp": "2025-10-17T19:00:00.000000Z",
  "level": "INFO",
  "client_ip": "177.123.45.67",
  "user_id": 42,
  "user_name": "John Doe",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "http": {
    "request": {
      "method": "GET",
      "referrer": "https://example.com/previous/page"
    },
    "response": {
      "status_code": 200,
      "bytes": 12345
    },
    "url": "/products/example/1234",
    "version": "1.1"
  },
  "user_agent": {
    "original": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
  },
  "message": "GET /products/example/1234 - 200",
  "geocode": {
    "location": {
      "lat": 43.6532,
      "lon": -79.3832
    },
    "country_iso_code": "CA",
    "country_name": "Canada",
    "city_name": "Toronto"
  },
  "flow_name": "purchase"
}
```

**Note**: 
- `geocode` field is always present with geographic information
- `flow_name` field is present when the request is part of a user flow
- `error` field is added for status codes >= 400

## Traffic Generator API

The traffic generator exposes a REST API on port 8000 for runtime configuration and simulation.

### API Endpoints

#### GET /
Get API status and current configuration.

```bash
curl http://localhost:8000/
```

#### GET /status
Get detailed generator status including DDoS simulation state and active flows.

```bash
curl http://localhost:8000/status
```

#### POST /traffic/start
Start traffic generation.

```bash
curl -X POST http://localhost:8000/traffic/start
# Or use the script
./traffic-start.sh
```

#### POST /traffic/stop
Stop traffic generation.

```bash
curl -X POST http://localhost:8000/traffic/stop
# Or use the script
./traffic-stop.sh
```

#### POST /traffic/pause
Pause traffic generation (alias for stop).

```bash
curl -X POST http://localhost:8000/traffic/pause
```

#### POST /traffic/resume
Resume traffic generation (alias for start).

```bash
curl -X POST http://localhost:8000/traffic/resume
```

#### POST /update_interval
Update the log generation interval (time between log entries).

**Using the shell script:**
```bash
./update-interval.sh <min_interval> <max_interval>

# Example: Generate logs every 0.1 to 0.5 seconds (faster)
./update-interval.sh 0.1 0.5

# Example: Generate logs every 1 to 3 seconds (slower)
./update-interval.sh 1.0 3.0
```

**Using curl directly:**
```bash
curl -X POST http://localhost:8000/update_interval \
  -H "Content-Type: application/json" \
  -d '{"min_interval": 0.1, "max_interval": 0.5}'
```

#### POST /simulate_ddos
Simulate a DDoS attack with thousands of requests from a single region.

**Using the shell script:**
```bash
./simulate-ddos.sh <duration_seconds> [region]

# Example: 30-second DDoS from random region
./simulate-ddos.sh 30

# Example: 60-second DDoS from Asia
./simulate-ddos.sh 60 Asia
```

**Available regions:**
- Europe
- Asia
- South America
- Africa
- Australia
- North America

**Using curl directly:**
```bash
# Random region
curl -X POST http://localhost:8000/simulate_ddos \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 30}'

# Specific region
curl -X POST http://localhost:8000/simulate_ddos \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 60, "region": "Asia"}'
```

### Interactive API Documentation

FastAPI provides automatic interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Management Scripts

The following scripts are provided for easy traffic control:

- `traffic-start.sh` - Start traffic generation
- `traffic-stop.sh` - Stop traffic generation
- `traffic-status.sh` - Check current status
- `update-interval.sh` - Update log generation speed
- `simulate-ddos.sh` - Simulate DDoS attacks

## Customization

### Modify Log Generation Rate

**Recommended: Use the API** (no restart required):
```bash
./update-interval.sh 0.1 0.5
```

**Alternative: Edit code** (requires rebuild):
Edit `traffic-generator/traffic_generator.py` and change the default values in the `LogGeneratorConfig` class:
```python
class LogGeneratorConfig:
    def __init__(self):
        self.min_interval = 0.2  # Change these
        self.max_interval = 1.5  # Change these
```
Then rebuild the container.

### Add Custom Fields to Logs

Edit `traffic-generator/traffic_generator.py` in the `generate_log_entry()` function to add new fields to the `log_data` dictionary.

### Adjust Geographic Distribution

Edit the `ip_ranges` list in `traffic-generator/traffic_generator.py` to add/remove IP ranges for different regions.

### Customize User Flows

User flows are defined in the parent project's `user_flows.yml` file. Modify this file to create custom user journeys.

## Architecture

The fake traffic generator system consists of three interconnected services:

```
┌─────────────────────────┐
│   Traffic Generator     │ ──(GELF UDP)──► Log Aggregator
│  Port 8000 (API)        │    (port 12201)
│  /metrics (Prometheus)  │
└─────────────────────────┘
         │
         ├──► User Database (Port 8500)
         │    - GET /user/random
         │    - GET /users
         │    - GET /health
         │    - GELF logging
         │
         └──► Server Assignment (Port 8100)
              - Geographic server mapping
              - GELF logging
```

## Files

- `traffic-generator/` - Main traffic generation service
  - `traffic_generator.py` - Core log generation logic
  - `flow_manager.py` - User flow state machine manager
  - `error_manager.py` - Error simulation logic
  - `api.py` - FastAPI application for management
  - `Dockerfile` - Container image definition
  - `requirements.txt` - Python dependencies
- `user-database/` - User management service
  - `app.py` - Flask application
  - `README.md` - User database documentation
- `server-assignment/` - Geographic server assignment service
- Management scripts (*.sh) - Traffic control utilities

## Output Formats

### GELF Logs (UDP)

The traffic generator sends structured JSON logs via GELF protocol to UDP port 12201. Each log entry follows a consistent schema with fields for HTTP requests, user information, and geographic data. The GELF messages include:

- **short_message**: The JSON log entry as a string
- **_container_name**: Container name (e.g., `traffic_generator`)
- **_container_id**: Full container ID
- **_tag**: Service tag (e.g., `traffic-generator`)
- **level**: GELF severity level (6=INFO, 4=WARN, 3=ERROR)
- **timestamp**: Unix timestamp

These logs can be collected by any GELF-compatible log aggregation system (Promtail, Logstash, Graylog, etc.).

### Prometheus Metrics

The traffic generator exposes Prometheus-compatible metrics at the `/metrics` endpoint (port 8000):

- `logs_generated_total` - Counter: Total logs generated
- `http_requests_total` - Counter: HTTP requests by method and status code
- `http_requests_by_location_total` - Counter: Requests by geographic location (country, city, coordinates)
- `ddos_simulation_active` - Gauge: DDoS simulation status (0 or 1)
- `ddos_simulation_remaining_seconds` - Gauge: Remaining seconds of DDoS simulation
- `api_requests_total` - Counter: API requests by endpoint
- `traffic_generation_interval_seconds` - Gauge: Current min/max intervals
- `active_flows_total` - Gauge: Number of active user flows

These metrics can be scraped by any Prometheus-compatible monitoring system.

## Troubleshooting

### Traffic Generator Not Starting

1. Check if the user database is accessible:
   ```bash
   curl http://localhost:8500/health
   ```

2. Check container logs:
   ```bash
   docker-compose logs traffic-generator
   ```

3. Verify GELF endpoint is reachable:
   ```bash
   # Check if port 12201/udp is listening on the host
   netstat -uln | grep 12201
   ```

### No Logs Appearing in Log Aggregator

1. Verify traffic is running:
   ```bash
   curl http://localhost:8000/status
   ```

2. Check if GELF messages are being sent:
   ```bash
   # The container logs won't show JSON logs anymore (they go via GELF)
   # Check the log aggregator (Promtail/Logstash) logs instead
   ```

3. Verify GELF endpoint connectivity:
   ```bash
   docker exec traffic_generator ping -c 1 host.docker.internal
   ```

### API Not Responding

1. Ensure the container is running:
   ```bash
   docker-compose ps traffic-generator
   ```

2. Check for port conflicts on 8000, 8500, or 8600

## License

This project is provided as-is for educational and development purposes.

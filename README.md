# Fake Traffic Generator

A comprehensive traffic generation system for testing and demonstrating monitoring stack capabilities. This system generates realistic web application traffic with user flows, geographic distribution, and DDoS simulation capabilities.

## Overview

The fake traffic generator consists of three main services:

1. **Traffic Generator** - Generates realistic web application logs with user flows
2. **User Database** - Manages up to 100 users for log generation
3. **Server Assignment** - Provides geographic server assignment based on user location

## Services

### Traffic Generator
- **Port**: 8000 (Management API)
- **Purpose**: Generates realistic web application traffic and logs
- **Log Format**: JSON with structured fields via GELF
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
- **Port**: 8500 (API)
- **Purpose**: Manages up to 100 users for log generation
- **Storage**: Persistent JSON file in Docker volume
- **Logging**: Logs all requests to file for Filebeat collection
- **Endpoints**:
  - `GET /user/random` - Get or create a user
  - `GET /users` - List all users
  - `GET /health` - Health check
  - `POST /users/reset` - Reset all users
- **Documentation**: See [user-database/README.md](user-database/README.md)

### Server Assignment
- **Port**: 8100 (API)
- **Purpose**: Assigns users to geographic servers based on location
- **Features**: GeoJSON-based server mapping
- **Logging**: Logs all assignments for analysis

## Log Structure

Each generated log entry contains:

```json
{
  "timestamp": "2025-10-15T19:00:00.000Z",
  "level": "INFO",
  "client_ip": "177.123.45.67",
  "user_id": "user_42",
  "http": {
    "request": {
      "method": "GET",
      "referrer": "https://example.com"
    },
    "response": {
      "status_code": 200,
      "bytes": 12345
    },
    "url": "/products/example/1234",
    "version": "1.1"
  },
  "user_agent": {
    "original": "Mozilla/5.0..."
  },
  "message": "GET /products/example/1234 - 200"
}
```

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

The traffic generator integrates with the ELK stack as follows:

```
┌─────────────────────────┐
│   Traffic Generator     │ ──(GELF/UDP)──► Logstash ──► Elasticsearch
│  Port 8000 (API)        │
└─────────────────────────┘
         │
         ├──► User Database (Port 8500)
         │
         └──► Server Assignment (Port 8100)
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

## Integration with ELK Stack

This traffic generator is designed to work with an ELK stack deployment. It sends logs via GELF (Graylog Extended Log Format) to Logstash, which processes and enriches them before storing in Elasticsearch.

### Required Logstash Configuration

Ensure your Logstash pipeline has a GELF input configured:

```ruby
input {
  gelf {
    port => 12201
    type => "gelf"
  }
}
```

### Log Enrichment

After Logstash processing, logs are enriched with:
- `client.geo.*` - Geographic information (country, city, coordinates)
- `user_agent.parsed.*` - Parsed browser and OS information

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

### No Logs Appearing

1. Verify traffic is running:
   ```bash
   curl http://localhost:8000/status
   ```

2. Check if Logstash is receiving logs:
   ```bash
   docker-compose logs logstash | grep "message"
   ```

### API Not Responding

1. Ensure the container is running:
   ```bash
   docker-compose ps traffic-generator
   ```

2. Check for port conflicts on 8000, 8100, or 8500

## License

This project is provided as-is for educational and development purposes.

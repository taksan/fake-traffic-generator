"""
FastAPI application for traffic generator management
"""
import time
import random
import sys
import threading
import logging
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Response
from pydantic import BaseModel
import uvicorn
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

from traffic_generator import LogGeneratorConfig, run_log_generator, get_region_ip_ranges

# Initialize FastAPI app
app = FastAPI(title="Traffic Generator API", version="1.0.0")

# Global configuration instance
config = LogGeneratorConfig()

# Prometheus Metrics
logs_generated_total = Counter('logs_generated_total', 'Total number of logs generated')
http_requests_total = Counter('http_requests_total', 'Total HTTP requests by method and status', ['method', 'status_code'])
http_requests_by_location = Counter('http_requests_by_location_total', 'HTTP requests by geographic location', 
                                    ['country', 'city', 'latitude', 'longitude'])
http_requests_detailed = Counter('http_requests_detailed_total', 
                                 'Detailed HTTP requests with URI, user, location and status',
                                 ['uri', 'user_id', 'user_name', 'session_id', 'country', 'city', 'status_code'])
ddos_active_gauge = Gauge('ddos_simulation_active', 'Whether DDoS simulation is currently active')
ddos_duration_gauge = Gauge('ddos_simulation_remaining_seconds', 'Remaining seconds of DDoS simulation')
api_requests_total = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
traffic_generation_interval = Gauge('traffic_generation_interval_seconds', 'Current traffic generation interval', ['type'])
active_flows_gauge = Gauge('active_flows_total', 'Number of active user flows')

# Initialize interval gauges
traffic_generation_interval.labels(type='min').set(config.min_interval)
traffic_generation_interval.labels(type='max').set(config.max_interval)


# API Models
class IntervalUpdate(BaseModel):
    """Model for updating traffic generation interval."""
    min_interval: float
    max_interval: float


class DDoSSimulation(BaseModel):
    """Model for DDoS simulation parameters."""
    duration_seconds: int
    region: Optional[str] = None


# API Endpoints
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    api_requests_total.labels(endpoint='/metrics', method='GET').inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """API status and information."""
    api_requests_total.labels(endpoint='/', method='GET').inc()
    return {
        "service": "Traffic Generator API",
        "status": "running" if config.traffic_enabled else "paused",
        "config": {
            "traffic_enabled": config.traffic_enabled,
            "min_interval": config.min_interval,
            "max_interval": config.max_interval,
            "ddos_active": config.ddos_active,
            "ddos_region": config.ddos_region if config.ddos_active else None
        }
    }


@app.post("/update_interval")
async def update_interval(interval: IntervalUpdate):
    """Update log generation interval."""
    api_requests_total.labels(endpoint='/update_interval', method='POST').inc()
    if interval.min_interval < 0 or interval.max_interval < 0:
        return {"error": "Intervals must be positive"}
    if interval.min_interval > interval.max_interval:
        return {"error": "min_interval must be less than or equal to max_interval"}
    
    config.min_interval = interval.min_interval
    config.max_interval = interval.max_interval
    
    # Update Prometheus gauges
    traffic_generation_interval.labels(type='min').set(config.min_interval)
    traffic_generation_interval.labels(type='max').set(config.max_interval)
    
    return {
        "status": "success",
        "message": "Interval updated",
        "min_interval": config.min_interval,
        "max_interval": config.max_interval
    }


@app.post("/simulate_ddos")
async def simulate_ddos(ddos: DDoSSimulation):
    """Simulate DDoS attack from a specific region."""
    api_requests_total.labels(endpoint='/simulate_ddos', method='POST').inc()
    if ddos.duration_seconds <= 0:
        return {"error": "Duration must be positive"}
    
    # Select random region if not specified
    regions = list(get_region_ip_ranges().keys())
    selected_region = ddos.region if ddos.region in regions else random.choice(regions)
    
    config.ddos_active = True
    config.ddos_region = selected_region
    config.ddos_end_time = time.time() + ddos.duration_seconds
    
    # Update Prometheus gauge
    ddos_active_gauge.set(1)
    
    return {
        "status": "success",
        "message": f"DDoS simulation started from {selected_region}",
        "region": selected_region,
        "duration_seconds": ddos.duration_seconds,
        "end_time": datetime.fromtimestamp(config.ddos_end_time).isoformat()
    }


@app.get("/status")
async def get_status():
    """Get current generator status."""
    api_requests_total.labels(endpoint='/status', method='GET').inc()
    
    # Update active flows gauge
    active_flows = config.flow_manager.get_active_flow_count()
    active_flows_gauge.set(active_flows)
    
    # Update DDoS remaining time gauge
    if config.ddos_active:
        remaining = max(0, config.ddos_end_time - time.time())
        ddos_duration_gauge.set(remaining)
    else:
        ddos_duration_gauge.set(0)
    
    return {
        "traffic_enabled": config.traffic_enabled,
        "min_interval": config.min_interval,
        "max_interval": config.max_interval,
        "ddos_active": config.ddos_active,
        "ddos_region": config.ddos_region if config.ddos_active else None,
        "ddos_remaining": max(0, config.ddos_end_time - time.time()) if config.ddos_active else 0,
        "active_flows": active_flows
    }


@app.post("/traffic/start")
async def start_traffic():
    """Start traffic generation."""
    if config.traffic_enabled:
        return {
            "status": "info",
            "message": "Traffic generation is already running"
        }
    
    config.traffic_enabled = True
    return {
        "status": "success",
        "message": "Traffic generation started",
        "traffic_enabled": config.traffic_enabled
    }


@app.post("/traffic/stop")
async def stop_traffic():
    """Stop traffic generation."""
    if not config.traffic_enabled:
        return {
            "status": "info",
            "message": "Traffic generation is already stopped"
        }
    
    config.traffic_enabled = False
    return {
        "status": "success",
        "message": "Traffic generation stopped",
        "traffic_enabled": config.traffic_enabled
    }


@app.post("/traffic/pause")
async def pause_traffic():
    """Pause traffic generation (alias for stop)."""
    return await stop_traffic()


@app.post("/traffic/resume")
async def resume_traffic():
    """Resume traffic generation (alias for start)."""
    return await start_traffic()


if __name__ == "__main__":
    # Configure uvicorn logging to use stderr
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["handlers"]["default"]["stream"] = sys.stderr
    log_config["handlers"]["access"]["stream"] = sys.stderr
    
    # Prepare metrics dictionary for traffic generator
    metrics_dict = {
        'logs_generated_total': logs_generated_total,
        'http_requests_total': http_requests_total,
        'http_requests_by_location': http_requests_by_location,
        'http_requests_detailed': http_requests_detailed,
        'ddos_active_gauge': ddos_active_gauge
    }
    
    # Start log generator in background thread
    generator_thread = threading.Thread(target=run_log_generator, args=(config, metrics_dict), daemon=True)
    generator_thread.start()
    
    # Start FastAPI server with logging to stderr
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=log_config)

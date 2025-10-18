"""
Server Assignment Service - FastAPI Application

Assigns sessions to geographic servers and logs assignments for analysis.
"""
import json
import random
import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Server Assignment API", version="1.0.0")

# Global state
servers: List[Dict] = []
assignments: Dict[str, Dict] = {}  # session_id -> assignment info
ASSIGNMENT_LOG_FILE = "/var/log/server-assignment/assignments.log"


class ServerInfo(BaseModel):
    """Server information model."""
    server_name: str
    server_ip: str
    region: str
    provider: str
    coordinates: List[float]


class AssignmentRequest(BaseModel):
    """Request model for session assignment."""
    session_id: str
    client_ip: Optional[str] = None
    user_id: Optional[int] = None


class AssignmentResponse(BaseModel):
    """Response model for session assignment."""
    session_id: str
    server_name: str
    server_ip: str
    region: str
    assigned_at: str


def load_geo_servers():
    """Load geographic server configuration from geojson file."""
    try:
        with open('/app/geo_servers.geojson', 'r') as f:
            data = json.load(f)
            return data['features']
    except Exception as e:
        print(f"Error loading geo_servers.geojson: {e}", flush=True)
        return []


def ip_range_to_random_ip(ip_range: str) -> str:
    """Convert IP range to a random IP within that range."""
    try:
        start_ip, end_ip = ip_range.split('-')
        start_parts = [int(x) for x in start_ip.split('.')]
        end_parts = [int(x) for x in end_ip.split('.')]
        
        # Generate random IP within range
        ip_parts = []
        for i in range(4):
            if start_parts[i] == end_parts[i]:
                ip_parts.append(start_parts[i])
            else:
                ip_parts.append(random.randint(start_parts[i], end_parts[i]))
        
        return '.'.join(map(str, ip_parts))
    except Exception as e:
        print(f"Error generating IP from range {ip_range}: {e}", flush=True)
        return "0.0.0.0"


def get_city_name_from_region(region: str) -> str:
    """Map AWS region to city name."""
    region_to_city = {
        "us-east-1": "Virginia",
        "us-west-1": "San Francisco",
        "sa-east-1": "São Paulo",
        "eu-west-1": "Dublin",
        "eu-central-1": "Frankfurt",
        "ap-southeast-1": "Singapore",
        "ap-southeast-2": "Sydney",
        "ap-northeast-1": "Tokyo",
        "ca-central-1": "Montreal",
        "me-central-1": "Dubai",
        "af-south-1": "Cape Town"
    }
    return region_to_city.get(region, "Unknown")


def get_country_info_from_region(region: str) -> tuple:
    """Map AWS region to country name and ISO code."""
    region_to_country = {
        "us-east-1": ("United States", "US"),
        "us-west-1": ("United States", "US"),
        "sa-east-1": ("Brazil", "BR"),
        "eu-west-1": ("Ireland", "IE"),
        "eu-central-1": ("Germany", "DE"),
        "ap-southeast-1": ("Singapore", "SG"),
        "ap-southeast-2": ("Australia", "AU"),
        "ap-northeast-1": ("Japan", "JP"),
        "ca-central-1": ("Canada", "CA"),
        "me-central-1": ("United Arab Emirates", "AE"),
        "af-south-1": ("South Africa", "ZA")
    }
    return region_to_country.get(region, ("Unknown", "XX"))


def initialize_servers():
    """Initialize server list from geo_servers.geojson."""
    global servers
    features = load_geo_servers()
    
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Generate a random IP from the range
        server_ip = ip_range_to_random_ip(props['ip_range'])
        
        # Get geocode information
        country_name, country_code = get_country_info_from_region(props['region'])
        city_name = get_city_name_from_region(props['region'])
        
        server = {
            'server_name': props['server_name'],
            'server_ip': server_ip,
            'region': props['region'],
            'provider': props['provider'],
            'coordinates': coords,
            'ip_range': props['ip_range'],
            'session_count': 0,
            'geocode': {
                'location': {
                    'lon': coords[0],
                    'lat': coords[1]
                },
                'country_iso_code': country_code,
                'country_name': country_name,
                'city_name': city_name
            }
        }
        servers.append(server)
    
    print(f"Initialized {len(servers)} servers", flush=True)
    for server in servers:
        print(f"  - {server['server_name']} ({server['region']}): {server['server_ip']}", flush=True)


def select_server() -> Dict:
    """Select a server using round-robin or least-loaded strategy."""
    if not servers:
        raise HTTPException(status_code=500, detail="No servers available")
    
    # Use least-loaded strategy
    selected = min(servers, key=lambda s: s['session_count'])
    selected['session_count'] += 1
    return selected


def log_assignment(assignment: Dict):
    """Log assignment to file for Filebeat collection."""
    try:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(ASSIGNMENT_LOG_FILE), exist_ok=True)
        
        # Write as JSON line
        with open(ASSIGNMENT_LOG_FILE, 'a') as f:
            f.write(json.dumps(assignment) + '\n')
    except Exception as e:
        print(f"Error logging assignment: {e}", flush=True)


@app.on_event("startup")
async def startup_event():
    """Initialize servers on startup."""
    initialize_servers()


@app.get("/")
async def root():
    """API status and information."""
    return {
        "service": "Server Assignment API",
        "version": "1.0.0",
        "servers_available": len(servers),
        "total_assignments": len(assignments)
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "servers": len(servers),
        "assignments": len(assignments)
    }


@app.get("/servers")
async def list_servers():
    """List all available servers."""
    return {
        "servers": [
            {
                "server_name": s['server_name'],
                "server_ip": s['server_ip'],
                "region": s['region'],
                "provider": s['provider'],
                "session_count": s['session_count']
            }
            for s in servers
        ]
    }


@app.post("/assign", response_model=AssignmentResponse)
async def assign_session(request: AssignmentRequest):
    """Assign a session to a server."""
    session_id = request.session_id
    
    # Check if session already assigned
    if session_id in assignments:
        existing = assignments[session_id]
        return AssignmentResponse(**existing)
    
    # Select server
    server = select_server()
    
    # Create assignment
    assigned_at = datetime.utcnow().isoformat() + "Z"
    assignment = {
        "log_type": "server_assignment",
        "session_id": session_id,
        "server_name": server['server_name'],
        "server_ip": server['server_ip'],
        "region": server['region'],
        "assigned_at": assigned_at,
        "client_ip": request.client_ip,
        "user_id": request.user_id,
        "geocode": server['geocode']
    }
    
    # Store assignment
    assignments[session_id] = assignment
    
    # Log assignment
    log_assignment(assignment)
    
    return AssignmentResponse(
        session_id=session_id,
        server_name=server['server_name'],
        server_ip=server['server_ip'],
        region=server['region'],
        assigned_at=assigned_at
    )


@app.get("/assignment/{session_id}")
async def get_assignment(session_id: str):
    """Get assignment for a specific session."""
    if session_id not in assignments:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return assignments[session_id]


@app.get("/stats")
async def get_stats():
    """Get assignment statistics."""
    server_stats = {}
    for server in servers:
        server_stats[server['server_name']] = {
            "region": server['region'],
            "session_count": server['session_count'],
            "server_ip": server['server_ip']
        }
    
    return {
        "total_servers": len(servers),
        "total_assignments": len(assignments),
        "server_stats": server_stats
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)

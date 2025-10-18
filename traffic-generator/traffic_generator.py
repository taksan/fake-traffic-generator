"""Log generation module - handles all log generation logic
"""
import time
import json
import random
import uuid
import sys
from datetime import datetime
from faker import Faker
import requests
from flow_manager import FlowManager
from error_manager import ErrorManager

fake = Faker()

# Load geo_servers configuration
def load_geo_servers():
    """Load geographic server configuration from geojson file."""
    try:
        with open('/app/geo_servers.geojson', 'r') as f:
            data = json.load(f)
            return data['features']
    except Exception as e:
        print(f"Warning: Could not load geo_servers.geojson: {e}", file=sys.stderr, flush=True)
        return []

GEO_SERVERS = load_geo_servers()


class LogGeneratorConfig:
    """Configuration for traffic generator."""
    def __init__(self):
        self.traffic_enabled = True  # Traffic generation on/off
        self.min_interval = 0.1
        self.max_interval = 3.0
        self.ddos_active = False
        self.ddos_end_time = 0
        self.ddos_region = None
        self.user_db_url = "http://user-database:8500"
        self.flow_manager = FlowManager()
        self.error_manager = ErrorManager()


def get_region_geocode_data():
    """Return IP ranges with geocoding information organized by region."""
    return {
        "Europe": {
            "ranges": [
                ("2.16.0.0", "2.31.255.255"),
                ("5.0.0.0", "5.255.255.255"),
                ("31.0.0.0", "31.255.255.255"),
                ("37.0.0.0", "37.255.255.255"),
                ("46.0.0.0", "46.255.255.255"),
                ("62.0.0.0", "62.255.255.255"),
                ("78.0.0.0", "78.255.255.255"),
                ("80.0.0.0", "80.255.255.255"),
                ("82.0.0.0", "82.255.255.255"),
                ("88.0.0.0", "88.255.255.255"),
            ],
            "countries": [
                {"name": "United Kingdom", "code": "GB", "cities": [
                    {"name": "London", "lat": 51.5074, "lon": -0.1278},
                    {"name": "Manchester", "lat": 53.4808, "lon": -2.2426},
                    {"name": "Birmingham", "lat": 52.4862, "lon": -1.8904},
                ]},
                {"name": "Germany", "code": "DE", "cities": [
                    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
                    {"name": "Munich", "lat": 48.1351, "lon": 11.5820},
                    {"name": "Frankfurt", "lat": 50.1109, "lon": 8.6821},
                ]},
                {"name": "France", "code": "FR", "cities": [
                    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
                    {"name": "Lyon", "lat": 45.7640, "lon": 4.8357},
                    {"name": "Marseille", "lat": 43.2965, "lon": 5.3698},
                ]},
            ]
        },
        "Asia": {
            "ranges": [
                ("1.0.0.0", "1.255.255.255"),
                ("14.0.0.0", "14.255.255.255"),
                ("27.0.0.0", "27.255.255.255"),
                ("36.0.0.0", "36.255.255.255"),
                ("42.0.0.0", "42.255.255.255"),
                ("58.0.0.0", "58.255.255.255"),
                ("103.0.0.0", "103.255.255.255"),
                ("110.0.0.0", "110.255.255.255"),
                ("116.0.0.0", "116.255.255.255"),
                ("125.0.0.0", "125.255.255.255"),
            ],
            "countries": [
                {"name": "Japan", "code": "JP", "cities": [
                    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
                    {"name": "Osaka", "lat": 34.6937, "lon": 135.5023},
                    {"name": "Kyoto", "lat": 35.0116, "lon": 135.7681},
                ]},
                {"name": "China", "code": "CN", "cities": [
                    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
                    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737},
                    {"name": "Shenzhen", "lat": 22.5431, "lon": 114.0579},
                ]},
                {"name": "India", "code": "IN", "cities": [
                    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
                    {"name": "Delhi", "lat": 28.7041, "lon": 77.1025},
                    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
                ]},
            ]
        },
        "South America": {
            "ranges": [
                ("177.0.0.0", "177.255.255.255"),
                ("179.0.0.0", "179.255.255.255"),
                ("181.0.0.0", "181.255.255.255"),
                ("186.0.0.0", "186.255.255.255"),
                ("189.0.0.0", "189.255.255.255"),
                ("190.0.0.0", "190.255.255.255"),
                ("191.0.0.0", "191.255.255.255"),
                ("200.0.0.0", "200.255.255.255"),
                ("201.0.0.0", "201.255.255.255"),
                ("187.0.0.0", "187.255.255.255"),
            ],
            "countries": [
                {"name": "Brazil", "code": "BR", "cities": [
                    {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333},
                    {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
                    {"name": "Brasília", "lat": -15.8267, "lon": -47.9218},
                ]},
                {"name": "Argentina", "code": "AR", "cities": [
                    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816},
                    {"name": "Córdoba", "lat": -31.4201, "lon": -64.1888},
                    {"name": "Rosario", "lat": -32.9442, "lon": -60.6505},
                ]},
                {"name": "Colombia", "code": "CO", "cities": [
                    {"name": "Bogotá", "lat": 4.7110, "lon": -74.0721},
                    {"name": "Medellín", "lat": 6.2476, "lon": -75.5658},
                    {"name": "Cali", "lat": 3.4516, "lon": -76.5320},
                ]},
            ]
        },
        "Africa": {
            "ranges": [
                ("41.0.0.0", "41.255.255.255"),
                ("102.0.0.0", "102.255.255.255"),
                ("105.0.0.0", "105.255.255.255"),
                ("154.0.0.0", "154.255.255.255"),
                ("196.0.0.0", "196.255.255.255"),
                ("197.0.0.0", "197.255.255.255"),
                ("129.0.0.0", "129.255.255.255"),
                ("155.0.0.0", "155.255.255.255"),
                ("160.0.0.0", "160.255.255.255"),
                ("169.0.0.0", "169.255.255.255"),
            ],
            "countries": [
                {"name": "South Africa", "code": "ZA", "cities": [
                    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473},
                    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
                    {"name": "Durban", "lat": -29.8587, "lon": 31.0218},
                ]},
                {"name": "Nigeria", "code": "NG", "cities": [
                    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792},
                    {"name": "Abuja", "lat": 9.0765, "lon": 7.3986},
                    {"name": "Kano", "lat": 12.0022, "lon": 8.5920},
                ]},
                {"name": "Egypt", "code": "EG", "cities": [
                    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357},
                    {"name": "Alexandria", "lat": 31.2001, "lon": 29.9187},
                    {"name": "Giza", "lat": 30.0131, "lon": 31.2089},
                ]},
            ]
        },
        "Australia": {
            "ranges": [
                ("1.128.0.0", "1.159.255.255"),
                ("27.32.0.0", "27.47.255.255"),
                ("49.0.0.0", "49.255.255.255"),
                ("101.0.0.0", "101.255.255.255"),
                ("203.0.0.0", "203.255.255.255"),
            ],
            "countries": [
                {"name": "Australia", "code": "AU", "cities": [
                    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
                    {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631},
                    {"name": "Brisbane", "lat": -27.4698, "lon": 153.0251},
                ]},
            ]
        },
        "North America": {
            "ranges": [
                ("8.0.0.0", "8.255.255.255"),
                ("12.0.0.0", "12.255.255.255"),
                ("24.0.0.0", "24.255.255.255"),
                ("50.0.0.0", "50.255.255.255"),
                ("66.0.0.0", "66.255.255.255"),
            ],
            "countries": [
                {"name": "United States", "code": "US", "cities": [
                    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
                    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
                    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
                    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
                ]},
                {"name": "Canada", "code": "CA", "cities": [
                    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
                    {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207},
                    {"name": "Montreal", "lat": 45.5017, "lon": -73.5673},
                ]},
            ]
        },
    }


def get_region_ip_ranges():
    """Return IP ranges organized by region (legacy format)."""
    geocode_data = get_region_geocode_data()
    return {region: data["ranges"] for region, data in geocode_data.items()}


def generate_distributed_ip_with_geocode():
    """Generate IP addresses with geocoding information."""
    geocode_data = get_region_geocode_data()
    
    # Select a random region
    region = random.choice(list(geocode_data.keys()))
    region_data = geocode_data[region]
    
    # Select a random IP range from that region
    ip_ranges = region_data["ranges"]
    start_ip, end_ip = random.choice(ip_ranges)
    
    # Generate IP
    start_parts = [int(x) for x in start_ip.split('.')]
    end_parts = [int(x) for x in end_ip.split('.')]
    
    ip_parts = []
    for i in range(4):
        if i < 3:
            ip_parts.append(random.randint(start_parts[i], end_parts[i]))
        else:
            ip_parts.append(random.randint(1, 254))
    
    ip = '.'.join(map(str, ip_parts))
    
    # Select a random country and city from that region
    country = random.choice(region_data["countries"])
    city = random.choice(country["cities"])
    
    geocode = {
        "location": {
            "lat": city["lat"],
            "lon": city["lon"]
        },
        "country_iso_code": country["code"],
        "country_name": country["name"],
        "city_name": city["name"]
    }
    
    return ip, geocode


def generate_distributed_ip():
    """Generate IP addresses from various countries for better geographic distribution (legacy)."""
    ip, _ = generate_distributed_ip_with_geocode()
    return ip


def _generate_distributed_ip_legacy():
    """Legacy IP generation without geocode."""
    # IP ranges organized by region with equal representation
    ip_ranges = [
        # Europe (10 ranges)
        ("2.16.0.0", "2.31.255.255"),
        ("5.0.0.0", "5.255.255.255"),
        ("31.0.0.0", "31.255.255.255"),
        ("37.0.0.0", "37.255.255.255"),
        ("46.0.0.0", "46.255.255.255"),
        ("62.0.0.0", "62.255.255.255"),
        ("78.0.0.0", "78.255.255.255"),
        ("80.0.0.0", "80.255.255.255"),
        ("82.0.0.0", "82.255.255.255"),
        ("88.0.0.0", "88.255.255.255"),
        
        # Asia (10 ranges)
        ("1.0.0.0", "1.255.255.255"),
        ("14.0.0.0", "14.255.255.255"),
        ("27.0.0.0", "27.255.255.255"),
        ("36.0.0.0", "36.255.255.255"),
        ("42.0.0.0", "42.255.255.255"),
        ("58.0.0.0", "58.255.255.255"),
        ("103.0.0.0", "103.255.255.255"),
        ("110.0.0.0", "110.255.255.255"),
        ("116.0.0.0", "116.255.255.255"),
        ("125.0.0.0", "125.255.255.255"),
        
        # South America (10 ranges)
        ("177.0.0.0", "177.255.255.255"),
        ("179.0.0.0", "179.255.255.255"),
        ("181.0.0.0", "181.255.255.255"),
        ("186.0.0.0", "186.255.255.255"),
        ("189.0.0.0", "189.255.255.255"),
        ("190.0.0.0", "190.255.255.255"),
        ("191.0.0.0", "191.255.255.255"),
        ("200.0.0.0", "200.255.255.255"),
        ("201.0.0.0", "201.255.255.255"),
        ("187.0.0.0", "187.255.255.255"),
        
        # Africa (10 ranges)
        ("41.0.0.0", "41.255.255.255"),
        ("102.0.0.0", "102.255.255.255"),
        ("105.0.0.0", "105.255.255.255"),
        ("154.0.0.0", "154.255.255.255"),
        ("196.0.0.0", "196.255.255.255"),
        ("197.0.0.0", "197.255.255.255"),
        ("129.0.0.0", "129.255.255.255"),
        ("155.0.0.0", "155.255.255.255"),
        ("160.0.0.0", "160.255.255.255"),
        ("169.0.0.0", "169.255.255.255"),
        
        # Australia/Oceania (5 ranges)
        ("1.128.0.0", "1.159.255.255"),
        ("27.32.0.0", "27.47.255.255"),
        ("49.0.0.0", "49.255.255.255"),
        ("101.0.0.0", "101.255.255.255"),
        ("203.0.0.0", "203.255.255.255"),
        
        # North America - US (5 ranges, reduced)
        ("8.0.0.0", "8.255.255.255"),
        ("12.0.0.0", "12.255.255.255"),
        ("24.0.0.0", "24.255.255.255"),
        ("50.0.0.0", "50.255.255.255"),
        ("66.0.0.0", "66.255.255.255"),
    ]
    
    # Select a random IP range
    start_ip, end_ip = random.choice(ip_ranges)
    
    # Convert IP to integer
    start_parts = [int(x) for x in start_ip.split('.')]
    end_parts = [int(x) for x in end_ip.split('.')]
    
    # Generate random IP within the range
    ip_parts = []
    for i in range(4):
        if i < 3:
            ip_parts.append(random.randint(start_parts[i], end_parts[i]))
        else:
            ip_parts.append(random.randint(1, 254))
    
    return '.'.join(map(str, ip_parts))


def generate_ip_from_region_with_geocode(region_name):
    """Generate IP from a specific region with geocode information."""
    geocode_data = get_region_geocode_data()
    if region_name not in geocode_data:
        region_name = random.choice(list(geocode_data.keys()))
    
    region_data = geocode_data[region_name]
    ip_ranges = region_data["ranges"]
    start_ip, end_ip = random.choice(ip_ranges)
    
    start_parts = [int(x) for x in start_ip.split('.')]
    end_parts = [int(x) for x in end_ip.split('.')]
    
    ip_parts = []
    for i in range(4):
        if i < 3:
            ip_parts.append(random.randint(start_parts[i], end_parts[i]))
        else:
            ip_parts.append(random.randint(1, 254))
    
    ip = '.'.join(map(str, ip_parts))
    
    # Select a random country and city from that region
    country = random.choice(region_data["countries"])
    city = random.choice(country["cities"])
    
    geocode = {
        "location": {
            "lat": city["lat"],
            "lon": city["lon"]
        },
        "country_iso_code": country["code"],
        "country_name": country["name"],
        "city_name": city["name"]
    }
    
    return ip, geocode


def generate_ip_from_region(region_name):
    """Generate IP from a specific region (legacy)."""
    ip, _ = generate_ip_from_region_with_geocode(region_name)
    return ip


def fetch_user_from_db(user_db_url):
    """Fetch a random user from the user database API."""
    try:
        response = requests.get(f"{user_db_url}/user/random", timeout=5)
        if response.status_code in [200, 201]:
            user_data = response.json()
            return user_data['id'], user_data['name']
    except Exception as e:
        print(f"Error fetching user from database: {e}", file=sys.stderr, flush=True)
    
    # Fallback to fake user if API fails
    return None, fake.user_name()


def generate_log_entry(override_ip=None, override_geocode=None, user_db_url=None, uri=None, flow_context=None, 
                       is_ddos=False, error_manager=None, flow_manager=None):
    """Generates a single, structured log entry with geocoding.
    
    Args:
        override_ip: Override IP address (for DDoS simulation)
        override_geocode: Override geocode data (for DDoS simulation)
        user_db_url: URL of user database service
        uri: Specific URI to use (from flow)
        flow_context: Context from flow (IP, user agent, user info)
        is_ddos: Whether this is a DDoS request
        error_manager: ErrorManager instance for generating realistic errors
        flow_manager: FlowManager instance for method mapping
    """
    
    # Use flow context if provided, otherwise generate new
    if flow_context:
        client_ip = flow_context.get('client_ip')
        user_agent = flow_context.get('user_agent')
        user_id = flow_context.get('user_id')
        user_name = flow_context.get('user_name')
        session_id = flow_context.get('session_id')  # Get session_id from flow
        geocode = flow_context.get('geocode')  # Get geocode from flow
    else:
        if override_ip:
            client_ip = override_ip
            geocode = override_geocode if override_geocode else None
        else:
            client_ip, geocode = generate_distributed_ip_with_geocode()
        user_agent = fake.user_agent()
        user_id, user_name = fetch_user_from_db(user_db_url) if user_db_url else (None, fake.user_name())
        session_id = str(uuid.uuid4())  # Generate random session_id for anonymous requests
    
    # Determine HTTP method based on URI
    if uri:
        # Use flow_manager's method mapping if available
        if flow_manager:
            method = flow_manager.get_http_method(uri)
        else:
            # Fallback to GET if no flow_manager
            method = "GET"
    else:
        # Random request
        method = random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])
        uri = fake.uri_path()
        
        # Add product or user context to some URLs
        if random.random() < 0.3:
            uri = f"/products/{fake.word()}/{random.randint(1000, 9999)}"
        elif random.random() < 0.2 and user_id:
            uri = f"/users/{user_id}/profile"
        elif random.random() < 0.2:
            uri = f"/users/{fake.user_name()}/profile"
    
    # Generate realistic status code and error message using ErrorManager
    is_authenticated = user_id is not None
    if error_manager:
        status_code, error_message = error_manager.get_status_code(
            uri=uri,
            is_authenticated=is_authenticated,
            is_ddos=is_ddos,
            method=method
        )
        response_bytes = error_manager.get_response_bytes(status_code)
    else:
        # Fallback to simple random selection
        status_code = random.choices(
            [200, 201, 204, 301, 400, 401, 403, 404, 500, 503], 
            weights=[15, 5, 2, 3, 5, 3, 2, 10, 4, 1], 
            k=1
        )[0]
        error_message = f"HTTP {status_code}"
        response_bytes = random.randint(50, 50000)
        
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": "INFO" if status_code < 400 else ("ERROR" if status_code >= 500 else "WARN"),
        "client_ip": client_ip,
        "user_id": user_id,
        "user_name": user_name,
        "session_id": session_id,
        "http": {
            "request": {
                "method": method,
                "referrer": fake.uri()
            },
            "response": {
                "status_code": status_code,
                "bytes": response_bytes
            },
            "url": uri,
            "version": "1.1"
        },
        "user_agent": {
            "original": user_agent
        },
        "message": f'{method} {uri} - {status_code}'
    }
    
    # Add error message for non-success responses
    if status_code >= 400 and error_manager:
        log_data['error'] = error_message
    
    # Add flow name if part of a flow
    if flow_context and 'flow_name' in flow_context:
        log_data['flow_name'] = flow_context['flow_name']
    
    # Add geocode information if available
    if geocode:
        log_data['geocode'] = geocode
    
    return log_data


def track_log_metrics(log_entry, metrics):
    """Track Prometheus metrics for a log entry."""
    if not metrics:
        return
    
    metrics['logs_generated_total'].inc()
    status_code = str(log_entry['http']['response']['status_code'])
    method = log_entry['http']['request']['method']
    metrics['http_requests_total'].labels(method=method, status_code=status_code).inc()
    
    # Track geographic metrics
    if 'geocode' in log_entry:
        geo = log_entry['geocode']
        metrics['http_requests_by_location'].labels(
            country=geo['country_name'],
            city=geo['city_name'],
            latitude=str(geo['location']['lat']),
            longitude=str(geo['location']['lon'])
        ).inc()
    
    # Track detailed metrics with URI, user, location and status
    if 'http_requests_detailed' in metrics and 'geocode' in log_entry:
        uri = log_entry['http']['url']
        user_id = str(log_entry.get('user_id', 'anonymous'))
        user_name = log_entry.get('user_name', 'anonymous')
        session_id = log_entry.get('session_id', 'none')
        geo = log_entry['geocode']
        
        metrics['http_requests_detailed'].labels(
            uri=uri,
            user_id=user_id,
            user_name=user_name,
            session_id=session_id,
            country=geo['country_name'],
            city=geo['city_name'],
            status_code=status_code
        ).inc()


def run_log_generator(config: LogGeneratorConfig, metrics=None):
    """Main traffic generation loop with Prometheus metrics support."""
    print("Traffic generator started", file=sys.stderr, flush=True)
    
    # Wait for user database to be ready
    print("Waiting for user database to be ready...", file=sys.stderr, flush=True)
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{config.user_db_url}/health", timeout=2)
            if response.status_code == 200:
                print("User database is ready!", file=sys.stderr, flush=True)
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        print("Warning: User database not responding, will use fallback users", file=sys.stderr, flush=True)
    
    last_cleanup = time.time()
    
    while True:
        # Check if traffic generation is enabled
        if not config.traffic_enabled:
            time.sleep(1)  # Sleep while paused
            continue
        
        # Periodic cleanup of old flows
        if time.time() - last_cleanup > 60:
            config.flow_manager.cleanup_old_flows()
            last_cleanup = time.time()
        
        # Check if DDoS simulation is active
        if config.ddos_active and time.time() < config.ddos_end_time:
            # Generate DDoS traffic - many requests from same region
            ddos_ip, ddos_geocode = generate_ip_from_region_with_geocode(config.ddos_region)
            for _ in range(random.randint(50, 100)):
                log_entry = generate_log_entry(
                    override_ip=ddos_ip,
                    override_geocode=ddos_geocode,
                    user_db_url=config.user_db_url,
                    is_ddos=True,
                    error_manager=config.error_manager,
                    flow_manager=config.flow_manager
                )
                print(json.dumps(log_entry), flush=True)
                track_log_metrics(log_entry, metrics)
            time.sleep(0.1)  # Short burst interval during DDoS
        elif config.ddos_active and time.time() >= config.ddos_end_time:
            # DDoS simulation ended
            config.ddos_active = False
            config.ddos_region = None
            print(f"DDoS simulation ended", file=sys.stderr, flush=True)
        else:
            # Normal traffic generation with flows
            
            # Decide: flow request or random request
            if config.flow_manager.should_generate_random_request():
                # Generate random request (anonymous user)
                log_entry = generate_log_entry(
                    user_db_url=config.user_db_url,
                    error_manager=config.error_manager,
                    flow_manager=config.flow_manager
                )
                print(json.dumps(log_entry), flush=True)
                track_log_metrics(log_entry, metrics)
                time.sleep(random.uniform(config.min_interval, config.max_interval))
            else:
                # Try to get next step from existing flow
                flow_request = config.flow_manager.get_next_flow_request()
                
                if flow_request:
                    # Continue existing flow
                    uri, flow_context = flow_request
                    log_entry = generate_log_entry(
                        user_db_url=config.user_db_url,
                        uri=uri,
                        flow_context=flow_context,
                        error_manager=config.error_manager,
                        flow_manager=config.flow_manager
                    )
                    print(json.dumps(log_entry), flush=True)
                    track_log_metrics(log_entry, metrics)
                    time.sleep(config.flow_manager.get_step_delay())
                else:
                    # Start new flow
                    # Get user from database
                    user_id, user_name = fetch_user_from_db(config.user_db_url)
                    client_ip, geocode = generate_distributed_ip_with_geocode()
                    user_agent = fake.user_agent()
                    
                    # Start the flow (add geocode to flow context)
                    flow = config.flow_manager.start_new_flow(
                        client_ip=client_ip,
                        user_agent=user_agent,
                        user_id=user_id,
                        user_name=user_name,
                        geocode=geocode
                    )
                    
                    if flow:
                        # Generate first step of the flow
                        flow_request = config.flow_manager.get_next_flow_request()
                        if flow_request:
                            uri, flow_context = flow_request
                            log_entry = generate_log_entry(
                                user_db_url=config.user_db_url,
                                uri=uri,
                                flow_context=flow_context,
                                error_manager=config.error_manager,
                                flow_manager=config.flow_manager
                            )
                            print(json.dumps(log_entry), flush=True)
                            track_log_metrics(log_entry, metrics)
                            time.sleep(config.flow_manager.get_step_delay())
                        else:
                            # Flow was abandoned immediately, generate random
                            log_entry = generate_log_entry(
                                user_db_url=config.user_db_url,
                                error_manager=config.error_manager,
                                flow_manager=config.flow_manager
                            )
                            print(json.dumps(log_entry), flush=True)
                            track_log_metrics(log_entry, metrics)
                            time.sleep(random.uniform(config.min_interval, config.max_interval))
                    else:
                        # Fallback to random if no flows configured
                        log_entry = generate_log_entry(
                            user_db_url=config.user_db_url,
                            error_manager=config.error_manager,
                            flow_manager=config.flow_manager
                        )
                        print(json.dumps(log_entry), flush=True)
                        track_log_metrics(log_entry, metrics)
                        time.sleep(random.uniform(config.min_interval, config.max_interval))

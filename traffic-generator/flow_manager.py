"""
Flow Manager - Manages user flow state machines
"""
import random
import yaml
import uuid
import sys
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from faker import Faker

fake = Faker()


class FlowStateMachine:
    """Represents a single user flow with consistent context."""
    
    def __init__(self, flow_name: str, steps: List[str], user_context: Dict[str, Any], placeholder_config: Dict):
        self.flow_name = flow_name
        self.steps = steps
        self.current_step = 0
        self.user_context = user_context
        self.placeholder_config = placeholder_config
        self.placeholder_values = {}
        self.started_at = datetime.utcnow()
        # Generate a unique session ID for this flow
        self.session_id = str(uuid.uuid4())
        
    def get_next_step(self) -> Optional[str]:
        """Get the next step in the flow and advance."""
        if self.current_step >= len(self.steps):
            return None
        
        step = self.steps[self.current_step]
        self.current_step += 1
        
        # Replace placeholders with consistent values
        return self._resolve_placeholders(step)
    
    def _resolve_placeholders(self, path: str) -> str:
        """Replace placeholders in path with generated values."""
        if ':' not in path:
            return path
        
        parts = path.split('/')
        resolved_parts = []
        
        for part in parts:
            if part.startswith(':'):
                placeholder_name = part[1:]  # Remove the ':'
                
                # Reuse existing value if already generated for this flow
                if placeholder_name in self.placeholder_values:
                    resolved_parts.append(str(self.placeholder_values[placeholder_name]))
                else:
                    # Generate new value
                    value = self._generate_placeholder_value(placeholder_name)
                    self.placeholder_values[placeholder_name] = value
                    resolved_parts.append(str(value))
            else:
                resolved_parts.append(part)
        
        return '/'.join(resolved_parts)
    
    def _generate_placeholder_value(self, placeholder_name: str) -> Any:
        """Generate a value for a placeholder based on configuration."""
        if placeholder_name not in self.placeholder_config:
            # Default to random integer if not configured
            return random.randint(1000, 9999)
        
        config = self.placeholder_config[placeholder_name]
        placeholder_type = config.get('type', 'integer')
        
        if placeholder_type == 'integer':
            return random.randint(config.get('min', 1), config.get('max', 9999))
        elif placeholder_type == 'choice':
            return random.choice(config.get('values', ['default']))
        else:
            return random.randint(1000, 9999)
    
    def is_complete(self) -> bool:
        """Check if the flow is complete."""
        return self.current_step >= len(self.steps)
    
    def get_progress(self) -> float:
        """Get flow completion progress (0.0 to 1.0)."""
        return self.current_step / len(self.steps) if self.steps else 1.0


class FlowManager:
    """Manages multiple concurrent user flows."""
    
    def __init__(self, config_path: str = '/app/user_flows.yml', server_assignment_url: str = "http://server-assignment:8100"):
        self.config_path = config_path
        self.server_assignment_url = server_assignment_url
        self.flows_config = {}
        self.placeholder_config = {}
        self.method_mapping = {}
        self.config = {}
        self.active_flows: List[FlowStateMachine] = []
        self.load_config()
    
    def load_config(self):
        """Load flow configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                self.flows_config = data.get('flows', {})
                self.placeholder_config = data.get('placeholders', {})
                self.method_mapping = data.get('method_mapping', {})
                self.config = data.get('config', {})
                print(f"Loaded {len(self.flows_config)} flow definitions", file=sys.stderr, flush=True)
                print(f"Loaded {len(self.method_mapping)} method mappings", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"Error loading flow config: {e}", file=sys.stderr, flush=True)
            # Use defaults if config fails to load
            self.flows_config = {}
            self.placeholder_config = {}
            self.config = {
                'random_request_percentage': 30,
                'flow_step_delay_min': 0.5,
                'flow_step_delay_max': 3.0,
                'flow_abandon_probability': 0.15
            }
    
    def should_generate_random_request(self) -> bool:
        """Determine if next request should be random (not from a flow)."""
        random_pct = self.config.get('random_request_percentage', 30)
        return random.random() * 100 < random_pct
    
    def assign_server_to_session(self, session_id: str, client_ip: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict]:
        """Assign a server to a session via the server-assignment API."""
        try:
            response = requests.post(
                f"{self.server_assignment_url}/assign",
                json={
                    "session_id": session_id,
                    "client_ip": client_ip,
                    "user_id": user_id
                },
                timeout=2
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Server assignment failed: {response.status_code}", file=sys.stderr, flush=True)
                return None
        except Exception as e:
            print(f"Error assigning server: {e}", file=sys.stderr, flush=True)
            return None
    
    def start_new_flow(self, client_ip: str, user_agent: str, user_id: Optional[int], user_name: Optional[str], geocode: Optional[Dict] = None) -> FlowStateMachine:
        """Start a new flow with consistent user context."""
        if not self.flows_config:
            return None
        
        # Select flow based on weights
        flow_name = self._select_weighted_flow()
        flow_def = self.flows_config[flow_name]
        
        # Create flow to get session_id
        flow = FlowStateMachine(
            flow_name=flow_name,
            steps=flow_def['steps'],
            user_context={},  # Will be populated below
            placeholder_config=self.placeholder_config
        )
        
        # Assign server to this session
        server_assignment = self.assign_server_to_session(
            session_id=flow.session_id,
            client_ip=client_ip,
            user_id=user_id
        )
        
        # Create user context that will be consistent throughout the flow
        user_context = {
            'client_ip': client_ip,
            'user_agent': user_agent,
            'user_id': user_id,
            'user_name': user_name,
            'flow_name': flow_name
        }
        
        # Add geocode if provided
        if geocode:
            user_context['geocode'] = geocode
        
        # Update flow context
        flow.user_context = user_context
        
        self.active_flows.append(flow)
        return flow
    
    def _select_weighted_flow(self) -> str:
        """Select a flow based on weights."""
        flows = []
        weights = []
        
        for name, config in self.flows_config.items():
            flows.append(name)
            weights.append(config.get('weight', 1))
        
        return random.choices(flows, weights=weights, k=1)[0]
    
    def get_next_flow_request(self) -> Optional[tuple]:
        """Get next request from active flows (round-robin style)."""
        if not self.active_flows:
            return None
        
        # Randomly select a flow to advance
        flow = random.choice(self.active_flows)
        
        # Check if flow should be abandoned
        if random.random() < self.config.get('flow_abandon_probability', 0.15):
            self.active_flows.remove(flow)
            return None
        
        # Get next step
        next_step = flow.get_next_step()
        
        if next_step is None or flow.is_complete():
            # Flow complete, remove it
            self.active_flows.remove(flow)
            if next_step is None:
                return None
        
        # Include session_id in the context
        context_with_session = flow.user_context.copy()
        context_with_session['session_id'] = flow.session_id
        
        return (next_step, context_with_session)
    
    def get_step_delay(self) -> float:
        """Get delay between flow steps."""
        min_delay = self.config.get('flow_step_delay_min', 0.5)
        max_delay = self.config.get('flow_step_delay_max', 3.0)
        return random.uniform(min_delay, max_delay)
    
    def get_active_flow_count(self) -> int:
        """Get number of active flows."""
        return len(self.active_flows)
    
    def cleanup_old_flows(self, max_age_seconds: int = 300):
        """Remove flows that have been active too long."""
        now = datetime.utcnow()
        self.active_flows = [
            flow for flow in self.active_flows
            if (now - flow.started_at).total_seconds() < max_age_seconds
        ]
    
    def get_http_method(self, uri: str) -> str:
        """
        Get HTTP method for a URI based on method_mapping.
        Returns the method if a pattern matches, otherwise returns 'GET'.
        
        Args:
            uri: The URI path to check
            
        Returns:
            HTTP method (GET, POST, PUT, DELETE, etc.)
        """
        if not uri or not self.method_mapping:
            return 'GET'
        
        # Check each pattern in method_mapping
        # Patterns are matched using substring matching
        for pattern, method in self.method_mapping.items():
            if pattern in uri:
                return method
        
        # Default to GET if no match found
        return 'GET'

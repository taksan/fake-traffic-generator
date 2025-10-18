"""
Error Manager - Generates realistic HTTP errors based on context
"""
import random
from typing import Optional, Tuple


class ErrorManager:
    """Manages realistic error generation based on request context."""
    
    # Base error rates
    BASE_ERROR_RATE = 0.15  # 15% of requests have errors
    ANONYMOUS_ERROR_MULTIPLIER = 2.0  # Anonymous users error 2x more
    DDOS_ERROR_RATE = 0.70  # 70% of DDoS requests error
    
    # Error distributions by context
    ERROR_TYPES = {
        'authenticated': {
            200: 70,  # Success
            201: 10,  # Created
            204: 3,   # No content
            301: 2,   # Redirect
            400: 3,   # Bad request
            401: 1,   # Unauthorized (session expired)
            403: 2,   # Forbidden
            404: 4,   # Not found
            429: 1,   # Rate limit
            500: 3,   # Server error
            503: 1,   # Service unavailable
        },
        'anonymous': {
            200: 60,  # Success
            201: 5,   # Created
            301: 3,   # Redirect
            400: 8,   # Bad request (invalid input)
            401: 10,  # Unauthorized (not logged in)
            403: 5,   # Forbidden
            404: 6,   # Not found
            429: 1,   # Rate limit
            500: 1,   # Server error
            503: 1,   # Service unavailable
        },
        'ddos': {
            200: 15,  # Some succeed
            400: 10,  # Bad request
            401: 5,   # Unauthorized
            403: 15,  # Forbidden (blocked)
            404: 30,  # Not found (random paths)
            429: 20,  # Rate limit (most common)
            500: 3,   # Server overload
            503: 2,   # Service unavailable
        }
    }
    
    # URL-specific error patterns
    URL_ERROR_PATTERNS = {
        '/login': {
            200: 70,
            400: 15,  # Invalid credentials
            401: 10,  # Bad password
            429: 3,   # Too many attempts
            500: 2,
        },
        '/checkout': {
            200: 65,
            400: 15,  # Invalid payment info
            402: 8,   # Payment required (card declined)
            500: 7,   # Payment processing error
            503: 5,   # Payment gateway down
        },
        '/add_to_cart': {
            200: 80,
            400: 8,   # Invalid product
            404: 5,   # Product not found
            409: 5,   # Out of stock
            500: 2,
        },
        '/cart': {
            200: 85,
            400: 5,
            404: 5,   # Cart not found
            410: 3,   # Cart expired
            500: 2,
        },
        '/products': {
            200: 85,
            404: 10,  # Product not found
            500: 3,
            503: 2,
        },
        '/profile': {
            200: 80,
            401: 10,  # Not authenticated
            403: 5,   # Not authorized
            404: 3,   # Profile not found
            500: 2,
        },
        '/order': {
            200: 75,
            400: 10,  # Invalid order
            404: 8,   # Order not found
            403: 5,   # Not your order
            500: 2,
        },
    }
    
    def __init__(self):
        pass
    
    def get_status_code(self, uri: str, is_authenticated: bool, is_ddos: bool = False, 
                       method: str = "GET") -> Tuple[int, str]:
        """
        Generate a status code based on context.
        
        Returns:
            Tuple of (status_code, error_message)
        """
        # DDoS requests have high error rate
        if is_ddos:
            return self._get_ddos_error(uri, method)
        
        # Check for URL-specific error patterns
        status_code = self._get_url_specific_error(uri, is_authenticated, method)
        if status_code:
            return status_code, self._get_error_message(status_code, uri, method)
        
        # General error generation
        context = 'authenticated' if is_authenticated else 'anonymous'
        error_rate = self.BASE_ERROR_RATE
        
        if not is_authenticated:
            error_rate *= self.ANONYMOUS_ERROR_MULTIPLIER
        
        # Decide if this request should error
        if random.random() > error_rate:
            # Success - return 2xx
            status_code = random.choices(
                [200, 201, 204],
                weights=[85, 10, 5],
                k=1
            )[0]
        else:
            # Error - use context-based distribution
            codes = list(self.ERROR_TYPES[context].keys())
            weights = list(self.ERROR_TYPES[context].values())
            status_code = random.choices(codes, weights=weights, k=1)[0]
        
        return status_code, self._get_error_message(status_code, uri, method)
    
    def _get_ddos_error(self, uri: str, method: str) -> Tuple[int, str]:
        """Generate error for DDoS request."""
        codes = list(self.ERROR_TYPES['ddos'].keys())
        weights = list(self.ERROR_TYPES['ddos'].values())
        status_code = random.choices(codes, weights=weights, k=1)[0]
        return status_code, self._get_error_message(status_code, uri, method)
    
    def _get_url_specific_error(self, uri: str, is_authenticated: bool, 
                                method: str) -> Optional[int]:
        """Check if URL has specific error patterns."""
        # Match URL patterns
        for pattern, error_dist in self.URL_ERROR_PATTERNS.items():
            if pattern in uri:
                # Use URL-specific distribution
                codes = list(error_dist.keys())
                weights = list(error_dist.values())
                
                # Adjust weights for anonymous users
                if not is_authenticated and 401 in codes:
                    # Increase 401 errors for anonymous
                    idx = codes.index(401)
                    weights[idx] *= 3
                
                return random.choices(codes, weights=weights, k=1)[0]
        
        return None
    
    def _get_error_message(self, status_code: int, uri: str, method: str) -> str:
        """Generate contextual error message."""
        messages = {
            200: "Success",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            400: self._get_400_message(uri),
            401: "Unauthorized - Authentication required",
            402: "Payment Required - Card declined",
            403: "Forbidden - Access denied",
            404: "Not Found",
            409: "Conflict - Item out of stock",
            410: "Gone - Resource expired",
            429: "Too Many Requests - Rate limit exceeded",
            500: "Internal Server Error",
            503: "Service Unavailable",
        }
        
        return messages.get(status_code, f"HTTP {status_code}")
    
    def _get_400_message(self, uri: str) -> str:
        """Generate specific 400 error message based on URL."""
        if '/login' in uri:
            return random.choice([
                "Bad Request - Invalid credentials",
                "Bad Request - Missing password",
                "Bad Request - Invalid email format",
            ])
        elif '/checkout' in uri:
            return random.choice([
                "Bad Request - Invalid payment information",
                "Bad Request - Missing billing address",
                "Bad Request - Invalid card number",
            ])
        elif '/add_to_cart' in uri:
            return random.choice([
                "Bad Request - Invalid product ID",
                "Bad Request - Invalid quantity",
                "Bad Request - Product unavailable",
            ])
        elif '/profile' in uri or '/user' in uri:
            return random.choice([
                "Bad Request - Invalid user data",
                "Bad Request - Missing required fields",
            ])
        else:
            return "Bad Request - Invalid parameters"
    
    def get_response_bytes(self, status_code: int) -> int:
        """Generate realistic response size based on status code."""
        if status_code < 300:
            # Success responses are larger
            return random.randint(1000, 50000)
        elif status_code < 400:
            # Redirects are small
            return random.randint(100, 500)
        elif status_code < 500:
            # Client errors are medium
            return random.randint(200, 2000)
        else:
            # Server errors are small (error pages)
            return random.randint(150, 1500)

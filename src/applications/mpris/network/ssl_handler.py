"""SSL/HTTPS handling for secure connections."""
import time

class SSLHandler:
    """Handles SSL/HTTPS connection configuration and error recovery."""
    
    def __init__(self, strict_privacy=True):
        """Initialize SSL handler with privacy settings.
        
        Args:
            strict_privacy: If True, enforces HTTPS and fails on non-secure connections
        """
        self.strict_privacy = strict_privacy
        self.https_failed = False
        self.consecutive_failures = {}
    
    def enforce_https(self, url):
        """Enforce HTTPS if privacy mode is enabled.
        
        Args:
            url: The URL to check/modify
            
        Returns:
            URL with HTTPS protocol if strict privacy is enabled
        """
        if self.strict_privacy:
            if url.startswith('http:'):
                url = url.replace('http:', 'https:', 1)
                print("Warning: Forcing HTTPS connection for security")
            
            if not url.startswith('https:'):
                print("WARNING: Server URL doesn't use HTTPS - your media data could be exposed")
        
        return url
    
    def handle_ssl_error(self, endpoint, error):
        """Handle SSL connection errors with backoff.
        
        Args:
            endpoint: The API endpoint that failed
            error: The exception or error message
            
        Returns:
            Dict with error info and backoff duration
        """
        print(f"HTTPS connection error: {error}")
        self.consecutive_failures[endpoint] = self.consecutive_failures.get(endpoint, 0) + 1
        
        failure_count = self.consecutive_failures[endpoint]
        backoff = min(5 * (2 ** failure_count), 120)
        
        print(f"Privacy mode enforces HTTPS - connection failed. Retrying in {backoff}s")
        print("Troubleshooting tips:")
        print("1. Verify your server supports HTTPS with a valid certificate")
        print("2. Check that the port is correct and accessible")
        print("3. Confirm your network allows HTTPS connections")
        
        return {
            "error": f"Secure connection failed: {error}",
            "backoff": backoff,
            "failures": failure_count
        }
    
    def reset_failure_count(self, endpoint):
        """Reset failure counter for an endpoint after successful connection."""
        if endpoint in self.consecutive_failures:
            self.consecutive_failures[endpoint] = 0
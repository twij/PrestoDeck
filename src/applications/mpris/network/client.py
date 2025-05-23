"""Base HTTP client with caching support for MicroPython."""
import urequests as requests
import ujson as json
import time
from applications.mpris.network.etag_cache import ETagCache
from applications.mpris.network.ssl_handler import SSLHandler

class CachingClient:
    """HTTP client with ETag caching and error recovery."""
    
    def __init__(self, base_url, api_token=None, strict_privacy=True):
        """Initialize the HTTP client.
        
        Args:
            base_url: Base server URL
            api_token: Optional API auth token
            strict_privacy: Whether to enforce HTTPS
        """
        self.ssl_handler = SSLHandler(strict_privacy)
        self.server_url = self.ssl_handler.enforce_https(base_url)
        self.api_token = api_token
        self.etag_cache = ETagCache()
        self.response_cache = {}
        self.binary_cache = {}
        
        self.check_intervals = {
            "default": 5,
            "current": 5,
            "artwork": 5
        }
        self.last_check = {}
    
    def make_request(self, endpoint, method="GET", data=None, force=False):
        """Make request to the server with caching and error handling.
        
        Args:
            endpoint: API endpoint to request
            method: HTTP method (GET, POST)
            data: Optional data for POST requests
            force: Whether to force a fresh request
            
        Returns:
            API response data or cached response
        """
        url = f"{self.server_url}/{endpoint}"
        current_time = time.time()
        
        interval = self.check_intervals.get(endpoint, self.check_intervals["default"])
        if not force and endpoint in self.last_check:
            if current_time - self.last_check[endpoint] < interval:
                cached = self.response_cache.get(endpoint)
                if cached:
                    print(f"Using cached response for {endpoint} (within interval)")
                    return cached
        
        self.last_check[endpoint] = current_time
        
        headers = {}
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
            
        etag = self.etag_cache.get(endpoint)
        if etag:
            headers['If-None-Match'] = etag
            print(f"Sending If-None-Match: {etag}")
        else:
            print(f"No ETag available for {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            
            self.ssl_handler.reset_failure_count(endpoint)
            
            if response.status_code == 401:
                print("Authentication failed - check your API token")
                response.close()
                return {"error": "Authentication failed"}
            
            if response.status_code == 304:
                print(f"304 Not Modified for {endpoint} - using cached response")
                if endpoint in self.response_cache:
                    result = {}
                    for key, value in self.response_cache[endpoint].items():
                        result[key] = value
                        
                    result['from_304_cache'] = True
                    
                    if endpoint == "artwork" and 'art_data' in result:
                        result['art_from_304_cache'] = True
                        if endpoint in self.binary_cache:
                            _, cached_binary = self.binary_cache[endpoint]
                            if isinstance(cached_binary, (bytes, memoryview)):
                                result['art_data'] = cached_binary
                                result['is_binary'] = True
                    
                    return result
                else:
                    self.etag_cache.delete(endpoint)
                    return {"error": "304 with missing cache"}
            
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                try:
                    result = response.json()
                    self.response_cache[endpoint] = result.copy()
                    
                    if 'ETag' in response.headers:
                        self.etag_cache.set(endpoint, response.headers['ETag'])
                    
                    return result
                except Exception as json_error:
                    print(f"Error parsing JSON: {json_error}")
                    return {"error": f"Failed to parse response: {json_error}"}
            elif endpoint == "artwork":
                try:
                    raw_data = response.content
                    
                    if 'ETag' in response.headers:
                        self.etag_cache.set(endpoint, response.headers['ETag'])
                    
                    result = {
                        "art_data": raw_data,
                        "content_type": content_type
                    }
                    
                    self.binary_cache[endpoint] = (time.time(), raw_data)
                    self.response_cache[endpoint] = result.copy()
                    
                    return result
                except Exception as bin_error:
                    print(f"Error handling binary data: {bin_error}")
                    return {"error": f"Failed to process binary data: {bin_error}"}
            else:
                print(f"Received non-JSON response with Content-Type: {content_type}")
                return {"error": "Unexpected Content-Type"}
                
        except OSError as e:
            error_info = self.ssl_handler.handle_ssl_error(endpoint, e)
            self.check_intervals[endpoint] = error_info["backoff"]
            return {"error": error_info["error"]}
        
        except Exception as e:
            print(f"Request error: {e}")
            
            self.ssl_handler.consecutive_failures[endpoint] = self.ssl_handler.consecutive_failures.get(endpoint, 0) + 1
            failure_count = self.ssl_handler.consecutive_failures[endpoint]
            backoff = min(5 * (2 ** failure_count), 120)
            self.check_intervals[endpoint] = backoff
            
            print(f"Retrying in {backoff}s")
            return {"error": f"Request failed: {e}"}
        finally:
            if 'response' in locals():
                try:
                    response.close()
                except:
                    pass
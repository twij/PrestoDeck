"""ETag caching for efficient network requests."""
import os

class ETagCache:
    """Handles loading, saving, and managing HTTP ETags."""
    
    def __init__(self):
        """Initialize the ETag cache."""
        self.etags = {}
        self.etag_path = None
        self.load()
    
    def get(self, endpoint):
        """Get ETag for an endpoint if available."""
        return self.etags.get(endpoint)
    
    def set(self, endpoint, etag):
        """Set ETag for an endpoint and save to storage."""
        if etag:
            self.etags[endpoint] = etag
            self.save()
            print(f"Received new ETag: {etag} for {endpoint}")
    
    def delete(self, endpoint):
        """Remove ETag for an endpoint."""
        if endpoint in self.etags:
            del self.etags[endpoint]
            self.save()
    
    def clear(self):
        """Clear all ETags."""
        self.etags = {}
        self.save()
    
    def save(self):
        """Save ETags to persistent storage with error handling - can remove now?"""
        try:
            if not self.etags or not isinstance(self.etags, dict):
                print("No valid ETags to save")
                return
                
            potential_paths = [
                "etags.txt",
                "/etags.txt",
                "/flash/etags.txt",
                "/sd/etags.txt"
            ]
            
            saved = False
            for path in potential_paths:
                try:
                    with open(path, 'w') as f:
                        for endpoint, etag in self.etags.items():
                            f.write(f"{endpoint}:{etag}\n")
                    saved = True
                    self.etag_path = path
                    print(f"Saved {len(self.etags)} ETags to {path}")
                    break
                except OSError as e:
                    print(f"Could not save to {path}: {e}")
                    continue
            
            if not saved:
                print("Failed to save ETags to any location")
        except Exception as e:
            print(f"Failed to save ETags: {e}")
    
    def load(self):
        """Load ETags from storage."""
        self.etags = {}
        
        if hasattr(self, 'etag_path') and self.etag_path is not None:
            try:
                with open(self.etag_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            endpoint, etag = line.split(':', 1)
                            self.etags[endpoint] = etag
                print(f"Loaded {len(self.etags)} ETags from {self.etag_path}")
                return
            except Exception as e:
                print(f"Could not load from previous path {self.etag_path}: {e}")
        
        potential_paths = [
            "etags.txt",
            "/etags.txt",
            "/flash/etags.txt",
            "/sd/etags.txt"
        ]
        
        for path in potential_paths:
            try:
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if ':' in line:
                            endpoint, etag = line.split(':', 1)
                            self.etags[endpoint] = etag
                self.etag_path = path
                print(f"Loaded {len(self.etags)} ETags from {path}")
                return
            except OSError:
                continue
            except Exception as e:
                print(f"Error loading from {path}: {e}")
        
        print("No saved ETags found in any location")
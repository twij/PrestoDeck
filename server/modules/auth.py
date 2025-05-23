"""Authentication module for MPRIS server API."""
from functools import wraps
from flask import request, jsonify
from config import get_api_token

API_TOKEN = get_api_token()

def require_auth(func):
    """API token authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            token = request.args.get('token')
            
        if token and token == API_TOKEN:
            return func(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    
    return wrapper
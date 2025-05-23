"""SSL certificate utilities for MPRIS server."""
import os
import socket
from config import CERT_FILE, KEY_FILE

def create_ssl_context():
    """Create SSL context with self-signed certificate if needed."""
    if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
        print("Generating self-signed certificate for HTTPS...")
        try:
            from OpenSSL import crypto
            
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 2048)

            cert = crypto.X509()
            cert.get_subject().C = "GB"
            cert.get_subject().ST = "State"
            cert.get_subject().L = "City"
            cert.get_subject().O = "PrestoDeck"
            cert.get_subject().OU = "MPRIS Server"
            cert.get_subject().CN = socket.gethostname()
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            cert.sign(k, 'sha256')
            
            with open(CERT_FILE, "wb") as f:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            with open(KEY_FILE, "wb") as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

            os.chmod(CERT_FILE, 0o644)
            os.chmod(KEY_FILE, 0o600)
            
            print(f"Created self-signed certificate at {CERT_FILE}")
        except ImportError:
            print("pyOpenSSL not installed. Using Flask's adhoc SSL context instead.")
            return 'adhoc'
    
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return (CERT_FILE, KEY_FILE)
    else:
        print("Using Flask's adhoc SSL context as fallback.")
        return 'adhoc'

def get_server_ip():
    """Get the server's IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address
#!/usr/bin/env python3

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket
import json
import sys
from urllib.parse import urlparse

def test_dns(hostname):
    """Test if DNS resolution works"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✓ DNS Resolution: {hostname} -> {ip}")
        return ip
    except socket.gaierror as e:
        print(f"✗ DNS Resolution Failed: {e}")
        return None

def test_socket_connect(hostname, port, timeout=5):
    """Test raw socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()
        if result == 0:
            print(f"✓ Socket Connection: {hostname}:{port} is reachable")
            return True
        else:
            print(f"✗ Socket Connection Failed: Port {port} is not open (error code: {result})")
            return False
    except socket.timeout:
        print(f"✗ Socket Connection Timeout: Could not connect to {hostname}:{port} within {timeout}s")
        return False
    except Exception as e:
        print(f"✗ Socket Connection Error: {e}")
        return False

def check_endpoint_fast(url, method='GET', headers=None, data=None):
    """
    Fast endpoint check with aggressive timeouts and no connection pooling
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    
    print(f"=== Connection Diagnostics ===")
    print(f"URL: {url}")
    print(f"Host: {hostname}")
    print(f"Port: {port}")
    print(f"Scheme: {parsed.scheme}\n")
    
    # Step 1: Test DNS
    ip = test_dns(hostname)
    if not ip:
        return None, None
    
    # Step 2: Test socket connection
    print()
    if not test_socket_connect(hostname, port, timeout=3):
        print("\n⚠️  Cannot establish TCP connection. Possible issues:")
        print("  - Firewall blocking the connection")
        print("  - Host is down or unreachable")
        print("  - Wrong port number")
        print("  - Network connectivity issues")
        return None, None
    
    print(f"\n=== HTTP Request ===")
    
    try:
        # Create a session with disabled connection pooling
        session = requests.Session()
        
        # Disable connection pooling and keep-alive
        session.mount('http://', HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0))
        session.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0))
        
        # Set Connection: close header
        if headers is None:
            headers = {}
        headers['Connection'] = 'close'
        
        # Make request with aggressive timeouts
        # (connect timeout, read timeout)
        response = session.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=(5, 10),  # 5s to connect, 10s to read
            stream=False,
            allow_redirects=True
        )
        
        status_code = response.status_code
        
        # Parse response
        try:
            response_data = response.json()
            response_text = json.dumps(response_data, indent=2)[:2000]
        except:
            response_text = response.text[:2000]
        
        # Close everything
        response.close()
        session.close()
        
        print(f"✓ HTTP Request Successful")
        print(f"\nStatus Code: {status_code}")
        print(f"Success: {'✓ YES' if status_code == 200 else '✗ NO'}")
        print(f"\nResponse Headers:")
        for key, value in list(response.headers.items())[:10]:
            print(f"  {key}: {value}")
        print(f"\nResponse Body (first 2000 chars):")
        print(response_text)
        
        return status_code, response_text
        
    except requests.exceptions.ConnectTimeout:
        print(f"✗ Connection Timeout: Could not connect within 5 seconds")
        print("  - Server might be overloaded")
        print("  - Network latency is too high")
        return None, None
    except requests.exceptions.ReadTimeout:
        print(f"✗ Read Timeout: Server didn't respond within 10 seconds")
        print("  - Server is processing but too slow")
        return None, None
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL Error: {e}")
        print("  - Try using http:// instead of https://")
        print("  - Or add verify=False (not recommended for production)")
        return None, None
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        return None, None
    except Exception as e:
        print(f"✗ Unexpected Error: {type(e).__name__} - {e}")
        return None, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python endpoint_check_v2.py <URL> [METHOD]")
        print("\nExamples:")
        print("  python endpoint_check_v2.py https://httpbin.org/get")
        print("  python endpoint_check_v2.py http://localhost:8080/api/health")
        print("  python endpoint_check_v2.py https://api.example.com/status POST")
        sys.exit(1)
    
    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'GET'
    
    check_endpoint_fast(url, method=method)


import requests
import json
import sys

def check_endpoint(url, method='GET', headers=None, data=None, timeout=10):
    """
    Check endpoint and return status code and response
    
    Args:
        url: The endpoint URL to check
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dict
        data: Optional request body
        timeout: Request timeout in seconds
    """
    try:
        # Make request with timeout and explicitly close connection
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=timeout,
            # These parameters help prevent hanging connections
            stream=False,  # Don't stream the response
        )
        
        # Get response details
        status_code = response.status_code
        
        # Try to parse as JSON, fall back to text
        try:
            response_data = response.json()
            response_text = json.dumps(response_data, indent=2)
        except:
            response_text = response.text[:1000]  # Limit text response
        
        # Explicitly close the connection
        response.close()
        
        print(f"Status Code: {status_code}")
        print(f"Success: {status_code == 200}")
        print(f"\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print(f"\nResponse Body (first 1000 chars):")
        print(response_text)
        
        return status_code, response_text
        
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out after {timeout} seconds")
        return None, None
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection error - {e}")
        return None, None
    except Exception as e:
        print(f"ERROR: {type(e).__name__} - {e}")
        return None, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python endpoint_check.py <URL> [METHOD]")
        print("Example: python endpoint_check.py https://api.example.com/health GET")
        sys.exit(1)
    
    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'GET'
    
    print(f"Checking endpoint: {url}")
    print(f"Method: {method}\n")
    
    check_endpoint(url, method=method)

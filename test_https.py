import requests
import sys

def test_https(url):
    """Test if a URL properly redirects to HTTPS"""
    try:
        # Try to access the HTTP version
        http_url = url.replace('https://', 'http://')
        print(f"Testing HTTP redirect: {http_url}")
        
        # Disable SSL verification for self-signed certs
        response = requests.get(http_url, allow_redirects=True, verify=False)
        
        # Check if we were redirected to HTTPS
        final_url = response.url
        print(f"Final URL: {final_url}")
        
        if final_url.startswith('https://'):
            print("✅ Success! HTTP redirects to HTTPS")
            return True
        else:
            print("❌ Failed! HTTP does not redirect to HTTPS")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HTTPS: {str(e)}")
        return False

if __name__ == "__main__":
    # Use command line argument or default to localhost
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    test_https(url)
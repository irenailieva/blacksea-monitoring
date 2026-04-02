import requests

def test_upload():
    url = "http://localhost:8000/scenes/upload"
    
    # Create fake TIFF content
    file_content = b"fake_tiff_data_here"
    
    files = {
        'file': ('test.tif', file_content, 'image/tiff')
    }
    
    print(f"Uploading files to {url}...")
    try:
        # Assuming no auth required or just a public endpoint?
        # Wait, the endpoint requires "researcher" or "admin".
        # If I don't provide a valid token cookie / session cookie, it will return 401 or 403!
        response = requests.post(url, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_upload()

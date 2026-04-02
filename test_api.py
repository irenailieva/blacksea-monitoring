import requests

def test():
    session = requests.Session()
    # Login
    resp = session.post("http://localhost:8000/auth/login", json={"username": "tester_admin", "password": "123", "set_cookie": True})
    print("Login:", resp.status_code, resp.text)
    token = resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Trigger ETL
    resp2 = session.post("http://localhost:8000/scenes/etl-trigger")
    print("ETL Trigger:", resp2.status_code, resp2.text)

    # File upload
    file_content = b"fake_tiff_data_here"
    files = {
        'file': ('test.tif', file_content, 'image/tiff')
    }
    resp3 = session.post("http://localhost:8000/scenes/upload", files=files)
    print("Upload:", resp3.status_code, resp3.text)

if __name__ == "__main__":
    test()

import requests, json, sys

BASE = 'http://localhost:8000'
session = requests.Session()

# 1. Login as admin
print('--- 1. Login ---')
r = session.post(
    f'{BASE}/auth/login',
    json={'username': 'admin', 'password': 'admin123', 'set_cookie': True}
)
print(f'  Status: {r.status_code}')
if r.status_code != 200:
    print(f'  Body: {r.text}')
    sys.exit(1)
token = r.json()['access_token']
session.headers.update({'Authorization': f'Bearer {token}'})
print('  OK, got token')

# 2. List regions
print('--- 2. GET /regions ---')
r = session.get(f'{BASE}/regions')
print(f'  Status: {r.status_code}')
regions = r.json()
print(f'  Count: {len(regions)}')

# 3. Create region
print('--- 3. POST /regions ---')
payload = {
    'name': 'TEST_CRUD_Region',
    'description': 'Created by automated CRUD test',
    'area_km2': 5.0,
    'geometry': {
        'type': 'Polygon',
        'coordinates': [[[27.9, 43.1], [28.0, 43.1], [28.0, 43.2], [27.9, 43.2], [27.9, 43.1]]]
    }
}
r = session.post(f'{BASE}/regions', json=payload)
print(f'  Status: {r.status_code}')
if r.status_code != 201:
    print(f'  Body: {r.text}')
    sys.exit(1)
created = r.json()
rid = created['id']
name = created['name']
print(f'  Created ID: {rid}, name: {name}')

# 4. Read single region
print('--- 4. GET /regions/{id} ---')
r = session.get(f'{BASE}/regions/{rid}')
print(f'  Status: {r.status_code}')
reg = r.json()
print(f'  name={reg["name"]}, desc={reg.get("description")}')

# 5. Update region
print('--- 5. PUT /regions/{id} ---')
r = session.put(f'{BASE}/regions/{rid}', json={'name': 'TEST_CRUD_Region_EDITED', 'description': 'Updated by CRUD test'})
print(f'  Status: {r.status_code}')
if r.status_code != 200:
    print(f'  Body: {r.text}')
    sys.exit(1)
updated = r.json()
print(f'  Updated name: {updated["name"]}, desc: {updated.get("description")}')

# 6. Delete region
print('--- 6. DELETE /regions/{id} ---')
r = session.delete(f'{BASE}/regions/{rid}')
print(f'  Status: {r.status_code}')
if r.status_code != 204:
    print(f'  Body: {r.text}')
    sys.exit(1)
print('  Deleted OK')

# 7. Confirm gone with 404
print('--- 7. GET /regions/{id} (expect 404) ---')
r = session.get(f'{BASE}/regions/{rid}')
print(f'  Status: {r.status_code} (expected 404)')
if r.status_code != 404:
    print('  FAIL: expected 404 after deletion')
    sys.exit(1)

print()
print('All CRUD operations PASSED.')

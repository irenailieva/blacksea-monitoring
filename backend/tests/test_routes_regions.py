"""
Unit тестове за API routes на Region.
"""
import pytest
from fastapi import status

from app.schemas import RegionCreate


def test_create_region_success(client, auth_headers_analyst):
    """Тест за успешно създаване на регион чрез API."""
    region_data = {
        "name": "Test Region",
        "description": "Test description",
        "area_km2": 100.5,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    response = client.post(
        "/regions/",
        json=region_data,
        headers=auth_headers_analyst
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Region"
    assert data["id"] is not None


def test_create_region_unauthorized(client):
    """Тест за създаване на регион без автентикация."""
    region_data = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    response = client.post("/regions/", json=region_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_region_forbidden_viewer(client, auth_headers_viewer):
    """Тест за създаване на регион с viewer роля (недостатъчни права)."""
    region_data = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    response = client.post(
        "/regions/",
        json=region_data,
        headers=auth_headers_viewer
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_regions_success(client, auth_headers_viewer):
    """Тест за получаване на списък от региони."""
    response = client.get("/regions/", headers=auth_headers_viewer)
    
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_get_region_by_id_success(client, auth_headers_analyst):
    """Тест за получаване на регион по ID."""
    # Създаваме регион
    region_data = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    create_response = client.post(
        "/regions/",
        json=region_data,
        headers=auth_headers_analyst
    )
    region_id = create_response.json()["id"]
    
    # Получаваме региона
    response = client.get(f"/regions/{region_id}", headers=auth_headers_viewer)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == region_id
    assert data["name"] == "Test Region"


def test_get_region_not_found(client, auth_headers_viewer):
    """Тест за получаване на несъществуващ регион."""
    response = client.get("/regions/999", headers=auth_headers_viewer)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_region_success(client, auth_headers_analyst):
    """Тест за успешно обновяване на регион."""
    # Създаваме регион
    region_data = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    create_response = client.post(
        "/regions/",
        json=region_data,
        headers=auth_headers_analyst
    )
    region_id = create_response.json()["id"]
    
    # Обновяваме региона
    update_data = {"name": "Updated Region", "description": "Updated description"}
    response = client.put(
        f"/regions/{region_id}",
        json=update_data,
        headers=auth_headers_analyst
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Region"
    assert data["description"] == "Updated description"


def test_delete_region_success(client, auth_headers_admin):
    """Тест за успешно изтриване на регион."""
    # Създаваме регион
    region_data = {
        "name": "Test Region",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    }
    
    create_response = client.post(
        "/regions/",
        json=region_data,
        headers=auth_headers_admin
    )
    region_id = create_response.json()["id"]
    
    # Изтриваме региона
    response = client.delete(
        f"/regions/{region_id}",
        headers=auth_headers_admin
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Проверяваме, че регионът е изтрит
    get_response = client.get(f"/regions/{region_id}", headers=auth_headers_admin)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


"""
Unit тестове за CRUD операции на Region.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud import region as crud_region
from app.schemas import RegionCreate, RegionUpdate
from app.models.region import Region


def test_create_region_success(db: Session):
    """Тест за успешно създаване на регион."""
    region_data = RegionCreate(
        name="Test Region",
        description="Test description",
        area_km2=100.5,
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    
    region = crud_region.create(db=db, obj_in=region_data)
    
    assert region.id is not None
    assert region.name == "Test Region"
    assert region.description == "Test description"
    assert region.area_km2 == 100.5
    assert region.geometry is not None


def test_create_region_duplicate_name(db: Session):
    """Тест за създаване на регион с дублирано име."""
    region_data = RegionCreate(
        name="Test Region",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    
    crud_region.create(db=db, obj_in=region_data)
    
    # Опит за създаване на регион с същото име
    with pytest.raises(HTTPException) as exc_info:
        crud_region.create(db=db, obj_in=region_data)
    
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


def test_get_region_by_id(db: Session):
    """Тест за получаване на регион по ID."""
    region_data = RegionCreate(
        name="Test Region",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    
    created_region = crud_region.create(db=db, obj_in=region_data)
    retrieved_region = crud_region.get(db=db, id=created_region.id)
    
    assert retrieved_region is not None
    assert retrieved_region.id == created_region.id
    assert retrieved_region.name == "Test Region"


def test_get_region_not_found(db: Session):
    """Тест за получаване на несъществуващ регион."""
    region = crud_region.get(db=db, id=999)
    assert region is None


def test_update_region_success(db: Session):
    """Тест за успешно обновяване на регион."""
    region_data = RegionCreate(
        name="Test Region",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    
    created_region = crud_region.create(db=db, obj_in=region_data)
    
    update_data = RegionUpdate(name="Updated Region", description="Updated description")
    updated_region = crud_region.update(db=db, db_obj=created_region, obj_in=update_data)
    
    assert updated_region.name == "Updated Region"
    assert updated_region.description == "Updated description"


def test_update_region_duplicate_name(db: Session):
    """Тест за обновяване на регион с дублирано име."""
    region1_data = RegionCreate(
        name="Region 1",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    region2_data = RegionCreate(
        name="Region 2",
        geometry={
            "type": "Polygon",
            "coordinates": [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
        }
    )
    
    crud_region.create(db=db, obj_in=region1_data)
    region2 = crud_region.create(db=db, obj_in=region2_data)
    
    # Опит за обновяване на region2 с името на region1
    update_data = RegionUpdate(name="Region 1")
    with pytest.raises(HTTPException) as exc_info:
        crud_region.update(db=db, db_obj=region2, obj_in=update_data)
    
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


def test_delete_region_success(db: Session):
    """Тест за успешно изтриване на регион."""
    region_data = RegionCreate(
        name="Test Region",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    
    created_region = crud_region.create(db=db, obj_in=region_data)
    region_id = created_region.id
    
    deleted_region = crud_region.delete(db=db, id=region_id)
    
    assert deleted_region.id == region_id
    assert crud_region.get(db=db, id=region_id) is None


def test_delete_region_not_found(db: Session):
    """Тест за изтриване на несъществуващ регион."""
    with pytest.raises(HTTPException) as exc_info:
        crud_region.delete(db=db, id=999)
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


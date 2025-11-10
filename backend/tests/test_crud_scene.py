"""
Unit тестове за CRUD операции на Scene.
"""
import pytest
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud import scene as crud_scene
from app.crud import region as crud_region
from app.schemas import SceneCreate, SceneUpdate, RegionCreate
from app.models.scene import Scene


@pytest.fixture
def test_region(db: Session):
    """Създава тестов регион."""
    region_data = RegionCreate(
        name="Test Region",
        geometry={
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }
    )
    return crud_region.create(db=db, obj_in=region_data)


def test_create_scene_success(db: Session, test_region):
    """Тест за успешно създаване на сцена."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        satellite="Sentinel-2",
        cloud_cover=5.5,
        tile="35TMT",
        path="/path/to/scene",
        region_id=test_region.id
    )
    
    scene = crud_scene.create(db=db, obj_in=scene_data)
    
    assert scene.id is not None
    assert scene.scene_id == "S2A_MSIL2A_20240703T085601"
    assert scene.acquisition_date == date(2024, 7, 3)
    assert scene.region_id == test_region.id


def test_create_scene_duplicate_scene_id(db: Session, test_region):
    """Тест за създаване на сцена с дублиран scene_id."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        region_id=test_region.id
    )
    
    crud_scene.create(db=db, obj_in=scene_data)
    
    # Опит за създаване на сцена с същия scene_id
    with pytest.raises(HTTPException) as exc_info:
        crud_scene.create(db=db, obj_in=scene_data)
    
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


def test_create_scene_invalid_region(db: Session):
    """Тест за създаване на сцена с несъществуващ регион."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        region_id=999
    )
    
    with pytest.raises(HTTPException) as exc_info:
        crud_scene.create(db=db, obj_in=scene_data)
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_scene_by_id(db: Session, test_region):
    """Тест за получаване на сцена по ID."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        region_id=test_region.id
    )
    
    created_scene = crud_scene.create(db=db, obj_in=scene_data)
    retrieved_scene = crud_scene.get(db=db, id=created_scene.id)
    
    assert retrieved_scene is not None
    assert retrieved_scene.id == created_scene.id
    assert retrieved_scene.scene_id == "S2A_MSIL2A_20240703T085601"


def test_update_scene_success(db: Session, test_region):
    """Тест за успешно обновяване на сцена."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        region_id=test_region.id
    )
    
    created_scene = crud_scene.create(db=db, obj_in=scene_data)
    
    update_data = SceneUpdate(cloud_cover=10.0, tile="35TMT")
    updated_scene = crud_scene.update(db=db, db_obj=created_scene, obj_in=update_data)
    
    assert updated_scene.cloud_cover == 10.0
    assert updated_scene.tile == "35TMT"


def test_delete_scene_success(db: Session, test_region):
    """Тест за успешно изтриване на сцена."""
    scene_data = SceneCreate(
        scene_id="S2A_MSIL2A_20240703T085601",
        acquisition_date=date(2024, 7, 3),
        region_id=test_region.id
    )
    
    created_scene = crud_scene.create(db=db, obj_in=scene_data)
    scene_id = created_scene.id
    
    deleted_scene = crud_scene.delete(db=db, id=scene_id)
    
    assert deleted_scene.id == scene_id
    assert crud_scene.get(db=db, id=scene_id) is None


"""
Скрипт за тестване на системата - проверява основните функционалности.
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Добавяне на backend директорията към пътя
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тест за импорти на основните модули."""
    print("=" * 60)
    print("Тест 1: Проверка на импорти...")
    print("=" * 60)
    
    try:
        from app.models import Base, User, Region, Scene, IndexType, IndexValue
        print("✓ Модели импортирани успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на модели: {e}")
        return False
    
    try:
        from app.schemas import UserCreate, RegionCreate, SceneCreate
        print("✓ Schemas импортирани успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на schemas: {e}")
        return False
    
    try:
        from app.crud import user, region, scene, index_type, index_value
        print("✓ CRUD модули импортирани успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на CRUD: {e}")
        return False
    
    try:
        from app.core.security import get_current_user, require_role, create_access_token
        print("✓ Security модул импортиран успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на security: {e}")
        return False
    
    try:
        from app.routes import regions, scenes, index_types, index_values
        print("✓ Routes импортирани успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на routes: {e}")
        return False
    
    try:
        from app.main import app
        print("✓ FastAPI app импортиран успешно")
    except Exception as e:
        print(f"✗ Грешка при импорт на main app: {e}")
        return False
    
    return True


def test_schemas():
    """Тест за валидация на schemas."""
    print("\n" + "=" * 60)
    print("Тест 2: Проверка на Pydantic schemas...")
    print("=" * 60)
    
    try:
        from app.schemas import UserCreate, RegionCreate, SceneCreate
        
        # Тест за UserCreate
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="viewer"
        )
        assert user_data.username == "testuser"
        print("✓ UserCreate schema работи")
        
        # Тест за RegionCreate
        region_data = RegionCreate(
            name="Test Region",
            geometry={
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        )
        assert region_data.name == "Test Region"
        print("✓ RegionCreate schema работи")
        
        # Тест за SceneCreate
        from datetime import date
        scene_data = SceneCreate(
            scene_id="S2A_MSIL2A_20240703T085601",
            acquisition_date=date(2024, 7, 3),
            region_id=1
        )
        assert scene_data.scene_id == "S2A_MSIL2A_20240703T085601"
        print("✓ SceneCreate schema работи")
        
        return True
    except Exception as e:
        print(f"✗ Грешка при тестване на schemas: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crud_structure():
    """Тест за структурата на CRUD класовете."""
    print("\n" + "=" * 60)
    print("Тест 3: Проверка на CRUD структура...")
    print("=" * 60)
    
    try:
        from app.crud import user, region, scene, index_type, index_value
        from app.crud.base import CRUDBase
        
        # Проверка за методи
        assert hasattr(user, 'create')
        assert hasattr(user, 'get')
        assert hasattr(user, 'get_multi')
        assert hasattr(user, 'update')
        assert hasattr(user, 'delete')
        print("✓ CRUDUser има всички необходими методи")
        
        assert hasattr(region, 'create')
        assert hasattr(region, 'get')
        assert hasattr(region, 'get_by_name')
        print("✓ CRUDRegion има специфични методи")
        
        assert hasattr(scene, 'create')
        assert hasattr(scene, 'get_by_scene_id')
        print("✓ CRUDScene има специфични методи")
        
        return True
    except Exception as e:
        print(f"✗ Грешка при тестване на CRUD структура: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routes_structure():
    """Тест за структурата на routes."""
    print("\n" + "=" * 60)
    print("Тест 4: Проверка на routes структура...")
    print("=" * 60)
    
    try:
        from app.routes import regions, scenes, index_types, index_values
        
        # Проверка за router
        assert hasattr(regions, 'router')
        assert hasattr(scenes, 'router')
        assert hasattr(index_types, 'router')
        assert hasattr(index_values, 'router')
        print("✓ Всички routes имат router")
        
        # Проверка за endpoints
        routes_list = regions.router.routes
        route_paths = [route.path for route in routes_list]
        assert "/regions/" in route_paths or any("/regions" in path for path in route_paths)
        print("✓ Regions routes са дефинирани")
        
        return True
    except Exception as e:
        print(f"✗ Грешка при тестване на routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_structure():
    """Тест за структурата на FastAPI app."""
    print("\n" + "=" * 60)
    print("Тест 5: Проверка на FastAPI app структура...")
    print("=" * 60)
    
    try:
        from app.main import app
        
        # Проверка за routes
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        print("✓ App има основните routes")
        
        # Проверка за включени routers
        assert len(app.routes) > 5  # Поне няколко routes
        print("✓ App има включени routers")
        
        return True
    except Exception as e:
        print(f"✗ Грешка при тестване на app: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главна функция за изпълнение на всички тестове."""
    print("\n" + "=" * 60)
    print("СТАРТИРАНЕ НА СИСТЕМНИ ТЕСТОВЕ")
    print("=" * 60 + "\n")
    
    tests = [
        ("Импорти", test_imports),
        ("Schemas", test_schemas),
        ("CRUD структура", test_crud_structure),
        ("Routes структура", test_routes_structure),
        ("App структура", test_app_structure),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Критична грешка в тест '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Обобщение
    print("\n" + "=" * 60)
    print("ОБОБЩЕНИЕ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ ПРОЙДЕН" if result else "✗ ПРОВАЛЕН"
        print(f"{name}: {status}")
    
    print(f"\nРезултат: {passed}/{total} теста преминаха успешно")
    
    if passed == total:
        print("\n🎉 Всички тестове преминаха успешно!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} теста не преминаха. Проверете грешките по-горе.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


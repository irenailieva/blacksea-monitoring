"""CRUD операции за всички модели."""
from .base import CRUDBase
from .user import user
from .region import region
from .scene import scene
from .index_type import index_type
from .index_value import index_value

__all__ = [
    "CRUDBase",
    "user",
    "region",
    "scene",
    "index_type",
    "index_value",
]


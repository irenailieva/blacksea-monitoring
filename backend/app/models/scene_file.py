from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
if TYPE_CHECKING:
    from .scene import Scene

class SceneFile(Base):
    """
    ORM модел за файловете, свързани със сателитна сцена.
    Една сцена може да има множество файлове (напр. различни честотни ленти/bands като B02, B03, B04).
    """
    __tablename__ = "scene_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Външен ключ към сцената
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)

    file_type: Mapped[str] = mapped_column(String(50), nullable=False) # Тип на файла (напр. 'TCI', 'B04', 'metadata')
    path: Mapped[str] = mapped_column(String(255), nullable=False) # Път до файла в локалната файлова система или S3
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True) # Размер в байтове
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True) # Checksum (напр. MD5/SHA256) за валидация

    scene: Mapped["Scene"] = relationship(back_populates="files")

    def __repr__(self) -> str:
        """Стрингова репрезентация за дебъгване."""
        return f"<SceneFile(scene_id={self.scene_id}, type={self.file_type}, path={self.path})>"

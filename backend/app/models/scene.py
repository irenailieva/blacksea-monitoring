from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr

Base = declarative_base()
#TODO: finish models: scnene, team, user
class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(String, unique=True, nullable=False)  # напр. S2A_MSIL2A_20240703T085601
    acquisition_date = Column(Date, nullable=False)
    satellite = Column(String, nullable=False, default="Sentinel-2")
    cloud_cover = Column(Float, nullable=True)
    tile = Column(String, nullable=True)
    path = Column(String, nullable=True)  # локален път до сцената

    # 🔗 Външни ключове
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    index_type_id = Column(Integer, ForeignKey("index_types.id"), nullable=True)
    index_value_id = Column(Integer, ForeignKey("index_values.id"), nullable=True)

    # 🔁 Релации
    region = relationship("Region", back_populates="scenes")
    index_type = relationship("IndexType", back_populates="scenes")
    index_value = relationship("IndexValue", back_populates="scenes")

    def __repr__(self):
        return f"<Scene(id={self.id}, scene_id='{self.scene_id}', region_id={self.region_id})>"

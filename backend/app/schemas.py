"""
Pydantic schemas за валидация на входни и изходни данни.
"""
from datetime import datetime, date
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ==================== Base Schemas ====================

class BaseSchema(BaseModel):
    """Базов schema с обща конфигурация."""
    model_config = ConfigDict(from_attributes=True)


# ==================== User Schemas ====================

class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(admin|researcher|viewer)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|researcher|viewer)$")
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime


# ==================== Region Schemas ====================

class RegionBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    area_km2: Optional[float] = Field(None, gt=0)
    type: Optional[str] = Field(default="aoi", pattern="^(aoi|exclusion)$")


class RegionCreate(RegionBase):
    geometry: dict = Field(..., description="GeoJSON geometry (POLYGON)")


class RegionUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    area_km2: Optional[float] = Field(None, gt=0)
    geometry: Optional[dict] = None


class RegionRead(RegionBase):
    id: int
    created_at: datetime
    updated_at: datetime


# ==================== Scene Schemas ====================

class SceneBase(BaseSchema):
    scene_id: str = Field(..., min_length=1, max_length=100)
    acquisition_date: date
    satellite: str = Field(default="Sentinel-2", max_length=50)
    cloud_cover: Optional[float] = Field(None, ge=0, le=100)
    tile: Optional[str] = Field(None, max_length=20)
    path: Optional[str] = Field(None, max_length=255)


class SceneCreate(SceneBase):
    region_id: int = Field(..., gt=0)


class SceneUpdate(BaseSchema):
    scene_id: Optional[str] = Field(None, min_length=1, max_length=100)
    acquisition_date: Optional[date] = None
    satellite: Optional[str] = Field(None, max_length=50)
    cloud_cover: Optional[float] = Field(None, ge=0, le=100)
    tile: Optional[str] = Field(None, max_length=20)
    path: Optional[str] = Field(None, max_length=255)
    region_id: Optional[int] = Field(None, gt=0)


class SceneRead(SceneBase):
    id: int
    region_id: int
    created_at: datetime
    updated_at: datetime


# ==================== IndexType Schemas ====================

class IndexTypeBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    formula: Optional[str] = Field(None, max_length=255)


class IndexTypeCreate(IndexTypeBase):
    pass


class IndexTypeUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    formula: Optional[str] = Field(None, max_length=255)


class IndexTypeRead(IndexTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime


# ==================== IndexValue Schemas ====================

class IndexValueBase(BaseSchema):
    mean_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class IndexValueCreate(IndexValueBase):
    scene_id: int = Field(..., gt=0)
    index_type_id: int = Field(..., gt=0)
    region_id: Optional[int] = Field(None, gt=0)


class IndexValueUpdate(BaseSchema):
    mean_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    scene_id: Optional[int] = Field(None, gt=0)
    index_type_id: Optional[int] = Field(None, gt=0)
    region_id: Optional[int] = Field(None, gt=0)


class IndexValueRead(IndexValueBase):
    id: int
    scene_id: int
    index_type_id: int
    region_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# ==================== SceneFile Schemas ====================

class SceneFileBase(BaseSchema):
    file_type: str = Field(..., max_length=50)
    path: str = Field(..., max_length=255)
    size_bytes: Optional[int] = Field(None, ge=0)
    checksum: Optional[str] = Field(None, max_length=64)


class SceneFileCreate(SceneFileBase):
    scene_id: int = Field(..., gt=0)


class SceneFileUpdate(BaseSchema):
    file_type: Optional[str] = Field(None, max_length=50)
    path: Optional[str] = Field(None, max_length=255)
    size_bytes: Optional[int] = Field(None, ge=0)
    checksum: Optional[str] = Field(None, max_length=64)


class SceneFileRead(SceneFileBase):
    id: int
    scene_id: int
    created_at: datetime
    updated_at: datetime


# ==================== ModelRun Schemas ====================

class ModelRunBase(BaseSchema):
    model_name: str = Field(..., max_length=100)
    parameters: Optional[dict[str, Any]] = None
    status: str = Field(default="completed", pattern="^(pending|running|completed|failed)$")
    metrics: Optional[dict[str, Any]] = None


class ModelRunCreate(ModelRunBase):
    pass


class ModelRunUpdate(BaseSchema):
    model_name: Optional[str] = Field(None, max_length=100)
    parameters: Optional[dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed)$")
    metrics: Optional[dict[str, Any]] = None
    finished_at: Optional[datetime] = None


class ModelRunRead(ModelRunBase):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ==================== ShapValue Schemas ====================

class ShapValueBase(BaseSchema):
    feature_name: str = Field(..., max_length=100)
    value: float


class ShapValueCreate(ShapValueBase):
    model_run_id: int = Field(..., gt=0)
    scene_id: int = Field(..., gt=0)
    index_type_id: int = Field(..., gt=0)


class ShapValueUpdate(BaseSchema):
    feature_name: Optional[str] = Field(None, max_length=100)
    value: Optional[float] = None


class ShapValueRead(ShapValueBase):
    id: int
    model_run_id: int
    scene_id: int
    index_type_id: int
    created_at: datetime
    updated_at: datetime


# ==================== ClassificationResult Schemas ====================

class ClassificationResultBase(BaseSchema):
    label: str = Field(..., max_length=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class ClassificationResultCreate(ClassificationResultBase):
    scene_id: int = Field(..., gt=0)
    model_run_id: Optional[int] = Field(None, gt=0)
    region_id: Optional[int] = Field(None, gt=0)


class ClassificationResultUpdate(BaseSchema):
    label: Optional[str] = Field(None, max_length=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    model_run_id: Optional[int] = Field(None, gt=0)
    region_id: Optional[int] = Field(None, gt=0)


class ClassificationResultRead(ClassificationResultBase):
    id: int
    scene_id: int
    model_run_id: Optional[int]
    region_id: Optional[int]
    created_at: datetime
    updated_at: datetime


# ==================== ETLJob Schemas ====================

class ETLJobBase(BaseSchema):
    job_type: str = Field(..., max_length=50)
    status: str = Field(default="pending", pattern="^(pending|running|processing|completed|failed)$")
    payload: Optional[dict[str, Any]] = None


class ETLJobCreate(ETLJobBase):
    pass


class ETLJobUpdate(BaseSchema):
    job_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(pending|running|processing|completed|failed)$")
    payload: Optional[dict[str, Any]] = None
    finished_at: Optional[datetime] = None


class ETLJobRead(ETLJobBase):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ==================== ErrorLog Schemas ====================

class ErrorLogBase(BaseSchema):
    level: str = Field(default="ERROR", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    message: str
    stacktrace: Optional[str] = None


class ErrorLogCreate(ErrorLogBase):
    etl_job_id: int = Field(..., gt=0)


class ErrorLogRead(ErrorLogBase):
    id: int
    etl_job_id: int
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


# ==================== Notification Schemas ====================

class NotificationBase(BaseSchema):
    title: str = Field(..., max_length=120)
    message: str = Field(..., max_length=500)
    read: bool = Field(default=False)


class NotificationCreate(NotificationBase):
    user_id: int = Field(..., gt=0)


class NotificationUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=120)
    message: Optional[str] = Field(None, max_length=500)
    read: Optional[bool] = None


class NotificationRead(NotificationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


# ==================== Team Schemas ====================

class TeamBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class TeamRead(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime


# ==================== TeamMembership Schemas ====================

class TeamMembershipBase(BaseSchema):
    role: str = Field(default="member", pattern="^(member|moderator|admin)$")


class TeamMembershipCreate(TeamMembershipBase):
    user_id: int = Field(..., gt=0)
    team_id: int = Field(..., gt=0)


class TeamMembershipUpdate(BaseSchema):
    role: Optional[str] = Field(None, pattern="^(member|moderator|admin)$")


class TeamMembershipRead(TeamMembershipBase):
    user_id: int
    team_id: int
    user: Optional["UserRead"] = None
    created_at: datetime
    updated_at: datetime


# ==================== WebhookIntegration Schemas ====================

class WebhookIntegrationBase(BaseSchema):
    provider: str = Field(..., max_length=50)
    endpoint_url: str = Field(..., max_length=255)
    secret: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True)


class WebhookIntegrationCreate(WebhookIntegrationBase):
    user_id: int = Field(..., gt=0)


class WebhookIntegrationUpdate(BaseSchema):
    provider: Optional[str] = Field(None, max_length=50)
    endpoint_url: Optional[str] = Field(None, max_length=255)
    secret: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class WebhookIntegrationRead(WebhookIntegrationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


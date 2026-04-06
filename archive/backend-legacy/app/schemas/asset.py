from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# --- Asset Schemas ---

class AssetOut(BaseModel):
    id: str
    name: str
    asset_type: str
    category: str
    channel: Optional[str]
    tags: List[str]
    source: Optional[str]
    mood: Optional[str]
    status: str
    duration_seconds: Optional[float]
    resolution: Optional[str]
    format: Optional[str]
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssetDetail(AssetOut):
    source_url: Optional[str]
    license_type: Optional[str]
    file_path: Optional[str]
    file_size_mb: Optional[float]
    fps: Optional[float]
    description: Optional[str]
    last_used_at: Optional[datetime]
    updated_at: datetime
    extra_data: Dict[str, Any]


class CreateAsset(BaseModel):
    name: str
    asset_type: str  # video, animation, music, sfx, graphic, font, lut
    category: str  # b-roll, motion-graphic, kinetic-text, transition, etc.
    channel: Optional[str] = None
    tags: List[str] = []
    source: Optional[str] = None
    source_url: Optional[str] = None
    license_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    format: Optional[str] = None
    fps: Optional[float] = None
    description: Optional[str] = None
    mood: Optional[str] = None
    extra_data: Dict[str, Any] = {}


class UpdateAsset(BaseModel):
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    channel: Optional[str] = None
    mood: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class AssetSearch(BaseModel):
    query: Optional[str] = None  # free text search across name, description, tags
    asset_type: Optional[str] = None
    category: Optional[str] = None
    channel: Optional[str] = None
    mood: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    resolution: Optional[str] = None
    status: Optional[str] = "available"


# --- Collection Schemas ---

class CollectionOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    channel: Optional[str]
    collection_type: str
    asset_ids: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreateCollection(BaseModel):
    name: str
    description: Optional[str] = None
    channel: Optional[str] = None
    collection_type: str
    asset_ids: List[str] = []


class UpdateCollection(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    asset_ids: Optional[List[str]] = None

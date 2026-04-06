import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, Text


from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # video, animation, music, sfx, graphic, font, lut
    category = Column(String, nullable=False)  # b-roll, motion-graphic, kinetic-text, transition, lower-third, background, icon, data-viz, ambient, soundtrack, sound-effect, color-lut
    channel = Column(String, nullable=True)  # channel slug or None for shared assets
    tags = Column(JSON, default=list)  # searchable tags like ["cinematic", "finance", "dark-mood"]
    source = Column(String, nullable=True)  # artgrid, storyblocks, envato, epidemic-sound, custom
    source_url = Column(String, nullable=True)
    license_type = Column(String, nullable=True)  # royalty-free, editorial, custom, creative-commons
    file_path = Column(String, nullable=True)  # local path to downloaded asset
    file_size_mb = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # for video/audio assets
    resolution = Column(String, nullable=True)  # e.g. "3840x2160", "1920x1080"
    format = Column(String, nullable=True)  # mp4, mov, wav, mp3, png, json (lottie), aep
    fps = Column(Float, nullable=True)  # for video assets
    description = Column(Text, nullable=True)
    mood = Column(String, nullable=True)  # cinematic, energetic, calm, dramatic, playful, dark, inspiring
    status = Column(String, default="available")  # available, downloading, processing, archived, expired
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    extra_data = Column(JSON, default=dict)  # flexible extra data (color palette, bpm for music, etc.)


class AssetCollection(Base):
    __tablename__ = "asset_collections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # e.g. "Finance Channel Intro Pack", "Dark Cinematic Transitions"
    description = Column(Text, nullable=True)
    channel = Column(String, nullable=True)  # channel slug or None for shared
    asset_ids = Column(JSON, default=list)  # list of asset IDs in this collection
    collection_type = Column(String, nullable=False)  # template-pack, mood-board, channel-kit, project-assets
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

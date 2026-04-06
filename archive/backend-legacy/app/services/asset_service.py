from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from datetime import datetime, timezone
from typing import Optional, List

from app.models.asset import Asset, AssetCollection
from app.schemas.asset import CreateAsset, UpdateAsset, AssetSearch, CreateCollection, UpdateCollection


# --- Asset CRUD ---

async def create_asset(db: AsyncSession, data: CreateAsset) -> Asset:
    asset = Asset(**data.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def create_assets_bulk(db: AsyncSession, assets: List[CreateAsset]) -> List[Asset]:
    records = [Asset(**a.model_dump()) for a in assets]
    db.add_all(records)
    await db.commit()
    for r in records:
        await db.refresh(r)
    return records


async def get_asset(db: AsyncSession, asset_id: str) -> Optional[Asset]:
    return await db.get(Asset, asset_id)


async def update_asset(db: AsyncSession, asset_id: str, data: UpdateAsset) -> Optional[Asset]:
    asset = await db.get(Asset, asset_id)
    if not asset:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    asset.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, asset_id: str) -> bool:
    asset = await db.get(Asset, asset_id)
    if not asset:
        return False
    await db.delete(asset)
    await db.commit()
    return True


async def record_asset_usage(db: AsyncSession, asset_id: str) -> Optional[Asset]:
    asset = await db.get(Asset, asset_id)
    if not asset:
        return None
    asset.usage_count = (asset.usage_count or 0) + 1
    asset.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(asset)
    return asset


# --- Asset Search ---

async def search_assets(db: AsyncSession, search: AssetSearch) -> List[Asset]:
    query = select(Asset)

    if search.status:
        query = query.where(Asset.status == search.status)
    if search.asset_type:
        query = query.where(Asset.asset_type == search.asset_type)
    if search.category:
        query = query.where(Asset.category == search.category)
    if search.channel:
        # Include channel-specific AND shared assets
        query = query.where(or_(Asset.channel == search.channel, Asset.channel.is_(None)))
    if search.mood:
        query = query.where(Asset.mood == search.mood)
    if search.source:
        query = query.where(Asset.source == search.source)
    if search.resolution:
        query = query.where(Asset.resolution == search.resolution)
    if search.min_duration is not None:
        query = query.where(Asset.duration_seconds >= search.min_duration)
    if search.max_duration is not None:
        query = query.where(Asset.duration_seconds <= search.max_duration)

    # Free text search across name, description, and tags
    if search.query:
        term = f"%{search.query.lower()}%"
        query = query.where(
            or_(
                func.lower(Asset.name).contains(search.query.lower()),
                func.lower(Asset.description).contains(search.query.lower()),
            )
        )

    # Tag filtering: asset must have ALL specified tags
    if search.tags:
        for tag in search.tags:
            query = query.where(Asset.tags.contains(tag))

    query = query.order_by(Asset.usage_count.desc(), Asset.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_assets(
    db: AsyncSession,
    asset_type: Optional[str] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Asset]:
    query = select(Asset).where(Asset.status == "available")
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    if category:
        query = query.where(Asset.category == category)
    if channel:
        query = query.where(or_(Asset.channel == channel, Asset.channel.is_(None)))
    query = query.order_by(Asset.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_asset_stats(db: AsyncSession) -> dict:
    result = await db.execute(select(Asset).where(Asset.status == "available"))
    assets = list(result.scalars().all())

    stats = {
        "total_assets": len(assets),
        "by_type": {},
        "by_category": {},
        "by_source": {},
        "by_mood": {},
        "most_used": [],
    }

    for a in assets:
        stats["by_type"][a.asset_type] = stats["by_type"].get(a.asset_type, 0) + 1
        stats["by_category"][a.category] = stats["by_category"].get(a.category, 0) + 1
        if a.source:
            stats["by_source"][a.source] = stats["by_source"].get(a.source, 0) + 1
        if a.mood:
            stats["by_mood"][a.mood] = stats["by_mood"].get(a.mood, 0) + 1

    # Top 10 most used
    sorted_by_usage = sorted(assets, key=lambda x: x.usage_count or 0, reverse=True)[:10]
    stats["most_used"] = [{"id": a.id, "name": a.name, "usage_count": a.usage_count} for a in sorted_by_usage]

    return stats


# --- Collection CRUD ---

async def create_collection(db: AsyncSession, data: CreateCollection) -> AssetCollection:
    collection = AssetCollection(**data.model_dump())
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection


async def get_collection(db: AsyncSession, collection_id: str) -> Optional[AssetCollection]:
    return await db.get(AssetCollection, collection_id)


async def list_collections(
    db: AsyncSession,
    channel: Optional[str] = None,
    collection_type: Optional[str] = None,
) -> List[AssetCollection]:
    query = select(AssetCollection)
    if channel:
        query = query.where(or_(AssetCollection.channel == channel, AssetCollection.channel.is_(None)))
    if collection_type:
        query = query.where(AssetCollection.collection_type == collection_type)
    query = query.order_by(AssetCollection.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_collection(db: AsyncSession, collection_id: str, data: UpdateCollection) -> Optional[AssetCollection]:
    collection = await db.get(AssetCollection, collection_id)
    if not collection:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(collection, field, value)
    collection.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(collection)
    return collection


async def add_assets_to_collection(db: AsyncSession, collection_id: str, asset_ids: List[str]) -> Optional[AssetCollection]:
    collection = await db.get(AssetCollection, collection_id)
    if not collection:
        return None
    current = list(collection.asset_ids or [])
    for aid in asset_ids:
        if aid not in current:
            current.append(aid)
    collection.asset_ids = current
    collection.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(collection)
    return collection


async def delete_collection(db: AsyncSession, collection_id: str) -> bool:
    collection = await db.get(AssetCollection, collection_id)
    if not collection:
        return False
    await db.delete(collection)
    await db.commit()
    return True

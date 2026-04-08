from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.asset import (
    AssetOut, AssetDetail, CreateAsset, UpdateAsset, AssetSearch,
    CollectionOut, CreateCollection, UpdateCollection,
)
from app.services import asset_service

router = APIRouter(prefix="/api/assets", tags=["assets"])


# --- Asset Endpoints ---

@router.get("", response_model=list[AssetOut])
async def list_assets(
    asset_type: Optional[str] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    return await asset_service.list_assets(db, asset_type, category, channel, limit, offset)


@router.get("/stats")
async def get_asset_stats(db: AsyncSession = Depends(get_db)):
    return await asset_service.get_asset_stats(db)


@router.get("/search", response_model=list[AssetOut])
async def search_assets(
    query: Optional[str] = None,
    asset_type: Optional[str] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    mood: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[str] = None,  # comma-separated
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
    resolution: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    search = AssetSearch(
        query=query,
        asset_type=asset_type,
        category=category,
        channel=channel,
        mood=mood,
        source=source,
        tags=tags.split(",") if tags else None,
        min_duration=min_duration,
        max_duration=max_duration,
        resolution=resolution,
    )
    return await asset_service.search_assets(db, search)


@router.get("/{asset_id}", response_model=AssetDetail)
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    asset = await asset_service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("", response_model=AssetOut, status_code=201)
async def create_asset(data: CreateAsset, db: AsyncSession = Depends(get_db)):
    return await asset_service.create_asset(db, data)


@router.post("/bulk", response_model=list[AssetOut], status_code=201)
async def create_assets_bulk(assets: List[CreateAsset], db: AsyncSession = Depends(get_db)):
    return await asset_service.create_assets_bulk(db, assets)


@router.put("/{asset_id}", response_model=AssetOut)
async def update_asset(asset_id: str, data: UpdateAsset, db: AsyncSession = Depends(get_db)):
    asset = await asset_service.update_asset(db, asset_id, data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/{asset_id}/use", response_model=AssetOut)
async def record_usage(asset_id: str, db: AsyncSession = Depends(get_db)):
    """Record that an asset was used in a video. Increments usage count."""
    asset = await asset_service.record_asset_usage(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await asset_service.delete_asset(db, asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")


# --- Collection Endpoints ---

@router.get("/collections/", response_model=list[CollectionOut])
async def list_collections(
    channel: Optional[str] = None,
    collection_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await asset_service.list_collections(db, channel, collection_type)


@router.get("/collections/{collection_id}", response_model=CollectionOut)
async def get_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    collection = await asset_service.get_collection(db, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/collections", response_model=CollectionOut, status_code=201)
async def create_collection(data: CreateCollection, db: AsyncSession = Depends(get_db)):
    return await asset_service.create_collection(db, data)


@router.put("/collections/{collection_id}", response_model=CollectionOut)
async def update_collection(collection_id: str, data: UpdateCollection, db: AsyncSession = Depends(get_db)):
    collection = await asset_service.update_collection(db, collection_id, data)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.post("/collections/{collection_id}/assets")
async def add_assets_to_collection(
    collection_id: str,
    asset_ids: List[str],
    db: AsyncSession = Depends(get_db),
):
    collection = await asset_service.add_assets_to_collection(db, collection_id, asset_ids)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.delete("/collections/{collection_id}", status_code=204)
async def delete_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await asset_service.delete_collection(db, collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collection not found")

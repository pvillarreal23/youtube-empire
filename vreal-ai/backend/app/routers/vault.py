from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.vault import CredentialEntry

router = APIRouter(prefix="/api/vault", tags=["vault"])


class AddCredentialRequest(BaseModel):
    service: str
    account_name: str
    category: str = "social"
    platform_url: str = ""
    notes: str = ""
    api_key_hint: str = ""
    managed_by: str = ""


@router.get("/credentials")
async def list_credentials(category: str = "", db: AsyncSession = Depends(get_db)):
    """List all credential entries (no actual passwords — just the index)."""
    query = select(CredentialEntry).order_by(CredentialEntry.category, CredentialEntry.service)
    if category:
        query = query.where(CredentialEntry.category == category)
    result = await db.execute(query)
    entries = result.scalars().all()
    return [{
        "id": e.id, "service": e.service, "account_name": e.account_name,
        "category": e.category, "platform_url": e.platform_url,
        "notes": e.notes, "api_key_hint": e.api_key_hint,
        "managed_by": e.managed_by, "status": e.status,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    } for e in entries]


@router.post("/credentials")
async def add_credential(data: AddCredentialRequest, db: AsyncSession = Depends(get_db)):
    """Add a new credential entry to the vault tracker."""
    entry = CredentialEntry(
        id=str(uuid.uuid4()),
        service=data.service,
        account_name=data.account_name,
        category=data.category,
        platform_url=data.platform_url,
        notes=data.notes,
        api_key_hint=data.api_key_hint,
        managed_by=data.managed_by,
    )
    db.add(entry)
    await db.commit()
    return {"id": entry.id, "service": entry.service, "status": "added"}


@router.put("/credentials/{credential_id}")
async def update_credential(credential_id: str, data: AddCredentialRequest, db: AsyncSession = Depends(get_db)):
    entry = await db.get(CredentialEntry, credential_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Credential not found")
    entry.service = data.service
    entry.account_name = data.account_name
    entry.category = data.category
    entry.platform_url = data.platform_url
    entry.notes = data.notes
    entry.api_key_hint = data.api_key_hint
    entry.managed_by = data.managed_by
    entry.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": entry.id, "status": "updated"}


@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str, db: AsyncSession = Depends(get_db)):
    entry = await db.get(CredentialEntry, credential_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Credential not found")
    await db.delete(entry)
    await db.commit()
    return {"status": "deleted"}


@router.get("/summary")
async def vault_summary(db: AsyncSession = Depends(get_db)):
    """Quick summary of all credentials by category."""
    result = await db.execute(select(CredentialEntry))
    entries = result.scalars().all()

    by_category = {}
    for e in entries:
        if e.category not in by_category:
            by_category[e.category] = []
        by_category[e.category].append({
            "service": e.service, "account": e.account_name,
            "status": e.status, "managed_by": e.managed_by,
        })

    return {"total": len(entries), "categories": by_category}

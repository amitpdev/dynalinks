from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import List, Optional
from uuid import UUID
import qrcode
from io import BytesIO
import base64
import json
from app.db_pg import PostgresDB, get_db_instance
from app.schemas import (
    DynamicLinkCreate,
    DynamicLinkUpdate,
    DynamicLinkResponse,
    QRCodeRequest,
    ErrorResponse
)
from app.utils import generate_unique_short_code, generate_custom_short_code
from app.cache import cache
from app.config import settings

router = APIRouter(prefix="/api/v1/links", tags=["Dynamic Links"])


@router.post("/", response_model=DynamicLinkResponse)
async def create_dynamic_link(
    link_data: DynamicLinkCreate,
    custom_code: Optional[str] = Query(None, description="Custom short code (optional)"),
    db: PostgresDB = Depends(get_db_instance)
):
    """Create a new dynamic link."""

    # Generate or validate short code
    if custom_code:
        short_code = await generate_custom_short_code(custom_code, db)
        if not short_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom short code is invalid or already taken"
            )
    else:
        short_code = await generate_unique_short_code(db)

    # Create the link
    link_dict = link_data.model_dump()
    query = """
        INSERT INTO dynamic_links (
            short_code, ios_url, android_url, fallback_url, desktop_url, title,
            description, image_url, social_title, social_description, social_image_url,
            is_active, expires_at, creator_id, custom_parameters
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        RETURNING *;
    """
    
    db_link = await db.fetchrow(
        query,
        short_code,
        str(link_dict.get("ios_url")) if link_dict.get("ios_url") else None,
        str(link_dict.get("android_url")) if link_dict.get("android_url") else None,
        str(link_dict.get("fallback_url")) if link_dict.get("fallback_url") else None,
        str(link_dict.get("desktop_url")) if link_dict.get("desktop_url") else None,
        link_dict.get("title"),
        link_dict.get("description"),
        str(link_dict.get("image_url")) if link_dict.get("image_url") else None,
        link_dict.get("social_title"),
        link_dict.get("social_description"),
        str(link_dict.get("social_image_url")) if link_dict.get("social_image_url") else None,
        link_dict.get("is_active", True),
        link_dict.get("expires_at"),
        link_dict.get("creator_id"),
        json.dumps(link_dict.get("custom_parameters")) if link_dict.get("custom_parameters") else None,
    )

    # Build response with short URL
    db_link_dict = dict(db_link)
    db_link_dict["short_url"] = f"{settings.short_domain}/{short_code}"
    response_data = DynamicLinkResponse.model_validate(db_link_dict)

    # Cache the link for faster access
    cache_key = f"link:{short_code}"
    await cache.set(cache_key, response_data.model_dump_json(), expire=3600)

    return response_data


@router.get("/", response_model=List[DynamicLinkResponse])
async def list_dynamic_links(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: PostgresDB = Depends(get_db_instance)
):
    """List dynamic links with pagination."""
    if active_only:
        query = "SELECT * FROM dynamic_links WHERE is_active = TRUE ORDER BY created_at DESC LIMIT $1 OFFSET $2;"
        links = await db.fetch(query, limit, skip)
    else:
        query = "SELECT * FROM dynamic_links ORDER BY created_at DESC LIMIT $1 OFFSET $2;"
        links = await db.fetch(query, limit, skip)
    
    response_links = []
    for link in links:
        link_dict = dict(link)
        link_dict["short_url"] = f"{settings.short_domain}/{link['short_code']}"
        response_data = DynamicLinkResponse.model_validate(link_dict)
        response_links.append(response_data)

    return response_links


@router.get("/{short_code}", response_model=DynamicLinkResponse)
async def get_dynamic_link(short_code: str, db: PostgresDB = Depends(get_db_instance)):
    """Get a specific dynamic link by short code."""
    
    # Try cache first
    cache_key = f"link:{short_code}"
    cached_link = await cache.get(cache_key)
    if cached_link:
        try:
            return DynamicLinkResponse.model_validate_json(cached_link)
        except Exception:
            # Cache data is corrupted, delete it and fetch from database
            await cache.delete(cache_key)

    # Query database
    query = "SELECT * FROM dynamic_links WHERE short_code = $1;"
    db_link = await db.fetchrow(query, short_code)

    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic link not found"
        )
    
    db_link_dict = dict(db_link)
    db_link_dict["short_url"] = f"{settings.short_domain}/{short_code}"
    response_data = DynamicLinkResponse.model_validate(db_link_dict)

    # Cache for future requests
    await cache.set(cache_key, response_data.model_dump_json(), expire=3600)

    return response_data


@router.put("/{short_code}", response_model=DynamicLinkResponse)
async def update_dynamic_link(
    short_code: str,
    link_update: DynamicLinkUpdate,
    db: PostgresDB = Depends(get_db_instance)
):
    """Update a dynamic link."""
    update_data = link_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clauses = []
    values = []
    i = 1
    url_fields = ["ios_url", "android_url", "fallback_url", "desktop_url", "image_url", "social_image_url"]
    for field, value in update_data.items():
        if field == "custom_parameters":
            value = json.dumps(value)
        elif field in url_fields and value is not None:
            value = str(value)
        set_clauses.append(f"{field} = ${i}")
        values.append(value)
        i += 1

    values.append(short_code)
    query = f"UPDATE dynamic_links SET {', '.join(set_clauses)}, updated_at = now() WHERE short_code = ${i} RETURNING *;"
    
    db_link = await db.fetchrow(query, *values)

    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic link not found"
        )

    # Update cache
    cache_key = f"link:{short_code}"
    db_link_dict = dict(db_link)
    db_link_dict["short_url"] = f"{settings.short_domain}/{short_code}"
    response_data = DynamicLinkResponse.model_validate(db_link_dict)
    await cache.set(cache_key, response_data.model_dump_json(), expire=3600)

    return response_data


@router.delete("/{short_code}")
async def delete_dynamic_link(short_code: str, db: PostgresDB = Depends(get_db_instance)):
    """Delete a dynamic link (soft delete by deactivating)."""
    query = "UPDATE dynamic_links SET is_active = FALSE WHERE short_code = $1 RETURNING id;"
    result = await db.fetchrow(query, short_code)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic link not found"
        )

    # Remove from cache
    cache_key = f"link:{short_code}"
    await cache.delete(cache_key)

    return {"message": "Dynamic link deactivated successfully"}


@router.get("/{short_code}/qr")
async def generate_qr_code(
    short_code: str,
    size: int = Query(200, ge=50, le=1000),
    border: int = Query(4, ge=1, le=20),
    format: str = Query("PNG", pattern="^(PNG|JPEG)$"),
    db: PostgresDB = Depends(get_db_instance)
):
    """Generate QR code for the dynamic link."""

    # Verify link exists
    query = "SELECT is_active FROM dynamic_links WHERE short_code = $1;"
    db_link = await db.fetchrow(query, short_code)
    if not db_link or not db_link['is_active']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dynamic link not found or inactive"
        )

    # Generate QR code
    short_url = f"{settings.short_domain}/{short_code}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size // 25,  # Adjust box size based on requested size
        border=border,
    )
    qr.add_data(short_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format=format)
    img_buffer.seek(0)

    # Return image response
    media_type = f"image/{format.lower()}"
    return Response(
        content=img_buffer.getvalue(),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename=qr_{short_code}.{format.lower()}"}
    )

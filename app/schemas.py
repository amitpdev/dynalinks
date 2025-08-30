from pydantic import BaseModel, HttpUrl, AnyUrl, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from uuid import UUID


class DynamicLinkCreate(BaseModel):
    ios_url: Optional[AnyUrl] = None
    android_url: Optional[AnyUrl] = None
    fallback_url: HttpUrl
    desktop_url: Optional[HttpUrl] = None
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    
    social_title: Optional[str] = Field(None, max_length=255)
    social_description: Optional[str] = None
    social_image_url: Optional[HttpUrl] = None
    
    expires_at: Optional[datetime] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    
    @field_validator('expires_at')
    def validate_expires_at(cls, v):
        if v and v <= datetime.now(timezone.utc):
            raise ValueError('Expiration date must be in the future')
        return v


class DynamicLinkUpdate(BaseModel):
    ios_url: Optional[AnyUrl] = None
    android_url: Optional[AnyUrl] = None
    fallback_url: Optional[HttpUrl] = None
    desktop_url: Optional[HttpUrl] = None
    
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    
    social_title: Optional[str] = Field(None, max_length=255)
    social_description: Optional[str] = None
    social_image_url: Optional[HttpUrl] = None
    
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    custom_parameters: Optional[Dict[str, Any]] = None


class DynamicLinkResponse(BaseModel):
    id: UUID
    short_code: str
    short_url: str
    
    ios_url: Optional[str] = None
    android_url: Optional[str] = None
    fallback_url: str
    desktop_url: Optional[str] = None
    
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    
    social_title: Optional[str] = None
    social_description: Optional[str] = None
    social_image_url: Optional[str] = None
    
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    custom_parameters: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class LinkAnalyticsResponse(BaseModel):
    total_clicks: int
    unique_clicks: int
    clicks_by_platform: Dict[str, int]
    clicks_by_country: Dict[str, int]
    clicks_by_date: Dict[str, int]
    top_referrers: Dict[str, int]
    
    model_config = ConfigDict(from_attributes=True)


class QRCodeRequest(BaseModel):
    size: int = Field(default=200, ge=50, le=1000)
    border: int = Field(default=4, ge=1, le=20)
    format: str = Field(default="PNG", pattern="^(PNG|JPEG)$")


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
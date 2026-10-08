"""
PNMP Sites API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models import User, Site, Device
from ...schemas import SiteCreate, SiteUpdate, SiteResponse

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get("/", response_model=List[SiteResponse])
async def get_sites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all sites"""
    sites = db.query(Site).offset(skip).limit(limit).all()
    
    # Add device count
    result = []
    for site in sites:
        device_count = db.query(Device).filter(Device.site_id == site.id).count()
        site_dict = {
            "id": site.id,
            "name": site.name,
            "description": site.description,
            "address": site.address,
            "device_count": device_count,
            "created_at": site.created_at,
            "updated_at": site.updated_at
        }
        result.append(site_dict)
    
    return result


@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new site"""
    # Check if name exists
    if db.query(Site).filter(Site.name == site_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Site name already exists"
        )
    
    # Create site
    db_site = Site(
        name=site_data.name,
        description=site_data.description,
        address=site_data.address
    )
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    
    return {
        "id": db_site.id,
        "name": db_site.name,
        "description": db_site.description,
        "address": db_site.address,
        "device_count": 0,
        "created_at": db_site.created_at,
        "updated_at": db_site.updated_at
    }


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get site by ID"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    device_count = db.query(Device).filter(Device.site_id == site.id).count()
    
    return {
        "id": site.id,
        "name": site.name,
        "description": site.description,
        "address": site.address,
        "device_count": device_count,
        "created_at": site.created_at,
        "updated_at": site.updated_at
    }


@router.put("/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update site"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Check if new name exists (if changing name)
    if site_data.name and site_data.name != site.name:
        if db.query(Site).filter(Site.name == site_data.name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site name already exists"
            )
    
    # Update fields
    update_data = site_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(site, key, value)
    
    db.commit()
    db.refresh(site)
    
    device_count = db.query(Device).filter(Device.site_id == site.id).count()
    
    return {
        "id": site.id,
        "name": site.name,
        "description": site.description,
        "address": site.address,
        "device_count": device_count,
        "created_at": site.created_at,
        "updated_at": site.updated_at
    }


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete site"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    
    # Check if site has devices
    device_count = db.query(Device).filter(Device.site_id == site_id).count()
    if device_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete site with {device_count} devices. Move or delete devices first."
        )
    
    db.delete(site)
    db.commit()

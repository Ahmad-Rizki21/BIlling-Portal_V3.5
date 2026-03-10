from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging

from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User as UserModel

# Import Skema Pydantic
from ..schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventoryItemType as InventoryItemTypeSchema,
    InventoryStatus as InventoryStatusSchema,
)
from ..schemas.inventory_history import InventoryHistoryResponse
from ..services.inventory_service import InventoryService

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

async def get_inventory_service(db: AsyncSession = Depends(get_db)) -> InventoryService:
    return InventoryService(db)

@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item: InventoryItemCreate, 
    service: InventoryService = Depends(get_inventory_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Create a new inventory item via service."""
    return await service.create_item(item.model_dump(), current_user.id)

@router.get("/", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    response: Response,
    service: InventoryService = Depends(get_inventory_service)
):
    """Retrieve all inventory items via service."""
    # Bypass Cloudflare cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return await service.get_all_items()

@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdate,
    response: Response,
    service: InventoryService = Depends(get_inventory_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Update inventory item via service."""
    # Bypass Cloudflare cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    
    update_data = item_update.model_dump(exclude_unset=True)
    return await service.update_item(item_id, update_data, current_user.id)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int, 
    service: InventoryService = Depends(get_inventory_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Delete inventory item via service."""
    await service.delete_item(item_id, current_user.id)
    return

@router.get("/types", response_model=List[InventoryItemTypeSchema])
async def get_item_types(service: InventoryService = Depends(get_inventory_service)):
    """Get metadata: item types."""
    return await service.get_item_types()

@router.get("/statuses", response_model=List[InventoryStatusSchema])
async def get_statuses(service: InventoryService = Depends(get_inventory_service)):
    """Get metadata: statuses."""
    return await service.get_statuses()

@router.post("/validate-barcode")
async def validate_barcode(
    barcode_data: dict, 
    service: InventoryService = Depends(get_inventory_service)
):
    """Validate barcode via service."""
    barcode_text = barcode_data.get("barcode", "").strip()
    barcode_type = barcode_data.get("type", "serial")
    return await service.validate_barcode(barcode_text, barcode_type)

@router.get("/{item_id}/history", response_model=List[InventoryHistoryResponse])
async def get_inventory_history(
    item_id: int, 
    service: InventoryService = Depends(get_inventory_service)
):
    """Get history for a specific item via service."""
    return await service.get_item_history(item_id)

@router.get("/history/all", response_model=List[dict])
async def get_all_inventory_history(service: InventoryService = Depends(get_inventory_service)):
    """Get all history via service."""
    return await service.get_all_history()

@router.get("/template/download")
async def download_inventory_template(service: InventoryService = Depends(get_inventory_service)):
    """Download import template via service."""
    response = await service.generate_import_template()
    # Ensure cache headers for the streaming response
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@router.post("/bulk-import")
async def bulk_import_inventory(
    file: UploadFile = File(...),
    service: InventoryService = Depends(get_inventory_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Bulk import items via service."""
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="File format not supported")
    
    contents = await file.read()
    return await service.bulk_import(contents, file.filename, current_user.id)

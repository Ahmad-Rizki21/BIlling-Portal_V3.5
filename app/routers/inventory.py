from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi import status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from typing import List, Dict, Any
import logging
import re
import pandas as pd
import io
from datetime import datetime

from ..database import get_db
from ..auth import get_current_active_user

# Import Model dengan alias
from ..models.inventory_item import InventoryItem as InventoryItemModel
from ..models.inventory_item_type import InventoryItemType as InventoryItemTypeModel
from ..models.inventory_status import InventoryStatus as InventoryStatusModel
from ..models.inventory_history import InventoryHistory as InventoryHistoryModel
from ..models.user import User as UserModel

# Import Skema Pydantic dengan alias
from ..schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventoryItemType as InventoryItemTypeSchema,
    InventoryStatus as InventoryStatusSchema,
)
from ..schemas.inventory_history import InventoryHistoryResponse

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


async def log_inventory_change(
    db: AsyncSession,
    item_id: int,
    action: str,
    user_id: int
):
    """
    Helper function untuk mencatat perubahan inventory ke history
    """
    try:
        from sqlalchemy import text

        # Use direct SQL INSERT to avoid session conflicts
        query = text("""
            INSERT INTO inventory_history (item_id, action, user_id, timestamp)
            VALUES (:item_id, :action, :user_id, NOW())
        """)

        await db.execute(query, {
            "item_id": item_id,
            "action": action,
            "user_id": user_id
        })
        await db.commit()  # Commit immediately to avoid conflicts

        logger.info(f"Logged inventory history: item_id={item_id}, action={action}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Failed to log inventory history: {str(e)}")
        # Jangan raise exception agar tidak mengganggu flow utama


@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item: InventoryItemCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    try:
        db_item = InventoryItemModel(**item.model_dump())
        db.add(db_item)
        await db.commit()

        # Log history
        action_text = f"Created item - SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"
        await log_inventory_change(db, db_item.id, action_text, current_user.id)

        # Muat relasi secara eksplisit setelah commit
        await db.refresh(db_item, ["item_type", "status"])

        logger.info(f"Created inventory item with ID: {db_item.id}")
        return db_item
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating inventory item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory item: {str(e)}",
        )


@router.get("/", response_model=List[InventoryItemResponse])
async def get_inventory_items(
    db: AsyncSession = Depends(get_db),
    # Cloudflare cache bypass headers
    response: Response = None
):
    try:
        query = (
            select(InventoryItemModel)
            .options(
                selectinload(InventoryItemModel.item_type),
                selectinload(InventoryItemModel.status),
            )
            .order_by(InventoryItemModel.id)
        )
        result = await db.execute(query)
        items = result.scalars().all()

        # DEBUG: Log item ID 4 location for tracking
        item_4 = next((item for item in items if item.id == 4), None)
        if item_4:
            # logger.info(f"🔧 DEBUG: GET items - Item 4 location = '{item_4.location}'")
            pass

        # Bypass Cloudflare cache for inventory endpoints
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return items
    except Exception as e:
        logger.error(f"Error retrieving inventory items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory items: {str(e)}",
        )


@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    # Cloudflare cache bypass headers
    response: Response = None
):
    # DEBUG LOG untuk memastikan kode yang jalan adalah yang baru
    # logger.info(f"🔧 INVENTORY UPDATE v2.0 - Item ID: {item_id}")
    # logger.info(f"🔧 DEBUG: Update data = {item_update.model_dump(exclude_unset=True)}")

    try:
        db_item = await db.get(InventoryItemModel, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")

        update_data = item_update.model_dump(exclude_unset=True)

        # DEBUG: Log update data yang valid
        # logger.info(f"🔧 DEBUG: Valid update data = {update_data}")

        # Remove any invalid fields that might have slipped through
        invalid_fields = ['created_at', 'updated_at', 'id']
        for field in invalid_fields:
            if field in update_data:
                # logger.warning(f"🔧 WARNING: Removing invalid field '{field}' from update data")
                del update_data[field]

        changes = []

        # Track changes before applying
        for key, value in update_data.items():
            old_value = getattr(db_item, key)
            if old_value != value:
                if key == 'status_id':
                    changes.append(f"Status changed from {old_value} to {value}")
                elif key == 'location':
                    changes.append(f"Location changed from '{old_value}' to '{value}'")
                elif key == 'item_type_id':
                    changes.append(f"Type changed from {old_value} to {value}")
                else:
                    changes.append(f"{key} changed from '{old_value}' to '{value}'")

        # Apply updates
        for key, value in update_data.items():
            setattr(db_item, key, value)

        await db.commit()

        # Log history if there are changes
        if changes:
            action_text = f"Updated item - SN: {db_item.serial_number}, Changes: {', '.join(changes)}"
            await log_inventory_change(db, db_item.id, action_text, current_user.id)

        # Refresh the item completely to get updated data
        await db.refresh(db_item)
        # logger.info(f"🔧 DEBUG: After db.refresh - location = {db_item.location}")

        # Also refresh relationships for response
        await db.refresh(db_item, ["item_type", "status"])
        # logger.info(f"🔧 DEBUG: Response ready - location = {db_item.location}")

        logger.info(f"Updated inventory item with ID: {db_item.id}")

        # Bypass Cloudflare cache for inventory endpoints
        if response:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return db_item
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating inventory item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory item: {str(e)}",
        )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(item_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    try:
        db_item = await db.get(InventoryItemModel, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Save info for history before deleting
        item_info = f"SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"

        # Log history before delete
        action_text = f"Deleted item - {item_info}"
        await log_inventory_change(db, item_id, action_text, current_user.id)

        await db.delete(db_item)
        await db.commit()

        logger.info(f"Deleted inventory item with ID: {item_id}")
        return
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting inventory item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete inventory item: {str(e)}",
        )


# Helper endpoints untuk dropdown
@router.get("/types", response_model=List[InventoryItemTypeSchema])
async def get_item_types(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving item types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve item types: {str(e)}",
        )


@router.get("/statuses", response_model=List[InventoryStatusSchema])
async def get_statuses(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error retrieving statuses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statuses: {str(e)}",
        )


@router.post("/validate-barcode")
async def validate_barcode(barcode_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Validasi dan format barcode data untuk Serial Number atau MAC Address
    """
    try:
        barcode_text = barcode_data.get("barcode", "").strip()
        barcode_type = barcode_data.get("type", "serial")  # 'serial' atau 'mac'

        if not barcode_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode text cannot be empty"
            )

        result = {
            "original": barcode_text,
            "type": barcode_type,
            "valid": False,
            "formatted": None,
            "message": ""
        }

        if barcode_type == "mac":
            # Clean MAC address
            cleaned = re.sub(r'[^a-fA-F0-9]', '', barcode_text)

            if len(cleaned) != 12:
                result["message"] = "MAC Address harus terdiri dari 12 karakter hexadesimal"
                return result

            # Validate hex characters
            if not all(c in "0123456789ABCDEF" for c in cleaned.upper()):
                result["message"] = "MAC Address hanya boleh mengandung karakter hexadesimal (0-9, A-F)"
                return result

            # Format as AA:BB:CC:DD:EE:FF
            formatted_mac = ":".join([cleaned[i:i+2] for i in range(0, 12, 2)]).upper()

            # Check for duplicates
            existing = await db.execute(
                select(InventoryItemModel).where(InventoryItemModel.mac_address == formatted_mac)
            )
            if existing.scalar():
                result["message"] = "MAC Address sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = formatted_mac
            result["message"] = "MAC Address valid"

        elif barcode_type == "serial":
            # Clean serial number
            cleaned = re.sub(r'[^A-Za-z0-9\-_]', '', barcode_text).upper()

            if not cleaned:
                result["message"] = "Serial Number tidak valid"
                return result

            if len(cleaned) > 100:
                result["message"] = "Serial Number terlalu panjang (maksimal 100 karakter)"
                return result

            # Check for duplicates
            existing = await db.execute(
                select(InventoryItemModel).where(InventoryItemModel.serial_number == cleaned)
            )
            if existing.scalar():
                result["message"] = "Serial Number sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = cleaned
            result["message"] = "Serial Number valid"

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating barcode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate barcode: {str(e)}",
        )


@router.get("/{item_id}/history", response_model=List[InventoryHistoryResponse])
async def get_inventory_history(item_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan history perubahan untuk inventory item tertentu
    """
    try:
        # Cek apakah item ada
        item = await db.get(InventoryItemModel, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        # Query history dengan relasi user
        query = (
            select(InventoryHistoryModel)
            .options(selectinload(InventoryHistoryModel.user))
            .where(InventoryHistoryModel.item_id == item_id)
            .order_by(InventoryHistoryModel.timestamp.desc())
        )
        result = await db.execute(query)
        history_items = result.scalars().all()

        logger.info(f"Retrieved {len(history_items)} history items for inventory item {item_id}")
        return history_items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving inventory history for item {item_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory history: {str(e)}",
        )


@router.get("/history/all", response_model=List[dict])
async def get_all_inventory_history(db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan semua history inventory dari semua item dengan informasi item
    """
    try:
        # Query all history dengan join ke item dan user
        query = (
            select(
                InventoryHistoryModel,
                InventoryItemModel.serial_number,
                InventoryItemModel.mac_address
            )
            .join(InventoryItemModel, InventoryHistoryModel.item_id == InventoryItemModel.id)
            .options(selectinload(InventoryHistoryModel.user))
            .order_by(InventoryHistoryModel.timestamp.desc())
        )
        result = await db.execute(query)
        history_rows = result.all()

        # Format response
        history_items = []
        for history_row in history_rows:
            history, serial_number, mac_address = history_row
            history_items.append({
                "id": history.id,
                "item_id": history.item_id,
                "action": history.action,
                "timestamp": history.timestamp,
                "serial_number": serial_number,
                "mac_address": mac_address,
                "user": {
                    "id": history.user.id if history.user else None,
                    "name": history.user.name if history.user else "System"
                }
            })

        logger.info(f"Retrieved {len(history_items)} total history items")
        return history_items

    except Exception as e:
        logger.error(f"Error retrieving all inventory history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve inventory history: {str(e)}",
        )


@router.get("/template/download")
async def download_inventory_template(db: AsyncSession = Depends(get_db)):
    """
    Download template CSV/Excel untuk bulk import inventory items
    """
    try:
        # Get item types and statuses untuk dropdown reference
        item_types_result = await db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
        item_types = item_types_result.scalars().all()

        statuses_result = await db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
        statuses = statuses_result.scalars().all()

        # Find default item type (ONT ZTE) and status (DI GUDANG)
        default_item_type_id = None
        default_status_id = None

        # Try to find ONT ZTE as default item type
        for item_type in item_types:
            if 'ont' in item_type.name.lower() and 'zte' in item_type.name.lower():
                default_item_type_id = item_type.id
                break
        # Fallback to first item type if ONT ZTE not found
        if not default_item_type_id and item_types:
            default_item_type_id = item_types[0].id

        # Try to find "DI GUDANG" as default status
        for status_obj in statuses:
            if 'gudang' in status_obj.name.lower():
                default_status_id = status_obj.id
                break
        # Fallback to first status if DI GUDANG not found
        if not default_status_id and statuses:
            default_status_id = statuses[0].id

        # Create template data with user-friendly names - pastikan urutan kolom benar
        template_data = {
            'Serial Number': ['SN001', 'SN002', 'SN003'],
            'MAC Address': ['AA:BB:CC:DD:EE:01', 'AA:BB:CC:DD:EE:02', 'AA:BB:CC:DD:EE:03'],
            'Tipe Barang': [item_types[0].name if item_types else 'ONT ZTE'] * 3,
            'Status': [statuses[0].name if statuses else 'DI GUDANG'] * 3,
            'Lokasi': ['Gudang A', 'Gudang B', 'Gudang C'],
            'Tanggal Pembelian': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'Catatan': ['Catatan untuk item 1', 'Catatan untuk item 2', 'Catatan untuk item 3']
        }

        # Create DataFrame dengan urutan kolom yang pasti
        df = pd.DataFrame(template_data, columns=[
            'Serial Number', 'MAC Address', 'Tipe Barang', 'Status',
            'Lokasi', 'Tanggal Pembelian', 'Catatan'
        ])

        # Create Excel file dengan multiple sheets dan dropdown
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Template Data
            df.to_excel(writer, sheet_name='Template', index=False)
            worksheet = writer.sheets['Template']

            # Note: Excel dropdown validation temporarily disabled due to xlsxwriter compatibility
            # Users can refer to the reference sheets for valid values

            # Sheet 2: Item Types Reference
            if item_types:
                item_types_df = pd.DataFrame([
                    {'ID': item_type.id, 'Nama Tipe': item_type.name, 'Default': '✓' if 'ont' in item_type.name.lower() and 'zte' in item_type.name.lower() else ''}
                    for item_type in item_types
                ])
                item_types_df.to_excel(writer, sheet_name='Referensi Tipe', index=False)

            # Sheet 3: Statuses Reference
            if statuses:
                statuses_df = pd.DataFrame([
                    {'ID': status_obj.id, 'Nama Status': status_obj.name, 'Default': '✓' if 'gudang' in status_obj.name.lower() else ''}
                    for status_obj in statuses
                ])
                statuses_df.to_excel(writer, sheet_name='Referensi Status', index=False)

            # Get workbook and worksheet untuk format
            workbook = writer.book
            worksheet = writer.sheets['Template']

            # Add format untuk header
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BD',
                'border': 1
            })

            # Apply format ke header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

                # Add comments untuk setiap column
                if col_num == 0:  # Serial Number
                    worksheet.write_comment(0, col_num, "Serial Number unik perangkat (wajib diisi)")
                elif col_num == 1:  # MAC Address
                    worksheet.write_comment(0, col_num, "MAC Address dalam format XX:XX:XX:XX:XX:XX")
                elif col_num == 2:  # Tipe Barang
                    worksheet.write_comment(0, col_num, f"Tipe perangkat (lihat sheet Referensi Tipe). Default: {item_types[0].name if item_types else 'ONT ZTE'}")
                elif col_num == 3:  # Status
                    worksheet.write_comment(0, col_num, f"Status perangkat (lihat sheet Referensi Status). Default: {statuses[0].name if statuses else 'DI GUDANG'}")
                elif col_num == 4:  # Lokasi
                    worksheet.write_comment(0, col_num, "Lokasi penyimpanan perangkat")
                elif col_num == 5:  # Tanggal Pembelian
                    worksheet.write_comment(0, col_num, "Tanggal pembelian (format: YYYY-MM-DD)")
                elif col_num == 6:  # Catatan
                    worksheet.write_comment(0, col_num, "Catatan tambahan (opsional)")

            # Adjust column widths dengan lebar yang sesuai untuk Libre Office
            column_widths = {
                'Serial Number': 20,
                'MAC Address': 20,
                'Tipe Barang': 15,
                'Status': 15,
                'Lokasi': 15,
                'Tanggal Pembelian': 20,  # Lebar cukup untuk tanggal
                'Catatan': 25
            }

            for i, col in enumerate(df.columns):
                width = column_widths.get(col, 20)
                worksheet.set_column(i, i, width)

        output.seek(0)

        # Generate filename dengan timestamp dan random ID untuk cache busting
        import random
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = random.randint(1000, 9999)
        filename = f"template_inventory_import_{timestamp}_{random_id}.xlsx"

        logger.info(f"Generated inventory import template: {filename}")
        logger.info(f"Final template columns after Excel creation: {list(df.columns)}")
        logger.info(f"Total columns in template: {len(df.columns)}")

        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except Exception as e:
        logger.error(f"Error generating inventory template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}",
        )


@router.post("/bulk-import")
async def bulk_import_inventory(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Bulk import inventory items dari file Excel/CSV
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File harus berformat .xlsx, .xls, atau .csv"
            )

        # Read file content
        contents = await file.read()

        # Read Excel atau CSV
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading file: {str(e)}"
            )

        # Fungsi untuk mencocokkan nama kolom dengan berbagai variasi
        def find_column(df_columns, possible_names):
            """Mencari kolom dengan berbagai variasi nama"""
            for col in df_columns:
                # Normalisasi kolom: lowercase, strip spasi, ganti spasi dan dash dengan underscore
                normalized_col = str(col).lower().strip().replace(' ', '_').replace('-', '_').replace('.', '_')
                for name in possible_names:
                    # Normalisasi nama yang dicari
                    normalized_name = name.lower().strip().replace(' ', '_').replace('-', '_').replace('.', '_')
                    if normalized_col == normalized_name:
                        return col
            return None

        # Debug: Log nama kolom untuk membantu troubleshooting
        logger.info(f"Kolom-kolom yang ditemukan dalam file: {list(df.columns)}")

        # Cek apakah kolom-kolom wajib ada (dengan variasi nama)
        serial_number_col = find_column(df.columns, [
            'serial_number', 'serialnumber', 'serial_no', 'serial no', 'no serial', 'nomor serial', 'sn', 'serial number',
            'Serial_Number', 'SerialNumber', 'Serial_no', 'Serial no', 'No Serial', 'Nomor Serial', 'Serial Number',
            'serial number', 'serial number'
        ])
        if not serial_number_col:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kolom wajib tidak ditemukan: Serial Number. Kolom yang ditemukan: {list(df.columns)}"
            )

        # Cek item_type atau item_type_id atau Tipe Barang
        item_type_col = find_column(df.columns, [
            'item_type', 'itemtype', 'item_type_id', 'itemtypeid', 'jenis_barang', 'tipe_barang', 'type', 'tipe',
            'Item_Type', 'ItemType', 'Item_type', 'Itemtype', 'Jenis_Barang', 'Tipe_Barang', 'Type', 'Tipe',
            'tipe barang', 'tipe_barang'
        ])
        if not item_type_col:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kolom wajib tidak ditemukan: Tipe Barang/Item Type. Kolom yang ditemukan: {list(df.columns)}"
            )

        # Cek status atau status_id
        status_col = find_column(df.columns, [
            'status', 'status_id', 'statusid', 'kondisi', 'keadaan', 'Status', 'Status_id', 'Kondisi', 'Keadaan', 'status id'
        ])
        if not status_col:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kolom wajib tidak ditemukan: Status. Kolom yang ditemukan: {list(df.columns)}"
            )

        logger.info(f"Kolom yang berhasil dipetakan: serial_number='{serial_number_col}', item_type='{item_type_col}', status='{status_col}'")

        # Fungsi untuk mencari dan mengganti nama kolom tambahan
        def find_and_rename_additional_column(df, current_cols, possible_names, new_name):
            col_found = find_column(current_cols, possible_names)
            if col_found and col_found != new_name:
                df.rename(columns={col_found: new_name}, inplace=True)

        # Rename kolom untuk standardisasi
        df.rename(columns={
            serial_number_col: 'serial_number',
            item_type_col: 'item_type',
            status_col: 'status'
        }, inplace=True)

        # Rename kolom tambahan jika ditemukan
        find_and_rename_additional_column(df, df.columns,
            ['location', 'lokasi', 'tempat', 'letak'], 'location')
        find_and_rename_additional_column(df, df.columns,
            ['mac_address', 'mac', 'macaddress', 'alamat_mac', 'mac addr'], 'mac_address')
        find_and_rename_additional_column(df, df.columns,
            ['notes', 'catatan', 'keterangan', 'note'], 'notes')
        find_and_rename_additional_column(df, df.columns,
            ['purchase_date', 'tanggal_pembelian', 'tgl_pembelian', 'purchasedate'], 'purchase_date')

        # Get valid item types and statuses
        item_types_result = await db.execute(select(InventoryItemTypeModel))
        item_types = item_types_result.scalars().all()
        valid_item_type_ids = {item_type.id for item_type in item_types}
        item_type_names = {item_type.name.lower(): item_type.id for item_type in item_types}

        statuses_result = await db.execute(select(InventoryStatusModel))
        statuses = statuses_result.scalars().all()
        valid_status_ids = {status_obj.id for status_obj in statuses}
        status_names = {status_obj.name.lower(): status_obj.id for status_obj in statuses}

        # Find default item type (ONT ZTE) and status (DI GUDANG)
        default_item_type_id = None
        default_status_id = None

        for item_type in item_types:
            if 'ont' in item_type.name.lower() and 'zte' in item_type.name.lower():
                default_item_type_id = item_type.id
                break
        if not default_item_type_id and item_types:
            default_item_type_id = item_types[0].id

        for status_obj in statuses:
            if 'gudang' in status_obj.name.lower():
                default_status_id = status_obj.id
                break
        if not default_status_id and statuses:
            default_status_id = statuses[0].id

        # Create helper functions for type/status resolution
        def resolve_item_type(value):
            """Resolve item type by ID or name"""
            if pd.isna(value) or value == '':
                return default_item_type_id

            # Try to convert to int first (ID)
            try:
                int_val = int(value)
                if int_val in valid_item_type_ids:
                    return int_val
            except (ValueError, TypeError):
                pass

            # Try to resolve by name
            if str(value).lower() in item_type_names:
                return item_type_names[str(value).lower()]

            return default_item_type_id

        def resolve_status(value):
            """Resolve status by ID or name"""
            if pd.isna(value) or value == '':
                return default_status_id

            # Try to convert to int first (ID)
            try:
                int_val = int(value)
                if int_val in valid_status_ids:
                    return int_val
            except (ValueError, TypeError):
                pass

            # Try to resolve by name
            if str(value).lower() in status_names:
                return status_names[str(value).lower()]

            return default_status_id

        # Process each row
        success_count = 0
        error_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('serial_number')) or not str(row.get('serial_number')).strip():
                    continue

                # Validate data
                row_data = {}

                # Serial Number
                serial_number = str(row.get('serial_number', '')).strip().upper()
                if not serial_number:
                    errors.append(f"Baris {index + 2}: Serial Number wajib diisi")
                    error_count += 1
                    continue

                # Check duplicate serial number
                existing = await db.execute(
                    select(InventoryItemModel).where(InventoryItemModel.serial_number == serial_number)
                )
                if existing.scalar():
                    errors.append(f"Baris {index + 2}: Serial Number '{serial_number}' sudah ada")
                    error_count += 1
                    continue

                row_data['serial_number'] = serial_number

                # MAC Address (optional)
                mac_address = row.get('mac_address')
                if pd.notna(mac_address) and str(mac_address).strip():
                    mac_str = str(mac_address).strip().upper()
                    # Clean MAC address
                    mac_clean = re.sub(r'[^a-fA-F0-9]', '', mac_str)
                    if len(mac_clean) == 12:
                        formatted_mac = ":".join([mac_clean[i:i+2] for i in range(0, 12, 2)])
                        row_data['mac_address'] = formatted_mac
                    else:
                        errors.append(f"Baris {index + 2}: Format MAC Address tidak valid")
                        error_count += 1
                        continue

                # Location (optional)
                location = row.get('location')
                if pd.notna(location) and str(location).strip():
                    row_data['location'] = str(location).strip()

                # Purchase Date (optional)
                purchase_date = row.get('purchase_date')
                if pd.notna(purchase_date):
                    try:
                        if isinstance(purchase_date, str):
                            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
                        elif isinstance(purchase_date, datetime):
                            purchase_date = purchase_date.date()
                        row_data['purchase_date'] = purchase_date
                    except:
                        errors.append(f"Baris {index + 2}: Format tanggal tidak valid (gunakan YYYY-MM-DD)")
                        error_count += 1
                        continue

                # Notes (optional)
                notes = row.get('notes')
                if pd.notna(notes) and str(notes).strip():
                    row_data['notes'] = str(notes).strip()

                # Item Type (required, with default) - can be name or ID
                item_type_value = row.get('item_type')
                if pd.isna(item_type_value) or item_type_value == '':
                    # Use default item type
                    row_data['item_type_id'] = default_item_type_id
                else:
                    # Use resolve_item_type function which handles both name and ID
                    resolved_item_type_id = resolve_item_type(item_type_value)

                    # Check if the resolved ID is valid (not default unless it was the actual default)
                    original_item_type_str = str(item_type_value).strip().lower()
                    original_is_default = False

                    # Check if the original value matches the default name
                    for item_type in item_types:
                        if item_type.id == default_item_type_id:
                            if item_type.name.lower() == original_item_type_str:
                                original_is_default = True
                            break

                    # If resolved to default but original wasn't default and original value exists, it might be invalid
                    # However, let's use a different approach: check if original value could be resolved to any valid ID/name
                    item_type_found = False
                    # For ID
                    try:
                        int_val = int(item_type_value)
                        if int_val in valid_item_type_ids:
                            item_type_found = True
                    except (ValueError, TypeError):
                        pass
                    # For name
                    if str(item_type_value).lower() in item_type_names:
                        item_type_found = True

                    if not item_type_found and resolved_item_type_id == default_item_type_id:
                        errors.append(f"Baris {index + 2}: Tipe barang '{item_type_value}' tidak valid")
                        error_count += 1
                        continue
                    row_data['item_type_id'] = resolved_item_type_id

                # Status (required, with default) - can be name or ID
                status_value = row.get('status')
                if pd.isna(status_value) or status_value == '':
                    # Use default status
                    row_data['status_id'] = default_status_id
                else:
                    # Use resolve_status function which handles both name and ID
                    resolved_status_id = resolve_status(status_value)

                    # Check if the resolved ID is valid (not default unless it was the actual default)
                    original_status_str = str(status_value).strip().lower()
                    original_is_default = False

                    # Check if the original value matches the default name
                    for status_obj in statuses:
                        if status_obj.id == default_status_id:
                            if status_obj.name.lower() == original_status_str:
                                original_is_default = True
                            break

                    # Check if original value could be resolved to any valid status
                    status_found = False
                    # For ID
                    try:
                        int_val = int(status_value)
                        if int_val in valid_status_ids:
                            status_found = True
                    except (ValueError, TypeError):
                        pass
                    # For name
                    if str(status_value).lower() in status_names:
                        status_found = True

                    if not status_found and resolved_status_id == default_status_id:
                        errors.append(f"Baris {index + 2}: Status '{status_value}' tidak valid")
                        error_count += 1
                        continue
                    row_data['status_id'] = resolved_status_id

                # Create inventory item
                db_item = InventoryItemModel(**row_data)
                db.add(db_item)
                await db.flush()  # Get ID without committing

                # Log history
                action_text = f"Imported item - SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"
                await log_inventory_change(db, db_item.id, action_text, current_user.id)

                success_count += 1

            except Exception as row_error:
                errors.append(f"Baris {index + 2}: {str(row_error)}")
                error_count += 1
                continue

        # Commit all successful items
        await db.commit()

        logger.info(f"Bulk import completed: {success_count} success, {error_count} errors")

        return {
            "success": True,
            "message": f"Import selesai! {success_count} item berhasil ditambahkan, {error_count} item gagal.",
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[:50]  # Limit errors to first 50
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during bulk import: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed during bulk import: {str(e)}",
        )

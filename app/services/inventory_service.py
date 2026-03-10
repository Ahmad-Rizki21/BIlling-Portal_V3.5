import logging
import re
import io
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import text, func
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from ..models.inventory_item import InventoryItem as InventoryItemModel
from ..models.inventory_item_type import InventoryItemType as InventoryItemTypeModel
# Fix: Import Status from correct model
from ..models.inventory_status import InventoryStatus as InventoryStatusModel
from ..models.inventory_history import InventoryHistory as InventoryHistoryModel
from ..models.user import User as UserModel
from .base_service import BaseService

logger = logging.getLogger(__name__)

class InventoryService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(InventoryItemModel, db)

    async def log_inventory_change(self, item_id: int, action: str, user_id: int):
        """Helper to log inventory history."""
        try:
            query = text("""
                INSERT INTO inventory_history (item_id, action, user_id, timestamp)
                VALUES (:item_id, :action, :user_id, NOW())
            """)
            await self.db.execute(query, {
                "item_id": item_id,
                "action": action,
                "user_id": user_id
            })
            await self.db.commit()
            logger.info(f"Logged inventory history: item_id={item_id}, action={action}, user_id={user_id}")
        except Exception as e:
            logger.error(f"Failed to log inventory history: {str(e)}")

    async def create_item(self, item_data: Dict[str, Any], current_user_id: int) -> InventoryItemModel:
        """Create a new inventory item and log the action."""
        try:
            db_item = InventoryItemModel(**item_data)
            self.db.add(db_item)
            await self.db.commit()
            
            action_text = f"Created item - SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"
            await self.log_inventory_change(db_item.id, action_text, current_user_id)
            
            await self.db.refresh(db_item, ["item_type", "status"])
            return db_item
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating inventory item: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create inventory item: {str(e)}",
            )

    async def get_all_items(self) -> List[InventoryItemModel]:
        """Get all inventory items with relations."""
        try:
            query = (
                select(InventoryItemModel)
                .options(
                    selectinload(InventoryItemModel.item_type),
                    selectinload(InventoryItemModel.status),
                )
                .order_by(InventoryItemModel.id)
            )
            result = await self.db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error retrieving inventory items: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve inventory items: {str(e)}",
            )

    async def update_item(self, item_id: int, update_data: Dict[str, Any], current_user_id: int) -> InventoryItemModel:
        """Update an inventory item, track changes and login history."""
        try:
            db_item = await self.db.get(InventoryItemModel, item_id)
            if not db_item:
                raise HTTPException(status_code=404, detail="Item not found")

            # Validate fields (remove restricted ones)
            restricted_fields = ['created_at', 'updated_at', 'id']
            for field in restricted_fields:
                if field in update_data:
                    del update_data[field]

            changes = []
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
                    
                    setattr(db_item, key, value)

            if changes:
                await self.db.commit()
                action_text = f"Updated item - SN: {db_item.serial_number}, Changes: {', '.join(changes)}"
                await self.log_inventory_change(db_item.id, action_text, current_user_id)
                await self.db.refresh(db_item, ["item_type", "status"])
            
            return db_item
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating inventory item {item_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update inventory item: {str(e)}",
            )

    async def delete_item(self, item_id: int, current_user_id: int):
        """Delete an inventory item and log the action."""
        try:
            db_item = await self.db.get(InventoryItemModel, item_id)
            if not db_item:
                raise HTTPException(status_code=404, detail="Item not found")

            item_info = f"SN: {db_item.serial_number}, Type ID: {db_item.item_type_id}, Location: {db_item.location or 'Not set'}"
            action_text = f"Deleted item - {item_info}"
            
            await self.log_inventory_change(item_id, action_text, current_user_id)
            await self.db.delete(db_item)
            await self.db.commit()
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting inventory item {item_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete inventory item: {str(e)}",
            )

    async def get_item_types(self) -> List[InventoryItemTypeModel]:
        """Get all item types."""
        result = await self.db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
        return list(result.scalars().all())

    async def get_statuses(self) -> List[InventoryStatusModel]:
        """Get all inventory statuses."""
        result = await self.db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
        return list(result.scalars().all())

    async def validate_barcode(self, barcode_text: str, barcode_type: str = "serial") -> Dict[str, Any]:
        """Validate and format barcode data."""
        if not barcode_text:
            raise HTTPException(status_code=400, detail="Barcode text cannot be empty")

        result = {
            "original": barcode_text,
            "type": barcode_type,
            "valid": False,
            "formatted": None,
            "message": ""
        }

        if barcode_type == "mac":
            cleaned = re.sub(r'[^a-fA-F0-9]', '', barcode_text)
            if len(cleaned) != 12:
                result["message"] = "MAC Address harus terdiri dari 12 karakter hexadesimal"
                return result

            formatted_mac = ":".join([cleaned[i:i+2] for i in range(0, 12, 2)]).upper()
            existing = await self.db.execute(
                select(InventoryItemModel).where(InventoryItemModel.mac_address == formatted_mac)
            )
            if existing.scalar():
                result["message"] = "MAC Address sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = formatted_mac
            result["message"] = "MAC Address valid"

        elif barcode_type == "serial":
            cleaned = re.sub(r'[^A-Za-z0-9\-_]', '', barcode_text).upper()
            if not cleaned:
                result["message"] = "Serial Number tidak valid"
                return result
            
            if len(cleaned) > 100:
                result["message"] = "Serial Number terlalu panjang (maksimal 100 karakter)"
                return result

            existing = await self.db.execute(
                select(InventoryItemModel).where(InventoryItemModel.serial_number == cleaned)
            )
            if existing.scalar():
                result["message"] = "Serial Number sudah terdaftar dalam sistem"
                return result

            result["valid"] = True
            result["formatted"] = cleaned
            result["message"] = "Serial Number valid"

        return result

    async def get_item_history(self, item_id: int) -> List[InventoryHistoryModel]:
        """Get history for a specific item."""
        item = await self.db.get(InventoryItemModel, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")

        query = (
            select(InventoryHistoryModel)
            .options(selectinload(InventoryHistoryModel.user))
            .where(InventoryHistoryModel.item_id == item_id)
            .order_by(InventoryHistoryModel.timestamp.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all_history(self) -> List[Dict[str, Any]]:
        """Get all history records with item info."""
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
        result = await self.db.execute(query)
        history_rows = result.all()

        return [
            {
                "id": h.id,
                "item_id": h.item_id,
                "action": h.action,
                "timestamp": h.timestamp,
                "serial_number": sn,
                "mac_address": mac,
                "user": {
                    "id": h.user.id if h.user else None,
                    "name": h.user.name if h.user else "System"
                }
            }
            for h, sn, mac in history_rows
        ]

    async def generate_import_template(self) -> StreamingResponse:
        """Generate Excel template for bulk import."""
        try:
            item_types = await self.get_item_types()
            statuses = await self.get_statuses()

            template_data = {
                'Serial Number': ['SN001', 'SN002', 'SN003'],
                'MAC Address': ['AA:BB:CC:DD:EE:01', 'AA:BB:CC:DD:EE:02', 'AA:BB:CC:DD:EE:03'],
                'Tipe Barang': [item_types[0].name if item_types else 'ONT ZTE'] * 3,
                'Status': [statuses[0].name if statuses else 'DI GUDANG'] * 3,
                'Lokasi': ['Gudang A', 'Gudang B', 'Gudang C'],
                'Tanggal Pembelian': ['2024-01-15', '2024-01-16', '2024-01-17'],
                'Catatan': ['Catatan untuk item 1', 'Catatan untuk item 2', 'Catatan untuk item 3']
            }

            df = pd.DataFrame(template_data, columns=[
                'Serial Number', 'MAC Address', 'Tipe Barang', 'Status',
                'Lokasi', 'Tanggal Pembelian', 'Catatan'
            ])

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Template', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Template']

                header_format = workbook.add_format({
                    'bold': True, 'text_wrap': True, 'valign': 'top',
                    'fg_color': '#D7E4BD', 'border': 1
                })

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Reference sheets
                if item_types:
                    item_types_df = pd.DataFrame([{'ID': i.id, 'Nama Tipe': i.name} for i in item_types])
                    item_types_df.to_excel(writer, sheet_name='Referensi Tipe', index=False)
                if statuses:
                    statuses_df = pd.DataFrame([{'ID': s.id, 'Nama Status': s.name} for s in statuses])
                    statuses_df.to_excel(writer, sheet_name='Referensi Status', index=False)

            output.seek(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"template_inventory_import_{timestamp}.xlsx"

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        except Exception as e:
            logger.error(f"Error generating inventory template: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def bulk_import(self, file_content: bytes, filename: str, current_user_id: int) -> Dict[str, Any]:
        """Bulk import items from file."""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            # Helper to find columns
            def find_col(possible_names):
                for col in df.columns:
                    norm = str(col).lower().strip().replace(' ', '_').replace('-', '_').replace('.', '_')
                    for name in possible_names:
                        if norm == name.lower().strip().replace(' ', '_').replace('-', '_').replace('.', '_'):
                            return col
                return None

            sn_col = find_col(['serial_number', 'serialnumber', 'sn', 'serial_no', 'serial no', 'no serial'])
            type_col = find_col(['item_type', 'itemtype', 'item_type_id', 'tipe_barang', 'type', 'tipe'])
            status_col = find_col(['status', 'status_id', 'kondisi', 'keadaan'])

            if not all([sn_col, type_col, status_col]):
                 raise HTTPException(status_code=400, detail="Missing required columns: Serial Number, Tipe Barang, or Status")

            # Standardize names
            df.rename(columns={sn_col: 'serial_number', type_col: 'item_type', status_col: 'status'}, inplace=True)
            
            # Optional columns
            opt_cols = {
                'location': ['location', 'lokasi', 'tempat'],
                'mac_address': ['mac_address', 'mac', 'macaddress'],
                'notes': ['notes', 'catatan', 'note'],
                'purchase_date': ['purchase_date', 'tanggal_pembelian', 'tgl_pembelian']
            }
            for target, aliases in opt_cols.items():
                found = find_col(aliases)
                if found and found != target:
                    df.rename(columns={found: target}, inplace=True)

            # Metadata for resolution
            item_types = await self.get_item_types()
            statuses = await self.get_statuses()
            
            type_map = {t.name.lower(): t.id for t in item_types}
            type_ids = {t.id for t in item_types}
            status_map = {s.name.lower(): s.id for s in statuses}
            status_ids = {s.id for s in statuses}
            
            def resolve(val, mapping, valid_ids):
                if pd.isna(val) or val == '': return None
                try:
                    iv = int(val)
                    if iv in valid_ids: return iv
                except: pass
                return mapping.get(str(val).lower().strip())

            success_count = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    sn = str(row.get('serial_number', '')).strip().upper()
                    if not sn: continue
                    
                    # Duplicate check
                    exists = await self.db.execute(select(InventoryItemModel).where(InventoryItemModel.serial_number == sn))
                    if exists.scalar():
                        errors.append(f"Row {idx+2}: Duplikat SN '{sn}'")
                        continue

                    # Resolve type & status
                    t_id = resolve(row.get('item_type'), type_map, type_ids)
                    s_id = resolve(row.get('status'), status_map, status_ids)
                    
                    if not t_id or not s_id:
                        errors.append(f"Row {idx+2}: Tipe/Status tidak valid")
                        continue

                    item_data = {
                        'serial_number': sn,
                        'item_type_id': t_id,
                        'status_id': s_id,
                        'location': str(row.get('location')).strip() if pd.notna(row.get('location')) else None,
                        'notes': str(row.get('notes')).strip() if pd.notna(row.get('notes')) else None
                    }
                    
                    # MAC
                    mac = row.get('mac_address')
                    if pd.notna(mac) and str(mac).strip():
                        mac_clean = re.sub(r'[^a-fA-F0-9]', '', str(mac).strip().upper())
                        if len(mac_clean) == 12:
                            item_data['mac_address'] = ":".join([mac_clean[i:i+2] for i in range(0, 12, 2)])
                        else:
                            errors.append(f"Row {idx+2}: MAC tidak valid")
                            continue

                    # Date
                    p_date = row.get('purchase_date')
                    if pd.notna(p_date):
                        try:
                            if isinstance(p_date, str):
                                item_data['purchase_date'] = datetime.strptime(p_date, '%Y-%m-%d').date()
                            else:
                                item_data['purchase_date'] = p_date.date()
                        except:
                            errors.append(f"Row {idx+2}: Format tanggal salah")
                            continue

                    db_item = InventoryItemModel(**item_data)
                    self.db.add(db_item)
                    await self.db.flush()
                    
                    action_text = f"Imported item - SN: {sn}"
                    await self.log_inventory_change(db_item.id, action_text, current_user_id)
                    success_count += 1

                except Exception as row_error:
                    errors.append(f"Row {idx+2}: {str(row_error)}")

            await self.db.commit()
            return {
                "success": True,
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors[:50]
            }
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

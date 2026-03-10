"""
Service Layer untuk Trouble Ticket.
Menangani logika bisnis terkait manajemen tiket gangguan, transisi status,
dan sinkronisasi downtime tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc, and_, or_, text
from fastapi import HTTPException, status, BackgroundTasks

from ..models.trouble_ticket import (
    TroubleTicket as TroubleTicketModel,
    TicketHistory as TicketHistoryModel,
    ActionTaken as ActionTakenModel,
    TicketStatus,
    TicketPriority,
    TicketCategory,
)
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.user import User as UserModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..schemas.trouble_ticket import (
    TroubleTicketCreate,
    TroubleTicketUpdate,
    TicketStatusUpdate,
    DowntimeUpdate,
    TicketAssignment,
)
from ..websocket_manager import manager
from .base_service import BaseService

logger = logging.getLogger(__name__)

class TroubleTicketService(BaseService[TroubleTicketModel, TroubleTicketCreate, TroubleTicketUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(TroubleTicketModel, db)

    async def get_by_id_with_relations(self, id: int, relations: Optional[List[str]] = None) -> TroubleTicketModel:
        """
        Override untuk handle nested relations yang dibutuhkan oleh TroubleTicket schema.
        Mencegah error sqlalchemy.exc.MissingGreenlet saat serialisasi response.
        """
        query = select(TroubleTicketModel).where(TroubleTicketModel.id == id)
        
        # Eager load semua relasi yang dibutuhkan oleh Pydantic schema TroubleTicket
        query = query.options(
            selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            selectinload(TroubleTicketModel.data_teknis).selectinload(DataTeknisModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            selectinload(TroubleTicketModel.assigned_user).selectinload(UserModel.role)
        )
        
        result = (await self.db.execute(query)).scalars().unique().one_or_none()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Trouble Ticket tidak ditemukan"
            )
        return result

    async def generate_ticket_number(self) -> str:
        """Generate unique ticket number dengan format TFTTH-XXXXX (sequential)"""
        prefix = "TFTTH"
        result = await self.db.execute(
            select(TroubleTicketModel.ticket_number)
            .where(TroubleTicketModel.ticket_number.like(f"{prefix}-%"))
            .order_by(desc(TroubleTicketModel.ticket_number))
            .limit(1)
        )
        last_ticket = result.scalar_one_or_none()

        if last_ticket:
            try:
                last_num = int(last_ticket.split("-")[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                next_num = 1
        else:
            next_num = 1

        return f"{prefix}-{next_num:04d}"

    async def validate_pelanggan(self, pelanggan_id: int) -> PelangganModel:
        """Validasi apakah pelanggan ada"""
        pelanggan = await self.db.get(PelangganModel, pelanggan_id)
        if not pelanggan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pelanggan dengan ID {pelanggan_id} tidak ditemukan"
            )
        return pelanggan

    async def validate_data_teknis(self, data_teknis_id: Optional[int]) -> Optional[DataTeknisModel]:
        """Validasi apakah data teknis ada (opsional)"""
        if data_teknis_id is None:
            return None
        data_teknis = await self.db.get(DataTeknisModel, data_teknis_id)
        if not data_teknis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data Teknis dengan ID {data_teknis_id} tidak ditemukan"
            )
        return data_teknis

    async def validate_user(self, user_id: Optional[int]) -> Optional[UserModel]:
        """Validasi apakah user ada (opsional)"""
        if user_id is None:
            return None
        user = await self.db.get(UserModel, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan ID {user_id} tidak ditemukan"
            )
        return user

    async def add_ticket_history(
        self,
        ticket_id: int,
        old_status: Optional[TicketStatus],
        new_status: TicketStatus,
        changed_by: Optional[int],
        notes: Optional[str] = None
    ):
        """Menambahkan entri history perubahan status ticket"""
        history = TicketHistoryModel(
            ticket_id=ticket_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        self.db.add(history)
        await self.db.flush()

    async def add_action_taken(
        self,
        ticket_id: int,
        action_description: Optional[str] = None,
        summary_problem: Optional[str] = None,
        summary_action: Optional[str] = None,
        evidence: Optional[str] = None,
        notes: Optional[str] = None,
        taken_by: Optional[int] = None
    ):
        """Menambahkan entri action taken"""
        action_taken = ActionTakenModel(
            ticket_id=ticket_id,
            action_description=action_description or "",
            summary_problem=summary_problem or "",
            summary_action=summary_action or "",
            evidence=evidence,
            notes=notes,
            taken_by=taken_by
        )
        self.db.add(action_taken)
        await self.db.flush()

    async def create_ticket(
        self,
        ticket_in: TroubleTicketCreate,
        current_user: UserModel,
        background_tasks: BackgroundTasks
    ) -> TroubleTicketModel:
        """Membuat Trouble Ticket baru dengan validasi lengkap"""
        try:
            # Validasi
            pelanggan = await self.validate_pelanggan(ticket_in.pelanggan_id)
            await self.validate_data_teknis(ticket_in.data_teknis_id)
            await self.validate_user(ticket_in.assigned_to)

            # Ticket Number
            ticket_number = await self.generate_ticket_number()
            
            # Safety check
            existing = await self.db.execute(
                select(TroubleTicketModel).where(TroubleTicketModel.ticket_number == ticket_number)
            )
            if existing.scalar_one_or_none():
                ticket_number = await self.generate_ticket_number()

            # Creation
            db_ticket = TroubleTicketModel(
                ticket_number=ticket_number,
                pelanggan_id=ticket_in.pelanggan_id,
                data_teknis_id=ticket_in.data_teknis_id,
                title=ticket_in.title,
                description=ticket_in.description,
                category=TicketCategory(ticket_in.category.value),
                priority=TicketPriority(ticket_in.priority.value),
                status=TicketStatus.OPEN,
                assigned_to=ticket_in.assigned_to,
                evidence=ticket_in.evidence,
                created_at=datetime.now(),
                downtime_start=datetime.now()
            )

            self.db.add(db_ticket)
            await self.db.flush()

            # History
            await self.add_ticket_history(
                db_ticket.id, None, TicketStatus.OPEN, current_user.id, "Ticket created"
            )

            await self.db.commit()

            # Evidence handling
            if ticket_in.evidence:
                try:
                    await self.add_action_taken(
                        ticket_id=db_ticket.id,
                        action_description="Ticket created with evidence",
                        summary_problem="Initial evidence provided during ticket creation",
                        summary_action="Evidence uploaded with initial ticket",
                        evidence=ticket_in.evidence,
                        taken_by=current_user.id
                    )
                    await self.db.commit()
                except Exception as e:
                    logger.error(f"❌ Failed to add initial action taken for ticket {ticket_number}: {e}")

            # Notify
            notification_data = {
                "type": "new_trouble_ticket",
                "message": f"Ticket baru dibuat: {ticket_number} - {ticket_in.title}",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "ticket_id": db_ticket.id,
                    "ticket_number": ticket_number,
                    "pelanggan_id": ticket_in.pelanggan_id,
                    "pelanggan_nama": pelanggan.nama,
                    "priority": ticket_in.priority.value,
                    "category": ticket_in.category.value,
                    "created_by": current_user.name
                }
            }
            background_tasks.add_task(manager.broadcast_to_roles, notification_data, ["NOC", "CS", "Admin"])

            return await self.get_by_id_with_relations(
                db_ticket.id, 
                ["pelanggan", "data_teknis", "assigned_user"]
            )

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to create trouble ticket: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal membuat trouble ticket: {str(e)}"
            )

    async def get_filtered_tickets(
        self,
        skip: int,
        limit: int,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        assigned_to: Optional[int] = None,
        pelanggan_id: Optional[int] = None,
        id_brand: Optional[str] = None,
        brand: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        include_relations: bool = False
    ) -> Tuple[List[TroubleTicketModel], int]:
        """Mendapatkan trouble tickets dengan filter dan pagination"""
        query = select(TroubleTicketModel)
        count_query = select(func.count(TroubleTicketModel.id))

        if include_relations:
            query = query.options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis).selectinload(DataTeknisModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.assigned_user).selectinload(UserModel.role)
            )

        filters = []
        if status_filter:
            filters.append(TroubleTicketModel.status == TicketStatus(status_filter))
        if priority_filter:
            filters.append(TroubleTicketModel.priority == TicketPriority(priority_filter))
        if category_filter:
            filters.append(TroubleTicketModel.category == TicketCategory(category_filter))
        if assigned_to:
            filters.append(TroubleTicketModel.assigned_to == assigned_to)
        if pelanggan_id:
            filters.append(TroubleTicketModel.pelanggan_id == pelanggan_id)
        if date_from:
            filters.append(TroubleTicketModel.created_at >= date_from)
        if date_to:
            filters.append(TroubleTicketModel.created_at <= date_to)
        if search:
            search_term = f"%{search}%"
            filters.append(
                or_(
                    TroubleTicketModel.title.ilike(search_term),
                    TroubleTicketModel.description.ilike(search_term),
                    TroubleTicketModel.ticket_number.ilike(search_term)
                )
            )

        if id_brand or brand:
            query = query.join(PelangganModel, TroubleTicketModel.pelanggan_id == PelangganModel.id)
            count_query = count_query.join(PelangganModel, TroubleTicketModel.pelanggan_id == PelangganModel.id)
            if id_brand:
                filters.append(PelangganModel.id_brand == id_brand)
            if brand:
                query = query.join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand)
                count_query = count_query.join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand)
                filters.append(HargaLayananModel.brand.ilike(f"%{brand}%"))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total_items = total_result.scalar_one()

        query = query.order_by(desc(TroubleTicketModel.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        tickets = result.scalars().unique().all()

        return list(tickets), total_items

    async def update_ticket(
        self,
        ticket_id: int,
        ticket_update: TroubleTicketUpdate,
        current_user: UserModel,
        background_tasks: BackgroundTasks
    ) -> TroubleTicketModel:
        """Update trouble ticket (partial update)"""
        try:
            ticket = await self.get_by_id(ticket_id)
            old_status = ticket.status
            status_changed = False

            update_data = ticket_update.model_dump(exclude_unset=True)

            if "status" in update_data:
                ticket.status = TicketStatus(update_data["status"])
                status_changed = True
                del update_data["status"]

            if "priority" in update_data:
                ticket.priority = TicketPriority(update_data["priority"])
                del update_data["priority"]

            if "category" in update_data:
                ticket.category = TicketCategory(update_data["category"])
                del update_data["category"]

            for key, value in update_data.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)

            ticket.updated_at = datetime.now()

            if status_changed:
                await self.add_ticket_history(
                    ticket_id, old_status, ticket.status, current_user.id
                )

            # Evidence handling
            if hasattr(ticket_update, 'evidence') and ticket_update.evidence is not None:
                old_evidence = getattr(ticket, 'evidence', None)
                if ticket_update.evidence != (old_evidence if old_evidence else None):
                    await self.add_action_taken(
                        ticket_id=ticket_id,
                        action_description="Evidence updated",
                        summary_problem="Ticket evidence was updated",
                        summary_action="Updated ticket evidence",
                        evidence=ticket_update.evidence,
                        taken_by=current_user.id
                    )

            await self.db.commit()

            if status_changed:
                notification_data = {
                    "type": "ticket_status_changed",
                    "message": f"Status ticket {ticket.ticket_number} berubah dari {old_status.value} ke {ticket.status.value}",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "ticket_id": ticket.id,
                        "ticket_number": ticket.ticket_number,
                        "old_status": old_status.value,
                        "new_status": ticket.status.value,
                        "updated_by": current_user.name
                    }
                }
                background_tasks.add_task(manager.broadcast_to_roles, notification_data, ["NOC", "CS", "Admin"])

            return await self.get_by_id_with_relations(
                ticket_id, 
                ["pelanggan", "data_teknis", "assigned_user"]
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to update trouble ticket {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal update trouble ticket: {str(e)}"
            )

    async def update_status(
        self,
        ticket_id: int,
        status_update: TicketStatusUpdate,
        current_user: UserModel,
        background_tasks: BackgroundTasks
    ) -> TroubleTicketModel:
        """Update status trouble ticket dengan history tracking"""
        try:
            ticket = await self.get_by_id(ticket_id)
            old_status = ticket.status
            new_status = TicketStatus(status_update.status.value)

            if old_status == new_status:
                return ticket

            ticket.status = new_status
            ticket.updated_at = datetime.now()

            # Resolution logic
            if new_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                ticket.resolved_at = datetime.now()
                if ticket.downtime_start and not ticket.downtime_end:
                    ticket.downtime_end = datetime.now()
                    ticket.update_downtime()
            
            # Reactivation logic
            elif new_status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS] and old_status not in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
                if not ticket.downtime_start or (ticket.downtime_end and ticket.downtime_start < ticket.downtime_end):
                    ticket.downtime_start = datetime.now()
                    ticket.downtime_end = None
                    ticket.update_downtime()

            await self.add_ticket_history(
                ticket_id, old_status, new_status, current_user.id, status_update.notes
            )
            
            if status_update.action_description or status_update.summary_problem or status_update.summary_action:
                evidence_str = status_update.evidence
                if isinstance(status_update.evidence, list):
                    import json
                    evidence_str = json.dumps(status_update.evidence)

                await self.add_action_taken(
                    ticket_id,
                    status_update.action_description,
                    status_update.summary_problem,
                    status_update.summary_action,
                    evidence_str,
                    status_update.notes,
                    current_user.id
                )

            await self.db.commit()

            notification_data = {
                "type": "ticket_status_changed",
                "message": f"Status ticket {ticket.ticket_number} berubah dari {old_status.value} ke {new_status.value}",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "notes": status_update.notes,
                    "updated_by": current_user.name
                }
            }
            background_tasks.add_task(manager.broadcast_to_roles, notification_data, ["NOC", "CS", "Admin"])

            return await self.get_by_id_with_relations(
                ticket_id, 
                ["pelanggan", "data_teknis", "assigned_user"]
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to update ticket status {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal update status ticket: {str(e)}"
            )

    async def update_downtime(
        self,
        ticket_id: int,
        downtime_in: DowntimeUpdate,
        current_user: UserModel
    ) -> TroubleTicketModel:
        """Update downtime tracking untuk ticket"""
        try:
            ticket = await self.get_by_id(ticket_id)

            if downtime_in.downtime_start is not None:
                ticket.downtime_start = downtime_in.downtime_start
            if downtime_in.downtime_end is not None:
                ticket.downtime_end = downtime_in.downtime_end

            ticket.update_downtime()
            ticket.updated_at = datetime.now()

            await self.db.commit()
            return await self.get_by_id_with_relations(
                ticket_id, 
                ["pelanggan", "data_teknis", "assigned_user"]
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to update ticket downtime {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal update downtime ticket: {str(e)}"
            )

    async def assign_ticket(
        self,
        ticket_id: int,
        assignment_in: TicketAssignment,
        current_user: UserModel,
        background_tasks: BackgroundTasks
    ) -> TroubleTicketModel:
        """Menugaskan ticket ke user tertentu"""
        try:
            ticket = await self.get_by_id(ticket_id)
            assigned_user = await self.validate_user(assignment_in.assigned_to)

            ticket.assigned_to = assignment_in.assigned_to
            ticket.updated_at = datetime.now()

            if ticket.status == TicketStatus.OPEN:
                old_status = ticket.status
                new_status = TicketStatus.IN_PROGRESS
                ticket.status = new_status
                
                await self.add_ticket_history(
                    ticket_id, old_status, new_status, current_user.id,
                    f"Auto-assigned to {assigned_user.name}. {assignment_in.notes or ''}"
                )
                
                if not ticket.downtime_start or (ticket.downtime_end and ticket.downtime_start < ticket.downtime_end):
                    ticket.downtime_start = datetime.now()
                    ticket.downtime_end = None
                    ticket.update_downtime()

            await self.db.commit()

            notification_data = {
                "type": "ticket_assigned",
                "message": f"Ticket {ticket.ticket_number} ditugaskan kepada Anda",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "title": ticket.title,
                    "assigned_by": current_user.name,
                    "notes": assignment_in.notes
                }
            }
            background_tasks.add_task(manager.send_to_user, notification_data, assignment_in.assigned_to)

            return await self.get_by_id_with_relations(
                ticket_id, 
                ["pelanggan", "data_teknis", "assigned_user"]
            )
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to assign ticket {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal menugaskan ticket: {str(e)}"
            )

    async def add_action(
        self,
        ticket_id: int,
        action_in: TicketStatusUpdate,
        current_user: UserModel
    ) -> ActionTakenModel:
        """Menambahkan action history tanpa mengganti status ticket"""
        try:
            ticket = await self.get_by_id(ticket_id)

            if not action_in.action_description and not action_in.summary_problem and not action_in.summary_action:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one of these fields is required: action_description, summary_problem, or summary_action"
                )

            action_taken = ActionTakenModel(
                ticket_id=ticket_id,
                action_description=action_in.action_description,
                summary_problem=action_in.summary_problem,
                summary_action=action_in.summary_action,
                evidence=action_in.evidence,
                notes=action_in.notes,
                taken_by=current_user.id
            )
            
            self.db.add(action_taken)
            if action_in.evidence:
                ticket.evidence = action_in.evidence
                
            await self.db.commit()
            
            result = await self.db.execute(
                select(ActionTakenModel)
                .where(ActionTakenModel.id == action_taken.id)
                .options(selectinload(ActionTakenModel.taken_user).selectinload(UserModel.role))
            )
            return result.scalar_one()
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to add ticket action {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal menambahkan action ticket: {str(e)}"
            )

    async def delete_ticket(self, ticket_id: int, current_user: UserModel):
        """Menghapus trouble ticket (hanya untuk status resolved/closed/cancelled)"""
        try:
            ticket = await self.get_by_id(ticket_id)

            if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELLED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Hanya ticket dengan status Resolved/Closed/Cancelled yang dapat dihapus. Status saat ini: {ticket.status.value}"
                )

            from sqlalchemy import delete
            await self.db.execute(delete(TicketHistoryModel).where(TicketHistoryModel.ticket_id == ticket_id))
            await self.db.execute(delete(ActionTakenModel).where(ActionTakenModel.ticket_id == ticket_id))
            await self.db.execute(delete(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id))

            await self.db.commit()
            logger.info(f"✅ Trouble Ticket {ticket_id} ({ticket.ticket_number}) deleted by {current_user.name}")
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to delete trouble ticket {ticket_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gagal menghapus trouble ticket: {str(e)}"
            )

    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Mendapatkan statistik trouble tickets untuk dashboard"""
        try:
            total = (await self.db.execute(select(func.count(TroubleTicketModel.id)))).scalar_one()
            
            open_t = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.status == TicketStatus.OPEN))).scalar_one()
            in_prog = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.status == TicketStatus.IN_PROGRESS))).scalar_one()
            res = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.status == TicketStatus.RESOLVED))).scalar_one()
            cls = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.status == TicketStatus.CLOSED))).scalar_one()
            
            high = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.priority == TicketPriority.HIGH))).scalar_one()
            crit = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.priority == TicketPriority.CRITICAL))).scalar_one()
            
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.created_at >= month_start))).scalar_one()
            
            yesterday = now - timedelta(hours=24)
            unres_24h = (await self.db.execute(
                select(func.count(TroubleTicketModel.id))
                .where(and_(
                    TroubleTicketModel.created_at <= yesterday,
                    TroubleTicketModel.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING_CUSTOMER, TicketStatus.PENDING_VENDOR])
                ))
            )).scalar_one()

            avg_res = (await self.db.execute(
                select(func.avg(func.timestampdiff(text('HOUR'), TroubleTicketModel.created_at, TroubleTicketModel.resolved_at)))
                .where(and_(TroubleTicketModel.resolved_at.isnot(None), TroubleTicketModel.created_at.isnot(None)))
            )).scalar_one()

            return {
                "total_tickets": total,
                "open_tickets": open_t,
                "in_progress_tickets": in_prog,
                "resolved_tickets": res,
                "closed_tickets": cls,
                "high_priority_tickets": high,
                "critical_priority_tickets": crit,
                "avg_resolution_time_hours": round(avg_res, 2) if avg_res else None,
                "tickets_this_month": this_month,
                "unresolved_over_24h": unres_24h,
            }
        except Exception as e:
            logger.error(f"❌ Failed to get ticket statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_history(self, ticket_id: int) -> List[TicketHistoryModel]:
        """Mendapatkan history perubahan status ticket"""
        await self.get_by_id(ticket_id)
        result = await self.db.execute(
            select(TicketHistoryModel)
            .where(TicketHistoryModel.ticket_id == ticket_id)
            .options(selectinload(TicketHistoryModel.changed_user).selectinload(UserModel.role))
            .order_by(desc(TicketHistoryModel.created_at))
        )
        return list(result.scalars().all())

    async def get_actions(self, ticket_id: int) -> List[ActionTakenModel]:
        """Mendapatkan history action taken untuk ticket"""
        await self.get_by_id(ticket_id)
        result = await self.db.execute(
            select(ActionTakenModel)
            .where(ActionTakenModel.ticket_id == ticket_id)
            .options(selectinload(ActionTakenModel.taken_user).selectinload(UserModel.role))
            .order_by(desc(ActionTakenModel.created_at))
        )
        return list(result.scalars().all())

    async def get_monthly_trends(self, months: int) -> Dict[str, Any]:
        """Mendapatkan data tren bulanan untuk trouble tickets"""
        try:
            trends_data = []
            now = datetime.now()

            for i in range(months):
                month_date = now - timedelta(days=30 * i)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                if month_date.month == 12:
                    next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
                else:
                    next_month = month_date.replace(month=month_date.month + 1, day=1)

                monthly_stats = {}
                
                # Total
                total = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(and_(TroubleTicketModel.created_at >= month_start, TroubleTicketModel.created_at < next_month)))).scalar_one() or 0
                monthly_stats['total'] = total

                # Resolved
                resolved = (await self.db.execute(select(func.count(TroubleTicketModel.id)).where(and_(TroubleTicketModel.resolved_at >= month_start, TroubleTicketModel.resolved_at < next_month)))).scalar_one() or 0
                monthly_stats['resolved'] = resolved

                # Avg resolution
                avg_res = (await self.db.execute(select(func.avg(func.timestampdiff(text('HOUR'), TroubleTicketModel.created_at, TroubleTicketModel.resolved_at))).where(and_(TroubleTicketModel.resolved_at >= month_start, TroubleTicketModel.resolved_at < next_month, TroubleTicketModel.created_at.isnot(None))))).scalar_one() or 0
                monthly_stats['avg_resolution_hours'] = round(avg_res, 2)

                # By category
                cat_res = await self.db.execute(select(TroubleTicketModel.category, func.count(TroubleTicketModel.id).label('count')).where(and_(TroubleTicketModel.created_at >= month_start, TroubleTicketModel.created_at < next_month)).group_by(TroubleTicketModel.category))
                monthly_stats['by_category'] = {row.category.value: row.count for row in cat_res}

                # By priority
                pri_res = await self.db.execute(select(TroubleTicketModel.priority, func.count(TroubleTicketModel.id).label('count')).where(and_(TroubleTicketModel.created_at >= month_start, TroubleTicketModel.created_at < next_month)).group_by(TroubleTicketModel.priority))
                monthly_stats['by_priority'] = {row.priority.value: row.count for row in pri_res}

                trends_data.append({
                    'month': month_date.strftime('%Y-%m'),
                    'month_name': month_date.strftime('%B %Y'),
                    'statistics': monthly_stats
                })

            return {
                'trends': trends_data[::-1],
                'summary': {
                    'total_months': months,
                    'data_generated_at': now.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get monthly trends: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_category_performance(self, date_from: Optional[datetime], date_to: Optional[datetime]) -> Dict[str, Any]:
        """Mendapatkan performa ticket berdasarkan kategori"""
        try:
            query = select(
                TroubleTicketModel.category,
                func.count(TroubleTicketModel.id).label('total_tickets'),
                func.sum(TroubleTicketModel.total_downtime_minutes).label('total_downtime_minutes')
            )

            if date_from or date_to:
                df = []
                if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                query = query.where(and_(*df))
            
            query = query.group_by(TroubleTicketModel.category).order_by(desc('total_tickets'))
            category_performance = []
            results = await self.db.execute(query)

            for row in results:
                cat = row.category
                total = row.total_tickets
                total_dt = row.total_downtime_minutes or 0

                res_query = select(func.count(TroubleTicketModel.id)).where(and_(TroubleTicketModel.category == cat, TroubleTicketModel.status == TicketStatus.RESOLVED))
                if date_from or date_to:
                    df = []
                    if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                    if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                    res_query = res_query.where(and_(*df))
                
                resolved = (await self.db.execute(res_query)).scalar_one() or 0

                avg_res = 0.0
                if resolved > 0:
                    rt_query = select(TroubleTicketModel.created_at, TroubleTicketModel.resolved_at).where(and_(TroubleTicketModel.category == cat, TroubleTicketModel.status == TicketStatus.RESOLVED, TroubleTicketModel.resolved_at.isnot(None), TroubleTicketModel.created_at.isnot(None)))
                    if date_from or date_to:
                        df = []
                        if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                        if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                        rt_query = rt_query.where(and_(*df))
                    
                    rows = (await self.db.execute(rt_query)).all()
                    if rows:
                        t_time = sum((r.resolved_at - r.created_at).total_seconds() / 3600.0 for r in rows if r.created_at and r.resolved_at)
                        avg_res = round(t_time / len(rows), 2)

                category_performance.append({
                    'category': str(cat),
                    'category_display': str(cat).replace('_', ' ').title(),
                    'total_tickets': total,
                    'resolved_tickets': resolved,
                    'resolution_rate_percent': round((resolved / total * 100), 2) if total > 0 else 0,
                    'avg_resolution_hours': avg_res,
                    'avg_downtime_minutes': round(total_dt / resolved, 2) if resolved > 0 else 0,
                    'total_downtime_minutes': total_dt
                })

            return {
                'category_performance': category_performance,
                'filters_applied': {
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get category performance: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_performance(self, date_from: Optional[datetime], date_to: Optional[datetime]) -> Dict[str, Any]:
        """Mendapatkan performa ticket berdasarkan user/teknisi"""
        try:
            query = select(
                UserModel.id,
                UserModel.name,
                func.count(TroubleTicketModel.id).label('total_assigned')
            ).select_from(TroubleTicketModel).join(UserModel, TroubleTicketModel.assigned_to == UserModel.id)

            if date_from or date_to:
                df = []
                if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                query = query.where(and_(TroubleTicketModel.assigned_to.isnot(None), *df))
            else:
                query = query.where(TroubleTicketModel.assigned_to.isnot(None))

            query = query.group_by(UserModel.id, UserModel.name).order_by(desc('total_assigned'))
            results = await self.db.execute(query)
            user_perf = []

            for row in results:
                res_query = select(func.count(TroubleTicketModel.id)).where(and_(TroubleTicketModel.assigned_to == row.id, TroubleTicketModel.status == TicketStatus.RESOLVED))
                if date_from or date_to:
                    df = []
                    if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                    if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                    res_query = res_query.where(and_(*df))
                
                resolved = (await self.db.execute(res_query)).scalar_one() or 0

                avg_res = 0.0
                if resolved > 0:
                    rt_query = select(TroubleTicketModel.created_at, TroubleTicketModel.resolved_at).where(and_(TroubleTicketModel.assigned_to == row.id, TroubleTicketModel.status == TicketStatus.RESOLVED, TroubleTicketModel.resolved_at.isnot(None), TroubleTicketModel.created_at.isnot(None)))
                    if date_from or date_to:
                        df = []
                        if date_from: df.append(TroubleTicketModel.created_at >= date_from)
                        if date_to: df.append(TroubleTicketModel.created_at <= date_to)
                        rt_query = rt_query.where(and_(*df))
                    
                    rows = (await self.db.execute(rt_query)).all()
                    if rows:
                        t_time = sum((r.resolved_at - r.created_at).total_seconds() / 3600.0 for r in rows if r.created_at and r.resolved_at)
                        avg_res = round(t_time / len(rows), 2)

                user_perf.append({
                    'user_id': row.id,
                    'user_name': row.name,
                    'total_assigned': row.total_assigned,
                    'resolved_tickets': resolved,
                    'resolution_rate_percent': round((resolved / row.total_assigned * 100), 2) if row.total_assigned > 0 else 0,
                    'avg_resolution_hours': avg_res
                })

            return {
                'user_performance': user_perf,
                'filters_applied': {
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to get user performance: {e}")
            raise HTTPException(status_code=500, detail=str(e))

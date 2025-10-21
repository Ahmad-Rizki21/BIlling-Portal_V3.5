from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    BackgroundTasks,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.sql import text
from typing import List, Optional
from datetime import datetime
import logging

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
from ..database import get_db
from ..auth import get_current_active_user
from ..websocket_manager import manager
from ..schemas.trouble_ticket import (
    TroubleTicket,
    TroubleTicketCreate,
    TroubleTicketUpdate,
    TroubleTicketWithRelations,
    TicketStatusUpdate,
    DowntimeUpdate,
    TicketHistory,
    ActionTaken,
    TicketFilter,
    PaginatedTroubleTicketResponse,
    PaginationInfo,
    TicketStatistics,
    TicketAssignment,
    TicketStatusEnum,
    TicketPriorityEnum,
    TicketCategoryEnum,
)

router = APIRouter(
    prefix="/trouble-tickets",
    tags=["Trouble Tickets"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


# Helper function untuk generate ticket number
async def generate_ticket_number(db: AsyncSession) -> str:
    """Generate unique ticket number dengan format TFTTH-XXXXX (sequential)"""
    from sqlalchemy import select
    from ..models.trouble_ticket import TroubleTicket as TroubleTicketModel

    # Format tetap TFTTH-XXXXX
    prefix = "TFTTH"

    # Get ticket number terakhir dengan format TFTTH-XXXXX
    result = await db.execute(
        select(TroubleTicketModel.ticket_number)
        .where(TroubleTicketModel.ticket_number.like(f"{prefix}-%"))
        .order_by(desc(TroubleTicketModel.ticket_number))
        .limit(1)
    )
    last_ticket = result.scalar_one_or_none()

    if last_ticket:
        # Extract angka dari format TFTTH-XXXXX
        try:
            last_num = int(last_ticket.split("-")[1])
            next_num = last_num + 1
        except (IndexError, ValueError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}-{next_num:04d}"


# Helper function untuk validasi pelanggan
async def validate_pelanggan(pelanggan_id: int, db: AsyncSession) -> PelangganModel:
    """Validasi apakah pelanggan ada"""
    pelanggan = await db.get(PelangganModel, pelanggan_id)
    if not pelanggan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pelanggan dengan ID {pelanggan_id} tidak ditemukan"
        )
    return pelanggan


# Helper function untuk validasi data teknis
async def validate_data_teknis(data_teknis_id: Optional[int], db: AsyncSession) -> Optional[DataTeknisModel]:
    """Validasi apakah data teknis ada (opsional)"""
    if data_teknis_id is None:
        return None

    data_teknis = await db.get(DataTeknisModel, data_teknis_id)
    if not data_teknis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data Teknis dengan ID {data_teknis_id} tidak ditemukan"
        )
    return data_teknis


# Helper function untuk validasi user
async def validate_user(user_id: Optional[int], db: AsyncSession) -> Optional[UserModel]:
    """Validasi apakah user ada (opsional)"""
    if user_id is None:
        return None

    user = await db.get(UserModel, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User dengan ID {user_id} tidak ditemukan"
        )
    return user


# Helper function untuk menambahkan history perubahan status
async def add_ticket_history(
    db: AsyncSession,
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
    db.add(history)
    await db.flush()


# Helper function untuk menambahkan action taken
async def add_action_taken(
    db: AsyncSession,
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
        evidence=evidence,  # Evidence as JSON string array
        notes=notes,
        taken_by=taken_by
    )
    db.add(action_taken)
    await db.flush()


@router.post("/", response_model=TroubleTicket, status_code=status.HTTP_201_CREATED)
async def create_trouble_ticket(
    ticket: TroubleTicketCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Membuat Trouble Ticket baru dengan validasi lengkap.
    """
    try:
        # Validasi pelanggan
        pelanggan = await validate_pelanggan(ticket.pelanggan_id, db)

        # Validasi data teknis (opsional)
        data_teknis = await validate_data_teknis(ticket.data_teknis_id, db)

        # Validasi assigned user (opsional)
        assigned_user = await validate_user(ticket.assigned_to, db)

        # Generate ticket number unik dengan sequence
        ticket_number = await generate_ticket_number(db)

        # Cek apakah ticket number sudah ada (backup safety check)
        existing_ticket = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.ticket_number == ticket_number)
        )
        if existing_ticket.scalar_one_or_none():
            # Regenerate jika conflict (should not happen with sequence)
            ticket_number = await generate_ticket_number(db)

        # Konversi enum dari schema ke model
        # Untuk pembuatan baru, status default adalah OPEN (tidak ada di schema TroubleTicketCreate)
        status_enum = TicketStatus.OPEN
        priority_enum = TicketPriority(ticket.priority.value)
        category_enum = TicketCategory(ticket.category.value)

        # Create ticket
        db_ticket = TroubleTicketModel(
            ticket_number=ticket_number,
            pelanggan_id=ticket.pelanggan_id,
            data_teknis_id=ticket.data_teknis_id,
            title=ticket.title,
            description=ticket.description,
            category=category_enum,
            priority=priority_enum,
            status=status_enum,
            assigned_to=ticket.assigned_to,
            evidence=ticket.evidence,  # Add evidence from form
            created_at=datetime.now(),
            # Set downtime start saat tiket dibuat
            downtime_start=datetime.now()
        )

        db.add(db_ticket)
        await db.flush()

        # Log payload yang diterima untuk debugging
        logger.info(f"📤 Create ticket payload: {ticket}")

        # Add initial history
        await add_ticket_history(
            db, db_ticket.id, None, status_enum, current_user.id, "Ticket created"
        )

        # Commit transaction
        await db.commit()

        # Add action taken if evidence was provided during ticket creation
        if ticket.evidence:
            try:
                await add_action_taken(
                    db,
                    ticket_id=db_ticket.id,
                    action_description="Ticket created with evidence",
                    summary_problem="Initial evidence provided during ticket creation",
                    summary_action="Evidence uploaded with initial ticket",
                    evidence=ticket.evidence,  # Evidence JSON string
                    taken_by=current_user.id
                )
                await db.commit()
                logger.info(f"✅ Initial action taken added for ticket {ticket_number} with evidence")
            except Exception as e:
                logger.error(f"❌ Failed to add initial action taken for ticket {ticket_number}: {e}")
                # Don't raise exception, just log the error as the ticket was created successfully

        # Send notification ke background (non-blocking)
        notification_data = {
            "type": "new_trouble_ticket",
            "message": f"Ticket baru dibuat: {ticket_number} - {ticket.title}",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "ticket_id": db_ticket.id,
                "ticket_number": ticket_number,
                "pelanggan_id": ticket.pelanggan_id,
                "pelanggan_nama": pelanggan.nama,
                "priority": ticket.priority.value,
                "category": ticket.category.value,
                "created_by": current_user.name
            }
        }

        background_tasks.add_task(
            manager.broadcast_to_roles,
            notification_data,
            ["NOC", "CS", "Admin"]
        )

        logger.info(f"✅ Trouble Ticket created: {ticket_number} by {current_user.name}")

        # Load relasi lengkap untuk response
        result = await db.execute(
            select(TroubleTicketModel)
            .where(TroubleTicketModel.id == db_ticket.id)
            .options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )
        )
        ticket_with_relations = result.scalar_one()
        return ticket_with_relations

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to create trouble ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat trouble ticket: {str(e)}"
        )


@router.get("/", response_model=PaginatedTroubleTicketResponse)
async def get_trouble_tickets(
    skip: int = Query(0, ge=0, description="Jumlah items untuk dilewati"),
    limit: int = Query(15, ge=1, le=100, description="Jumlah items per halaman"),
    status: Optional[TicketStatusEnum] = Query(None, description="Filter berdasarkan status"),
    priority: Optional[TicketPriorityEnum] = Query(None, description="Filter berdasarkan prioritas"),
    category: Optional[TicketCategoryEnum] = Query(None, description="Filter berdasarkan kategori"),
    assigned_to: Optional[int] = Query(None, gt=0, description="Filter berdasarkan user yang ditugaskan"),
    pelanggan_id: Optional[int] = Query(None, gt=0, description="Filter berdasarkan pelanggan"),
    id_brand: Optional[str] = Query(None, max_length=20, description="Filter berdasarkan ID Brand (ajn-01, ajn-02, ajn-03)"),
    brand: Optional[str] = Query(None, max_length=50, description="Filter berdasarkan nama brand (JAKINET, JELANTIK, JELANTIK NAGRAK)"),
    date_from: Optional[datetime] = Query(None, description="Filter tanggal dari"),
    date_to: Optional[datetime] = Query(None, description="Filter tanggal sampai"),
    search: Optional[str] = Query(None, max_length=100, description="Pencarian judul/deskripsi"),
    include_relations: bool = Query(False, description="Include relasi pelanggan dan data teknis"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan daftar trouble tickets dengan pagination dan filter.
    """
    try:
        # Base query
        query = select(TroubleTicketModel)
        count_query = select(func.count(TroubleTicketModel.id))

        # Include relations jika diminta
        if include_relations:
            query = query.options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )

        # Apply filters
        filters = []

        if status:
            filters.append(TroubleTicketModel.status == TicketStatus(status.value))

        if priority:
            filters.append(TroubleTicketModel.priority == TicketPriority(priority.value))

        if category:
            filters.append(TroubleTicketModel.category == TicketCategory(category.value))

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

        # Handle brand-based filtering
        if id_brand or brand:
            # Join with pelanggan table untuk brand filtering
            from sqlalchemy.orm import aliased

            # Add join for brand filtering to both queries
            query = query.join(PelangganModel, TroubleTicketModel.pelanggan_id == PelangganModel.id)
            count_query = count_query.join(PelangganModel, TroubleTicketModel.pelanggan_id == PelangganModel.id)

            if id_brand:
                filters.append(PelangganModel.id_brand == id_brand)

            if brand:
                # Join with harga_layanan table untuk brand name filtering
                query = query.join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand)
                count_query = count_query.join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand)
                filters.append(HargaLayananModel.brand.ilike(f"%{brand}%"))

        # Apply filters to queries
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total_items = total_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(desc(TroubleTicketModel.created_at)).offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        tickets = result.scalars().unique().all()

        # Calculate pagination info
        total_pages = (total_items + limit - 1) // limit
        current_page = (skip // limit) + 1 if limit > 0 else 1

        pagination_info = PaginationInfo(
            totalItems=total_items,
            currentPage=current_page,
            itemsPerPage=limit,
            totalPages=total_pages,
            hasNext=current_page < total_pages,
            hasPrevious=current_page > 1,
        )

        response = PaginatedTroubleTicketResponse(
            data=list(tickets),
            pagination=pagination_info,
            meta={
                "filters_applied": {
                    "status": status.value if status else None,
                    "priority": priority.value if priority else None,
                    "category": category.value if category else None,
                    "assigned_to": assigned_to,
                    "pelanggan_id": pelanggan_id,
                    "id_brand": id_brand,
                    "brand": brand,
                    "search": search,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "include_relations": include_relations,
                }
            },
        )

        logger.info(f"✅ Retrieved {len(tickets)} trouble tickets from total {total_items}")
        return response

    except Exception as e:
        logger.error(f"❌ Failed to get trouble tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil trouble tickets: {str(e)}"
        )


@router.get("/{ticket_id}", response_model=TroubleTicketWithRelations)
async def get_trouble_ticket_by_id(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan detail trouble ticket berdasarkan ID dengan informasi lengkap pelanggan dan brand.
    """
    try:
        query = select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id).options(
            selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            selectinload(TroubleTicketModel.data_teknis),
            selectinload(TroubleTicketModel.assigned_user)
        )

        result = await db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        return ticket

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get trouble ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil trouble ticket: {str(e)}"
        )


@router.patch("/{ticket_id}", response_model=TroubleTicket)
async def update_trouble_ticket(
    ticket_id: int,
    ticket_update: TroubleTicketUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update trouble ticket (partial update).
    """
    try:
        # Get existing ticket
        result = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Track status change untuk history
        old_status = ticket.status
        status_changed = False

        # Update data
        update_data = ticket_update.model_dump(exclude_unset=True)

        # Handle enum conversions
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

        # Apply other updates
        for key, value in update_data.items():
            setattr(ticket, key, value)

        # Update timestamp
        ticket.updated_at = datetime.now()

        # Add history jika status berubah
        if status_changed:
            await add_ticket_history(
                db, ticket_id, old_status, ticket.status, current_user.id
            )

        # Add action taken if evidence was updated
        if hasattr(ticket_update, 'evidence') and ticket_update.evidence is not None:
            old_evidence = getattr(ticket, 'evidence', None)
            # Compare evidence, treating both null and empty string as equivalent
            old_evidence_clean = old_evidence if old_evidence else None
            new_evidence_clean = ticket_update.evidence if ticket_update.evidence else None
            if new_evidence_clean != old_evidence_clean:
                await add_action_taken(
                    db,
                    ticket_id=ticket_id,
                    action_description="Evidence updated",
                    summary_problem="Ticket evidence was updated",
                    summary_action="Updated ticket evidence",
                    evidence=ticket_update.evidence,  # Updated evidence JSON
                    taken_by=current_user.id
                )

        # Commit changes
        await db.commit()

        # Send notification untuk status change
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

            background_tasks.add_task(
                manager.broadcast_to_roles,
                notification_data,
                ["NOC", "CS", "Admin"]
            )

        logger.info(f"✅ Trouble Ticket {ticket_id} updated by {current_user.name}")

        # Load relasi lengkap untuk response
        result = await db.execute(
            select(TroubleTicketModel)
            .where(TroubleTicketModel.id == ticket_id)
            .options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )
        )
        ticket_with_relations = result.scalar_one()
        return ticket_with_relations

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to update trouble ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal update trouble ticket: {str(e)}"
        )


@router.post("/{ticket_id}/status", response_model=TroubleTicket)
async def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update status trouble ticket dengan history tracking.
    """
    try:
        # Get existing ticket
        result = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        old_status = ticket.status
        new_status = TicketStatus(status_update.status.value)

        # Jika status sama, tidak perlu update
        if old_status == new_status:
            return ticket

        # Update status
        ticket.status = new_status
        ticket.updated_at = datetime.now()

        # Auto-set resolved_at jika status berubah ke RESOLVED atau CLOSED
        if new_status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            ticket.resolved_at = datetime.now()
            # Update downtime end jika belum ada
            if ticket.downtime_start and not ticket.downtime_end:
                ticket.downtime_end = datetime.now()
                ticket.update_downtime()
        
        # Auto-start downtime tracking jika status berubah ke status yang menunjukkan permasalahan aktif
        elif new_status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS] and old_status not in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
            # Jika sebelumnya permasalahan tidak aktif, catat waktu mulai downtime baru
            if not ticket.downtime_start or (ticket.downtime_end and ticket.downtime_start < ticket.downtime_end):
                # Jika sebelumnya tiket ditutup dan sekarang dibuka kembali, mulai downtime baru
                ticket.downtime_start = datetime.now()
                ticket.downtime_end = None  # Reset end time jika sebelumnya sudah ditutup
                ticket.update_downtime()

        # Add status history
        await add_ticket_history(
            db, ticket_id, old_status, new_status, current_user.id, status_update.notes
        )
        
        # Add action taken if provided
        if status_update.action_description or status_update.summary_problem or status_update.summary_action:
            # Convert evidence array to JSON string if it's an array
            evidence_str = status_update.evidence
            if isinstance(status_update.evidence, list):
                import json
                evidence_str = json.dumps(status_update.evidence)

            await add_action_taken(
                db, ticket_id,
                status_update.action_description,
                status_update.summary_problem,
                status_update.summary_action,
                evidence_str,  # Pass JSON string
                status_update.notes,
                current_user.id
            )

        # Commit
        await db.commit()

        # Send notification
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

        background_tasks.add_task(
            manager.broadcast_to_roles,
            notification_data,
            ["NOC", "CS", "Admin"]
        )

        logger.info(f"✅ Trouble Ticket {ticket_id} status updated to {new_status.value} by {current_user.name}")

        # Load relasi lengkap untuk response
        result = await db.execute(
            select(TroubleTicketModel)
            .where(TroubleTicketModel.id == ticket_id)
            .options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )
        )
        ticket_with_relations = result.scalar_one()
        return ticket_with_relations

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to update ticket status {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal update status ticket: {str(e)}"
        )


@router.post("/{ticket_id}/downtime", response_model=TroubleTicket)
async def update_ticket_downtime(
    ticket_id: int,
    downtime_update: DowntimeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update downtime tracking untuk ticket.
    """
    try:
        # Get existing ticket
        result = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Update downtime
        if downtime_update.downtime_start is not None:
            ticket.downtime_start = downtime_update.downtime_start

        if downtime_update.downtime_end is not None:
            ticket.downtime_end = downtime_update.downtime_end

        # Auto-calculate total downtime
        ticket.update_downtime()
        ticket.updated_at = datetime.now()

        # Commit
        await db.commit()

        logger.info(f"✅ Trouble Ticket {ticket_id} downtime updated by {current_user.name}")

        # Load relasi lengkap untuk response
        result = await db.execute(
            select(TroubleTicketModel)
            .where(TroubleTicketModel.id == ticket_id)
            .options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )
        )
        ticket_with_relations = result.scalar_one()
        return ticket_with_relations

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to update ticket downtime {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal update downtime ticket: {str(e)}"
        )


@router.post("/{ticket_id}/assign", response_model=TroubleTicket)
async def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignment,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menugaskan ticket ke user tertentu.
    """
    try:
        # Get existing ticket
        result = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Validate assigned user
        assigned_user = await validate_user(assignment.assigned_to, db)

        old_assigned = ticket.assigned_to
        ticket.assigned_to = assignment.assigned_to
        ticket.updated_at = datetime.now()

        # Auto-update status ke IN_PROGRESS jika status masih OPEN
        if ticket.status == TicketStatus.OPEN:
            old_status = ticket.status
            new_status = TicketStatus.IN_PROGRESS
            ticket.status = new_status
            await add_ticket_history(
                db, ticket_id, old_status, new_status, current_user.id,
                f"Auto-assigned to {assigned_user.name}. {assignment.notes or ''}"
            )
            
            # Update downtime tracking jika status berubah ke IN_PROGRESS dari OPEN
            if old_status == TicketStatus.OPEN and new_status == TicketStatus.IN_PROGRESS:
                # Jika sebelumnya permasalahan tidak aktif, catat waktu mulai downtime baru
                if not ticket.downtime_start or (ticket.downtime_end and ticket.downtime_start < ticket.downtime_end):
                    # Jika sebelumnya tiket ditutup dan sekarang dibuka kembali, mulai downtime baru
                    ticket.downtime_start = datetime.now()
                    ticket.downtime_end = None  # Reset end time jika sebelumnya sudah ditutup
                    ticket.update_downtime()

        # Commit
        await db.commit()

        # Send notification ke assigned user
        notification_data = {
            "type": "ticket_assigned",
            "message": f"Ticket {ticket.ticket_number} ditugaskan kepada Anda",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "ticket_id": ticket.id,
                "ticket_number": ticket.ticket_number,
                "title": ticket.title,
                "assigned_by": current_user.name,
                "notes": assignment.notes
            }
        }

        background_tasks.add_task(
            manager.send_to_user,
            notification_data,
            assignment.assigned_to
        )

        logger.info(f"✅ Trouble Ticket {ticket_id} assigned to user {assignment.assigned_to} by {current_user.name}")

        # Load relasi lengkap untuk response
        result = await db.execute(
            select(TroubleTicketModel)
            .where(TroubleTicketModel.id == ticket_id)
            .options(
                selectinload(TroubleTicketModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                selectinload(TroubleTicketModel.data_teknis),
                selectinload(TroubleTicketModel.assigned_user)
            )
        )
        ticket_with_relations = result.scalar_one()
        return ticket_with_relations

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to assign ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menugaskan ticket: {str(e)}"
        )


@router.post("/{ticket_id}/action", response_model=ActionTaken)
async def add_ticket_action(
    ticket_id: int,
    action_data: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menambahkan action history tanpa mengganti status ticket.
    """
    try:
        # Validate ticket exists
        ticket = await db.get(TroubleTicketModel, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Validate that at least one action field is provided
        if not action_data.action_description and not action_data.summary_problem and not action_data.summary_action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of these fields is required: action_description, summary_problem, or summary_action"
            )

        # Add action taken record
        action_taken = ActionTakenModel(
            ticket_id=ticket_id,
            action_description=action_data.action_description,
            summary_problem=action_data.summary_problem,
            summary_action=action_data.summary_action,
            evidence=action_data.evidence,
            notes=action_data.notes,
            taken_by=current_user.id
        )
        
        db.add(action_taken)
        await db.flush()  # To get the ID
        
        # Update evidence in main ticket if provided
        if action_data.evidence:
            ticket.evidence = action_data.evidence
            
        await db.commit()
        await db.refresh(action_taken)  # Refresh to get the full object with relationships

        # Now load the relationships for the response
        result = await db.execute(
            select(ActionTakenModel)
            .where(ActionTakenModel.id == action_taken.id)
            .options(selectinload(ActionTakenModel.taken_user))
        )
        
        full_action_taken = result.scalar_one()
        return full_action_taken

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to add ticket action {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menambahkan action ticket: {str(e)}"
        )


@router.get("/{ticket_id}/history", response_model=List[TicketHistory])
async def get_ticket_history(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan history perubahan status ticket.
    """
    try:
        # Validate ticket exists
        ticket = await db.get(TroubleTicketModel, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Get history with user relation
        result = await db.execute(
            select(TicketHistoryModel)
            .where(TicketHistoryModel.ticket_id == ticket_id)
            .options(selectinload(TicketHistoryModel.changed_user))
            .order_by(desc(TicketHistoryModel.created_at))
        )

        history = result.scalars().all()
        return list(history)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get ticket history {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil history ticket: {str(e)}"
        )


@router.get("/{ticket_id}/actions", response_model=List[ActionTaken])
async def get_ticket_actions(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan history action taken untuk ticket.
    """
    try:
        # Validate ticket exists
        ticket = await db.get(TroubleTicketModel, ticket_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Get action taken records with user relation
        result = await db.execute(
            select(ActionTakenModel)
            .where(ActionTakenModel.ticket_id == ticket_id)
            .options(selectinload(ActionTakenModel.taken_user))
            .order_by(desc(ActionTakenModel.created_at))
        )

        actions = result.scalars().all()
        return list(actions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get ticket actions {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil action taken ticket: {str(e)}"
        )


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trouble_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menghapus trouble ticket (hanya untuk status resolved/closed).
    """
    try:
        # Get existing ticket
        result = await db.execute(
            select(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trouble Ticket dengan ID {ticket_id} tidak ditemukan"
            )

        # Validate ticket status - only allow deletion for resolved/closed tickets
        if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hanya ticket dengan status Resolved/Closed/Cancelled yang dapat dihapus. Status saat ini: {ticket.status.value}"
            )

        # Delete related records first (due to foreign key constraints)
        # Delete ticket history
        await db.execute(
            select(TicketHistoryModel).where(TicketHistoryModel.ticket_id == ticket_id)
        )
        # Actually delete the history records
        from sqlalchemy import delete
        await db.execute(delete(TicketHistoryModel).where(TicketHistoryModel.ticket_id == ticket_id))

        # Delete action taken records
        await db.execute(delete(ActionTakenModel).where(ActionTakenModel.ticket_id == ticket_id))

        # Delete the ticket
        await db.execute(delete(TroubleTicketModel).where(TroubleTicketModel.id == ticket_id))

        # Commit
        await db.commit()

        logger.info(f"✅ Trouble Ticket {ticket_id} ({ticket.ticket_number}) deleted by {current_user.name}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to delete trouble ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menghapus trouble ticket: {str(e)}"
        )


@router.get("/statistics/dashboard", response_model=TicketStatistics)
async def get_ticket_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan statistik trouble tickets untuk dashboard.
    """
    try:
        # Base counts
        total_result = await db.execute(select(func.count(TroubleTicketModel.id)))
        total_tickets = total_result.scalar_one()

        # Status counts
        open_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.status == TicketStatus.OPEN)
        )
        open_tickets = open_result.scalar_one()

        in_progress_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.status == TicketStatus.IN_PROGRESS)
        )
        in_progress_tickets = in_progress_result.scalar_one()

        resolved_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.status == TicketStatus.RESOLVED)
        )
        resolved_tickets = resolved_result.scalar_one()

        closed_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.status == TicketStatus.CLOSED)
        )
        closed_tickets = closed_result.scalar_one()

        # Priority counts
        high_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.priority == TicketPriority.HIGH)
        )
        high_priority_tickets = high_result.scalar_one()

        critical_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.priority == TicketPriority.CRITICAL)
        )
        critical_priority_tickets = critical_result.scalar_one()

        # This month tickets
        from datetime import datetime, timedelta
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        this_month_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(TroubleTicketModel.created_at >= month_start)
        )
        tickets_this_month = this_month_result.scalar_one()

        # Unresolved over 24h
        yesterday = now - timedelta(hours=24)
        unresolved_24h_result = await db.execute(
            select(func.count(TroubleTicketModel.id))
            .where(
                and_(
                    TroubleTicketModel.created_at <= yesterday,
                    TroubleTicketModel.status.in_([
                        TicketStatus.OPEN,
                        TicketStatus.IN_PROGRESS,
                        TicketStatus.PENDING_CUSTOMER,
                        TicketStatus.PENDING_VENDOR
                    ])
                )
            )
        )
        unresolved_over_24h = unresolved_24h_result.scalar_one()

        # Average resolution time (calculate in hours)
        avg_resolution_result = await db.execute(
            select(
                func.avg(
                    func.timestampdiff(text('HOUR'), TroubleTicketModel.created_at, TroubleTicketModel.resolved_at)
                )
            )
            .where(
                and_(
                    TroubleTicketModel.resolved_at.isnot(None),
                    TroubleTicketModel.created_at.isnot(None)
                )
            )
        )
        avg_resolution_time_hours = avg_resolution_result.scalar_one()

        statistics = TicketStatistics(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            high_priority_tickets=high_priority_tickets,
            critical_priority_tickets=critical_priority_tickets,
            avg_resolution_time_hours=round(avg_resolution_time_hours, 2) if avg_resolution_time_hours else None,
            tickets_this_month=tickets_this_month,
            unresolved_over_24h=unresolved_over_24h,
        )

        return statistics

    except Exception as e:
        logger.error(f"❌ Failed to get ticket statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil statistik ticket: {str(e)}"
        )


# Additional endpoints for comprehensive reporting
@router.get("/reports/monthly-trends", response_model=dict)
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=24, description="Number of months to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan data tren bulanan untuk trouble tickets.
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import extract

        trends_data = []
        now = datetime.now()

        for i in range(months):
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get next month for range
            if month_date.month == 12:
                next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)

            # Monthly statistics
            monthly_stats = {}

            # Total tickets in month
            total_result = await db.execute(
                select(func.count(TroubleTicketModel.id))
                .where(
                    and_(
                        TroubleTicketModel.created_at >= month_start,
                        TroubleTicketModel.created_at < next_month
                    )
                )
            )
            monthly_stats['total'] = total_result.scalar_one() or 0

            # Resolved tickets in month
            resolved_result = await db.execute(
                select(func.count(TroubleTicketModel.id))
                .where(
                    and_(
                        TroubleTicketModel.resolved_at >= month_start,
                        TroubleTicketModel.resolved_at < next_month
                    )
                )
            )
            monthly_stats['resolved'] = resolved_result.scalar_one() or 0

            # Average resolution time for month
            avg_resolution_result = await db.execute(
                select(
                    func.avg(
                        func.timestampdiff(text('HOUR'), TroubleTicketModel.created_at, TroubleTicketModel.resolved_at)
                    )
                )
                .where(
                    and_(
                        TroubleTicketModel.resolved_at >= month_start,
                        TroubleTicketModel.resolved_at < next_month,
                        TroubleTicketModel.created_at.isnot(None)
                    )
                )
            )
            monthly_stats['avg_resolution_hours'] = round(avg_resolution_result.scalar_one() or 0, 2)

            # By category
            category_results = await db.execute(
                select(
                    TroubleTicketModel.category,
                    func.count(TroubleTicketModel.id).label('count')
                )
                .where(
                    and_(
                        TroubleTicketModel.created_at >= month_start,
                        TroubleTicketModel.created_at < next_month
                    )
                )
                .group_by(TroubleTicketModel.category)
            )

            monthly_stats['by_category'] = {}
            for cat_result in category_results:
                monthly_stats['by_category'][cat_result.category.value] = cat_result.count

            # By priority
            priority_results = await db.execute(
                select(
                    TroubleTicketModel.priority,
                    func.count(TroubleTicketModel.id).label('count')
                )
                .where(
                    and_(
                        TroubleTicketModel.created_at >= month_start,
                        TroubleTicketModel.created_at < next_month
                    )
                )
                .group_by(TroubleTicketModel.priority)
            )

            monthly_stats['by_priority'] = {}
            for pri_result in priority_results:
                monthly_stats['by_priority'][pri_result.priority.value] = pri_result.count

            trends_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': month_date.strftime('%B %Y'),
                'statistics': monthly_stats
            })

        return {
            'trends': trends_data[::-1],  # Reverse to show oldest to newest
            'summary': {
                'total_months': months,
                'data_generated_at': now.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"❌ Failed to get monthly trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data tren bulanan: {str(e)}"
        )


@router.get("/reports/category-performance", response_model=dict)
async def get_category_performance(
    date_from: Optional[datetime] = Query(None, description="Filter tanggal dari"),
    date_to: Optional[datetime] = Query(None, description="Filter tanggal sampai"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan performa ticket berdasarkan kategori.
    """
    try:
        # Base query
        query = select(
            TroubleTicketModel.category,
            func.count(TroubleTicketModel.id).label('total_tickets'),
            # Calculate average resolution time by getting individual tickets and calculating in Python
            func.sum(TroubleTicketModel.total_downtime_minutes).label('total_downtime_minutes')
        )

        # Apply date filters
        if date_from or date_to:
            date_filters = []
            if date_from:
                date_filters.append(TroubleTicketModel.created_at >= date_from)
            if date_to:
                date_filters.append(TroubleTicketModel.created_at <= date_to)
            query = query.where(and_(*date_filters))
        
        # Group and order
        query = query.group_by(TroubleTicketModel.category).order_by(desc('total_tickets'))

        category_performance = []

        # Get performance by category
        category_results = await db.execute(query)

        for cat_result in category_results:
            category = cat_result.category
            total = cat_result.total_tickets
            total_downtime = cat_result.total_downtime_minutes or 0

            # Get resolved tickets count for this category
            resolved_query = select(func.count(TroubleTicketModel.id)).where(
                and_(
                    TroubleTicketModel.category == category,
                    TroubleTicketModel.status == TicketStatus.RESOLVED
                )
            )

            # Apply date filters if present
            if date_from or date_to:
                date_filters = []
                if date_from:
                    date_filters.append(TroubleTicketModel.created_at >= date_from)
                if date_to:
                    date_filters.append(TroubleTicketModel.created_at <= date_to)
                resolved_query = resolved_query.where(and_(*date_filters))

            resolved_result = await db.execute(resolved_query)
            resolved = resolved_result.scalar_one() or 0

            # Calculate average resolution time by getting individual resolved tickets
            avg_resolution = 0.0
            if resolved > 0:  # Only calculate if there are resolved tickets
                # Get resolved tickets for this category to calculate average resolution time
                resolution_tickets_query = select(
                    TroubleTicketModel.created_at,
                    TroubleTicketModel.resolved_at
                ).where(
                    and_(
                        TroubleTicketModel.category == category,
                        TroubleTicketModel.status == TicketStatus.RESOLVED,
                        TroubleTicketModel.resolved_at.isnot(None),
                        TroubleTicketModel.created_at.isnot(None)
                    )
                )
                
                # Apply date filters if present
                if date_from or date_to:
                    date_filters = []
                    if date_from:
                        date_filters.append(TroubleTicketModel.created_at >= date_from)
                    if date_to:
                        date_filters.append(TroubleTicketModel.created_at <= date_to)
                    resolution_tickets_query = resolution_tickets_query.where(and_(*date_filters))
                
                resolution_tickets_result = await db.execute(resolution_tickets_query)
                resolution_tickets = resolution_tickets_result.all()
                
                if resolution_tickets:
                    total_resolution_time = 0
                    valid_tickets = 0
                    for ticket in resolution_tickets:
                        if ticket.created_at and ticket.resolved_at:
                            resolution_time_hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600.0
                            total_resolution_time += resolution_time_hours
                            valid_tickets += 1
                    
                    avg_resolution = round(total_resolution_time / valid_tickets, 2) if valid_tickets > 0 else 0

            resolution_rate = round((resolved / total * 100), 2) if total > 0 else 0
            avg_downtime = round(total_downtime / resolved, 2) if resolved > 0 else 0

            category_performance.append({
                'category': str(category),
                'category_display': str(category).replace('_', ' ').title(),
                'total_tickets': total,
                'resolved_tickets': resolved,
                'resolution_rate_percent': resolution_rate,
                'avg_resolution_hours': avg_resolution,
                'avg_downtime_minutes': avg_downtime,
                'total_downtime_minutes': total_downtime
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data performa kategori: {str(e)}"
        )


@router.get("/reports/user-performance", response_model=dict)
async def get_user_performance(
    date_from: Optional[datetime] = Query(None, description="Filter tanggal dari"),
    date_to: Optional[datetime] = Query(None, description="Filter tanggal sampai"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan performa ticket berdasarkan user/teknisi.
    """
    try:
        # Base query
        query = select(
            UserModel.id,
            UserModel.name,
            func.count(TroubleTicketModel.id).label('total_assigned'),
            # Calculate average resolution time by getting individual tickets and calculating in Python
            func.min(TroubleTicketModel.created_at).label('first_ticket'),
            func.max(TroubleTicketModel.created_at).label('last_ticket')
        ).select_from(TroubleTicketModel).join(UserModel, TroubleTicketModel.assigned_to == UserModel.id)

        # Apply date filters
        if date_from or date_to:
            date_filters = []
            if date_from:
                date_filters.append(TroubleTicketModel.created_at >= date_from)
            if date_to:
                date_filters.append(TroubleTicketModel.created_at <= date_to)
            query = query.where(and_(
                TroubleTicketModel.assigned_to.isnot(None),
                *date_filters
            ))
        else:
            query = query.where(TroubleTicketModel.assigned_to.isnot(None))

        # Group and order
        query = query.group_by(UserModel.id, UserModel.name).order_by(desc('total_assigned'))

        user_performance = []

        # Get performance by assigned user
        user_results = await db.execute(query)

        for user_result in user_results:
            total_assigned = user_result.total_assigned
            first_ticket = user_result.first_ticket
            last_ticket = user_result.last_ticket

            # Get resolved tickets count for this user
            resolved_query = select(func.count(TroubleTicketModel.id)).where(
                and_(
                    TroubleTicketModel.assigned_to == user_result.id,
                    TroubleTicketModel.status == TicketStatus.RESOLVED
                )
            )

            # Apply date filters if present
            if date_from or date_to:
                date_filters = []
                if date_from:
                    date_filters.append(TroubleTicketModel.created_at >= date_from)
                if date_to:
                    date_filters.append(TroubleTicketModel.created_at <= date_to)
                resolved_query = resolved_query.where(and_(*date_filters))

            resolved_result = await db.execute(resolved_query)
            resolved = resolved_result.scalar_one() or 0

            # Calculate average resolution time by getting individual resolved tickets
            avg_resolution = 0.0
            if resolved > 0:  # Only calculate if there are resolved tickets
                # Get resolved tickets for this user to calculate average resolution time
                resolution_tickets_query = select(
                    TroubleTicketModel.created_at,
                    TroubleTicketModel.resolved_at
                ).where(
                    and_(
                        TroubleTicketModel.assigned_to == user_result.id,
                        TroubleTicketModel.status == TicketStatus.RESOLVED,
                        TroubleTicketModel.resolved_at.isnot(None),
                        TroubleTicketModel.created_at.isnot(None)
                    )
                )
                
                # Apply date filters if present
                if date_from or date_to:
                    date_filters = []
                    if date_from:
                        date_filters.append(TroubleTicketModel.created_at >= date_from)
                    if date_to:
                        date_filters.append(TroubleTicketModel.created_at <= date_to)
                    resolution_tickets_query = resolution_tickets_query.where(and_(*date_filters))
                
                resolution_tickets_result = await db.execute(resolution_tickets_query)
                resolution_tickets = resolution_tickets_result.all()
                
                if resolution_tickets:
                    total_resolution_time = 0
                    valid_tickets = 0
                    for ticket in resolution_tickets:
                        if ticket.created_at and ticket.resolved_at:
                            resolution_time_hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600.0
                            total_resolution_time += resolution_time_hours
                            valid_tickets += 1
                    
                    avg_resolution = round(total_resolution_time / valid_tickets, 2) if valid_tickets > 0 else 0

            resolution_rate = round((resolved / total_assigned * 100), 2) if total_assigned > 0 else 0

            user_performance.append({
                'user_id': user_result.id,
                'user_name': user_result.name,
                'total_assigned': total_assigned,
                'resolved_tickets': resolved,
                'resolution_rate_percent': resolution_rate,
                'avg_resolution_hours': avg_resolution,
                'first_ticket_date': first_ticket.isoformat() if first_ticket else None,
                'last_ticket_date': last_ticket.isoformat() if last_ticket else None
            })

        return {
            'user_performance': user_performance,
            'filters_applied': {
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None
            }
        }

    except Exception as e:
        logger.error(f"❌ Failed to get user performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data performa user: {str(e)}"
        )


@router.get("/reports/downtime-analysis", response_model=dict)
async def get_downtime_analysis(
    date_from: Optional[datetime] = Query(None, description="Filter tanggal dari"),
    date_to: Optional[datetime] = Query(None, description="Filter tanggal sampai"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan analisis downtime untuk pelanggan.
    """
    try:
        # Base date filter
        date_filter = []
        if date_from:
            date_filter.append(TroubleTicketModel.created_at >= date_from)
        if date_to:
            date_filter.append(TroubleTicketModel.created_at <= date_to)

        # Overall downtime statistics
        total_downtime_result = await db.execute(
            select(
                func.sum(TroubleTicketModel.total_downtime_minutes).label('total_downtime'),
                func.avg(TroubleTicketModel.total_downtime_minutes).label('avg_downtime'),
                func.max(TroubleTicketModel.total_downtime_minutes).label('max_downtime'),
                func.count(TroubleTicketModel.id).label('total_tickets_with_downtime')
            )
            .where(
                and_(
                    TroubleTicketModel.total_downtime_minutes.isnot(None),
                    TroubleTicketModel.total_downtime_minutes > 0,
                    *(date_filter if date_filter else [])
                )
            )
        )

        downtime_stats = total_downtime_result.first()

        # Downtime by category
        category_downtime_results = await db.execute(
            select(
                TroubleTicketModel.category,
                func.sum(TroubleTicketModel.total_downtime_minutes).label('total_downtime'),
                func.avg(TroubleTicketModel.total_downtime_minutes).label('avg_downtime'),
                func.count(TroubleTicketModel.id).label('ticket_count')
            )
            .where(
                and_(
                    TroubleTicketModel.total_downtime_minutes.isnot(None),
                    TroubleTicketModel.total_downtime_minutes > 0,
                    *(date_filter if date_filter else [])
                )
            )
            .group_by(TroubleTicketModel.category)
            .order_by(desc('total_downtime'))
        )

        category_downtime = []
        for cat_result in category_downtime_results:
            category_downtime.append({
                'category': cat_result.category.value,
                'category_display': cat_result.category.value.replace('_', ' ').title(),
                'total_downtime_minutes': cat_result.total_downtime or 0,
                'avg_downtime_minutes': round(cat_result.avg_downtime or 0, 2),
                'ticket_count': cat_result.ticket_count,
                'total_downtime_hours': round((cat_result.total_downtime or 0) / 60, 2),
                'avg_downtime_hours': round((cat_result.avg_downtime or 0) / 60, 2)
            })

        # Top customers with most downtime
        customer_downtime_results = await db.execute(
            select(
                PelangganModel.id,
                PelangganModel.nama,
                func.sum(TroubleTicketModel.total_downtime_minutes).label('total_downtime'),
                func.count(TroubleTicketModel.id).label('ticket_count'),
                func.avg(TroubleTicketModel.total_downtime_minutes).label('avg_downtime')
            )
            .select_from(TroubleTicketModel)
            .join(PelangganModel, TroubleTicketModel.pelanggan_id == PelangganModel.id)
            .where(
                and_(
                    TroubleTicketModel.total_downtime_minutes.isnot(None),
                    TroubleTicketModel.total_downtime_minutes > 0,
                    *(date_filter if date_filter else [])
                )
            )
            .group_by(PelangganModel.id, PelangganModel.nama)
            .order_by(desc('total_downtime'))
            .limit(20)
        )

        customer_downtime = []
        for cust_result in customer_downtime_results:
            customer_downtime.append({
                'customer_id': cust_result.id,
                'customer_name': cust_result.nama,
                'total_downtime_minutes': cust_result.total_downtime or 0,
                'ticket_count': cust_result.ticket_count,
                'avg_downtime_minutes': round(cust_result.avg_downtime or 0, 2),
                'total_downtime_hours': round((cust_result.total_downtime or 0) / 60, 2),
                'avg_downtime_hours': round((cust_result.avg_downtime or 0) / 60, 2)
            })

        return {
            'overall_statistics': {
                'total_downtime_minutes': downtime_stats.total_downtime or 0,
                'total_downtime_hours': round((downtime_stats.total_downtime or 0) / 60, 2),
                'total_downtime_days': round((downtime_stats.total_downtime or 0) / (60 * 24), 2),
                'avg_downtime_minutes': round(downtime_stats.avg_downtime or 0, 2),
                'avg_downtime_hours': round((downtime_stats.avg_downtime or 0) / 60, 2),
                'max_downtime_minutes': downtime_stats.max_downtime or 0,
                'max_downtime_hours': round((downtime_stats.max_downtime or 0) / 60, 2),
                'tickets_with_downtime': downtime_stats.total_tickets_with_downtime or 0
            },
            'by_category': category_downtime,
            'top_customers': customer_downtime,
            'filters_applied': {
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None
            }
        }

    except Exception as e:
        logger.error(f"❌ Failed to get downtime analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil analisis downtime: {str(e)}"
        )
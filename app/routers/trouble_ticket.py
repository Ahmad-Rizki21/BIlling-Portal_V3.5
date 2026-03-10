from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import logging

from ..models.trouble_ticket import (
    TicketStatus,
)
from ..models.user import User as UserModel
from ..database import get_db
from ..auth import get_current_active_user
from ..services.trouble_ticket_service import TroubleTicketService
from ..schemas.trouble_ticket import (
    TroubleTicket,
    TroubleTicketCreate,
    TroubleTicketUpdate,
    TroubleTicketWithRelations,
    TicketStatusUpdate,
    DowntimeUpdate,
    TicketHistory,
    ActionTaken,
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


# Standardized Service getter
async def get_ticket_service(db: AsyncSession = Depends(get_db)) -> TroubleTicketService:
    return TroubleTicketService(db)


@router.post("/", response_model=TroubleTicket, status_code=status.HTTP_201_CREATED)
async def create_trouble_ticket(
    ticket_in: TroubleTicketCreate,
    background_tasks: BackgroundTasks,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Membuat Trouble Ticket baru.
    """
    return await service.create_ticket(ticket_in, current_user, background_tasks)


@router.get("/", response_model=PaginatedTroubleTicketResponse)
async def get_trouble_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=100),
    status: Optional[TicketStatusEnum] = Query(None),
    priority: Optional[TicketPriorityEnum] = Query(None),
    category: Optional[TicketCategoryEnum] = Query(None),
    assigned_to: Optional[int] = Query(None, gt=0),
    pelanggan_id: Optional[int] = Query(None, gt=0),
    id_brand: Optional[str] = Query(None, max_length=20),
    brand: Optional[str] = Query(None, max_length=50),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    include_relations: bool = Query(False),
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan daftar trouble tickets dengan pagination dan filter.
    """
    tickets, total_items = await service.get_filtered_tickets(
        skip=skip,
        limit=limit,
        status_filter=status.value if status else None,
        priority_filter=priority.value if priority else None,
        category_filter=category.value if category else None,
        assigned_to=assigned_to,
        pelanggan_id=pelanggan_id,
        id_brand=id_brand,
        brand=brand,
        date_from=date_from,
        date_to=date_to,
        search=search,
        include_relations=include_relations
    )

    total_pages = (total_items + limit - 1) // limit
    current_page = (skip // limit) + 1 if limit > 0 else 1

    return PaginatedTroubleTicketResponse(
        data=tickets,
        pagination=PaginationInfo(
            totalItems=total_items,
            currentPage=current_page,
            itemsPerPage=limit,
            totalPages=total_pages,
            hasNext=current_page < total_pages,
            hasPrevious=current_page > 1,
        ),
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
        }
    )


@router.get("/{ticket_id}", response_model=TroubleTicketWithRelations)
async def get_trouble_ticket_by_id(
    ticket_id: int,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan detail trouble ticket berdasarkan ID.
    """
    return await service.get_by_id_with_relations(
        ticket_id, 
        ["pelanggan", "data_teknis", "assigned_user"]
    )


@router.patch("/{ticket_id}", response_model=TroubleTicket)
async def update_trouble_ticket(
    ticket_id: int,
    ticket_update: TroubleTicketUpdate,
    background_tasks: BackgroundTasks,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update trouble ticket (partial update).
    """
    return await service.update_ticket(ticket_id, ticket_update, current_user, background_tasks)


@router.post("/{ticket_id}/status", response_model=TroubleTicket)
async def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    background_tasks: BackgroundTasks,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update status trouble ticket dengan history tracking.
    """
    return await service.update_status(ticket_id, status_update, current_user, background_tasks)


@router.post("/{ticket_id}/downtime", response_model=TroubleTicket)
async def update_ticket_downtime(
    ticket_id: int,
    downtime_update: DowntimeUpdate,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update downtime tracking untuk ticket.
    """
    return await service.update_downtime(ticket_id, downtime_update, current_user)


@router.post("/{ticket_id}/assign", response_model=TroubleTicket)
async def assign_ticket(
    ticket_id: int,
    assignment: TicketAssignment,
    background_tasks: BackgroundTasks,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menugaskan ticket ke user tertentu.
    """
    return await service.assign_ticket(ticket_id, assignment, current_user, background_tasks)


@router.post("/{ticket_id}/action", response_model=ActionTaken)
async def add_ticket_action(
    ticket_id: int,
    action_data: TicketStatusUpdate,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menambahkan action history tanpa mengganti status ticket.
    """
    return await service.add_action(ticket_id, action_data, current_user)


@router.get("/{ticket_id}/history", response_model=List[TicketHistory])
async def get_ticket_history(
    ticket_id: int,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan history perubahan status ticket.
    """
    return await service.get_history(ticket_id)


@router.get("/{ticket_id}/actions", response_model=List[ActionTaken])
async def get_ticket_actions(
    ticket_id: int,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan history action taken untuk ticket.
    """
    return await service.get_actions(ticket_id)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trouble_ticket(
    ticket_id: int,
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menghapus trouble ticket (hanya untuk status resolved/closed/cancelled).
    """
    await service.delete_ticket(ticket_id, current_user)


@router.get("/statistics/dashboard", response_model=TicketStatistics)
async def get_ticket_statistics(
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan statistik trouble tickets untuk dashboard.
    """
    stats = await service.get_dashboard_statistics()
    return TicketStatistics(**stats)


# Additional endpoints for comprehensive reporting
@router.get("/reports/monthly-trends", response_model=dict)
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=24),
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan data tren bulanan untuk trouble tickets.
    """
    return await service.get_monthly_trends(months)


@router.get("/reports/category-performance", response_model=dict)
async def get_category_performance(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan performa ticket berdasarkan kategori.
    """
    return await service.get_category_performance(date_from, date_to)


@router.get("/reports/user-performance", response_model=dict)
async def get_user_performance(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan performa ticket berdasarkan user/teknisi.
    """
    return await service.get_user_performance(date_from, date_to)


@router.get("/reports/downtime-analysis", response_model=dict)
async def get_downtime_analysis(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    service: TroubleTicketService = Depends(get_ticket_service),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan analisis downtime untuk pelanggan.
    """
    return await service.get_downtime_analysis(date_from, date_to)

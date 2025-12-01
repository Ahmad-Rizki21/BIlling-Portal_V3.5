# app/routers/global_search.py
"""
Global Search Router - Pencarian multi-entitas (Fixed Version)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import re
from jose import JWTError

# Import dependencies
from app.database import get_db
from app.auth import get_current_active_user, verify_access_token
from app.models.user import User

# Optional OAuth2 scheme (auto_error=False)
oauth2_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional user authentication - returns user if valid token, None otherwise.
    """
    if not token:
        return None

    try:
        # Verify token
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        # Get user from database
        query = select(User).where(User.id == int(user_id)).options(
            selectinload(User.role).selectinload(User.role.permissions)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        return user
    except (JWTError, ValueError, TypeError):
        return None
    except Exception:
        return None

from app.models.pelanggan import Pelanggan
from app.models.langganan import Langganan
from app.models.activity_log import ActivityLog
from app.models.trouble_ticket import TroubleTicket
from app.models.invoice import Invoice

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/global-search", tags=["Global Search"])

# Constants
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 100
MIN_SEARCH_LENGTH = 2

# Regex untuk input sanitization
SEARCH_PATTERN = re.compile(r'^[a-zA-Z0-9\s@._-]+$')

def _has_permission(user: Optional[User], permission: str) -> bool:
    """Check if user has specific permission."""
    if not user:
        return False

    # Admin has all permissions
    if user.role and user.role.name.lower() == 'admin':
        return True

    # Check specific permissions
    if hasattr(user, 'role') and user.role and hasattr(user.role, 'permissions'):
        return any(p.name == permission for p in user.role.permissions)

    return False

@router.get("", response_model=Dict[str, Any])
async def global_search(
    q: str = Query(..., min_length=MIN_SEARCH_LENGTH, description="Search query"),
    limit: int = Query(DEFAULT_SEARCH_LIMIT, le=MAX_SEARCH_LIMIT, description="Maximum results per entity"),
    offset: int = Query(0, ge=0, description="Results offset"),
    categories: Optional[str] = Query(None, description="Comma-separated categories to search"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Global search across all entities in system.
    """
    # Input sanitization
    if not SEARCH_PATTERN.match(q):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query contains invalid characters"
        )

    # Parse categories if provided
    search_categories = []
    if categories:
        search_categories = [cat.strip().lower() for cat in categories.split(',') if cat.strip()]
        valid_categories = ['users', 'pelanggan', 'langganan', 'activity_logs', 'tickets', 'invoices']
        search_categories = [cat for cat in search_categories if cat in valid_categories]

    # If no categories specified, search all
    if not search_categories:
        search_categories = ['users', 'pelanggan', 'langganan', 'activity_logs', 'tickets', 'invoices']

    results = {
        'query': q,
        'categories': search_categories,
        'results': {},
        'total_count': 0,
        'search_time': datetime.utcnow().isoformat()
    }

    try:
        # Search in each category
        for category in search_categories:
            try:
                if category == 'users' and (not current_user or _has_permission(current_user, 'view_users')):
                    category_results = await _search_users(db, q, limit, offset)
                    results['results']['users'] = category_results
                    results['total_count'] += len(category_results)

                elif category == 'pelanggan' and (not current_user or _has_permission(current_user, 'view_pelanggan')):
                    category_results = await _search_pelanggan(db, q, limit, offset)
                    results['results']['pelanggan'] = category_results
                    results['total_count'] += len(category_results)

                elif category == 'langganan' and (not current_user or _has_permission(current_user, 'view_langganan')):
                    category_results = await _search_langganan(db, q, limit, offset)
                    results['results']['langganan'] = category_results
                    results['total_count'] += len(category_results)

                elif category == 'activity_logs' and (not current_user or _has_permission(current_user, 'view_activity_log')):
                    category_results = await _search_activity_logs(db, q, limit, offset)
                    results['results']['activity_logs'] = category_results
                    results['total_count'] += len(category_results)

                elif category == 'tickets' and (not current_user or _has_permission(current_user, 'view_trouble_tickets')):
                    category_results = await _search_trouble_tickets(db, q, limit, offset)
                    results['results']['tickets'] = category_results
                    results['total_count'] += len(category_results)

                elif category == 'invoices' and (not current_user or _has_permission(current_user, 'view_invoices')):
                    category_results = await _search_invoices(db, q, limit, offset)
                    results['results']['invoices'] = category_results
                    results['total_count'] += len(category_results)

            except Exception as e:
                logger.error(f"Error searching in {category}: {str(e)}")
                # Continue with other categories even if one fails
                continue

        logger.info(f"Global search completed for query '{q}': {results['total_count']} results")
        return results

    except Exception as e:
        logger.error(f"Global search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service temporarily unavailable"
        )

async def _search_users(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search users by name or email."""
    search_query = f"%{query.lower()}%"

    stmt = select(User).where(
        or_(
            func.lower(User.name).like(search_query),
            func.lower(User.email).like(search_query)
        )
    ).offset(offset).limit(limit)

    result = await db.execute(stmt)
    users_list = result.scalars().all()

    return [
        {
            'id': u.id,
            'type': 'users',
            'title': u.name,
            'subtitle': f"{u.email or ''} • Role: {u.role.name if u.role else 'No Role'}",
            'url': f'/users?search={u.id}',
            'data': {
                'email': u.email,
                'role': u.role.name if u.role else 'No Role',
                'is_active': u.is_active
            }
        }
        for u in users_list
    ]

async def _search_pelanggan(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search pelanggan by nama, email, atau no_telp."""
    search_query = f"%{query.lower()}%"

    stmt = select(Pelanggan).where(
        or_(
            func.lower(Pelanggan.nama).like(search_query),
            func.lower(Pelanggan.email).like(search_query),
            func.lower(Pelanggan.no_telp).like(search_query)
        )
    ).offset(offset).limit(limit)

    result = await db.execute(stmt)
    pelanggan_list = result.scalars().all()

    return [
        {
            'id': p.id,
            'type': 'pelanggan',
            'title': p.nama,
            'subtitle': f"{p.email or ''} {p.no_telp or ''}",
            'url': f'/pelanggan?search={p.id}',
            'data': {
                'email': p.email,
                'no_telp': p.no_telp,
                'alamat': p.alamat
            }
        }
        for p in pelanggan_list
    ]

async def _search_langganan(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search langganan by status, paket layanan, atau pelanggan name."""
    search_query = f"%{query.lower()}%"

    stmt = select(Langganan).options(
        selectinload(Langganan.pelanggan),
        selectinload(Langganan.paket_layanan)
    ).where(
        or_(
            func.lower(Langganan.status).like(search_query),
            func.lower(Langganan.alasan_berhenti).like(search_query) if search_query else False
        )
    ).offset(offset).limit(limit)

    result = await db.execute(stmt)
    langganan_list = result.scalars().all()

    return [
        {
            'id': l.id,
            'type': 'langganan',
            'title': l.pelanggan.nama if l.pelanggan else 'Unknown Customer',
            'subtitle': f"{l.paket_layanan.nama_paket if l.paket_layanan else 'Custom Package'} • Status: {l.status}",
            'url': f'/langganan?search={l.id}',
            'data': {
                'status': l.status,
                'paket_layanan': l.paket_layanan.nama_paket if l.paket_layanan else 'Custom Package',
                'pelanggan_id': l.pelanggan_id
            }
        }
        for l in langganan_list
    ]

async def _search_activity_logs(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search activity logs by action, user, atau details."""
    search_query = f"%{query.lower()}%"

    stmt = select(ActivityLog).options(
        selectinload(ActivityLog.user)
    ).where(
        or_(
            func.lower(ActivityLog.action).like(search_query),
            func.lower(ActivityLog.details).like(search_query) if ActivityLog.details else False
        )
    ).order_by(ActivityLog.timestamp.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            'id': log.id,
            'type': 'activity_logs',
            'title': f"{log.action} by {log.user.nama if log.user else 'Unknown User'}",
            'subtitle': f"{log.details[:100] if log.details else ''}... • {log.timestamp.strftime('%Y-%m-%d %H:%M')}",
            'url': f'/activity-logs?search={log.id}',
            'data': {
                'action': log.action,
                'user': log.user.nama if log.user else 'Unknown',
                'created_at': log.timestamp.isoformat(),
                'details': log.details
            }
        }
        for log in logs
    ]

async def _search_trouble_tickets(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search trouble tickets by title, description, atau status."""
    search_query = f"%{query.lower()}%"

    stmt = select(TroubleTicket).options(
        selectinload(TroubleTicket.pelanggan),
        selectinload(TroubleTicket.assigned_user)
    ).where(
        or_(
            func.lower(TroubleTicket.title).like(search_query),
            func.lower(TroubleTicket.description).like(search_query)
        )
    ).order_by(TroubleTicket.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    tickets = result.scalars().all()

    return [
        {
            'id': t.id,
            'type': 'tickets',
            'title': t.title,
            'subtitle': f"Priority: {t.priority.value if t.priority else 'Normal'} • Status: {t.status.value if t.status else 'Unknown'} • {t.pelanggan.nama if t.pelanggan else 'Unknown Customer'}",
            'url': f'/trouble-tickets?search={t.id}',
            'data': {
                'status': t.status.value if t.status else 'Unknown',
                'priority': t.priority.value if t.priority else 'Normal',
                'pelanggan_nama': t.pelanggan.nama if t.pelanggan else 'Unknown'
            }
        }
        for t in tickets
    ]

async def _search_invoices(db: AsyncSession, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """Search invoices by nomor invoice, status, atau pelanggan name."""
    search_query = f"%{query.lower()}%"

    stmt = select(Invoice).options(
        selectinload(Invoice.pelanggan)
    ).where(
        or_(
            func.lower(Invoice.invoice_number).like(search_query),
            func.lower(Invoice.status_invoice).like(search_query)
        )
    ).order_by(Invoice.tgl_invoice.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    invoices = result.scalars().all()

    return [
        {
            'id': inv.id,
            'type': 'invoices',
            'title': inv.invoice_number,
            'subtitle': f"Rp {inv.total_harga:,.0f} • Status: {inv.status_invoice} • {inv.pelanggan.nama if inv.pelanggan else 'Unknown Customer'}",
            'url': f'/invoices?search={inv.id}',
            'data': {
                'status': inv.status_invoice,
                'jumlah': float(inv.total_harga),
                'tanggal_terbit': inv.tgl_invoice.isoformat(),
                'pelanggan_nama': inv.pelanggan.nama if inv.pelanggan else 'Unknown'
            }
        }
        for inv in invoices
    ]

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=50, description="Partial search query"),
    limit: int = Query(5, le=10, description="Maximum suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get search suggestions based on partial query."""
    search_query = f"%{q.lower()}%"

    suggestions = []

    try:
        # Get common search terms from pelanggan names
        stmt = select(Pelanggan.nama).where(
            func.lower(Pelanggan.nama).like(search_query)
        ).limit(limit)

        result = await db.execute(stmt)
        names = result.scalars().all()

        for name in names:
            suggestions.append({
                'text': name,
                'type': 'pelanggan',
                'category': 'Customer'
            })

        return {
            'query': q,
            'suggestions': suggestions[:limit]
        }

    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        return {
            'query': q,
            'suggestions': []
        }

@router.get("/health")
async def search_health_check():
    """Health check endpoint for search service."""
    return {
        'status': 'healthy',
        'service': 'global_search',
        'timestamp': datetime.utcnow().isoformat()
    }
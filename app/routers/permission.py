# app/routers/permission.py
"""
Permission Management Router - CRUD operations untuk permission system

Router ini handle semua permission management operations di sistem billing.
Permission adalah hak akses granular yang bisa diassign ke role.

Permission Structure:
- Format: {action}_{resource}
- Contoh: create_pelanggan, view_invoice, delete_user
- Actions: create, view, edit, delete
- Resources: menus, widgets, system features

Permission Categories:
1. Menu Permissions - Akses ke navigasi menu
   - create_dashboard, view_billing, edit_network, dll
2. Widget Permissions - Akses ke dashboard widgets
   - view_widget_stats, view_widget_alerts, dll
3. System Feature Permissions - Akses ke fitur sistem
   - create_user, view_reports, manage_settings, dll

Security Features:
- Idempotent permission generation (no duplicates)
- Automatic permission creation dari config
- Database-driven permission checking
- Comprehensive permission coverage

Integration Points:
- Role management system
- Authorization decorators (@has_permission)
- Frontend access control
- Audit logging system

Usage Flow:
1. Generate permissions dari config
2. Assign permissions ke roles
3. Assign roles ke users
4. Check permissions di protected endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..models.permission import Permission as PermissionModel
from ..database import get_db
from ..schemas.permission import Permission as PermissionSchema

# --- PERBAIKAN DI SINI ---
from ..config import settings  # Impor 'settings' bukan 'MENUS'

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/generate", response_model=List[PermissionSchema])
async def generate_permissions(db: AsyncSession = Depends(get_db)):
    """
    Generate All System Permissions - Otomatis buat permission dari config

    Function ini generate semua permissions yang dibutuhkan sistem berdasarkan
    configuration dari settings.py. Ini一次性buat semua permission buat menus,
    widgets, dan system features.

    Generation Logic:
    1. Menu Permissions: CRUD operations untuk setiap menu
    2. Widget Permissions: View access untuk setiap dashboard widget
    3. System Feature Permissions: CRUD untuk fitur sistem lainnya

    Permission Patterns:
    - Menus: {action}_{menu_name} (create_dashboard, edit_billing, dll)
    - Widgets: view_widget_{widget_name} (view_widget_stats, dll)
    - Features: {action}_{feature_name} (create_user, delete_role, dll)

    Idempotent Operation:
    - Cek existing permission sebelum create
    - Hanya buat permission yang belum ada
    - Safe buat dijalankan berulang kali
    - Return list permission yang baru dibuat

    Use Cases:
    - Initial setup aplikasi baru
    - Add new menu/widget/feature
    - Permission system maintenance
    - Development environment setup

    Security Features:
    - Comprehensive permission coverage
    - Consistent naming conventions
    - No duplicate permissions
    - Atomic database operations

    Returns:
        List[PermissionSchema]: Permission yang baru dibuat (kosong kalau semua sudah ada)

    Raises:
        HTTPException 200: Kalau semua permission sudah ada
    """
    permissions_created = []

    # --- BAGIAN 1: Generate permissions untuk MENU (Kode Asli Anda) ---
    actions = ["create", "view", "edit", "delete"]
    for menu in settings.MENUS:
        for action in actions:
            permission_name = f"{action}_{menu.lower().replace(' & ', '_').replace(' ', '_')}"

            result = await db.execute(select(PermissionModel).where(PermissionModel.name == permission_name))
            existing_permission = result.scalars().first()

            if not existing_permission:
                new_permission = PermissionModel(name=permission_name)
                db.add(new_permission)
                await db.flush()
                permissions_created.append(new_permission)

    # --- BAGIAN 2: Generate permissions untuk WIDGET ---
    widget_action = "view_widget"
    for widget in settings.DASHBOARD_WIDGETS:
        permission_name = f"{widget_action}_{widget}"

        result = await db.execute(select(PermissionModel).where(PermissionModel.name == permission_name))
        existing_permission = result.scalars().first()

        if not existing_permission:
            new_permission = PermissionModel(name=permission_name)
            db.add(new_permission)
            await db.flush()
            permissions_created.append(new_permission)

    # --- BAGIAN 3: Generate permissions untuk SYSTEM FEATURES ---
    feature_actions = ["create", "view", "edit", "delete"]
    for feature in settings.SYSTEM_FEATURES:
        for action in feature_actions:
            permission_name = f"{action}_{feature}"

            result = await db.execute(select(PermissionModel).where(PermissionModel.name == permission_name))
            existing_permission = result.scalars().first()

            if not existing_permission:
                new_permission = PermissionModel(name=permission_name)
                db.add(new_permission)
                await db.flush()
                permissions_created.append(new_permission)

    # --- Sisa fungsi (Kode Asli Anda) ---
    await db.commit()

    for p in permissions_created:
        await db.refresh(p)

    if not permissions_created:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Semua permission sudah ter-generate.",
        )

    return permissions_created


@router.get("/", response_model=List[PermissionSchema])
async def get_permissions(db: AsyncSession = Depends(get_db)):
    """
    Get All Permissions - Retrieve complete permission list

    Function ini mengambil semua permissions yang ada di database.
    Biasanya dipake buat admin interface atau debugging.

    Query Features:
    - Return semua permissions tanpa pagination
    - Sort by permission name (alphabetical)
    - Efficient single query dengan proper ordering
    - Include all permission categories

    Return Format:
    - List PermissionSchema dengan id dan name
    - Sorted alphabetically by name
    - Complete permission list
    - Empty list kalau belum ada permissions

    Use Cases:
    - Admin permission management interface
    - Role assignment form
    - System debugging dan monitoring
    - Permission audit dan review

    Performance Notes:
    - Single efficient query
    - Proper database indexing
    - Minimal memory footprint
    - Fast response time

    Returns:
        List[PermissionSchema]: Complete list of all permissions
    """
    result = await db.execute(select(PermissionModel).order_by(PermissionModel.name))
    return result.scalars().all()

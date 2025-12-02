"""
Centralized notification service untuk menghilangkan duplikasi notification logic
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging

from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..websocket_manager import manager
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized notification service untuk menghilangkan duplikasi
    notification patterns di seluruh aplikasi
    """

    # Predefined role combinations untuk different notification types
    ROLE_COMBINATIONS = {
        "noc_cs_admin": ["NOC", "CS", "Admin"],
        "finance": ["Finance"],
        "admin_only": ["Admin"],
        "noc_only": ["NOC"],
        "cs_only": ["CS"],
        "all_teams": ["NOC", "CS", "Admin", "Finance"],
    }

    @staticmethod
    async def get_users_by_roles(db: AsyncSession, role_names: List[str]) -> List[int]:
        """
        Mengambil user IDs berdasarkan nama roles
        Menghilangkan duplikasi role-based user query logic
        """
        try:
            query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name).in_([r.lower() for r in role_names]))
            result = await db.execute(query)
            user_ids = result.scalars().all()

            logger.info(f"Found {len(user_ids)} users with roles: {role_names}")
            return list(user_ids)

        except Exception as e:
            logger.error(f"Failed to get users by roles {role_names}: {e}")
            return []

    @staticmethod
    async def broadcast_to_roles(db: AsyncSession, role_names: List[str], notification_data: Dict[str, Any]) -> bool:
        """
        Broadcast notification ke users dengan roles tertentu
        Menghilangkan duplikasi broadcast logic di semua routers
        """
        try:
            target_user_ids = await NotificationService.get_users_by_roles(db, role_names)

            if not target_user_ids:
                logger.warning(f"No users found with roles: {role_names}")
                return False

            # Add metadata ke notification
            enriched_notification = {
                **notification_data,
                "timestamp": datetime.now().isoformat(),
                "broadcast_to_roles": role_names,
                "target_user_count": len(target_user_ids),
            }

            # Broadcast menggunakan WebSocket manager
            await manager.broadcast_to_roles(enriched_notification, target_user_ids)

            SuccessHandler.log_success(
                operation="broadcast notification",
                resource_name="message",
                additional_info={
                    "roles": role_names,
                    "user_count": len(target_user_ids),
                    "message_type": notification_data.get("type", "unknown"),
                },
            )

            return True

        except Exception as e:
            ErrorHandler.handle_internal_server_error(
                e, "broadcast notification to roles", {"roles": role_names, "notification_type": notification_data.get("type")}
            )
            return False

    @staticmethod
    async def notify_new_customer(db: AsyncSession, customer_data: Dict[str, Any]) -> bool:
        """
        Notification untuk pelanggan baru - khusus untuk tim NOC, CS, dan Admin
        Menghilangkan duplikasi notification logic di pelanggan.py
        """
        notification_payload = {
            "type": "new_customer_for_noc",
            "message": f"Pelanggan baru '{customer_data.get('nama', 'N/A')}' telah ditambahkan. Segera buatkan Data Teknis.",
            "data": {
                "pelanggan_id": customer_data.get("id"),
                "pelanggan_nama": customer_data.get("nama"),
                "alamat": customer_data.get("alamat"),
                "no_telp": customer_data.get("no_telp"),
                "email": customer_data.get("email"),
                "action_required": "create_data_teknis",
            },
        }

        return await NotificationService.broadcast_to_roles(
            db, NotificationService.ROLE_COMBINATIONS["noc_cs_admin"], notification_payload
        )

    @staticmethod
    async def notify_new_data_teknis(db: AsyncSession, data_teknis: Dict[str, Any]) -> bool:
        """
        Notification untuk data teknis baru - khusus untuk tim NOC
        """
        notification_payload = {
            "type": "new_data_teknis",
            "message": f"Data Teknis untuk pelanggan '{data_teknis.get('pelanggan_nama', 'N/A')}' telah dibuat.",
            "data": {
                "data_teknis_id": data_teknis.get("id"),
                "pelanggan_id": data_teknis.get("pelanggan_id"),
                "pelanggan_nama": data_teknis.get("pelanggan_nama"),
                "ip_pelanggan": data_teknis.get("ip_pelanggan"),
                "action_required": "configure_mikrotik",
            },
        }

        return await NotificationService.broadcast_to_roles(
            db, NotificationService.ROLE_COMBINATIONS["noc_only"], notification_payload
        )

    @staticmethod
    async def notify_new_invoice(db: AsyncSession, invoice_data: Dict[str, Any]) -> bool:
        """
        Notification untuk invoice baru - khusus untuk tim Finance
        """
        notification_payload = {
            "type": "new_invoice",
            "message": f"Invoice baru #{invoice_data.get('nomor_invoice', 'N/A')} telah dibuat.",
            "data": {
                "invoice_id": invoice_data.get("id"),
                "nomor_invoice": invoice_data.get("nomor_invoice"),
                "pelanggan_nama": invoice_data.get("pelanggan_nama"),
                "total_harga": invoice_data.get("total_harga"),
                "tanggal_jatuh_tempo": invoice_data.get("tanggal_jatuh_tempo"),
                "action_required": "monitor_payment",
            },
        }

        return await NotificationService.broadcast_to_roles(
            db, NotificationService.ROLE_COMBINATIONS["finance"], notification_payload
        )

    @staticmethod
    async def notify_payment_received(db: AsyncSession, payment_data: Dict[str, Any]) -> bool:
        """
        Notification untuk pembayaran diterima - khusus untuk tim Finance
        """
        notification_payload = {
            "type": "payment_received",
            "message": f"Pembayaran invoice #{payment_data.get('nomor_invoice', 'N/A')} telah diterima.",
            "data": {
                "invoice_id": payment_data.get("invoice_id"),
                "nomor_invoice": payment_data.get("nomor_invoice"),
                "pelanggan_nama": payment_data.get("pelanggan_nama"),
                "jumlah_pembayaran": payment_data.get("jumlah_pembayaran"),
                "tanggal_pembayaran": payment_data.get("tanggal_pembayaran"),
                "action_required": "update_service_status",
            },
        }

        return await NotificationService.broadcast_to_roles(
            db, NotificationService.ROLE_COMBINATIONS["finance"], notification_payload
        )

    @staticmethod
    async def notify_service_suspended(db: AsyncSession, service_data: Dict[str, Any]) -> bool:
        """
        Notification untuk layanan di-suspend - khusus untuk tim NOC dan CS
        """
        notification_payload = {
            "type": "service_suspended",
            "message": f"Layanan untuk pelanggan '{service_data.get('pelanggan_nama', 'N/A')}' telah di-suspend.",
            "data": {
                "langganan_id": service_data.get("id"),
                "pelanggan_id": service_data.get("pelanggan_id"),
                "pelanggan_nama": service_data.get("pelanggan_nama"),
                "alasan": service_data.get("alasan", "Menunggak pembayaran"),
                "action_required": "contact_customer",
            },
        }

        return await NotificationService.broadcast_to_roles(db, ["NOC", "CS"], notification_payload)

    @staticmethod
    async def notify_mikrotik_issue(db: AsyncSession, issue_data: Dict[str, Any]) -> bool:
        """
        Notification untuk masalah Mikrotik - khusus untuk tim NOC
        """
        notification_payload = {
            "type": "mikrotik_issue",
            "message": f"Terdapat masalah koneksi ke Mikrotik server '{issue_data.get('server_name', 'N/A')}'.",
            "data": {
                "server_id": issue_data.get("server_id"),
                "server_name": issue_data.get("server_name"),
                "host_ip": issue_data.get("host_ip"),
                "error_message": issue_data.get("error_message"),
                "action_required": "check_server_connection",
            },
        }

        return await NotificationService.broadcast_to_roles(
            db, NotificationService.ROLE_COMBINATIONS["noc_only"], notification_payload
        )

    @staticmethod
    async def send_system_notification(
        db: AsyncSession,
        message: str,
        notification_type: str = "system",
        target_roles: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send custom system notification ke roles tertentu
        Method yang flexible untuk custom notifications
        """
        if target_roles is None:
            target_roles = NotificationService.ROLE_COMBINATIONS["admin_only"]

        notification_payload = {"type": notification_type, "message": message, "data": data or {}}

        return await NotificationService.broadcast_to_roles(db, target_roles, notification_payload)

    @staticmethod
    async def notify_user_activity(db: AsyncSession, user_id: int, activity_data: Dict[str, Any]) -> bool:
        """
        Send notification ke user spesifik (bukan berdasarkan role)
        Untuk personal notifications
        """
        try:
            notification_payload = {**activity_data, "timestamp": datetime.now().isoformat(), "target_user_id": user_id}

            # Send ke spesifik user
            await manager.send_to_user(user_id, notification_payload)  # type: ignore

            SuccessHandler.log_success(
                operation="send personal notification",
                resource_name="user notification",
                identifier=user_id,
                additional_info={"notification_type": activity_data.get("type")},  # type: ignore
            )

            return True

        except Exception as e:
            ErrorHandler.handle_internal_server_error(
                e, "send personal notification", {"user_id": user_id, "notification_type": activity_data.get("type")}
            )
            return False


class NotificationTemplate:
    """
    Template untuk notification messages yang konsisten
    """

    @staticmethod
    def create_success_notification(operation: str, resource: str, identifier: Any) -> Dict[str, Any]:
        return {
            "type": "operation_success",
            "message": f"Berhasil {operation} {resource} #{identifier}",
            "data": {"operation": operation, "resource": resource, "identifier": identifier, "status": "success"},
        }

    @staticmethod
    def create_error_notification(operation: str, resource: str, error: str) -> Dict[str, Any]:
        return {
            "type": "operation_error",
            "message": f"Gagal {operation} {resource}: {error}",
            "data": {"operation": operation, "resource": resource, "error": error, "status": "error"},
        }

    @staticmethod
    def create_warning_notification(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:  # type: ignore
        return {"type": "warning", "message": message, "data": {**(data or {}), "status": "warning"}}  # type: ignore

    @staticmethod
    def create_info_notification(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:  # type: ignore
        return {"type": "info", "message": message, "data": {**(data or {}), "status": "info"}}  # type: ignore

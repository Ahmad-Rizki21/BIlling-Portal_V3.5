# app/websocket_manager.py

import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Menyimpan koneksi aktif dengan key user_id
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Menerima koneksi WebSocket baru dan menyimpannya."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        """Menghapus koneksi saat pengguna terputus."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_to_roles(self, message: dict, user_ids: List[int]):
        """Mengirim pesan ke daftar user_id tertentu (berdasarkan role)."""
        if not user_ids:
            return

        message_json = json.dumps(message)
        tasks = []
        for user_id in user_ids:
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                tasks.append(websocket.send_text(message_json))
        
        if tasks:
            logger.info(f"Broadcasting '{message.get('type')}' notification to {len(tasks)} user(s).")
            await asyncio.gather(*tasks, return_exceptions=True)

# Buat satu instance manager untuk digunakan di seluruh aplikasi
manager = ConnectionManager()
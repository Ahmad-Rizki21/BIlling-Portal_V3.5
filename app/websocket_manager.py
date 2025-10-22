# app/websocket_manager.py
"""
WebSocket connection manager buat real-time notifications.
Ini system yang handle real-time updates ke frontend untuk billing system.

Features:
- Real-time notifications (invoice, payment, status changes)
- User-specific messaging
- Role-based broadcasting
- Connection health monitoring
- Rate limiting & security
- Performance optimization

Use cases:
- Invoice payment notifications
- Service status updates
- System alerts
- Dashboard live updates
- Admin notifications

Security:
- JWT token authentication
- Rate limiting per IP
- Single connection per user
- Heartbeat monitoring
- Graceful connection cleanup
"""

import asyncio
import datetime
import json
import logging
import time
from collections import defaultdict
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Main WebSocket connection manager class.
    Handle semua real-time connections buat billing system.

    Features:
    - Single connection per user (security)
    - Performance metrics & monitoring
    - Rate limiting protection
    - Batch message processing
    - Automatic heartbeat & cleanup
    - Role-based message targeting

    Architecture:
    - Dict-based connection storage (user_id -> WebSocket)
    - Metadata tracking buat performance
    - Queue-based batch processing
    - Async task management

    Usage:
        manager = ConnectionManager()
        await manager.connect(websocket, user_id)
        await manager.send_to_user(user_id, {"message": "Hello!"})
        await manager.broadcast_to_roles(message, user_ids)
    """

    def __init__(self):
        # Menyimpan koneksi aktif dengan key user_id
        self.active_connections: Dict[int, WebSocket] = {}

        # Performance optimization: Track connection metadata
        self.connection_metadata: Dict[int, dict] = {}

        # Track user roles for efficient broadcasting
        self.user_roles: Dict[int, Set[str]] = defaultdict(set)

        # Connection pool untuk batch operations
        self._connection_queue = asyncio.Queue(maxsize=1000)
        self._batch_size = 50
        self._batch_timeout = 0.1  # 100ms

        # Heartbeat mechanism
        self._heartbeat_task = None
        self._heartbeat_interval = 30  # 30 seconds

        # Rate limiting untuk mencegah spam koneksi
        self.connection_attempts: Dict[str, list] = {}  # IP address -> timestamps
        self.rate_limit_window = 60  # 60 seconds
        self.max_attempts_per_window = 30  # maksimal 30 koneksi per menit per IP (1 koneksi per 2 detik)

        # Performance metrics
        self.metrics = {
            "total_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "avg_response_time": 0,
            "connection_duration": defaultdict(list),
            "blocked_attempts": 0,
        }

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept dan setup WebSocket connection baru.
        Implement single connection policy buat security.

        Args:
            websocket: FastAPI WebSocket object
            user_id: User ID yang mau connect

        Security features:
        - Single connection per user (kick existing connection)
        - Graceful connection replacement
        - Metadata tracking buat monitoring
        - Auto-start heartbeat mechanism

        Process flow:
        1. Cek existing connection, kick kalau ada
        2. Accept new WebSocket connection
        3. Store connection dan metadata
        4. Start heartbeat monitoring
        5. Update metrics

        Note:
        - Existing connection bakal di-close gracefully
        - Metadata dipake buat performance monitoring
        - Heartbeat mulai otomatis
        """

        # Handle multiple connections from same user - allow only one connection per user
        if user_id in self.active_connections:
            # Close existing connection gracefully before accepting new one
            try:
                await self.active_connections[user_id].close(code=1000, reason="Connection replaced")
                # Remove old connection from active connections
                del self.active_connections[user_id]
                logger.info(f"Replaced old connection for user {user_id}")
            except Exception as e:
                logger.warning(f"Error closing old connection for user {user_id}: {e}")
                # Force remove from active connections if close fails
                if user_id in self.active_connections:
                    del self.active_connections[user_id]

        await websocket.accept()
        self.active_connections[user_id] = websocket

        # Track connection metadata for performance monitoring
        self.connection_metadata[user_id] = {
            "connected_at": time.time(),
            "last_ping": time.time(),
            "messages_sent": 0,
            "last_activity": time.time(),
        }

        self.metrics["total_connections"] += 1

        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

        # Start heartbeat if not already running
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def is_rate_limited(self, client_ip: str) -> bool:
        """
        Rate limiting protection buat prevent connection spam.
        Advanced rate limiting dengan auto-reset dan emergency protection.

        Args:
            client_ip: IP address client yang konek

        Returns:
            True kalau rate limited, False kalau boleh konek

        Rate limiting rules:
        - Max 30 connections per menit per IP
        - Auto-reset setelah cooldown period
        - Emergency protection untuk excessive attempts
        - Sliding window implementation

        Security features:
        - Prevent brute force connection attacks
        - Auto-recovery dari temporary blocks
        - Emergency cooldown buat abusive IPs
        - Track blocked attempts metrics

        Example:
            if manager.is_rate_limited("192.168.1.1"):
                return {"error": "Too many connection attempts"}

        Note:
        - Rate limit reset otomatis setelah cooldown
        - Emergency protection activate kalau excess attempts
        - Metrics tracking buat monitoring abuse patterns
        """
        current_time = time.time()

        # Clean old attempts
        if client_ip in self.connection_attempts:
            self.connection_attempts[client_ip] = [
                timestamp for timestamp in self.connection_attempts[client_ip]
                if current_time - timestamp < self.rate_limit_window
            ]

            # Auto-reset if attempts are very old (avoid permanent blocks)
            if len(self.connection_attempts[client_ip]) > 0:
                oldest_attempt = min(self.connection_attempts[client_ip])
                if current_time - oldest_attempt > self.rate_limit_window * 2:  # 2 minutes
                    self.connection_attempts[client_ip] = []
                    logger.info(f"Rate limit auto-reset for IP {client_ip} after cooling period")
        else:
            self.connection_attempts[client_ip] = []

        # Check if rate limit exceeded
        if len(self.connection_attempts[client_ip]) >= self.max_attempts_per_window:
            self.metrics["blocked_attempts"] += 1
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {len(self.connection_attempts[client_ip])} attempts")

            # Emergency reset - if too many attempts, force longer cooldown
            if len(self.connection_attempts[client_ip]) > self.max_attempts_per_window * 1.5:
                logger.warning(f"Emergency rate limit for IP {client_ip} - forcing 5 minute cooldown")
                self.connection_attempts[client_ip] = [current_time - 300]  # 5 minutes ago
                return True

            return True

        # Record this attempt
        self.connection_attempts[client_ip].append(current_time)
        return False

    def clear_rate_limit(self, client_ip: str):
        """Manually clear rate limit for specific IP (for admin use)."""
        if client_ip in self.connection_attempts:
            del self.connection_attempts[client_ip]
            logger.info(f"Rate limit manually cleared for IP {client_ip}")

    async def disconnect(self, user_id: int):
        """
        Clean disconnect user dari WebSocket manager.
        Cleanup semua metadata dan tracking data.

        Args:
            user_id: User ID yang mau disconnect

        Cleanup tasks:
        - Remove dari active connections
        - Track connection duration metrics
        - Clean up role assignments
        - Remove connection metadata
        - Update connection count

        Performance tracking:
        - Connection duration analysis
        - Message delivery statistics
        - User behavior patterns

        Note:
        - Graceful cleanup tanpa error
        - Metrics preserved buat analysis
        - Auto cleanup role assignments
        """
        if user_id in self.active_connections:
            # Track connection duration
            if user_id in self.connection_metadata:
                duration = time.time() - self.connection_metadata[user_id]["connected_at"]
                self.metrics["connection_duration"][user_id].append(duration)
                del self.connection_metadata[user_id]

            # Clean up role tracking
            if user_id in self.user_roles:
                del self.user_roles[user_id]

            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def add_user_role(self, user_id: int, role: str):
        """Add role to user for targeted broadcasting."""
        self.user_roles[user_id].add(role)
        logger.debug(f"Added role '{role}' to user {user_id}")

    def get_users_by_role(self, role: str) -> List[int]:
        """Get all users that have a specific role."""
        return [user_id for user_id, roles in self.user_roles.items() if role in roles]

    async def send_to_user(self, user_id: int, message: dict):
        """
        Kirim message ke user spesifik via WebSocket.
        Core messaging function buat individual notifications.

        Args:
            user_id: Target user ID
            message: Message dictionary dengan data

        Returns:
            True kalau berhasil, False kalau gagal/user tidak ada

        Message format:
        {
            "type": "notification|alert|update",
            "message": "Human readable message",
            "data": {"key": "value"},  // Optional
            "timestamp": "ISO format"
        }

        Features:
        - Auto timestamp addition
        - Activity tracking
        - Error handling & cleanup
        - JSON serialization

        Usage:
            await manager.send_to_user(
                user_id=123,
                message={
                    "type": "payment_received",
                    "message": "Payment received for INV-001",
                    "data": {"invoice_id": 1, "amount": 150000}
                }
            )

        Error handling:
        - Auto remove disconnected users
        - Graceful fallback on errors
        - Failed message tracking
        """
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} is not connected")
            return False

        # Ensure message has timestamp
        if "timestamp" not in message:
            message["timestamp"] = datetime.datetime.now().isoformat()

        try:
            # Serialize message
            message_json = json.dumps(message, ensure_ascii=False)
            # Send to specific user
            await self.active_connections[user_id].send_text(message_json)

            # Update user activity
            if user_id in self.connection_metadata:
                self.connection_metadata[user_id]["last_activity"] = time.time()
                self.connection_metadata[user_id]["messages_sent"] += 1

            self.metrics["messages_sent"] += 1
            logger.info(f"Message sent to user {user_id}")
            return True

        except Exception as e:
            self.metrics["messages_failed"] += 1
            logger.error(f"Failed to send message to user {user_id}: {e}")
            # Remove disconnected user
            await self.disconnect(user_id)
            return False

    async def broadcast_to_roles(self, message: dict, user_ids: List[int]):
        """
        Broadcast message ke multiple users dengan performance optimization.
        Main function buat mass notifications.

        Args:
            message: Message dictionary
            user_ids: List target user IDs

        Performance features:
        - Batch processing buat large broadcasts
        - JSON validation & serialization
        - Message format standardization
        - Metrics tracking

        Message processing:
        1. Validate message format
        2. Auto-add missing fields (timestamp, type)
        3. JSON serialization & validation
        4. Batch vs direct routing decision
        5. Performance metrics update

        Batch vs Direct:
        - < 50 users: Direct broadcast (faster)
        - > 50 users: Batch processing (more efficient)

        Usage:
            await manager.broadcast_to_roles(
                message={"type": "system_alert", "message": "Maintenance in 5 mins"},
                user_ids=[1, 2, 3, 4, 5]
            )

        Error handling:
        - Fallback message on serialization errors
        - Individual error tracking
        - Graceful degradation
        """
        if not user_ids:
            return

        start_time = time.time()

        # Validasi dan siapkan message dengan format yang konsisten
        if not isinstance(message, dict):
            logger.error("Message must be a dictionary")
            return

        # Pastikan message memiliki timestamp
        if "timestamp" not in message:
            message["timestamp"] = datetime.datetime.now().isoformat()

        # Pastikan message memiliki type
        if "type" not in message:
            message["type"] = "notification"

        # Pastikan message memiliki message text
        if "message" not in message:
            message["message"] = "New notification received"

        # Simplifikasi message untuk menghindari nested object yang kompleks
        simplified_message = {
            "type": message.get("type", "notification"),
            "message": message.get("message", "New notification received"),
            "timestamp": message.get("timestamp", datetime.datetime.now().isoformat()),
            "data": message.get("data", {}),
        }

        try:
            # Validasi JSON sebelum mengirim
            message_json = json.dumps(simplified_message, ensure_ascii=False)
            # Validasi bahwa ini JSON yang valid
            json.loads(message_json)
        except Exception as e:
            logger.error(f"Failed to serialize message to JSON: {e}")
            # Kirim message sederhana sebagai fallback
            fallback_message = {
                "type": "notification",
                "message": "New notification received",
                "timestamp": datetime.datetime.now().isoformat(),
                "data": {},
            }
            message_json = json.dumps(fallback_message, ensure_ascii=False)

        # Performance optimization: Batch processing untuk large broadcasts
        if len(user_ids) > self._batch_size:
            await self._batch_broadcast(message_json, user_ids)
        else:
            await self._direct_broadcast(message_json, user_ids)

        # Update metrics
        process_time = time.time() - start_time
        self.metrics["avg_response_time"] = (self.metrics["avg_response_time"] + process_time) / 2

    async def _direct_broadcast(self, message_json: str, user_ids: List[int]):
        """Direct broadcast untuk small batches."""
        tasks = []
        active_user_ids = []

        for user_id in user_ids:
            if user_id in self.active_connections:
                websocket = self.active_connections[user_id]
                active_user_ids.append(user_id)
                tasks.append(websocket.send_text(message_json))

        if tasks:
            logger.info(f"Broadcasting to {len(tasks)} user(s).")
            # Gunakan return_exceptions=True untuk mencegah satu error menghentikan semua
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Update metrics dan log error individu
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.metrics["messages_failed"] += 1
                    logger.error(f"Failed to send message to user {active_user_ids[i]}: {result}")
                else:
                    success_count += 1
                    # Update user activity
                    if active_user_ids[i] in self.connection_metadata:
                        self.connection_metadata[active_user_ids[i]]["last_activity"] = time.time()
                        self.connection_metadata[active_user_ids[i]]["messages_sent"] += 1

            self.metrics["messages_sent"] += success_count

    async def _batch_broadcast(self, message_json: str, user_ids: List[int]):
        """Batch processing untuk large broadcasts."""
        logger.info(f"Starting batch broadcast to {len(user_ids)} users")

        # Split into batches
        batches = [user_ids[i : i + self._batch_size] for i in range(0, len(user_ids), self._batch_size)]

        for batch in batches:
            active_batch = [uid for uid in batch if uid in self.active_connections]
            if active_batch:
                await self._direct_broadcast(message_json, active_batch)
                # Small delay between batches to prevent overwhelming
                await asyncio.sleep(0.01)

    async def _heartbeat_loop(self):
        """
        Main heartbeat loop untuk connection health monitoring.
        Jalan di background buat maintain connection stability.

        Process:
        1. Sleep setiap interval (30 detik)
        2. Send ping ke semua active connections
        3. Detect dan cleanup stale connections
        4. Update connection metadata

        Health checks:
        - Connection timeout detection
        - Ping/pong response monitoring
        - Stale connection cleanup
        - Error recovery

        Auto-cleanup:
        - No activity > 2x heartbeat interval = stale
        - Failed ping = connection problem
        - Auto remove stale connections
        - Graceful connection cleanup

        Performance:
        - Low impact background task
        - Non-blocking operation
        - Efficient connection monitoring
        """
        logger.info("Starting WebSocket heartbeat loop")

        while self.active_connections:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                await self._send_heartbeat()
            except asyncio.CancelledError:
                logger.info("Heartbeat loop cancelled")
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

        logger.info("Heartbeat loop ended")

    async def _send_heartbeat(self):
        """Send ping to all active connections and remove stale ones."""
        ping_time = time.time()
        stale_connections = []

        for user_id, websocket in list(self.active_connections.items()):
            try:
                # Check if connection is stale (no activity for 2x heartbeat interval)
                if user_id in self.connection_metadata:
                    last_activity = self.connection_metadata[user_id]["last_activity"]
                    if ping_time - last_activity > (self._heartbeat_interval * 2):
                        stale_connections.append(user_id)
                        continue

                # Send ping
                await websocket.send_text(json.dumps({"type": "ping", "timestamp": ping_time}))

                # Update metadata
                if user_id in self.connection_metadata:
                    self.connection_metadata[user_id]["last_ping"] = ping_time

            except Exception as e:
                logger.warning(f"Heartbeat failed for user {user_id}: {e}")
                stale_connections.append(user_id)

        # Clean up stale connections
        for user_id in stale_connections:
            await self.disconnect(user_id)

    def get_metrics(self) -> dict:
        """
        Generate comprehensive WebSocket performance metrics.
        Monitoring dashboard data buat system health.

        Returns:
            Dictionary dengan semua performance metrics

        Metrics categories:
        - Active connections: Current user count
        - Connection stats: Total connections, success rate
        - Performance: Response time, message delivery
        - Health: Average connection duration, heartbeat status

        Calculated metrics:
        - Success rate: (sent / (sent + failed)) * 100
        - Average duration: Total connection time / session count
        - Response time: Average broadcast processing time

        Dashboard usage:
            metrics = manager.get_metrics()
            return {
                "active_users": metrics["active_connections"],
                "success_rate": f"{metrics['success_rate']:.1f}%",
                "avg_response": f"{metrics['avg_response_time_ms']}ms"
            }

        Performance monitoring:
        - Real-time connection tracking
        - Message delivery reliability
        - System performance indicators
        - User engagement metrics
        """
        active_connections = len(self.active_connections)

        # Calculate average connection duration
        if self.metrics["connection_duration"]:
            total_duration = sum(sum(durations) for durations in self.metrics["connection_duration"].values())
            total_sessions = sum(len(durations) for durations in self.metrics["connection_duration"].values())
            avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
        else:
            avg_duration = 0

        return {
            "active_connections": active_connections,
            "total_connections": self.metrics["total_connections"],
            "messages_sent": self.metrics["messages_sent"],
            "messages_failed": self.metrics["messages_failed"],
            "success_rate": (
                self.metrics["messages_sent"] / (self.metrics["messages_sent"] + self.metrics["messages_failed"]) * 100
                if (self.metrics["messages_sent"] + self.metrics["messages_failed"]) > 0
                else 100
            ),
            "avg_response_time_ms": round(self.metrics["avg_response_time"] * 1000, 2),
            "avg_connection_duration_min": round(avg_duration / 60, 2),
            "heartbeat_interval_s": self._heartbeat_interval,
        }

    async def cleanup(self):
        """
        Graceful shutdown buat WebSocket manager.
        Cleanup semua resources saat aplikasi stop.

        Process:
        1. Cancel heartbeat task
        2. Close semua active connections
        3. Clear semua data structures
        4. Log shutdown completion

        Graceful shutdown:
        - Notify clients tentang server shutdown
        - Close connections dengan proper codes
        - Cancel background tasks
        - Memory cleanup

        Usage in FastAPI shutdown event:
            @app.on_event("shutdown")
            async def shutdown():
                await manager.cleanup()

        Safety:
        - Prevent resource leaks
        - Proper task cancellation
        - Client notification
        - Complete cleanup
        """
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for user_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[user_id].close(code=1001, reason="Server shutdown")
            except Exception:
                pass

        self.active_connections.clear()
        self.connection_metadata.clear()
        self.user_roles.clear()
        logger.info("WebSocket manager cleaned up")


# Global singleton instance - dipake di seluruh aplikasi
# Ini penting buat maintain consistency dan prevent multiple connection managers
manager = ConnectionManager()

"""
Cara pakai WebSocket manager:

from app.websocket_manager import manager

# Di WebSocket endpoint
@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Authenticate user dulu
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    # Connect user
    await manager.connect(websocket, user.id)

    try:
        while True:
            # Handle WebSocket messages
            data = await websocket.receive_text()
            # Process client messages...
    except WebSocketDisconnect:
        await manager.disconnect(user.id)

# Kirim notification dari background process
await manager.send_to_user(
    user_id=123,
    message={
        "type": "payment_received",
        "message": "Payment confirmed for INV-001",
        "data": {"invoice_id": 1, "amount": 150000}
    }
)

# Broadcast ke multiple users
await manager.broadcast_to_roles(
    message={"type": "system_alert", "message": "Maintenance in 5 minutes"},
    user_ids=[1, 2, 3, 4, 5]
)
"""

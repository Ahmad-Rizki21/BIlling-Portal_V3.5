# app/routers/notifications.py

from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_user_from_token
from ..database import get_db
from ..websocket_manager import manager

router = APIRouter(tags=["Notifications"])


@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
):
    try:
        user = await get_user_from_token(token=token, db=db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
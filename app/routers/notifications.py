# app/routers/notifications.py

import logging
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_user_from_token
from ..models.user import User as UserModel
from ..websocket_manager import manager

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notifications"])

# Test endpoint untuk memastikan router terdaftar
@router.get("/test-websocket")
async def test_websocket():
    return {"message": "WebSocket router is working", "status": "ok"}

@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"WebSocket connection attempt with token: {token[:20]}...")
    
    try:
        # Authenticate user
        user = await get_user_from_token(token=token, db=db)
        if not user:
            logger.warning("WebSocket authentication failed: Invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # logger.info(f"User authenticated: {user.username} (ID: {user.id})")
        logger.info(f"User authenticated: {user.name} (ID: {user.id})")

    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user.id
    
    try:
        # Accept WebSocket connection
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connected successfully for user {user_id}")
        
        # Keep connection alive
        while True:
            try:
                # Receive any message (ping/pong or actual data)
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
                # Handle other messages if needed
                logger.debug(f"Received message from user {user_id}: {message}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop for user {user_id}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {str(e)}")
    finally:
        manager.disconnect(user_id)
        logger.info(f"WebSocket connection cleanup completed for user {user_id}")
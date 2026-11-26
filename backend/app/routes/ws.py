"""WebSocket: live prices for everyone, live events for a class room."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import read_token
from app.core.ws_manager import manager
from app.database import SessionLocal
from app.market.feed import feed
from app.models import ClassSession, User
from app.services import classroom_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(socket: WebSocket, token: str = "", class_id: int | None = None):
    """Connect with ?token=...  Add &class_id=5 to join the room of class 5."""
    with SessionLocal() as db:
        user_id = read_token(token)
        user = db.get(User, user_id) if user_id else None
        allowed = user is not None and user.is_active
        if allowed and class_id is not None:
            session = db.get(ClassSession, class_id)
            allowed = session is not None and classroom_service.can_view(db, session, user)
    if not allowed:
        await socket.close(code=4401)
        return

    await manager.connect(socket, user_id, class_id)
    if class_id is None:
        await socket.send_json(feed.snapshot())  # show prices straight away
    try:
        while True:
            await socket.receive_text()  # we only listen to know when it closes
    except WebSocketDisconnect:
        manager.disconnect(socket)

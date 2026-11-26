"""AI advisor: ask for trade ideas, and see earlier ideas."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.security import require_roles
from app.database import get_db
from app.models import AiSuggestion, User
from app.services import advisor_service

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.post("/suggestions")
def new_suggestions(user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    return advisor_service.get_suggestions(db, user)


@router.get("/suggestions")
def old_suggestions(user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    rows = db.query(AiSuggestion).filter_by(user_id=user.id).order_by(AiSuggestion.id.desc()).limit(20).all()
    return [
        {
            "id": r.id, "symbol": r.symbol, "side": r.side, "quantity": r.quantity, "stop_loss": r.stop_loss,
            "outlook": r.outlook, "reason": r.reason, "confidence": r.confidence, "source": r.source,
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]

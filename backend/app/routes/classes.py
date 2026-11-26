"""Live classes: the trader teaches, students watch and ask."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.security import get_current_user, require_roles
from app.core.ws_manager import manager
from app.database import get_db
from app.models import ClassMember, ClassSession, StudentNote, User
from app.schemas.classroom import ClassIn, JoinIn, NoteIn, TextIn
from app.services import classroom_service as svc
from app.services.classroom_service import ClassError

router = APIRouter(tags=["classes"])


def load_class(db: Session, class_id: int, user: User, owner_only: bool = False) -> ClassSession:
    """Find a class and check that this user is allowed to see (or run) it."""
    try:
        session = svc.get_class(db, class_id)
    except ClassError as error:
        raise HTTPException(404, str(error)) from None
    if owner_only and session.trader_id != user.id:
        raise HTTPException(403, "Only the trader who made this class can do that")
    if not svc.can_view(db, session, user):
        raise HTTPException(403, "Join this class with its code first")
    return session


@router.post("/classes")
def create_class(data: ClassIn, user: User = Depends(require_roles(c.TRADER)), db: Session = Depends(get_db)):
    try:
        session = svc.create_class(db, user, data.title, [s.upper() for s in data.symbols])
    except ClassError as error:
        raise HTTPException(400, str(error)) from None
    return svc.class_to_dict(db, session)


@router.get("/classes")
def list_classes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(ClassSession)
    if user.role == c.TRADER:
        query = query.filter_by(trader_id=user.id)
    elif user.role == c.STUDENT:
        joined = [m.class_id for m in db.query(ClassMember).filter_by(user_id=user.id).all()]
        query = query.filter(ClassSession.id.in_(joined))
    return [svc.class_to_dict(db, s) for s in query.order_by(ClassSession.id.desc()).all()]


@router.post("/classes/join")
def join_class(data: JoinIn, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    try:
        session = svc.join_class(db, user, data.code)
    except ClassError as error:
        raise HTTPException(404, str(error)) from None
    return svc.class_to_dict(db, session)


@router.get("/classes/{class_id}")
def class_detail(class_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = load_class(db, class_id, user)
    return svc.class_detail(db, session, user)


async def change_status(class_id: int, status: str, user: User, db: Session):
    session = load_class(db, class_id, user, owner_only=True)
    try:
        svc.set_status(db, session, status)
    except ClassError as error:
        raise HTTPException(400, str(error)) from None
    await manager.send_class(class_id, {"type": "status", "status": status})
    return svc.class_to_dict(db, session)


@router.post("/classes/{class_id}/start")
async def start_class(class_id: int, user: User = Depends(require_roles(c.TRADER)), db: Session = Depends(get_db)):
    return await change_status(class_id, c.LIVE, user, db)


@router.post("/classes/{class_id}/end")
async def end_class(class_id: int, user: User = Depends(require_roles(c.TRADER)), db: Session = Depends(get_db)):
    return await change_status(class_id, c.ENDED, user, db)


@router.post("/classes/{class_id}/notes")
async def post_note(class_id: int, data: NoteIn, user: User = Depends(require_roles(c.TRADER)), db: Session = Depends(get_db)):
    session = load_class(db, class_id, user, owner_only=True)
    try:
        note = svc.add_note(db, session, data.text, data.symbol.upper() if data.symbol else None, data.kind)
    except ClassError as error:
        raise HTTPException(400, str(error)) from None
    note_data = svc.note_to_dict(note)
    await manager.send_class(class_id, {"type": "note", "note": note_data})
    return note_data


@router.post("/classes/{class_id}/questions")
async def ask_question(class_id: int, data: TextIn, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    session = load_class(db, class_id, user)
    question = svc.question_to_dict(db, svc.add_question(db, session, user, data.text))
    await manager.send_class(class_id, {"type": "question", "question": question})
    return question


@router.post("/questions/{question_id}/answer")
async def answer_question(question_id: int, data: TextIn, user: User = Depends(require_roles(c.TRADER)), db: Session = Depends(get_db)):
    try:
        question = svc.answer_question(db, user, question_id, data.text)
    except ClassError as error:
        raise HTTPException(400, str(error)) from None
    result = svc.question_to_dict(db, question)
    await manager.send_class(question.class_id, {"type": "answer", "question": result})
    return result


@router.post("/classes/{class_id}/my-notes")
def add_my_note(class_id: int, data: TextIn, user: User = Depends(require_roles(c.STUDENT)), db: Session = Depends(get_db)):
    load_class(db, class_id, user)
    db.add(StudentNote(class_id=class_id, user_id=user.id, text=data.text))
    db.commit()
    return {"ok": True}


@router.get("/classes/{class_id}/replay")
def replay(class_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = load_class(db, class_id, user)
    return svc.replay_data(db, session)

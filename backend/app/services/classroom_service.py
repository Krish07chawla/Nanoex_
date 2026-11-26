"""Live classes: create, start, end, notes, questions, replay."""

import random
import string

from sqlalchemy.orm import Session

from app.core import constants as c
from app.core.clock import utcnow
from app.market.feed import feed
from app.market.universe import STOCKS
from app.models import (
    ClassMember,
    ClassNote,
    ClassQuestion,
    ClassSession,
    PriceTick,
    StudentNote,
    User,
)


class ClassError(Exception):
    """A normal "you cannot do that" problem. The message is shown to the user."""


def iso(moment) -> str | None:
    return moment.isoformat() + "Z" if moment else None


def make_code(db: Session) -> str:
    """A random 6-letter join code that is not used yet."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=6))
        if not db.query(ClassSession).filter_by(code=code).first():
            return code


def create_class(db: Session, trader: User, title: str, symbols: list[str]) -> ClassSession:
    for symbol in symbols:
        if symbol not in STOCKS:
            raise ClassError(f"Unknown stock {symbol}")
    session = ClassSession(trader_id=trader.id, title=title, code=make_code(db), symbols=",".join(symbols))
    db.add(session)
    db.commit()
    return session


def get_class(db: Session, class_id: int) -> ClassSession:
    session = db.get(ClassSession, class_id)
    if session is None:
        raise ClassError("Class not found")
    return session


def can_view(db: Session, session: ClassSession, user: User) -> bool:
    """The owner trader, an admin, or a student who joined."""
    if user.role == c.ADMIN or session.trader_id == user.id:
        return True
    return db.query(ClassMember).filter_by(class_id=session.id, user_id=user.id).first() is not None


def set_status(db: Session, session: ClassSession, status: str):
    if status == c.LIVE and session.status != c.SCHEDULED:
        raise ClassError("Only a waiting class can be started")
    if status == c.ENDED and session.status != c.LIVE:
        raise ClassError("Only a live class can be ended")
    session.status = status
    if status == c.LIVE:
        session.started_at = utcnow()
    else:
        session.ended_at = utcnow()
    db.commit()


def join_class(db: Session, student: User, code: str) -> ClassSession:
    session = db.query(ClassSession).filter_by(code=code.upper()).first()
    if session is None:
        raise ClassError("No class with that code")
    if not db.query(ClassMember).filter_by(class_id=session.id, user_id=student.id).first():
        db.add(ClassMember(class_id=session.id, user_id=student.id))
        db.commit()
    return session


def add_note(db: Session, session: ClassSession, text: str, symbol: str | None, kind: str) -> ClassNote:
    if session.status != c.LIVE:
        raise ClassError("Notes can only be posted while the class is live")
    if symbol and symbol not in session.symbols.split(","):
        raise ClassError("That stock is not part of this class")
    note = ClassNote(class_id=session.id, symbol=symbol, kind=kind, text=text, price=feed.price(symbol) if symbol else None)
    db.add(note)
    db.commit()
    return note


def add_question(db: Session, session: ClassSession, student: User, text: str) -> ClassQuestion:
    question = ClassQuestion(class_id=session.id, student_id=student.id, text=text)
    db.add(question)
    db.commit()
    return question


def answer_question(db: Session, trader: User, question_id: int, text: str) -> ClassQuestion:
    question = db.get(ClassQuestion, question_id)
    if question is None:
        raise ClassError("Question not found")
    session = get_class(db, question.class_id)
    if session.trader_id != trader.id:
        raise ClassError("Only the class trader can answer")
    question.answer = text
    question.answered_at = utcnow()
    db.commit()
    return question


def save_ticks(db: Session, prices: dict):
    """Called on every price update. Saves prices for classes that are live."""
    for session in db.query(ClassSession).filter_by(status=c.LIVE).all():
        for symbol in session.symbols.split(","):
            quote = prices.get(symbol)
            if quote:
                db.add(PriceTick(class_id=session.id, symbol=symbol, price=quote["price"]))
    db.commit()


# ---------- turning rows into dictionaries for the API ----------


def note_to_dict(note: ClassNote) -> dict:
    return {
        "id": note.id,
        "symbol": note.symbol,
        "kind": note.kind,
        "text": note.text,
        "price": note.price,
        "created_at": iso(note.created_at),
    }


def question_to_dict(db: Session, question: ClassQuestion) -> dict:
    student = db.get(User, question.student_id)
    return {
        "id": question.id,
        "student": student.name if student else "?",
        "text": question.text,
        "answer": question.answer,
        "created_at": iso(question.created_at),
    }


def class_to_dict(db: Session, session: ClassSession) -> dict:
    trader = db.get(User, session.trader_id)
    return {
        "id": session.id,
        "title": session.title,
        "code": session.code,
        "symbols": session.symbols.split(","),
        "status": session.status,
        "trader": trader.name if trader else "?",
        "trader_id": session.trader_id,
        "students": db.query(ClassMember).filter_by(class_id=session.id).count(),
        "started_at": iso(session.started_at),
        "ended_at": iso(session.ended_at),
    }


def class_detail(db: Session, session: ClassSession, user: User) -> dict:
    notes = db.query(ClassNote).filter_by(class_id=session.id).order_by(ClassNote.id).all()
    questions = db.query(ClassQuestion).filter_by(class_id=session.id).order_by(ClassQuestion.id).all()
    my_notes = db.query(StudentNote).filter_by(class_id=session.id, user_id=user.id).order_by(StudentNote.id).all()
    data = class_to_dict(db, session)
    data["notes"] = [note_to_dict(n) for n in notes]
    data["questions"] = [question_to_dict(db, q) for q in questions]
    data["my_notes"] = [{"id": n.id, "text": n.text, "created_at": iso(n.created_at)} for n in my_notes]
    return data


def replay_data(db: Session, session: ClassSession) -> dict:
    ticks = db.query(PriceTick).filter_by(class_id=session.id).order_by(PriceTick.id).all()
    notes = db.query(ClassNote).filter_by(class_id=session.id).order_by(ClassNote.id).all()
    return {
        "class": class_to_dict(db, session),
        "ticks": [{"symbol": t.symbol, "price": t.price, "time": iso(t.created_at)} for t in ticks],
        "notes": [note_to_dict(n) for n in notes],
    }

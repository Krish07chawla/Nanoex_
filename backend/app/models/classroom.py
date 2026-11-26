"""Tables for live classes: sessions, members, notes, questions, saved prices."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.clock import utcnow
from app.database import Base


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True)
    trader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    code = Column(String(6), unique=True, nullable=False)  # students join with this
    symbols = Column(String(200), nullable=False)  # "TCS,INFY,RELIANCE"
    status = Column(String(10), default="SCHEDULED")  # SCHEDULED, LIVE, ENDED
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class ClassMember(Base):
    """A student who joined a class."""

    __tablename__ = "class_members"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class ClassNote(Base):
    """A note or buy/sell idea posted by the trader during the class."""

    __tablename__ = "class_notes"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=True)
    kind = Column(String(10), default="NOTE")  # NOTE, BUY_IDEA, SELL_IDEA
    text = Column(Text, nullable=False)
    price = Column(Float, nullable=True)  # price at the moment of the note
    created_at = Column(DateTime, default=utcnow)


class ClassQuestion(Base):
    __tablename__ = "class_questions"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    answered_at = Column(DateTime, nullable=True)


class StudentNote(Base):
    """A private note a student writes for themselves in a class."""

    __tablename__ = "student_notes"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class PriceTick(Base):
    """Prices saved while a class is live, so the class can be replayed later."""

    __tablename__ = "price_ticks"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("class_sessions.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utcnow)

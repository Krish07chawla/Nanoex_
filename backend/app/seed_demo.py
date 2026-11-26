"""Optional: makes a demo trader and two demo students with virtual money.

Run from the backend folder:   python -m app.seed_demo
"""

from app.core import constants as c
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User
from app.services import wallet_service

DEMO_USERS = [
    ("Demo Trader", "trader@demo.in", c.TRADER),
    ("Demo Student One", "student1@demo.in", c.STUDENT),
    ("Demo Student Two", "student2@demo.in", c.STUDENT),
]


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for name, email, role in DEMO_USERS:
            if db.query(User).filter_by(email=email).first():
                continue
            user = User(name=name, email=email, password_hash=hash_password("Demo1234"), role=role)
            db.add(user)
            db.flush()
            wallet_service.get_wallet(db, user.id)
            if role == c.STUDENT:
                wallet_service.change_balance(db, user.id, 100000, c.ADMIN_CREDIT, "Demo starting money")
        db.commit()
    print("Demo users ready. Password for all: Demo1234")


if __name__ == "__main__":
    main()

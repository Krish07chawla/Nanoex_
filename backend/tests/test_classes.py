from app.database import SessionLocal
from app.services import classroom_service
from tests.conftest import register


def make_class(client, trader):
    reply = client.post("/api/classes", json={"title": "Banking stocks", "symbols": ["HDFCBANK", "SBIN"]}, headers=trader["headers"])
    assert reply.status_code == 200, reply.text
    return reply.json()


def test_only_traders_can_create_classes(client):
    student = register(client, "Asha")
    reply = client.post("/api/classes", json={"title": "Hello", "symbols": ["TCS"]}, headers=student["headers"])
    assert reply.status_code == 403


def test_full_class_flow(client):
    trader = register(client, "Tara", "TRADER")
    student = register(client, "Asha")
    session = make_class(client, trader)
    assert session["status"] == "SCHEDULED" and len(session["code"]) == 6

    # the student joins with the code
    joined = client.post("/api/classes/join", json={"code": session["code"]}, headers=student["headers"])
    assert joined.json()["id"] == session["id"]

    # notes only work while the class is live
    note = {"text": "Banks look strong today", "symbol": "SBIN", "kind": "BUY_IDEA"}
    assert client.post(f"/api/classes/{session['id']}/notes", json=note, headers=trader["headers"]).status_code == 400
    client.post(f"/api/classes/{session['id']}/start", headers=trader["headers"])
    posted = client.post(f"/api/classes/{session['id']}/notes", json=note, headers=trader["headers"])
    assert posted.json()["price"] == 850.0  # price at the moment of the note

    # question and answer
    asked = client.post(f"/api/classes/{session['id']}/questions", json={"text": "What is RSI?"}, headers=student["headers"])
    answered = client.post(f"/api/questions/{asked.json()['id']}/answer", json={"text": "A momentum number."}, headers=trader["headers"])
    assert answered.json()["answer"] == "A momentum number."

    # the student's private note, then the whole class page
    client.post(f"/api/classes/{session['id']}/my-notes", json={"text": "revise RSI"}, headers=student["headers"])
    detail = client.get(f"/api/classes/{session['id']}", headers=student["headers"]).json()
    assert len(detail["notes"]) == 1 and len(detail["questions"]) == 1 and len(detail["my_notes"]) == 1

    client.post(f"/api/classes/{session['id']}/end", headers=trader["headers"])
    assert client.get("/api/classes", headers=student["headers"]).json()[0]["status"] == "ENDED"


def test_student_cannot_open_a_class_without_joining(client):
    trader = register(client, "Tara", "TRADER")
    outsider = register(client, "Ravi")
    session = make_class(client, trader)
    assert client.get(f"/api/classes/{session['id']}", headers=outsider["headers"]).status_code == 403


def test_other_trader_cannot_run_my_class(client):
    trader = register(client, "Tara", "TRADER")
    other = register(client, "Omar", "TRADER")
    session = make_class(client, trader)
    assert client.post(f"/api/classes/{session['id']}/start", headers=other["headers"]).status_code == 403


def test_wrong_code_is_rejected(client):
    student = register(client, "Asha")
    assert client.post("/api/classes/join", json={"code": "ZZZZZZ"}, headers=student["headers"]).status_code == 404


def test_prices_are_saved_for_replay_while_live(client):
    trader = register(client, "Tara", "TRADER")
    session = make_class(client, trader)
    client.post(f"/api/classes/{session['id']}/start", headers=trader["headers"])
    with SessionLocal() as db:
        classroom_service.save_ticks(db, {"SBIN": {"price": 851.0}, "TCS": {"price": 1.0}})
    replay = client.get(f"/api/classes/{session['id']}/replay", headers=trader["headers"]).json()
    assert [t["symbol"] for t in replay["ticks"]] == ["SBIN"]  # TCS is not part of this class

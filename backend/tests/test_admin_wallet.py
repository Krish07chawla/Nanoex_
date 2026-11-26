from tests.conftest import admin_login, register, rich_student


def test_admin_sends_money_and_student_sees_it(client):
    student = rich_student(client, "Asha", 50000)
    wallet = client.get("/api/wallet", headers=student["headers"]).json()
    assert wallet["balance"] == 50000
    assert wallet["capital"] == 50000
    assert wallet["transactions"][0]["kind"] == "ADMIN_CREDIT"


def test_admin_can_send_to_all_students(client):
    one = register(client, "Asha")
    two = register(client, "Ravi")
    reply = client.post(
        "/api/admin/wallet", json={"kind": "CREDIT", "amount": 1000, "all_students": True}, headers=admin_login(client)
    )
    assert reply.json()["students"] == 2
    assert client.get("/api/wallet", headers=one["headers"]).json()["balance"] == 1000
    assert client.get("/api/wallet", headers=two["headers"]).json()["balance"] == 1000


def test_admin_cannot_take_back_more_than_balance(client):
    student = rich_student(client, "Asha", 1000)
    reply = client.post(
        "/api/admin/wallet",
        json={"kind": "DEBIT", "amount": 5000, "user_ids": [student["id"]]},
        headers=admin_login(client),
    )
    assert reply.status_code == 400
    assert client.get("/api/wallet", headers=student["headers"]).json()["balance"] == 1000


def test_student_cannot_send_money(client):
    student = register(client, "Asha")
    reply = client.post(
        "/api/admin/wallet", json={"kind": "CREDIT", "amount": 99, "user_ids": [student["id"]]}, headers=student["headers"]
    )
    assert reply.status_code == 403


def test_money_actions_are_in_the_audit_log(client):
    rich_student(client, "Asha", 2000)
    audit = client.get("/api/admin/audit", headers=admin_login(client)).json()
    assert audit[0]["action"] == "ADMIN_CREDIT"


def test_admin_sees_student_account_details(client):
    student = rich_student(client, "Asha", 2000)
    detail = client.get(f"/api/admin/users/{student['id']}", headers=admin_login(client)).json()
    assert detail["portfolio"]["cash"] == 2000
    assert detail["transactions"][0]["amount"] == 2000

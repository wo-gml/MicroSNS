"""실제 MySQL에서 확인하는 테스트. TEST_DB_USER를 지정해야 실행됩니다."""

from threading import Barrier, Thread

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.db import connect, transaction
from app.deps import DbConn, LoginUser
from app.main import create_app
from app.security import AUTH_COOKIE_NAME, create_access_token, hash_password


def scalar(conn, sql, args=None):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return next(iter(cur.fetchone().values()))


def execute(conn, sql, args=None):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


def add_member(conn, email="a@example.com"):
    return execute(
        conn,
        "INSERT INTO member (email, password_hash, name) VALUES (%s, %s, %s)",
        (email, hash_password("pw"), "회원"),
    )


def add_recruitment(conn, capacity):
    """모집 글 작성자와 글, 모집을 만들고 모집 id를 돌려줍니다."""
    author_id = add_member(conn, "author@example.com")
    post_id = execute(
        conn, "INSERT INTO post (member_id, content) VALUES (%s, '모집')", (author_id,)
    )
    return execute(
        conn,
        "INSERT INTO recruitment (post_id, type, capacity, deadline) "
        "VALUES (%s, 'study', %s, NOW(6) + INTERVAL 1 DAY)",
        (post_id, capacity),
    )


def add_application(conn, recruitment_id, n, status="pending"):
    member_id = add_member(conn, f"applicant{n}@example.com")
    return execute(
        conn,
        "INSERT INTO application (recruitment_id, member_id, status) VALUES (%s, %s, %s)",
        (recruitment_id, member_id, status),
    )


@pytest.fixture
def client(db):
    router = APIRouter()

    @router.post("/members")
    def add(email: str, conn: DbConn):
        return {"id": add_member(conn, email)}

    @router.post("/test-posts")
    def add_post(member_id: int, content: str, conn: DbConn):
        execute(
            conn,
            "INSERT INTO post (member_id, content) VALUES (%s, %s)",
            (member_id, content),
        )

    @router.post("/follows")
    def add_follow(a: int, b: int, conn: DbConn):
        execute(conn, "INSERT INTO follow (follower_id, following_id) VALUES (%s, %s)", (a, b))

    @router.delete("/members/{member_id}")
    def remove(member_id: int, conn: DbConn):
        execute(conn, "DELETE FROM member WHERE id = %s", (member_id,))

    @router.get("/me")
    def me(user: LoginUser):
        return user

    app = create_app()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_connection_time_zone_is_fixed(db):
    assert scalar(db, "SELECT @@session.time_zone") == "+09:00"


def test_korean_and_emoji_round_trip(db):
    member_id = execute(
        db,
        "INSERT INTO member (email, password_hash, name) VALUES ('k@e.com', 'x', %s)",
        ("김민수😀",),
    )
    assert scalar(db, "SELECT name FROM member WHERE id = %s", (member_id,)) == "김민수😀"


def test_single_statement_is_saved_without_explicit_commit(db):
    member_id = add_member(db)
    other = connect()
    try:
        assert scalar(other, "SELECT COUNT(*) FROM member WHERE id = %s", (member_id,)) == 1
    finally:
        other.close()


def test_transaction_commits_all_statements(db):
    with transaction(db):
        member_id = add_member(db)
        execute(db, "INSERT INTO post (member_id, content) VALUES (%s, 'hi')", (member_id,))
    assert scalar(db, "SELECT COUNT(*) FROM post") == 1


def test_transaction_rolls_back_all_statements_on_error(db):
    with pytest.raises(RuntimeError):
        with transaction(db):
            add_member(db)
            raise RuntimeError("실패")
    assert scalar(db, "SELECT COUNT(*) FROM member") == 0


def test_autocommit_is_restored_after_transaction(db):
    with transaction(db):
        add_member(db, "first@example.com")
    add_member(db, "second@example.com")
    other = connect()
    try:
        assert scalar(other, "SELECT COUNT(*) FROM member") == 2
    finally:
        other.close()


def test_lock_sees_data_committed_after_an_earlier_read(db):
    """로그인 확인처럼 먼저 읽은 쿼리가 있어도 트랜잭션은 최신 데이터를 봐야 합니다."""
    recruitment_id = add_recruitment(db, 1)
    assert scalar(db, "SELECT COUNT(*) FROM application") == 0

    other = connect()
    try:
        add_application(other, recruitment_id, 1, status="accepted")
    finally:
        other.close()

    with transaction(db):
        scalar(db, "SELECT capacity FROM recruitment WHERE id = %s FOR UPDATE", (recruitment_id,))
        assert scalar(db, "SELECT COUNT(*) FROM application WHERE status = 'accepted'") == 1


def test_row_lock_prevents_exceeding_capacity_under_concurrency(db):
    recruitment_id = add_recruitment(db, 2)
    application_ids = [add_application(db, recruitment_id, n) for n in range(8)]
    barrier = Barrier(len(application_ids))
    failures = []

    def approve(application_id):
        try:
            conn = connect()
            try:
                barrier.wait()
                with transaction(conn):
                    capacity = scalar(
                        conn,
                        "SELECT capacity FROM recruitment WHERE id = %s FOR UPDATE",
                        (recruitment_id,),
                    )
                    approved = scalar(
                        conn,
                        "SELECT COUNT(*) FROM application "
                        "WHERE recruitment_id = %s AND status = 'accepted'",
                        (recruitment_id,),
                    )
                    if approved < capacity:
                        execute(
                            conn,
                            "UPDATE application SET status = 'accepted' WHERE id = %s",
                            (application_id,),
                        )
            finally:
                conn.close()
        except Exception as exc:  # 스레드 예외는 pytest가 잡지 못하므로 모아서 확인합니다.
            failures.append(exc)

    threads = [Thread(target=approve, args=(i,)) for i in application_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert failures == []
    assert scalar(db, "SELECT COUNT(*) FROM application WHERE status = 'accepted'") == 2


def test_duplicate_row_returns_409(client):
    assert client.post("/members", params={"email": "d@e.com"}).status_code == 200
    response = client.post("/members", params={"email": "d@e.com"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_missing_foreign_key_target_returns_404(client):
    response = client.post("/test-posts", params={"member_id": 999, "content": "hi"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_check_constraint_returns_400(client):
    response = client.post("/follows", params={"a": 1, "b": 1})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


def test_too_long_value_returns_400(client, db):
    member_id = add_member(db)
    response = client.post("/test-posts", params={"member_id": member_id, "content": "x" * 501})
    assert response.status_code == 400


def test_deleting_referenced_row_returns_409(client, db):
    member_id = add_member(db)
    execute(db, "INSERT INTO post (member_id, content) VALUES (%s, 'hi')", (member_id,))
    assert client.delete(f"/members/{member_id}").status_code == 409


def test_login_user_is_loaded_without_password_hash(client, db):
    member_id = add_member(db)
    client.cookies.set(AUTH_COOKIE_NAME, create_access_token(member_id))
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json()["id"] == member_id
    assert "password_hash" not in response.text

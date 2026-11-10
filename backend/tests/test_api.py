"""API를 실제 MySQL(microsns_test)에 연결해 확인하는 테스트. TEST_DB_USER를 지정해야 실행됩니다.

테스트마다 테이블을 비우고(conftest.py의 db), 필요한 회원과 글을 직접 만듭니다.
"""

from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import AUTH_COOKIE_NAME, create_access_token

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def sql(db, statement, args=None):
    with db.cursor() as cur:
        cur.execute(statement, args)
        return cur.lastrowid


@pytest.fixture
def client(db):
    return TestClient(create_app())


@pytest.fixture
def member(db):
    """회원을 만들고 id를 돌려줍니다. 로그인은 login_as로 합니다(비밀번호 해싱을 건너뜀)."""
    count = 0

    def make(name):
        nonlocal count
        count += 1
        return sql(
            db,
            "INSERT INTO member (email, password_hash, name) VALUES (%s, 'x', %s)",
            (f"m{count}@test.com", name),
        )

    return make


def login_as(client, member_id):
    client.cookies.clear()  # 지우지 않으면 이전 쿠키와 함께 두 개가 전송됩니다.
    client.cookies.set(AUTH_COOKIE_NAME, create_access_token(member_id))


def later(**delta):
    return (datetime.now(timezone.utc) + timedelta(**delta)).isoformat()


def write_post(client, content="글", **body):
    response = client.post("/posts", json={"content": content, **body})
    assert response.status_code == 201, response.text
    return response.json()


def write_recruitment(client, capacity=2, content="같이 공부해요"):
    recruitment = {"type": "study", "capacity": capacity, "deadline": later(days=1)}
    return write_post(client, content, recruitment=recruitment)["recruitment"]


def notification_types(client, member_id):
    login_as(client, member_id)
    return [n["type"] for n in client.get("/notifications").json()["items"]]


# 인증


def test_signup_then_login_sets_http_only_cookie_and_hides_password(client):
    body = {"email": "New@test.com", "password": "password1", "name": " 새회원 "}
    signup = client.post("/auth/signup", json=body)
    assert signup.status_code == 201
    assert signup.json()["name"] == "새회원"
    assert "password" not in signup.text

    client.post("/auth/logout")
    login = client.post("/auth/login", json={"email": "new@test.com", "password": "password1"})
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    assert client.get("/auth/me").json()["id"] == signup.json()["id"]


def test_duplicate_email_is_rejected_regardless_of_case(client):
    body = {"email": "dup@test.com", "password": "password1", "name": "회원"}
    assert client.post("/auth/signup", json=body).status_code == 201
    duplicate = client.post("/auth/signup", json={**body, "email": "DUP@test.com"})
    assert duplicate.status_code == 409


def test_wrong_password_returns_401(client):
    body = {"email": "a@test.com", "password": "password1", "name": "회원"}
    client.post("/auth/signup", json=body)
    response = client.post("/auth/login", json={"email": "a@test.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_logout_clears_login(client):
    body = {"email": "a@test.com", "password": "password1", "name": "회원"}
    client.post("/auth/signup", json=body)
    assert client.get("/auth/me").status_code == 200
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_invalid_cookie_is_anonymous_on_public_routes(client, member):
    login_as(client, member("작성자"))
    post = write_post(client)
    client.cookies.clear()
    client.cookies.set(AUTH_COOKIE_NAME, "invalid")
    assert client.get(f"/posts/{post['id']}").json()["liked_by_me"] is False
    assert client.get("/auth/me").status_code == 401


# 게시글


def test_post_round_trip_keeps_images_hashtags_recruitment_and_time(client, member):
    me = member("김민준")
    login_as(client, me)
    deadline = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=3)
    post = write_post(
        client,
        "  같이 해요 #SQL #스터디 #sql  ",
        image_urls=["/api/uploads/b.png", "/api/uploads/a.png"],
        recruitment={"type": "project", "capacity": 3, "deadline": deadline.isoformat()},
    )

    assert post["content"] == "같이 해요 #SQL #스터디 #sql"
    assert post["author"] == {"id": me, "name": "김민준", "is_following": False}
    assert post["image_urls"] == ["/api/uploads/b.png", "/api/uploads/a.png"]
    assert post["like_count"] == 0 and post["comment_count"] == 0
    recruitment = post["recruitment"]
    assert recruitment["status"] == "open" and recruitment["accepted_count"] == 0
    assert recruitment["my_application"] is None
    # DB에는 +09:00 기준으로 저장되지만 돌려받은 시각은 보낸 시각과 같아야 합니다.
    assert datetime.fromisoformat(recruitment["deadline"]) == deadline
    created = datetime.fromisoformat(post["created_at"])
    assert abs(datetime.now(timezone.utc) - created) < timedelta(seconds=10)

    # #SQL과 #sql은 같은 태그입니다.
    assert client.get("/hashtags/sql").json() == {"name": "sql", "post_count": 1}
    assert client.get("/hashtags/스터디/posts").json()["items"][0]["id"] == post["id"]
    assert client.get(f"/posts/{post['id']}").json() == post


@pytest.mark.parametrize(
    "body",
    [
        {"content": "   "},
        {"content": "x" * 501},
        {"content": "글", "image_urls": ["https://evil.example/a.jpg"]},
        {"content": "글", "image_urls": ["/api/mock-photos/a.jpg"]},
        {"content": "글", "image_urls": ["/api/uploads/a.jpg"] * 3},
    ],
)
def test_invalid_post_returns_422(client, member, body):
    login_as(client, member("회원"))
    response = client.post("/posts", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_past_deadline_returns_400(client, member):
    login_as(client, member("회원"))
    recruitment = {"type": "study", "capacity": 1, "deadline": later(days=-1)}
    response = client.post("/posts", json={"content": "글", "recruitment": recruitment})
    assert response.status_code == 400


def test_feed_contains_only_me_and_followed_users(client, member):
    me, followed, stranger = member("나"), member("친구"), member("모르는 사람")
    for author in (me, followed, stranger):
        login_as(client, author)
        write_post(client)
    login_as(client, me)
    client.post(f"/users/{followed}/follow")

    items = client.get("/posts/feed").json()["items"]
    assert [p["author"]["id"] for p in items] == [followed, me]  # 최신순
    assert items[0]["author"]["is_following"] is True


def test_feed_requires_login(client):
    assert client.get("/posts/feed").status_code == 401


def test_pagination_reports_has_more(client, member):
    author = member("작성자")
    login_as(client, author)
    ids = [write_post(client, f"글 {n}")["id"] for n in range(25)]

    first = client.get(f"/users/{author}/posts", params={"limit": 20}).json()
    second = client.get(f"/users/{author}/posts", params={"limit": 20, "offset": 20}).json()
    assert first["has_more"] is True and second["has_more"] is False
    assert [p["id"] for p in first["items"] + second["items"]] == ids[::-1]


def test_deleting_post_removes_everything_attached(client, db, member):
    author, other = member("작성자"), member("다른 회원")
    login_as(client, author)
    post = write_post(client, "#태그", recruitment={"type": "study", "capacity": 1, "deadline": later(days=1)})

    login_as(client, other)
    client.post(f"/posts/{post['id']}/like")
    client.post(f"/posts/{post['id']}/comments", json={"content": "댓글"})
    client.post(f"/recruitments/{post['recruitment']['id']}/applications", json={})
    assert client.delete(f"/posts/{post['id']}").status_code == 403

    login_as(client, author)
    assert len(client.get("/notifications").json()["items"]) == 3
    assert client.delete(f"/posts/{post['id']}").status_code == 204
    assert client.get(f"/posts/{post['id']}").status_code == 404
    assert client.delete(f"/posts/{post['id']}").status_code == 404
    assert client.get("/notifications").json()["items"] == []
    for table in ("comment", "post_like", "post_hashtag", "recruitment", "application"):
        with db.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
            assert cur.fetchone()["n"] == 0, table


# 좋아요, 댓글, 팔로우와 알림


def test_like_is_idempotent_and_notifies_once(client, member):
    author, fan = member("작성자"), member("김민준")
    login_as(client, author)
    post_id = write_post(client)["id"]

    login_as(client, fan)
    assert client.post(f"/posts/{post_id}/like").status_code == 204
    assert client.post(f"/posts/{post_id}/like").status_code == 204
    post = client.get(f"/posts/{post_id}").json()
    assert post["like_count"] == 1 and post["liked_by_me"] is True
    assert client.get(f"/users/{fan}/likes").json()["items"][0]["id"] == post_id

    login_as(client, author)
    notifications = client.get("/notifications").json()["items"]
    assert [n["type"] for n in notifications] == ["like"]
    assert notifications[0]["content"] == "김민준님이 회원님의 글을 좋아합니다."
    assert notifications[0]["actor"] == {"id": fan, "name": "김민준"}

    login_as(client, fan)
    assert client.delete(f"/posts/{post_id}/like").status_code == 204
    assert client.get(f"/posts/{post_id}").json()["like_count"] == 0
    assert notification_types(client, author) == []


def test_liking_own_post_does_not_notify(client, member):
    me = member("나")
    login_as(client, me)
    post_id = write_post(client)["id"]
    client.post(f"/posts/{post_id}/like")
    assert notification_types(client, me) == []


def test_repeating_like_keeps_one_notification(client, member):
    author, fan = member("작성자"), member("팬")
    login_as(client, author)
    post_id = write_post(client)["id"]
    login_as(client, fan)
    for _ in range(3):
        client.post(f"/posts/{post_id}/like")
        client.delete(f"/posts/{post_id}/like")
    client.post(f"/posts/{post_id}/like")
    assert notification_types(client, author) == ["like"]


def test_unlike_without_like_keeps_other_notifications(client, member):
    author, fan, other = member("작성자"), member("팬"), member("다른 회원")
    login_as(client, author)
    post_id = write_post(client)["id"]
    login_as(client, fan)
    client.post(f"/posts/{post_id}/like")
    login_as(client, other)
    assert client.delete(f"/posts/{post_id}/like").status_code == 204
    assert notification_types(client, author) == ["like"]


def test_like_on_missing_post_returns_404(client, member):
    login_as(client, member("회원"))
    assert client.post("/posts/999999/like").status_code == 404


def test_comment_flow_and_delete_permission(client, member):
    author, writer, other = member("작성자"), member("김민준"), member("다른 회원")
    login_as(client, author)
    post_id = write_post(client)["id"]

    login_as(client, writer)
    first = client.post(f"/posts/{post_id}/comments", json={"content": " 참여할게요 "})
    assert first.status_code == 201
    comment = first.json()
    assert comment["author"] == {"id": writer, "name": "김민준"}
    assert comment["content"] == "참여할게요"
    second = client.post(f"/posts/{post_id}/comments", json={"content": "둘째"}).json()

    rows = client.get(f"/posts/{post_id}/comments").json()["items"]
    assert [row["id"] for row in rows] == [comment["id"], second["id"]]  # 작성순
    assert client.get(f"/posts/{post_id}").json()["comment_count"] == 2
    assert notification_types(client, author) == ["comment", "comment"]

    login_as(client, other)
    assert client.delete(f"/comments/{comment['id']}").status_code == 403
    login_as(client, writer)
    assert client.delete(f"/comments/{comment['id']}").status_code == 204
    assert client.delete(f"/comments/{comment['id']}").status_code == 404
    assert notification_types(client, author) == ["comment"]


def test_comment_on_missing_post_returns_404(client, member):
    login_as(client, member("회원"))
    assert client.post("/posts/999999/comments", json={"content": "글"}).status_code == 404
    assert client.get("/posts/999999/comments").status_code == 404


def test_follow_updates_counts_and_rejects_self(client, member):
    me, target = member("나"), member("상대")
    login_as(client, me)
    before = client.get(f"/users/{target}").json()
    assert before["follower_count"] == 0 and before["is_following"] is False

    assert client.post(f"/users/{target}/follow").status_code == 204
    assert client.post(f"/users/{target}/follow").status_code == 204
    after = client.get(f"/users/{target}").json()
    assert after["follower_count"] == 1 and after["is_following"] is True
    assert client.get(f"/users/{me}").json()["following_count"] == 1

    assert client.post(f"/users/{me}/follow").status_code == 400
    assert client.post("/users/999999/follow").status_code == 404
    assert client.get("/users/999999").status_code == 404
    assert client.delete(f"/users/{target}/follow").status_code == 204
    assert client.get(f"/users/{target}").json()["follower_count"] == 0


def test_repeating_follow_keeps_one_notification(client, member):
    me, target = member("나"), member("상대")
    login_as(client, me)
    for _ in range(3):
        client.post(f"/users/{target}/follow")
        client.delete(f"/users/{target}/follow")
    client.post(f"/users/{target}/follow")
    assert notification_types(client, target) == ["follow"]
    assert client.get("/notifications").json()["items"][0]["post_id"] is None


def test_followers_and_following_lists(client, member):
    me, a, b, fan = member("나"), member("가"), member("나나"), member("팬")
    login_as(client, me)
    client.post(f"/users/{a}/follow")
    client.post(f"/users/{b}/follow")
    login_as(client, fan)
    client.post(f"/users/{me}/follow")

    login_as(client, me)
    assert [u["id"] for u in client.get(f"/users/{me}/followers").json()["items"]] == [fan]
    following = client.get(f"/users/{me}/following").json()["items"]
    assert [u["id"] for u in following] == [b, a]  # 최근에 팔로우한 순서
    assert all(u["is_following"] for u in following)


# 모집과 지원


def test_recruitment_applications_are_for_author_only(client, member):
    author, other = member("작성자"), member("다른 회원")
    login_as(client, author)
    recruitment_id = write_recruitment(client)["id"]
    assert client.get(f"/recruitments/{recruitment_id}/applications").status_code == 200
    login_as(client, other)
    assert client.get(f"/recruitments/{recruitment_id}/applications").status_code == 403
    assert client.get("/recruitments/999999/applications").status_code == 404


def test_apply_rules(client, db, member):
    author, applicant = member("작성자"), member("지원자")
    login_as(client, author)
    open_id = write_recruitment(client)["id"]
    expired_id = write_recruitment(client)["id"]
    sql(db, "UPDATE recruitment SET deadline = NOW(6) - INTERVAL 1 MINUTE WHERE id = %s", (expired_id,))
    # 내 모집
    assert client.post(f"/recruitments/{open_id}/applications", json={}).status_code == 403

    login_as(client, applicant)
    assert client.post(f"/recruitments/{expired_id}/applications", json={}).status_code == 409
    created = client.post(f"/recruitments/{open_id}/applications", json={"message": "지원합니다"})
    assert created.status_code == 201
    application = created.json()
    assert application["status"] == "pending" and application["message"] == "지원합니다"
    assert application["applicant"] == {"id": applicant, "name": "지원자"}
    # 이미 지원함
    assert client.post(f"/recruitments/{open_id}/applications", json={}).status_code == 409

    post_id = client.get(f"/users/{author}/posts").json()["items"][-1]["id"]
    mine = client.get(f"/posts/{post_id}").json()["recruitment"]["my_application"]
    assert mine == {"id": application["id"], "message": "지원합니다", "status": "pending"}

    assert client.delete(f"/applications/{application['id']}").status_code == 204
    assert client.get(f"/posts/{post_id}").json()["recruitment"]["my_application"] is None


def test_canceling_application_removes_notification(client, member):
    author, applicant = member("작성자"), member("지원자")
    login_as(client, author)
    recruitment_id = write_recruitment(client)["id"]

    login_as(client, applicant)
    created = client.post(f"/recruitments/{recruitment_id}/applications", json={}).json()
    assert notification_types(client, author) == ["application"]

    login_as(client, applicant)
    client.delete(f"/applications/{created['id']}")
    assert notification_types(client, author) == []
    login_as(client, applicant)
    client.post(f"/recruitments/{recruitment_id}/applications", json={})
    assert notification_types(client, author) == ["application"]


def test_accept_respects_capacity_and_notifies_applicant(client, member):
    author = member("작성자")
    applicants = [member(f"지원자{n}") for n in range(3)]
    login_as(client, author)
    recruitment = write_recruitment(client, capacity=2)
    ids = []
    for applicant in applicants:
        login_as(client, applicant)
        ids.append(client.post(f"/recruitments/{recruitment['id']}/applications", json={}).json()["id"])

    login_as(client, author)
    assert client.patch(f"/applications/{ids[0]}", json={"status": "accepted"}).status_code == 200
    assert client.patch(f"/applications/{ids[1]}", json={"status": "accepted"}).status_code == 200
    assert client.patch(f"/applications/{ids[2]}", json={"status": "accepted"}).status_code == 409
    assert client.get(f"/posts/{recruitment['post_id']}").json()["recruitment"]["accepted_count"] == 2
    # 이미 처리한 지원
    assert client.patch(f"/applications/{ids[0]}", json={"status": "rejected"}).status_code == 409
    # 정원이 차도 거절은 가능
    rejected = client.patch(f"/applications/{ids[2]}", json={"status": "rejected"})
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"

    assert notification_types(client, applicants[2]) == ["application_result"]
    login_as(client, applicants[0])
    # 처리된 지원은 취소할 수 없음
    assert client.delete(f"/applications/{ids[0]}").status_code == 409
    login_as(client, applicants[1])
    assert client.delete(f"/applications/{ids[0]}").status_code == 403


def test_concurrent_accepts_do_not_exceed_capacity(client, member):
    author = member("작성자")
    login_as(client, author)
    recruitment_id = write_recruitment(client, capacity=1)["id"]
    ids = []
    for n in range(4):
        login_as(client, member(f"지원자{n}"))
        ids.append(client.post(f"/recruitments/{recruitment_id}/applications", json={}).json()["id"])

    barrier = Barrier(len(ids))
    statuses = []

    def accept(own, application_id):
        barrier.wait()
        statuses.append(own.patch(f"/applications/{application_id}", json={"status": "accepted"}).status_code)

    # 앱은 스레드 밖에서 만듭니다. 동시에 만들면 FastAPI가 경고를 냅니다.
    clients = [TestClient(create_app()) for _ in ids]
    for own in clients:
        login_as(own, author)
    threads = [Thread(target=accept, args=(own, i)) for own, i in zip(clients, ids)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(statuses) == [200, 409, 409, 409]
    login_as(client, author)
    rows = client.get(f"/recruitments/{recruitment_id}/applications").json()["items"]
    assert [r["status"] for r in rows].count("accepted") == 1


def test_only_author_decides_or_closes(client, member):
    author, applicant = member("작성자"), member("지원자")
    login_as(client, author)
    recruitment_id = write_recruitment(client)["id"]
    login_as(client, applicant)
    application_id = client.post(f"/recruitments/{recruitment_id}/applications", json={}).json()["id"]

    assert client.patch(f"/applications/{application_id}", json={"status": "accepted"}).status_code == 403
    assert client.patch(f"/recruitments/{recruitment_id}", json={"status": "closed"}).status_code == 403

    login_as(client, author)
    closed = client.patch(f"/recruitments/{recruitment_id}", json={"status": "closed"})
    assert closed.status_code == 200 and closed.json()["status"] == "closed"
    login_as(client, member("늦은 지원자"))
    assert client.post(f"/recruitments/{recruitment_id}/applications", json={}).status_code == 409


# 알림, 해시태그


def test_notifications_read_only_affects_my_own(client, member):
    me, fan = member("나"), member("팬")
    login_as(client, me)
    post_id = write_post(client)["id"]
    login_as(client, fan)
    client.post(f"/posts/{post_id}/like")
    client.post(f"/users/{me}/follow")

    login_as(client, me)
    assert client.get("/notifications/unread-count").json() == {"count": 2}
    first = client.get("/notifications").json()["items"][0]
    assert first["type"] == "follow" and first["is_read"] is False  # 최신순

    login_as(client, fan)
    assert client.post(f"/notifications/{first['id']}/read").status_code == 204
    login_as(client, me)
    assert client.get("/notifications/unread-count").json() == {"count": 2}
    assert client.post(f"/notifications/{first['id']}/read").status_code == 204
    assert client.get("/notifications/unread-count").json() == {"count": 1}
    assert client.get("/notifications").json()["items"][0]["is_read"] is True


def test_trending_counts_posts_and_respects_limit(client, member):
    login_as(client, member("회원"))
    for content in ("#스터디 #프로젝트", "#스터디", "#스터디 #알고리즘", "#프로젝트"):
        write_post(client, content)
    deleted = write_post(client, "#알고리즘 #삭제됨")
    client.delete(f"/posts/{deleted['id']}")

    assert client.get("/hashtags/trending", params={"limit": 2}).json() == [
        {"name": "스터디", "post_count": 3},
        {"name": "프로젝트", "post_count": 2},
    ]
    names = [row["name"] for row in client.get("/hashtags/trending").json()]
    assert names == ["스터디", "프로젝트", "알고리즘"]  # 글이 모두 지워진 태그는 빠짐
    assert client.get("/hashtags/없는태그").json() == {"name": "없는태그", "post_count": 0}


# 사진 업로드


def test_upload_saves_image_and_serves_it(client, member):
    login_as(client, member("회원"))
    response = client.post("/uploads", files={"file": ("a.png", PNG, "image/png")})
    assert response.status_code == 201
    url = response.json()["url"]
    assert url.startswith("/api/uploads/") and url.endswith(".png")
    served = client.get(url.removeprefix("/api"))
    assert served.status_code == 200 and served.content == PNG


def test_upload_rejects_non_image_regardless_of_name(client, member):
    login_as(client, member("회원"))
    fake = ("a.png", b"<script>alert(1)</script>", "image/png")
    assert client.post("/uploads", files={"file": fake}).status_code == 400


def test_upload_requires_login(client):
    response = client.post("/uploads", files={"file": ("a.png", PNG, "image/png")})
    assert response.status_code == 401

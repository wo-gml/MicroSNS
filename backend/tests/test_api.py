"""메모리 저장소로 동작하는 API 테스트. DB 없이 실행됩니다."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.mock import store
from app.mock.data import SAMPLE_EMAIL, SAMPLE_PASSWORD
from app.security import AUTH_COOKIE_NAME, create_access_token

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest.fixture
def anonymous():
    store.reset()
    return TestClient(create_app())


@pytest.fixture
def client(anonymous):
    """샘플 계정(회원 2)으로 로그인한 상태입니다."""
    response = anonymous.post(
        "/auth/login", json={"email": SAMPLE_EMAIL, "password": SAMPLE_PASSWORD}
    )
    assert response.status_code == 200
    return anonymous


def login_as(client, member_id):
    client.cookies.clear()  # 지우지 않으면 로그인 때 받은 쿠키와 함께 두 개가 전송됩니다.
    client.cookies.set(AUTH_COOKIE_NAME, create_access_token(member_id))


def tomorrow():
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def test_login_sets_http_only_cookie_and_hides_password(anonymous):
    response = anonymous.post(
        "/auth/login", json={"email": SAMPLE_EMAIL, "password": SAMPLE_PASSWORD}
    )
    assert "httponly" in response.headers["set-cookie"].lower()
    assert response.json()["name"] == "김민준"
    assert "password" not in response.text
    assert anonymous.get("/auth/me").json()["id"] == 2


def test_wrong_password_returns_401(anonymous):
    response = anonymous.post("/auth/login", json={"email": SAMPLE_EMAIL, "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_signup_logs_in_and_rejects_duplicate_email(anonymous):
    body = {"email": "New@test.com", "password": "password1", "name": " 새회원 "}
    response = anonymous.post("/auth/signup", json=body)
    assert response.status_code == 201
    assert response.json()["name"] == "새회원"
    assert anonymous.get("/auth/me").status_code == 200

    duplicate = anonymous.post("/auth/signup", json={**body, "email": "new@test.com"})
    assert duplicate.status_code == 409


def test_logout_clears_login(client):
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_invalid_cookie_is_anonymous_on_public_routes(anonymous):
    anonymous.cookies.set(AUTH_COOKIE_NAME, "invalid")
    assert anonymous.get("/posts/1").json()["liked_by_me"] is False
    assert anonymous.get("/auth/me").status_code == 401


def test_feed_contains_only_me_and_followed_users(client):
    response = client.get("/posts/feed", params={"limit": 100})
    authors = {post["author"]["id"] for post in response.json()["items"]}
    assert authors == {2, 1, 8, 7, 5, 6, 4}


def test_feed_requires_login(anonymous):
    assert anonymous.get("/posts/feed").status_code == 401


def test_pagination_reports_has_more(client):
    first = client.get("/users/1/posts", params={"limit": 20}).json()
    second = client.get("/users/1/posts", params={"limit": 20, "offset": 20}).json()
    assert len(first["items"]) == 20 and first["has_more"] is True
    assert len(second["items"]) == 5 and second["has_more"] is False
    assert {p["id"] for p in first["items"]}.isdisjoint(p["id"] for p in second["items"])


def test_create_post_with_recruitment_appears_on_post(client):
    response = client.post(
        "/posts",
        json={
            "content": "  같이 해요 #새태그  ",
            "image_urls": [],
            "recruitment": {"type": "study", "capacity": 2, "deadline": tomorrow()},
        },
    )
    assert response.status_code == 201
    post = response.json()
    assert post["content"] == "같이 해요 #새태그"
    assert post["recruitment"]["status"] == "open"
    assert post["recruitment"]["accepted_count"] == 0
    assert client.get("/hashtags/새태그").json()["post_count"] == 1
    assert client.get("/hashtags/새태그/posts").json()["items"][0]["id"] == post["id"]


@pytest.mark.parametrize(
    "body",
    [
        {"content": "   "},
        {"content": "x" * 501},
        {"content": "글", "image_urls": ["https://evil.example/a.jpg"]},
        {"content": "글", "image_urls": ["/api/uploads/a.jpg"] * 3},
    ],
)
def test_invalid_post_returns_422(client, body):
    response = client.post("/posts", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_past_deadline_returns_400(client):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = client.post(
        "/posts",
        json={"content": "글", "recruitment": {"type": "study", "capacity": 1, "deadline": past}},
    )
    assert response.status_code == 400


def test_only_author_can_delete_post(client):
    assert client.delete("/posts/1").status_code == 403
    assert client.delete("/posts/11").status_code == 204
    assert client.get("/posts/11").status_code == 404
    assert client.delete("/posts/11").status_code == 404


def test_like_is_idempotent_and_notifies_once(client):
    before = client.get("/posts/2").json()["like_count"]
    assert client.post("/posts/2/like").status_code == 204
    assert client.post("/posts/2/like").status_code == 204
    post = client.get("/posts/2").json()
    assert post["like_count"] == before + 1 and post["liked_by_me"] is True

    login_as(client, 8)
    notifications = client.get("/notifications").json()["items"]
    assert [n["type"] for n in notifications] == ["like"]
    assert notifications[0]["content"] == "김민준님이 회원님의 글을 좋아합니다."

    login_as(client, 2)
    assert client.delete("/posts/2/like").status_code == 204
    assert client.get("/posts/2").json()["like_count"] == before


def notification_types(client, member_id):
    login_as(client, member_id)
    return [n["type"] for n in client.get("/notifications").json()["items"]]


def test_repeating_like_keeps_one_notification(client):
    for _ in range(3):
        client.post("/posts/2/like")
        client.delete("/posts/2/like")
    assert notification_types(client, 8) == []

    login_as(client, 2)
    client.post("/posts/2/like")
    assert notification_types(client, 8) == ["like"]


def test_unlike_without_like_keeps_other_notifications(client):
    client.post("/posts/2/like")
    login_as(client, 3)
    assert client.delete("/posts/2/like").status_code == 204
    assert notification_types(client, 8) == ["like"]


def test_repeating_follow_keeps_one_notification(client):
    for _ in range(3):
        client.post("/users/3/follow")
        client.delete("/users/3/follow")
    client.post("/users/3/follow")
    assert notification_types(client, 3) == ["follow"]


def test_deleting_comment_removes_only_its_notification(client):
    first = client.post("/posts/2/comments", json={"content": "첫 댓글"}).json()
    client.post("/posts/2/comments", json={"content": "둘째 댓글"})
    assert notification_types(client, 8) == ["comment", "comment"]

    login_as(client, 2)
    client.delete(f"/comments/{first['id']}")
    assert notification_types(client, 8) == ["comment"]


def test_canceling_application_removes_notification(client):
    created = client.post("/recruitments/1/applications", json={}).json()
    assert notification_types(client, 1) == ["application"]

    login_as(client, 2)
    client.delete(f"/applications/{created['id']}")
    client.post("/recruitments/1/applications", json={})
    assert notification_types(client, 1) == ["application"]


def test_comment_flow_and_delete_permission(client):
    created = client.post("/posts/1/comments", json={"content": "참여할게요"})
    assert created.status_code == 201
    comment = created.json()
    assert comment["author"] == {"id": 2, "name": "김민준"}

    rows = client.get("/posts/1/comments").json()["items"]
    assert [row["id"] for row in rows][-1] == comment["id"]

    login_as(client, 3)
    assert client.delete(f"/comments/{comment['id']}").status_code == 403
    login_as(client, 2)
    assert client.delete(f"/comments/{comment['id']}").status_code == 204


def test_comment_on_missing_post_returns_404(client):
    assert client.post("/posts/999999/comments", json={"content": "글"}).status_code == 404
    assert client.get("/posts/999999/comments").status_code == 404


def test_follow_updates_counts_and_rejects_self(client):
    before = client.get("/users/3").json()
    assert before["follower_count"] == 128 and before["is_following"] is False
    assert client.post("/users/3/follow").status_code == 204
    after = client.get("/users/3").json()
    assert after["follower_count"] == 129 and after["is_following"] is True

    assert client.post("/users/2/follow").status_code == 400
    assert client.post("/users/999999/follow").status_code == 404
    assert client.delete("/users/3/follow").status_code == 204


def test_followers_and_following_lists(client):
    assert [u["id"] for u in client.get("/users/2/followers").json()["items"]] == [7]
    following = client.get("/users/2/following").json()["items"]
    assert {u["id"] for u in following} == {1, 4, 5, 6, 7, 8}
    assert all(u["is_following"] for u in following)


def test_recruitment_applications_are_for_author_only(client):
    assert client.get("/recruitments/4/applications").status_code == 200
    assert client.get("/recruitments/1/applications").status_code == 403


def test_apply_rules(client):
    # 내 모집
    assert client.post("/recruitments/4/applications", json={}).status_code == 403
    # 이미 지원함
    assert client.post("/recruitments/2/applications", json={}).status_code == 409
    # 마감일 지남
    assert client.post("/recruitments/3/applications", json={}).status_code == 409

    created = client.post("/recruitments/1/applications", json={"message": "지원합니다"})
    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    mine = client.get("/posts/1").json()["recruitment"]["my_application"]
    assert mine["id"] == created.json()["id"]

    assert client.delete(f"/applications/{mine['id']}").status_code == 204
    assert client.get("/posts/1").json()["recruitment"]["my_application"] is None


def test_accept_respects_capacity_and_notifies_applicant(client):
    assert client.patch("/applications/3", json={"status": "accepted"}).status_code == 200
    assert client.patch("/applications/4", json={"status": "accepted"}).status_code == 200
    full = client.patch("/applications/5", json={"status": "accepted"})
    assert full.status_code == 409
    assert client.get("/posts/11").json()["recruitment"]["accepted_count"] == 2
    # 이미 처리한 지원
    assert client.patch("/applications/3", json={"status": "rejected"}).status_code == 409
    # 정원이 차도 거절은 가능
    assert client.patch("/applications/5", json={"status": "rejected"}).status_code == 200

    login_as(client, 8)
    assert client.get("/notifications").json()["items"][0]["type"] == "application_result"
    # 처리된 지원은 취소할 수 없음
    assert client.delete("/applications/3").status_code == 409


def test_only_author_decides_or_closes(client):
    assert client.patch("/applications/1", json={"status": "rejected"}).status_code == 403
    assert client.patch("/recruitments/1", json={"status": "closed"}).status_code == 403
    closed = client.patch("/recruitments/4", json={"status": "closed"})
    assert closed.status_code == 200 and closed.json()["status"] == "closed"

    login_as(client, 1)
    assert client.post("/recruitments/4/applications", json={}).status_code == 409


def test_notifications_read_only_affects_my_own(client):
    assert client.get("/notifications/unread-count").json() == {"count": 3}
    assert client.post("/notifications/1/read").status_code == 204
    assert client.get("/notifications/unread-count").json() == {"count": 2}

    login_as(client, 1)
    assert client.post("/notifications/2/read").status_code == 204
    login_as(client, 2)
    assert client.get("/notifications/unread-count").json() == {"count": 2}


def test_trending_respects_limit(client):
    rows = client.get("/hashtags/trending", params={"limit": 2}).json()
    assert rows == [{"name": "스터디", "post_count": 128}, {"name": "프로젝트", "post_count": 96}]


def test_upload_saves_image_and_serves_it(client):
    response = client.post("/uploads", files={"file": ("a.png", PNG, "image/png")})
    assert response.status_code == 201
    url = response.json()["url"]
    assert url.startswith("/api/uploads/") and url.endswith(".png")
    served = client.get(url.removeprefix("/api"))
    assert served.status_code == 200 and served.content == PNG


def test_upload_rejects_non_image_regardless_of_name(client):
    fake = ("a.png", b"<script>alert(1)</script>", "image/png")
    assert client.post("/uploads", files={"file": fake}).status_code == 400


def test_upload_requires_login(anonymous):
    response = anonymous.post("/uploads", files={"file": ("a.png", PNG, "image/png")})
    assert response.status_code == 401


def test_mock_photo_is_served(anonymous):
    response = anonymous.get("/mock-photos/laptop-cafe.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_swagger_documents_the_real_error_format(anonymous):
    spec = anonymous.get("/openapi.json").json()
    assert "HTTPValidationError" not in spec["components"]["schemas"]
    assert "access_token" in str(spec["components"]["securitySchemes"])
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            assert operation["summary"], f"{method} {path}"
            assert operation["tags"], f"{method} {path}"

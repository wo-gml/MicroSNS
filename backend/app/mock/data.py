"""DB가 준비되기 전까지 쓰는 예시 데이터. frontend/mock/server.mjs와 같은 값입니다."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.security import hash_password

SAMPLE_EMAIL = "admin@test.com"
SAMPLE_PASSWORD = "test1234"

HOUR = 60
DAY = 1440
KST = timezone(timedelta(hours=9))

_SAMPLE_PASSWORD_HASH = hash_password(SAMPLE_PASSWORD)


def _photo(name: str) -> str:
    return f"/api/mock-photos/{name}.jpg"


def build() -> SimpleNamespace:
    """처음 상태의 데이터를 만듭니다. 시각은 지금을 기준으로 계산합니다."""
    now = datetime.now(timezone.utc)

    def ago(minutes: int) -> datetime:
        return now - timedelta(minutes=minutes)

    def later(minutes: int) -> datetime:
        return now + timedelta(minutes=minutes)

    # 지원과 수락처럼 두 계정이 필요한 흐름을 확인할 수 있도록 모두 로그인할 수 있게 합니다.
    def user(id, name, bio, days, email=None, base=None, created_at=None):
        return {
            "id": id,
            "email": email or f"user{id}@test.com",
            "password_hash": _SAMPLE_PASSWORD_HASH,
            "name": name,
            "bio": bio,
            "base": base or {},
            "created_at": created_at or ago(days * DAY),
        }

    # id % 8이 시안의 아바타 위치와 맞도록 정했습니다.
    users = [
        user(1, "이도윤", "쿼리 튜닝 스터디 운영 중", 200),
        user(
            2,
            "김민준",
            "함께 공부할 사람을 찾고 있어요.",
            300,
            email=SAMPLE_EMAIL,
        ),
        user(
            3,
            "정민재",
            "컴퓨터공학과 3학년이에요. 데이터베이스와 백엔드 개발에 관심이 많고, 함께 공부할 사람을 찾고 있어요.",
            0,
            base={"posts": 8, "followers": 128, "following": 64},
            created_at=datetime(2026, 3, 10, 10, 0, tzinfo=KST),
        ),
        user(4, "서지안", None, 100),
        user(5, "한유진", None, 100),
        user(6, "강서준", None, 100),
        user(7, "박지호", None, 100),
        user(8, "최하은", None, 100),
    ]

    # likes와 comment_base는 시안의 숫자를 맞추기 위한 초깃값입니다.
    def post(id, author_id, content, minutes, likes, comment_base, image_urls=(), liked=False):
        return {
            "id": id,
            "author_id": author_id,
            "content": content,
            "created_at": ago(minutes),
            "likes": likes,
            "comment_base": comment_base,
            "image_urls": list(image_urls),
            "liked_by": {2} if liked else set(),
        }

    posts = [
        post(1, 1, "MySQL 쿼리 튜닝 스터디 같이 하실 분 구해요. 매주 토요일 오전에 만나고, 실행 계획 읽는 법부터 시작합니다. 지금 3명이고 2명 더 모집해요.\n#스터디 #데이터베이스", 2 * HOUR, 23, 0, [_photo("laptop-cafe")], True),
        post(2, 8, "졸업 프로젝트로 일정 공유 웹앱을 만들고 있어요. 함께할 프론트엔드 개발자 1명을 찾습니다. Next.js 경험이 있으면 좋아요.\n#프로젝트 #프론트엔드", 5 * HOUR, 12, 5, [_photo("whiteboard"), _photo("calendar-app")]),
        post(3, 7, "알고리즘 스터디 4기를 모집합니다. 온라인으로 주 2회 진행하고, 풀이는 깃허브에 올려서 서로 리뷰해요.\n#스터디 #알고리즘", 25 * HOUR, 37, 8),
        post(4, 5, "FastAPI 입문서 한 권을 같이 끝낼 분을 찾아요. 백엔드가 처음이어도 괜찮아요.\n#스터디 #백엔드", 2 * DAY + 60, 9, 2),
        post(5, 6, "스프링 부트로 게시판을 만드는 스터디를 시작해요. 자바 기초만 알면 돼요.\n#스터디 #백엔드", 3 * DAY + 60, 21, 6),
        post(6, 4, "해커톤에 같이 나갈 디자이너를 찾아요. 기획은 거의 끝났고, 개발자 2명이 함께하고 있어요.\n#프로젝트 #디자인", 4 * DAY + 60, 15, 3),
        post(7, 3, "SQL 인덱스 스터디원을 찾습니다. 인덱스 설계와 실행 계획을 예제로 함께 공부해요.\n#스터디 #데이터베이스", 3 * HOUR, 18, 4, [_photo("book-desk")]),
        post(8, 3, "미니 SNS를 만드는 팀 프로젝트에서 백엔드를 맡을 분을 찾아요. FastAPI와 MySQL을 사용합니다.\n#프로젝트 #백엔드", 4 * DAY, 30, 6, [], True),
        post(9, 3, "이번 학기 데이터베이스 수업을 같이 복습하실 분 있나요? 정규화부터 시작해요.\n#스터디 #데이터베이스", 14 * DAY, 7, 1),
        post(10, 3, "백엔드 포트폴리오를 서로 리뷰할 분을 구해요. 매주 한 번 온라인으로 만나요.\n#스터디 #백엔드", 31 * DAY, 11, 2),
        post(11, 2, "함께 사이드 프로젝트 하실 분을 찾아요. 주말에 온라인으로 만나요.\n#프로젝트", 5 * DAY, 0, 0),
        # "더 보기" 확인용
        *[
            post(100 + i, 1, f"지난 모집 글 {i + 1}\n#지난글", 20 * DAY + i * 100, 0, 0)
            for i in range(24)
        ],
    ]

    comments = [
        {"id": id, "post_id": 1, "author_id": author_id, "content": content, "created_at": ago(minutes)}
        for id, author_id, content, minutes in [
            (1, 3, "실행 계획을 제대로 본 적이 없는데 저도 참여할 수 있을까요?", HOUR + 5),
            (2, 8, "토요일 오전이면 저도 가능해요. 모임 시간은 몇 시인가요?", HOUR),
            (3, 5, "교재 정할 때 추천 목록도 같이 공유해 주시면 좋겠어요.", 30),
            (4, 7, "온라인으로 진행하면 저도 참여해 보고 싶어요.", 20),
            (5, 6, "스터디 기록은 어디에 남길 계획인가요?", 10),
        ]
    ]

    notifications = [
        {
            "id": id,
            "user_id": 2,
            "type": type,
            "actor_id": actor_id,
            "post_id": post_id,
            "content": content,
            "is_read": is_read,
            "created_at": ago(minutes),
        }
        for id, type, actor_id, post_id, content, is_read, minutes in [
            (1, "like", 1, 1, "이도윤님이 회원님의 글을 좋아합니다.", False, 3),
            (2, "application", 8, 11, "최하은님이 회원님의 모집에 지원했습니다.", False, 12),
            (3, "follow", 7, None, "박지호님이 회원님을 팔로우하기 시작했습니다.", False, HOUR),
            (4, "comment", 5, 1, "한유진님이 회원님의 글에 댓글을 남겼습니다.", True, 3 * HOUR),
            (5, "application_result", 1, 1, "이도윤님이 회원님의 지원을 수락했습니다.", True, 25 * HOUR),
        ]
    ]

    def recruitment(id, post_id, type, capacity, deadline, created_minutes):
        created_at = ago(created_minutes)
        return {
            "id": id,
            "post_id": post_id,
            "type": type,
            "capacity": capacity,
            "deadline": deadline,
            "status": "open",
            "created_at": created_at,
            "updated_at": created_at,
        }

    recruitments = [
        recruitment(1, 1, "study", 5, later(7 * DAY), 2 * HOUR),
        recruitment(2, 2, "project", 1, later(3 * DAY), 5 * HOUR),
        recruitment(3, 3, "study", 4, ago(HOUR), 25 * HOUR),
        recruitment(4, 11, "project", 2, later(5 * DAY), 5 * DAY),
    ]

    def application(id, recruitment_id, member_id, message, status, created_minutes, updated_minutes):
        return {
            "id": id,
            "recruitment_id": recruitment_id,
            "member_id": member_id,
            "message": message,
            "status": status,
            "created_at": ago(created_minutes),
            "updated_at": ago(updated_minutes),
        }

    applications = [
        application(1, 1, 3, "실행 계획을 배우고 싶어요.", "accepted", HOUR, 30),
        application(2, 2, 2, "Next.js 경험이 있어요.", "pending", HOUR, HOUR),
        application(3, 4, 8, "프론트엔드를 맡고 싶어요.", "pending", 12, 12),
        application(4, 4, 3, None, "pending", 60, 60),
        application(5, 4, 5, "기획도 도울 수 있어요.", "pending", 90, 90),
    ]

    return SimpleNamespace(
        users=users,
        follows={(2, 1), (2, 8), (2, 7), (2, 5), (2, 6), (2, 4), (7, 2)},
        posts=posts,
        comments=comments,
        notifications=notifications,
        recruitments=recruitments,
        applications=applications,
        trending=[("스터디", 128), ("프로젝트", 96), ("데이터베이스", 54), ("프론트엔드", 41), ("알고리즘", 37)],
        next_id=1000,
    )

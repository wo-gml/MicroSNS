"""DB가 준비되기 전까지 repositories/ 대신 쓰는 메모리 저장소.

데이터는 서버를 끄면 처음 상태로 돌아갑니다. 함수 형태를 리포지토리와 맞춰 두었으므로
DB가 준비되면 라우터의 store.xxx(...) 호출을 xxx_repo.xxx(db, ...)로 바꾸면 됩니다.
목록 함수는 리포지토리와 같이 limit개를 조회하고, 라우터는 page.fetch_limit을 넘깁니다.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional, Set

from app.mock import data

state = data.build()

# 프론트엔드 RichText와 같은 규칙입니다. 앞이 글자가 아닌 #단어만 해시태그로 봅니다.
_HASHTAG = re.compile(r"(?<!\w)#(\w+)")


def reset() -> None:
    """처음 상태로 되돌립니다. 테스트에서 씁니다."""
    global state
    state = data.build()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _next_id() -> int:
    state.next_id += 1
    return state.next_id


def _find(rows: List[dict], id: int) -> Optional[dict]:
    return next((row for row in rows if row["id"] == id), None)


def _newest_first(rows: List[dict]) -> List[dict]:
    return sorted(rows, key=lambda row: (row["created_at"], row["id"]), reverse=True)


# 회원


def find_user(user_id: int) -> Optional[dict]:
    return _find(state.users, user_id)


def find_user_by_email(email: str) -> Optional[dict]:
    target = email.lower()
    return next((u for u in state.users if u["email"].lower() == target), None)


def create_user(email: str, password_hash: str, name: str, bio: Optional[str]) -> dict:
    user = {
        "id": _next_id(),
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "bio": bio,
        "base": {},
        "created_at": _now(),
    }
    state.users.append(user)
    return user


def _summary(user_id: int) -> dict:
    user = find_user(user_id)
    return {"id": user["id"], "name": user["name"]}


def is_following(viewer_id: Optional[int], user_id: int) -> bool:
    return (viewer_id, user_id) in state.follows


def _user_item(user: dict, viewer_id: Optional[int]) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "bio": user["bio"],
        "is_following": is_following(viewer_id, user["id"]),
    }


def user_profile(user: dict, viewer_id: Optional[int]) -> dict:
    user_id = user["id"]
    base = user["base"]
    return {
        **_user_item(user, viewer_id),
        "created_at": user["created_at"],
        "post_count": base.get("posts", 0)
        + sum(p["author_id"] == user_id for p in state.posts),
        "follower_count": base.get("followers", 0)
        + sum(following == user_id for _, following in state.follows),
        "following_count": base.get("following", 0)
        + sum(follower == user_id for follower, _ in state.follows),
    }


def list_followers(user_id: int, viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    rows = [u for u in state.users if (u["id"], user_id) in state.follows]
    return [_user_item(u, viewer_id) for u in rows[offset : offset + limit]]


def list_following(user_id: int, viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    rows = [u for u in state.users if (user_id, u["id"]) in state.follows]
    return [_user_item(u, viewer_id) for u in rows[offset : offset + limit]]


def follow(follower_id: int, following_id: int) -> bool:
    """새로 팔로우했으면 True, 이미 팔로우 중이면 False입니다."""
    key = (follower_id, following_id)
    if key in state.follows:
        return False
    state.follows.add(key)
    return True


def unfollow(follower_id: int, following_id: int) -> bool:
    """팔로우를 취소했으면 True, 팔로우 중이 아니었으면 False입니다."""
    key = (follower_id, following_id)
    if key not in state.follows:
        return False
    state.follows.remove(key)
    return True


# 게시글


def find_post(post_id: int) -> Optional[dict]:
    return _find(state.posts, post_id)


def _accepted_count(recruitment_id: int) -> int:
    return sum(
        a["recruitment_id"] == recruitment_id and a["status"] == "accepted"
        for a in state.applications
    )


def recruitment_out(recruitment: dict, viewer_id: Optional[int]) -> dict:
    mine = next(
        (
            a
            for a in state.applications
            if a["recruitment_id"] == recruitment["id"] and a["member_id"] == viewer_id
        ),
        None,
    )
    return {
        **recruitment,
        "accepted_count": _accepted_count(recruitment["id"]),
        "my_application": mine
        and {"id": mine["id"], "message": mine["message"], "status": mine["status"]},
    }


def post_out(post: dict, viewer_id: Optional[int]) -> dict:
    recruitment = next((r for r in state.recruitments if r["post_id"] == post["id"]), None)
    return {
        "id": post["id"],
        "author": {
            **_summary(post["author_id"]),
            "is_following": is_following(viewer_id, post["author_id"]),
        },
        "content": post["content"],
        "image_urls": post["image_urls"],
        "created_at": post["created_at"],
        "like_count": post["likes"] + len(post["liked_by"]),
        "comment_count": post["comment_base"]
        + sum(c["post_id"] == post["id"] for c in state.comments),
        "liked_by_me": viewer_id in post["liked_by"],
        "recruitment": recruitment and recruitment_out(recruitment, viewer_id),
    }


def _posts_page(rows: List[dict], viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    page = _newest_first(rows)[offset : offset + limit]
    return [post_out(post, viewer_id) for post in page]


def feed(viewer_id: int, limit: int, offset: int) -> List[dict]:
    rows = [
        p
        for p in state.posts
        if p["author_id"] == viewer_id or is_following(viewer_id, p["author_id"])
    ]
    return _posts_page(rows, viewer_id, limit, offset)


def posts_by_author(author_id: int, viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    rows = [p for p in state.posts if p["author_id"] == author_id]
    return _posts_page(rows, viewer_id, limit, offset)


def posts_liked_by(user_id: int, viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    rows = [p for p in state.posts if user_id in p["liked_by"]]
    return _posts_page(rows, viewer_id, limit, offset)


def create_post(
    author_id: int, content: str, image_urls: List[str], recruitment: Optional[dict]
) -> dict:
    post = {
        "id": _next_id(),
        "author_id": author_id,
        "content": content,
        "created_at": _now(),
        "likes": 0,
        "comment_base": 0,
        "image_urls": image_urls,
        "liked_by": set(),
    }
    state.posts.append(post)
    if recruitment:
        now = _now()
        state.recruitments.append(
            {
                "id": _next_id(),
                "post_id": post["id"],
                **recruitment,
                "status": "open",
                "created_at": now,
                "updated_at": now,
            }
        )
    return post


def delete_post(post_id: int) -> None:
    """글에 딸린 댓글, 모집, 지원, 알림도 함께 지웁니다."""
    recruitment_ids = {r["id"] for r in state.recruitments if r["post_id"] == post_id}
    state.applications = [
        a for a in state.applications if a["recruitment_id"] not in recruitment_ids
    ]
    state.recruitments = [r for r in state.recruitments if r["post_id"] != post_id]
    state.comments = [c for c in state.comments if c["post_id"] != post_id]
    state.notifications = [n for n in state.notifications if n["post_id"] != post_id]
    state.posts = [p for p in state.posts if p["id"] != post_id]


def like(post: dict, member_id: int) -> bool:
    """새로 좋아요했으면 True, 이미 좋아요했으면 False입니다."""
    if member_id in post["liked_by"]:
        return False
    post["liked_by"].add(member_id)
    return True


def unlike(post: dict, member_id: int) -> bool:
    """좋아요를 취소했으면 True, 좋아요한 적이 없으면 False입니다."""
    if member_id not in post["liked_by"]:
        return False
    post["liked_by"].remove(member_id)
    return True


# 댓글


def find_comment(comment_id: int) -> Optional[dict]:
    return _find(state.comments, comment_id)


def _comment_out(comment: dict) -> dict:
    return {
        "id": comment["id"],
        "post_id": comment["post_id"],
        "author": _summary(comment["author_id"]),
        "content": comment["content"],
        "created_at": comment["created_at"],
    }


def list_comments(post_id: int, limit: int, offset: int) -> List[dict]:
    rows = sorted(
        (c for c in state.comments if c["post_id"] == post_id),
        key=lambda c: (c["created_at"], c["id"]),
    )
    return [_comment_out(c) for c in rows[offset : offset + limit]]


def create_comment(post_id: int, author_id: int, content: str) -> dict:
    comment = {
        "id": _next_id(),
        "post_id": post_id,
        "author_id": author_id,
        "content": content,
        "created_at": _now(),
    }
    state.comments.append(comment)
    return _comment_out(comment)


def delete_comment(comment_id: int) -> None:
    state.comments = [c for c in state.comments if c["id"] != comment_id]


# 모집과 지원


def find_recruitment(recruitment_id: int) -> Optional[dict]:
    return _find(state.recruitments, recruitment_id)


def is_recruiting(recruitment: dict) -> bool:
    """마감 처리, 마감일 지남, 정원 초과 중 하나라도 해당하면 False입니다."""
    return (
        recruitment["status"] == "open"
        and recruitment["deadline"] > _now()
        and _accepted_count(recruitment["id"]) < recruitment["capacity"]
    )


def is_full(recruitment: dict) -> bool:
    return _accepted_count(recruitment["id"]) >= recruitment["capacity"]


def close_recruitment(recruitment: dict) -> None:
    recruitment["status"] = "closed"
    recruitment["updated_at"] = _now()


def find_application(application_id: int) -> Optional[dict]:
    return _find(state.applications, application_id)


def find_my_application(recruitment_id: int, member_id: int) -> Optional[dict]:
    return next(
        (
            a
            for a in state.applications
            if a["recruitment_id"] == recruitment_id and a["member_id"] == member_id
        ),
        None,
    )


def application_out(application: dict) -> dict:
    return {
        "id": application["id"],
        "recruitment_id": application["recruitment_id"],
        "applicant": _summary(application["member_id"]),
        "message": application["message"],
        "status": application["status"],
        "created_at": application["created_at"],
        "updated_at": application["updated_at"],
    }


def list_applications(recruitment_id: int, limit: int, offset: int) -> List[dict]:
    rows = [a for a in state.applications if a["recruitment_id"] == recruitment_id]
    return [application_out(a) for a in rows[offset : offset + limit]]


def create_application(recruitment_id: int, member_id: int, message: Optional[str]) -> dict:
    now = _now()
    application = {
        "id": _next_id(),
        "recruitment_id": recruitment_id,
        "member_id": member_id,
        "message": message,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    state.applications.append(application)
    return application


def set_application_status(application: dict, status: str) -> None:
    application["status"] = status
    application["updated_at"] = _now()


def delete_application(application_id: int) -> None:
    state.applications = [a for a in state.applications if a["id"] != application_id]


# 해시태그


def _tags(post: dict) -> Set[str]:
    return set(_HASHTAG.findall(post["content"]))


def posts_by_hashtag(tag: str, viewer_id: Optional[int], limit: int, offset: int) -> List[dict]:
    rows = [p for p in state.posts if tag in _tags(p)]
    return _posts_page(rows, viewer_id, limit, offset)


def trending_hashtags(limit: int) -> List[dict]:
    return [
        {"name": name, "post_count": post_count} for name, post_count in state.trending[:limit]
    ]


def hashtag_stat(tag: str) -> dict:
    # 인기 해시태그의 개수는 시안의 숫자를 그대로 씁니다.
    seeded = dict(state.trending).get(tag)
    post_count = seeded if seeded is not None else sum(tag in _tags(p) for p in state.posts)
    return {"name": tag, "post_count": post_count}


# 알림


def notify(
    user_id: int, type: str, actor_id: int, post_id: Optional[int], message: str
) -> None:
    """본인의 행동은 본인에게 알리지 않습니다. message는 이름 뒤에 붙는 문구입니다."""
    if user_id == actor_id:
        return
    state.notifications.append(
        {
            "id": _next_id(),
            "user_id": user_id,
            "type": type,
            "actor_id": actor_id,
            "post_id": post_id,
            "content": f"{find_user(actor_id)['name']}{message}",
            "is_read": False,
            "created_at": _now(),
        }
    )


def retract_notification(user_id: int, type: str, actor_id: int, post_id: Optional[int]) -> None:
    """행동을 취소하면 그 행동으로 생긴 알림을 지웁니다. 가장 최근의 한 건만 지웁니다."""
    matches = [
        n
        for n in state.notifications
        if n["user_id"] == user_id
        and n["type"] == type
        and n["actor_id"] == actor_id
        and n["post_id"] == post_id
    ]
    if matches:
        state.notifications.remove(_newest_first(matches)[0])


def list_notifications(user_id: int, limit: int, offset: int) -> List[dict]:
    rows = _newest_first([n for n in state.notifications if n["user_id"] == user_id])
    return [
        {
            "id": n["id"],
            "type": n["type"],
            "actor": _summary(n["actor_id"]),
            "post_id": n["post_id"],
            "content": n["content"],
            "is_read": n["is_read"],
            "created_at": n["created_at"],
        }
        for n in rows[offset : offset + limit]
    ]


def unread_count(user_id: int) -> int:
    return sum(n["user_id"] == user_id and not n["is_read"] for n in state.notifications)


def mark_read(notification_id: int, user_id: int) -> None:
    for n in state.notifications:
        if n["id"] == notification_id and n["user_id"] == user_id:
            n["is_read"] = True

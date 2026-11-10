from typing import List, Optional

from pymysql.connections import Connection

from app.db import fetch_all, fetch_one, insert

# 보는 사람(viewer)이 이 회원을 팔로우하는지. viewer가 NULL이면 거짓입니다.
_IS_FOLLOWING = """EXISTS (
    SELECT 1 FROM follow f WHERE f.follower_id = %(viewer)s AND f.following_id = m.id
) AS is_following"""


def find_by_id(db: Connection, member_id: int) -> Optional[dict]:
    return fetch_one(
        db,
        "SELECT id, email, name, bio, created_at FROM member WHERE id = %s",
        (member_id,),
    )


def find_by_email(db: Connection, email: str) -> Optional[dict]:
    """로그인용이라 password_hash를 포함합니다. 이메일은 대소문자를 구분하지 않습니다."""
    return fetch_one(
        db,
        "SELECT id, email, password_hash, name, bio, created_at FROM member WHERE email = %s",
        (email,),
    )


def exists(db: Connection, member_id: int) -> bool:
    return fetch_one(db, "SELECT 1 FROM member WHERE id = %s", (member_id,)) is not None


def create(db: Connection, email: str, password_hash: str, name: str, bio: Optional[str]) -> dict:
    member_id = insert(
        db,
        "INSERT INTO member (email, password_hash, name, bio) VALUES (%s, %s, %s, %s)",
        (email, password_hash, name, bio),
    )
    return find_by_id(db, member_id)


def profile(db: Connection, member_id: int, viewer_id: Optional[int]) -> Optional[dict]:
    return fetch_one(
        db,
        f"""
        SELECT m.id, m.name, m.bio, m.created_at, {_IS_FOLLOWING},
               (SELECT COUNT(*) FROM post p WHERE p.member_id = m.id) AS post_count,
               (SELECT COUNT(*) FROM follow f WHERE f.following_id = m.id) AS follower_count,
               (SELECT COUNT(*) FROM follow f WHERE f.follower_id = m.id) AS following_count
        FROM member m
        WHERE m.id = %(id)s
        """,
        {"id": member_id, "viewer": viewer_id},
    )


def list_followers(
    db: Connection, member_id: int, viewer_id: Optional[int], limit: int, offset: int
) -> List[dict]:
    """나를 팔로우하는 회원. 최근에 팔로우한 순서입니다."""
    return fetch_all(
        db,
        f"""
        SELECT m.id, m.name, m.bio, {_IS_FOLLOWING}
        FROM follow r
        JOIN member m ON m.id = r.follower_id
        WHERE r.following_id = %(id)s
        ORDER BY r.created_at DESC, m.id DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"id": member_id, "viewer": viewer_id, "limit": limit, "offset": offset},
    )


def list_following(
    db: Connection, member_id: int, viewer_id: Optional[int], limit: int, offset: int
) -> List[dict]:
    """내가 팔로우하는 회원. 최근에 팔로우한 순서입니다."""
    return fetch_all(
        db,
        f"""
        SELECT m.id, m.name, m.bio, {_IS_FOLLOWING}
        FROM follow r
        JOIN member m ON m.id = r.following_id
        WHERE r.follower_id = %(id)s
        ORDER BY r.created_at DESC, m.id DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """,
        {"id": member_id, "viewer": viewer_id, "limit": limit, "offset": offset},
    )

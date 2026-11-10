import pymysql
from pymysql.connections import Connection

from app.db import execute

DUPLICATE_ENTRY = 1062


def follow(db: Connection, follower_id: int, following_id: int) -> bool:
    """새로 팔로우했으면 True, 이미 팔로우 중이면 False입니다."""
    try:
        execute(
            db,
            "INSERT INTO follow (follower_id, following_id) VALUES (%s, %s)",
            (follower_id, following_id),
        )
    except pymysql.err.IntegrityError as exc:
        if exc.args[0] == DUPLICATE_ENTRY:
            return False
        raise
    return True


def unfollow(db: Connection, follower_id: int, following_id: int) -> bool:
    """팔로우를 취소했으면 True, 팔로우 중이 아니었으면 False입니다."""
    deleted = execute(
        db,
        "DELETE FROM follow WHERE follower_id = %s AND following_id = %s",
        (follower_id, following_id),
    )
    return deleted > 0

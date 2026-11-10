import pymysql
from pymysql.connections import Connection

from app.db import execute
from app.repositories.follow_repo import DUPLICATE_ENTRY


def like(db: Connection, member_id: int, post_id: int) -> bool:
    """새로 좋아요했으면 True, 이미 좋아요했으면 False입니다."""
    try:
        execute(
            db,
            "INSERT INTO post_like (member_id, post_id) VALUES (%s, %s)",
            (member_id, post_id),
        )
    except pymysql.err.IntegrityError as exc:
        if exc.args[0] == DUPLICATE_ENTRY:
            return False
        raise
    return True


def unlike(db: Connection, member_id: int, post_id: int) -> bool:
    """좋아요를 취소했으면 True, 좋아요한 적이 없으면 False입니다."""
    deleted = execute(
        db,
        "DELETE FROM post_like WHERE member_id = %s AND post_id = %s",
        (member_id, post_id),
    )
    return deleted > 0

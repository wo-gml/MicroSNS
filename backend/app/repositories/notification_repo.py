from typing import List, Optional

from pymysql.connections import Connection

from app.db import execute, fetch_all, fetch_one


def notify(
    db: Connection,
    receiver_id: int,
    type: str,
    actor_id: int,
    post_id: Optional[int],
    message: str,
) -> None:
    """본인의 행동은 본인에게 알리지 않습니다. message는 행동한 회원 이름 뒤에 붙는 문구입니다."""
    if receiver_id == actor_id:
        return
    execute(
        db,
        """
        INSERT INTO notification (receiver_id, actor_id, type, post_id, content)
        SELECT %s, m.id, %s, %s, CONCAT(m.name, %s) FROM member m WHERE m.id = %s
        """,
        (receiver_id, type, post_id, message, actor_id),
    )


def retract(
    db: Connection, receiver_id: int, type: str, actor_id: int, post_id: Optional[int]
) -> None:
    """행동을 취소하면 그 행동으로 생긴 알림을 지웁니다. 가장 최근의 한 건만 지웁니다."""
    execute(
        db,
        """
        DELETE FROM notification
        WHERE receiver_id = %s AND type = %s AND actor_id = %s AND post_id <=> %s
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (receiver_id, type, actor_id, post_id),
    )


def list_for(db: Connection, receiver_id: int, limit: int, offset: int) -> List[dict]:
    """최신순입니다."""
    rows = fetch_all(
        db,
        """
        SELECT n.id, n.type, n.post_id, n.content, n.is_read, n.created_at,
               m.id AS actor_id, m.name AS actor_name
        FROM notification n JOIN member m ON m.id = n.actor_id
        WHERE n.receiver_id = %s
        ORDER BY n.created_at DESC, n.id DESC
        LIMIT %s OFFSET %s
        """,
        (receiver_id, limit, offset),
    )
    for row in rows:
        row["actor"] = {"id": row.pop("actor_id"), "name": row.pop("actor_name")}
        row["is_read"] = bool(row["is_read"])
    return rows


def unread_count(db: Connection, receiver_id: int) -> int:
    row = fetch_one(
        db,
        "SELECT COUNT(*) AS n FROM notification WHERE receiver_id = %s AND is_read = FALSE",
        (receiver_id,),
    )
    return row["n"]


def mark_read(db: Connection, notification_id: int, receiver_id: int) -> None:
    """내 알림만 처리합니다."""
    execute(
        db,
        "UPDATE notification SET is_read = TRUE WHERE id = %s AND receiver_id = %s",
        (notification_id, receiver_id),
    )

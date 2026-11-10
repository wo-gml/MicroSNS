from typing import List, Optional

from pymysql.connections import Connection

from app.db import execute, fetch_all, fetch_one, insert

_SELECT = """
    SELECT c.id, c.post_id, c.content, c.created_at, m.id AS author_id, m.name AS author_name
    FROM comment c JOIN member m ON m.id = c.member_id
"""


def _out(row: dict) -> dict:
    row["author"] = {"id": row.pop("author_id"), "name": row.pop("author_name")}
    return row


def find(db: Connection, comment_id: int) -> Optional[dict]:
    """권한 확인용입니다. 작성자 id(author_id)와 글 작성자 id(post_author_id)를 돌려줍니다."""
    return fetch_one(
        db,
        """
        SELECT c.id, c.post_id, c.member_id AS author_id, p.member_id AS post_author_id
        FROM comment c JOIN post p ON p.id = c.post_id
        WHERE c.id = %s
        """,
        (comment_id,),
    )


def out(db: Connection, comment_id: int) -> Optional[dict]:
    row = fetch_one(db, _SELECT + "WHERE c.id = %s", (comment_id,))
    return row and _out(row)


def list_by_post(db: Connection, post_id: int, limit: int, offset: int) -> List[dict]:
    """작성 시각 오름차순입니다."""
    rows = fetch_all(
        db,
        _SELECT + "WHERE c.post_id = %s ORDER BY c.created_at, c.id LIMIT %s OFFSET %s",
        (post_id, limit, offset),
    )
    return [_out(row) for row in rows]


def create(db: Connection, post_id: int, member_id: int, content: str) -> int:
    return insert(
        db,
        "INSERT INTO comment (post_id, member_id, content) VALUES (%s, %s, %s)",
        (post_id, member_id, content),
    )


def delete(db: Connection, comment_id: int) -> bool:
    return execute(db, "DELETE FROM comment WHERE id = %s", (comment_id,)) > 0

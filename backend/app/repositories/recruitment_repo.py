"""모집(recruitment)과 지원(application)."""

from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pymysql.connections import Connection

from app.db import execute, fetch_all, fetch_one, insert, placeholders

_ACCEPTED_COUNT = """(
    SELECT COUNT(*) FROM application a WHERE a.recruitment_id = r.id AND a.status = 'accepted'
)"""

_APPLICATION_COLUMNS = """
    a.id, a.recruitment_id, a.message, a.status, a.created_at, a.updated_at,
    m.id AS applicant_id, m.name AS applicant_name
"""


def _recruitment_out(row: dict) -> dict:
    my_id = row.pop("my_id")
    my_message = row.pop("my_message")
    my_status = row.pop("my_status")
    row["my_application"] = (
        None if my_id is None else {"id": my_id, "message": my_message, "status": my_status}
    )
    return row


def _application_out(row: dict) -> dict:
    row["applicant"] = {"id": row.pop("applicant_id"), "name": row.pop("applicant_name")}
    return row


def _select_out(where: str) -> str:
    return f"""
        SELECT r.id, r.post_id, r.type, r.capacity, r.deadline, r.status,
               r.created_at, r.updated_at, {_ACCEPTED_COUNT} AS accepted_count,
               mine.id AS my_id, mine.message AS my_message, mine.status AS my_status
        FROM recruitment r
        LEFT JOIN application mine ON mine.recruitment_id = r.id AND mine.member_id = %s
        WHERE {where}
    """


def for_posts(db: Connection, post_ids: Sequence[int], viewer_id: Optional[int]) -> Dict[int, dict]:
    """글 id별 모집 정보. 모집이 없는 글은 빠집니다."""
    if not post_ids:
        return {}
    rows = fetch_all(
        db, _select_out(f"r.post_id IN ({placeholders(post_ids)})"), (viewer_id, *post_ids)
    )
    return {row["post_id"]: _recruitment_out(row) for row in rows}


def out(db: Connection, recruitment_id: int, viewer_id: Optional[int]) -> Optional[dict]:
    row = fetch_one(db, _select_out("r.id = %s"), (viewer_id, recruitment_id))
    return row and _recruitment_out(row)


def find(db: Connection, recruitment_id: int) -> Optional[dict]:
    """권한 확인용으로 글 작성자 id(author_id)를 함께 돌려줍니다."""
    return fetch_one(
        db,
        """
        SELECT r.id, r.post_id, r.capacity, r.status, p.member_id AS author_id
        FROM recruitment r
        JOIN post p ON p.id = r.post_id
        WHERE r.id = %s
        """,
        (recruitment_id,),
    )


def create(
    db: Connection, post_id: int, type: str, capacity: int, deadline: datetime
) -> int:
    return insert(
        db,
        "INSERT INTO recruitment (post_id, type, capacity, deadline) VALUES (%s, %s, %s, %s)",
        (post_id, type, capacity, deadline),
    )


def close(db: Connection, recruitment_id: int) -> None:
    execute(db, "UPDATE recruitment SET status = 'closed' WHERE id = %s", (recruitment_id,))


def lock(db: Connection, recruitment_id: int) -> Optional[dict]:
    """정원 확인 전에 모집 행을 잠급니다. 트랜잭션의 첫 쿼리로 실행합니다(app/db.py 참고)."""
    return fetch_one(
        db, "SELECT id, capacity FROM recruitment WHERE id = %s FOR UPDATE", (recruitment_id,)
    )


def accepted_count(db: Connection, recruitment_id: int) -> int:
    row = fetch_one(
        db,
        "SELECT COUNT(*) AS n FROM application WHERE recruitment_id = %s AND status = 'accepted'",
        (recruitment_id,),
    )
    return row["n"]


def is_recruiting(db: Connection, recruitment_id: int) -> bool:
    """마감 처리, 마감일 지남, 정원 참 중 하나라도 해당하면 False입니다."""
    row = fetch_one(
        db,
        f"""
        SELECT 1 FROM recruitment r
        WHERE r.id = %s AND r.status = 'open' AND r.deadline > NOW(6)
          AND {_ACCEPTED_COUNT} < r.capacity
        """,
        (recruitment_id,),
    )
    return row is not None


# 지원


def find_application(db: Connection, application_id: int) -> Optional[dict]:
    return fetch_one(
        db,
        "SELECT id, recruitment_id, member_id, status FROM application WHERE id = %s",
        (application_id,),
    )


def has_applied(db: Connection, recruitment_id: int, member_id: int) -> bool:
    row = fetch_one(
        db,
        "SELECT 1 FROM application WHERE recruitment_id = %s AND member_id = %s",
        (recruitment_id, member_id),
    )
    return row is not None


def application_out(db: Connection, application_id: int) -> Optional[dict]:
    row = fetch_one(
        db,
        f"""
        SELECT {_APPLICATION_COLUMNS}
        FROM application a JOIN member m ON m.id = a.member_id
        WHERE a.id = %s
        """,
        (application_id,),
    )
    return row and _application_out(row)


def list_applications(db: Connection, recruitment_id: int, limit: int, offset: int) -> List[dict]:
    """지원한 순서입니다."""
    rows = fetch_all(
        db,
        f"""
        SELECT {_APPLICATION_COLUMNS}
        FROM application a JOIN member m ON m.id = a.member_id
        WHERE a.recruitment_id = %s
        ORDER BY a.created_at, a.id
        LIMIT %s OFFSET %s
        """,
        (recruitment_id, limit, offset),
    )
    return [_application_out(row) for row in rows]


def create_application(
    db: Connection, recruitment_id: int, member_id: int, message: Optional[str]
) -> int:
    return insert(
        db,
        "INSERT INTO application (recruitment_id, member_id, message) VALUES (%s, %s, %s)",
        (recruitment_id, member_id, message),
    )


def decide(db: Connection, application_id: int, status: str) -> bool:
    """대기 중인 지원만 수락·거절합니다. 그사이 취소됐거나 처리됐으면 False입니다."""
    updated = execute(
        db,
        "UPDATE application SET status = %s WHERE id = %s AND status = 'pending'",
        (status, application_id),
    )
    return updated > 0


def delete_pending(db: Connection, application_id: int) -> bool:
    """대기 중인 지원만 지웁니다. 그사이 처리됐으면 False입니다."""
    deleted = execute(
        db, "DELETE FROM application WHERE id = %s AND status = 'pending'", (application_id,)
    )
    return deleted > 0

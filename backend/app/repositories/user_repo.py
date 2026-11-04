from typing import Optional

from pymysql.connections import Connection


def find_by_id(db: Connection, member_id: int) -> Optional[dict]:
    with db.cursor() as cur:
        cur.execute(
            "SELECT id, email, name, bio, created_at FROM member WHERE id = %s",
            (member_id,),
        )
        return cur.fetchone()

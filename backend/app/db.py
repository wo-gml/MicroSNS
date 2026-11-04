"""MySQL 연결과 트랜잭션.

기본은 자동 commit입니다. 쿼리 하나짜리 INSERT/UPDATE/DELETE는 실행 즉시 저장됩니다.
여러 쿼리를 함께 성공/실패시켜야 할 때만 transaction()으로 묶습니다.

    with transaction(db):
        with db.cursor() as cur:
            cur.execute("INSERT INTO post ...", (...))
            cur.execute("INSERT INTO recruitment ...", (...))

행을 잠그는 경우 SELECT ... FOR UPDATE를 트랜잭션의 첫 쿼리로 실행합니다. 잠금 전에
일반 SELECT를 하면 그 시점의 스냅샷이 고정되어, 잠금을 얻은 뒤에도 다른 요청이 commit한
내용을 보지 못합니다.
"""

from contextlib import contextmanager
from typing import Iterator

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.config import get_settings


def connect() -> Connection:
    settings = get_settings()
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
        init_command=f"SET time_zone = '{settings.db_time_zone}'",
    )


def get_db() -> Iterator[Connection]:
    """요청 하나당 연결 하나를 빌려주는 FastAPI 의존성입니다."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction(conn: Connection) -> Iterator[Connection]:
    """블록이 끝나면 commit, 예외가 나면 rollback합니다. 중첩해서 쓰지 않습니다."""
    conn.begin()
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()

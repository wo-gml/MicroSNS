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
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Iterator, List, Sequence

import pymysql
from pymysql import converters
from pymysql.connections import Connection
from pymysql.constants import FIELD_TYPE
from pymysql.cursors import DictCursor

from app.config import get_settings


def db_timezone() -> timezone:
    """DB_TIME_ZONE(예: +09:00)을 timezone으로 바꿉니다."""
    offset = get_settings().db_time_zone
    sign = -1 if offset[0] == "-" else 1
    hours, minutes = offset[1:].split(":")
    return timezone(sign * timedelta(hours=int(hours), minutes=int(minutes)))


@lru_cache
def _conversions() -> dict:
    """DATETIME 컬럼에는 시간대가 없으므로 연결 시간대를 기준으로 읽고 씁니다.

    PyMySQL은 datetime을 쓸 때 시간대를 버리므로, UTC 시각을 그대로 넘기면 9시간 어긋나게
    저장됩니다. 그래서 쓸 때는 DB 시간대로 바꾸고, 읽을 때는 DB 시간대를 붙여 돌려줍니다.
    """
    tz = db_timezone()

    def encode(value: datetime, mapping=None) -> str:
        if value.tzinfo is not None:
            value = value.astimezone(tz).replace(tzinfo=None)
        return converters.escape_datetime(value, mapping)

    def decode(raw):
        value = converters.convert_datetime(raw)
        return value.replace(tzinfo=tz) if isinstance(value, datetime) else value

    conv = dict(converters.conversions)
    conv[datetime] = encode
    conv[FIELD_TYPE.DATETIME] = decode
    conv[FIELD_TYPE.TIMESTAMP] = decode
    return conv


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
        conv=_conversions(),
    )


def placeholders(values: Sequence) -> str:
    """IN 절에 넣을 %s 목록입니다. 값은 따로 파라미터로 넘깁니다."""
    return ", ".join(["%s"] * len(values))


def fetch_all(db: Connection, sql: str, args=None) -> List[dict]:
    with db.cursor() as cur:
        cur.execute(sql, args)
        return list(cur.fetchall())


def fetch_one(db: Connection, sql: str, args=None):
    with db.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()


def execute(db: Connection, sql: str, args=None) -> int:
    """바뀐 행 수를 돌려줍니다."""
    with db.cursor() as cur:
        return cur.execute(sql, args)


def insert(db: Connection, sql: str, args=None) -> int:
    """새 행의 id를 돌려줍니다."""
    with db.cursor() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


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

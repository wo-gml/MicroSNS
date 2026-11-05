"""테스트 공통 설정.

테스트는 .env의 DB를 쓰지 않습니다. 환경 변수가 .env보다 우선하므로 아래 값으로 고정됩니다.
MySQL 테스트는 TEST_DB_USER를 지정했을 때만 실행되며 microsns_test DB만 만들고 지웁니다.
"""

import os
import tempfile

TEST_DB_NAME = "microsns_test"

os.environ.update(
    DB_HOST=os.environ.get("TEST_DB_HOST", "127.0.0.1"),
    DB_PORT=os.environ.get("TEST_DB_PORT", "3306"),
    DB_USER=os.environ.get("TEST_DB_USER", "root"),
    DB_PASSWORD=os.environ.get("TEST_DB_PASSWORD", ""),
    DB_NAME=TEST_DB_NAME,
    DB_TIME_ZONE="+09:00",
    JWT_SECRET="test-only-secret-" * 3,
    JWT_EXPIRE_MINUTES="60",
    COOKIE_SECURE="false",
    CORS_ORIGINS='["http://localhost:3000"]',
    UPLOAD_DIR=tempfile.mkdtemp(prefix="microsns-test-uploads-"),
)

import pymysql  # noqa: E402
import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import connect  # noqa: E402

# 공통 기반 검증용 최소 테이블입니다. 실제 스키마는 db/01_schema.sql에서 관리합니다.
TEST_TABLES = [
    """CREATE TABLE member (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(50) NOT NULL,
        bio VARCHAR(200),
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    )""",
    """CREATE TABLE post (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        member_id BIGINT NOT NULL,
        content VARCHAR(10) NOT NULL,
        FOREIGN KEY (member_id) REFERENCES member (id)
    )""",
    """CREATE TABLE follow (
        follower_id BIGINT NOT NULL,
        following_id BIGINT NOT NULL,
        PRIMARY KEY (follower_id, following_id),
        CONSTRAINT ck_follow_not_self CHECK (follower_id <> following_id)
    )""",
    """CREATE TABLE recruitment (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        capacity INT NOT NULL
    )""",
    """CREATE TABLE application (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        recruitment_id BIGINT NOT NULL,
        status ENUM('PENDING', 'APPROVED') NOT NULL DEFAULT 'PENDING'
    )""",
]
TABLE_NAMES = ["application", "recruitment", "follow", "post", "member"]


@pytest.fixture(scope="session")
def mysql_schema():
    if "TEST_DB_USER" not in os.environ:
        pytest.skip("MySQL 테스트를 실행하려면 TEST_DB_USER를 지정하세요.")
    settings = get_settings()
    admin = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        autocommit=True,
    )
    try:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
            cur.execute(f"CREATE DATABASE {TEST_DB_NAME} CHARACTER SET utf8mb4")
            cur.execute(f"USE {TEST_DB_NAME}")
            for ddl in TEST_TABLES:
                cur.execute(ddl)
        yield
    finally:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
        admin.close()


@pytest.fixture
def db(mysql_schema):
    """테이블을 비운 상태의 연결을 제공합니다."""
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in TABLE_NAMES:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    yield conn
    conn.close()

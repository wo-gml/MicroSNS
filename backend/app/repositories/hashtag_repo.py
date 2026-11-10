import re
from typing import List

from pymysql.connections import Connection

from app.db import execute, fetch_all, fetch_one, insert

# 프론트엔드 RichText와 같은 규칙입니다. 앞이 글자가 아닌 #단어만 해시태그로 봅니다.
_HASHTAG = re.compile(r"(?<!\w)#(\w+)")
MAX_NAME_LENGTH = 50  # hashtag.name VARCHAR(50)


def extract(content: str) -> List[str]:
    """글 내용의 해시태그. 컬럼보다 긴 태그는 저장하지 않습니다."""
    names = []
    for name in _HASHTAG.findall(content):
        if len(name) <= MAX_NAME_LENGTH and name not in names:
            names.append(name)
    return names


def attach(db: Connection, post_id: int, names: List[str]) -> None:
    """태그가 없으면 만들고 글에 연결합니다. 글 작성 트랜잭션 안에서 부릅니다."""
    hashtag_ids = []
    for name in names:
        # 이미 있는 태그면 LAST_INSERT_ID(id)로 그 id를 돌려받습니다.
        # 대소문자를 구분하지 않으므로 #SQL과 #sql은 같은 id가 됩니다.
        hashtag_id = insert(
            db,
            "INSERT INTO hashtag (name) VALUES (%s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)",
            (name,),
        )
        if hashtag_id not in hashtag_ids:
            hashtag_ids.append(hashtag_id)
    for hashtag_id in hashtag_ids:
        execute(
            db,
            "INSERT INTO post_hashtag (post_id, hashtag_id) VALUES (%s, %s)",
            (post_id, hashtag_id),
        )


def stat(db: Connection, name: str) -> dict:
    row = fetch_one(
        db,
        """
        SELECT COUNT(ph.post_id) AS post_count
        FROM hashtag h JOIN post_hashtag ph ON ph.hashtag_id = h.id
        WHERE h.name = %s
        """,
        (name,),
    )
    return {"name": name, "post_count": row["post_count"]}


def trending(db: Connection, limit: int) -> List[dict]:
    """글이 많이 달린 태그 순서입니다. 글이 모두 지워진 태그는 빠집니다."""
    return fetch_all(
        db,
        """
        SELECT h.name, COUNT(*) AS post_count
        FROM hashtag h JOIN post_hashtag ph ON ph.hashtag_id = h.id
        GROUP BY h.id, h.name
        ORDER BY post_count DESC, h.name
        LIMIT %s
        """,
        (limit,),
    )

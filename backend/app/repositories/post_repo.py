"""게시글과 게시글 사진(post_image).

목록은 한 페이지의 글을 먼저 조회한 뒤, 그 글들의 사진과 모집을 한 번에 더 조회해 붙입니다.
글마다 따로 조회하지 않으므로 쿼리 수는 페이지 크기와 상관없이 세 번입니다.
"""

from typing import List, Optional

from pymysql.connections import Connection

from app.db import execute, fetch_all, fetch_one, insert, placeholders
from app.repositories import recruitment_repo

_SELECT = """
    SELECT p.id, p.content, p.created_at,
           m.id AS author_id, m.name AS author_name,
           EXISTS (
               SELECT 1 FROM follow f
               WHERE f.follower_id = %(viewer)s AND f.following_id = p.member_id
           ) AS author_is_following,
           (SELECT COUNT(*) FROM post_like l WHERE l.post_id = p.id) AS like_count,
           (SELECT COUNT(*) FROM comment c WHERE c.post_id = p.id) AS comment_count,
           EXISTS (
               SELECT 1 FROM post_like l WHERE l.post_id = p.id AND l.member_id = %(viewer)s
           ) AS liked_by_me
    FROM post p
    JOIN member m ON m.id = p.member_id
"""

_PAGE = "ORDER BY p.created_at DESC, p.id DESC LIMIT %(limit)s OFFSET %(offset)s"


def _hydrate(db: Connection, rows: List[dict], viewer_id: Optional[int]) -> List[dict]:
    post_ids = [row["id"] for row in rows]
    images = {post_id: [] for post_id in post_ids}
    if post_ids:
        for image in fetch_all(
            db,
            f"""
            SELECT post_id, url FROM post_image
            WHERE post_id IN ({placeholders(post_ids)})
            ORDER BY post_id, sort_order
            """,
            post_ids,
        ):
            images[image["post_id"]].append(image["url"])
    recruitments = recruitment_repo.for_posts(db, post_ids, viewer_id)

    return [
        {
            "id": row["id"],
            "author": {
                "id": row["author_id"],
                "name": row["author_name"],
                "is_following": bool(row["author_is_following"]),
            },
            "content": row["content"],
            "image_urls": images[row["id"]],
            "created_at": row["created_at"],
            "like_count": row["like_count"],
            "comment_count": row["comment_count"],
            "liked_by_me": bool(row["liked_by_me"]),
            "recruitment": recruitments.get(row["id"]),
        }
        for row in rows
    ]


def _page(
    db: Connection, sql: str, viewer_id: Optional[int], limit: int, offset: int, **args
) -> List[dict]:
    params = {"viewer": viewer_id, "limit": limit, "offset": offset, **args}
    return _hydrate(db, fetch_all(db, sql, params), viewer_id)


def find(db: Connection, post_id: int) -> Optional[dict]:
    """권한 확인용입니다. 작성자 id(author_id)를 돌려줍니다."""
    return fetch_one(
        db, "SELECT id, member_id AS author_id FROM post WHERE id = %s", (post_id,)
    )


def out(db: Connection, post_id: int, viewer_id: Optional[int]) -> Optional[dict]:
    rows = fetch_all(db, _SELECT + "WHERE p.id = %(id)s", {"viewer": viewer_id, "id": post_id})
    posts = _hydrate(db, rows, viewer_id)
    return posts[0] if posts else None


def feed(db: Connection, viewer_id: int, limit: int, offset: int) -> List[dict]:
    """내 글과 내가 팔로우한 회원의 글."""
    sql = (
        _SELECT
        + """
        WHERE p.member_id = %(viewer)s
           OR p.member_id IN (SELECT following_id FROM follow WHERE follower_id = %(viewer)s)
        """
        + _PAGE
    )
    return _page(db, sql, viewer_id, limit, offset)


def by_author(
    db: Connection, author_id: int, viewer_id: Optional[int], limit: int, offset: int
) -> List[dict]:
    sql = _SELECT + "WHERE p.member_id = %(author)s " + _PAGE
    return _page(db, sql, viewer_id, limit, offset, author=author_id)


def liked_by(
    db: Connection, member_id: int, viewer_id: Optional[int], limit: int, offset: int
) -> List[dict]:
    sql = (
        _SELECT
        + "JOIN post_like liked ON liked.post_id = p.id AND liked.member_id = %(member)s "
        + _PAGE
    )
    return _page(db, sql, viewer_id, limit, offset, member=member_id)


def by_hashtag(
    db: Connection, name: str, viewer_id: Optional[int], limit: int, offset: int
) -> List[dict]:
    sql = (
        _SELECT
        + """
        JOIN post_hashtag ph ON ph.post_id = p.id
        JOIN hashtag h ON h.id = ph.hashtag_id AND h.name = %(tag)s
        """
        + _PAGE
    )
    return _page(db, sql, viewer_id, limit, offset, tag=name)


def create(db: Connection, author_id: int, content: str, image_urls: List[str]) -> int:
    """글과 사진을 저장합니다. 글 작성 트랜잭션 안에서 부릅니다."""
    post_id = insert(
        db, "INSERT INTO post (member_id, content) VALUES (%s, %s)", (author_id, content)
    )
    for sort_order, url in enumerate(image_urls):
        execute(
            db,
            "INSERT INTO post_image (post_id, url, sort_order) VALUES (%s, %s, %s)",
            (post_id, url, sort_order),
        )
    return post_id


def delete(db: Connection, post_id: int) -> None:
    """댓글, 사진, 좋아요, 해시태그 연결, 모집, 지원, 알림은 DB가 함께 지웁니다(ON DELETE CASCADE)."""
    execute(db, "DELETE FROM post WHERE id = %s", (post_id,))

from fastapi import APIRouter

from app.deps import DbConn

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DbConn) -> dict:
    """서버와 DB 연결을 확인합니다."""
    with db.cursor() as cur:
        cur.execute("SELECT 1")
    return {"status": "ok"}

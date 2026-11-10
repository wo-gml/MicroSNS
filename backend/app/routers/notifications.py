from fastapi import APIRouter

from app.deps import DbConn, LoginUser
from app.pagination import PageQuery, PageResponse
from app.repositories import notification_repo
from app.schemas.error import errors
from app.schemas.notification import NotificationOut, UnreadCount

router = APIRouter(prefix="/notifications", tags=["알림"])


@router.get(
    "",
    response_model=PageResponse[NotificationOut],
    summary="알림 목록 조회",
    responses=errors(401, 422),
)
def list_notifications(db: DbConn, user: LoginUser, page: PageQuery):
    rows = notification_repo.list_for(db, user.id, limit=page.fetch_limit, offset=page.offset)
    return PageResponse.from_rows(rows, page)


@router.get(
    "/unread-count",
    response_model=UnreadCount,
    summary="안 읽은 알림 수 조회",
    responses=errors(401),
)
def unread_count(db: DbConn, user: LoginUser):
    return {"count": notification_repo.unread_count(db, user.id)}


@router.post(
    "/{notification_id}/read",
    status_code=204,
    summary="알림 읽음 처리",
    description="내 알림만 처리합니다.",
    responses=errors(401, 422),
)
def mark_read(notification_id: int, db: DbConn, user: LoginUser):
    notification_repo.mark_read(db, notification_id, user.id)

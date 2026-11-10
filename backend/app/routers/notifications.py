from fastapi import APIRouter

from app.mock import store
from app.mock.deps import LoginUser
from app.pagination import PageQuery, PageResponse
from app.schemas.error import errors
from app.schemas.notification import NotificationOut, UnreadCount

router = APIRouter(prefix="/notifications", tags=["알림"])


@router.get(
    "",
    response_model=PageResponse[NotificationOut],
    summary="알림 목록 조회",
    responses=errors(401, 422),
)
def list_notifications(user: LoginUser, page: PageQuery):
    rows = store.list_notifications(user.id, limit=page.fetch_limit, offset=page.offset)
    return PageResponse.from_rows(rows, page)


@router.get(
    "/unread-count",
    response_model=UnreadCount,
    summary="안 읽은 알림 수 조회",
    responses=errors(401),
)
def unread_count(user: LoginUser):
    return {"count": store.unread_count(user.id)}


@router.post(
    "/{notification_id}/read",
    status_code=204,
    summary="알림 읽음 처리",
    description="내 알림만 처리합니다.",
    responses=errors(401, 422),
)
def mark_read(notification_id: int, user: LoginUser):
    store.mark_read(notification_id, user.id)

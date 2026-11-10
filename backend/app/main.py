from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import BACKEND_DIR, get_settings
from app.errors import register_error_handlers
from app.routers import (
    auth,
    comments,
    follows,
    hashtags,
    health,
    likes,
    notifications,
    posts,
    recruitments,
    uploads,
    users,
)

API_DESCRIPTION = """
스터디·프로젝트 모집형 microSNS API입니다.

- **데이터:** DB 연결 전까지 메모리의 예시 데이터를 씁니다. 서버를 끄면 처음 상태로 돌아갑니다.
- **로그인:** `POST /auth/login`을 실행하면 쿠키가 심어져 이후 요청에 자동으로 포함됩니다.
  샘플 계정은 `admin@test.com` / `test1234`입니다.
- **에러:** 모든 에러는 `{"error": {"code", "message", "details"}}` 형식입니다.
- **목록:** `limit`, `offset`으로 조회하고, `has_more`로 다음 페이지가 있는지 알려 줍니다.
"""

# 예시 글의 사진. app/mock/data.py와 db/02_seed.sql의 예시 글이 씁니다.
MOCK_PHOTOS_DIR = BACKEND_DIR.parent / "frontend" / "mock" / "photos"


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_settings()  # .env에 빠진 값이 있으면 첫 요청이 아니라 서버 시작 시 실패합니다.
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="microSNS API", description=API_DESCRIPTION, lifespan=lifespan)
    register_error_handlers(app)

    # 메모리 저장소는 트랜잭션이 없으므로 요청을 하나씩 처리합니다. DB로 바꾸면 지웁니다.
    store_lock = anyio.Lock()

    @app.middleware("http")
    async def serialize_requests(request: Request, call_next):
        async with store_lock:
            return await call_next(request)

    # 프론트엔드는 Next.js 프록시(같은 출처)로 호출하므로 이 설정은 백엔드를 직접 호출할 때만 쓰입니다.
    # 쿠키 인증을 쓰므로 출처를 와일드카드로 열지 않습니다.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(posts.router)
    app.include_router(likes.router)
    app.include_router(comments.router)
    app.include_router(recruitments.router)
    app.include_router(users.router)
    app.include_router(follows.router)
    app.include_router(hashtags.router)
    app.include_router(notifications.router)
    app.include_router(uploads.router)
    # 폴더가 아직 없어도 서버는 뜨고, 없는 파일은 404로 응답합니다.
    app.mount(
        "/uploads",
        StaticFiles(directory=get_settings().upload_dir, check_dir=False),
        name="uploads",
    )
    app.mount(
        "/mock-photos",
        StaticFiles(directory=MOCK_PHOTOS_DIR, check_dir=False),
        name="mock-photos",
    )
    return app


app = create_app()

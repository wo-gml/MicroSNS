from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import register_error_handlers
from app.routers import health


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_settings()  # .env에 빠진 값이 있으면 첫 요청이 아니라 서버 시작 시 실패합니다.
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="microSNS API", lifespan=lifespan)
    register_error_handlers(app)
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
    return app


app = create_app()

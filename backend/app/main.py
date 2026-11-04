from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.errors import register_error_handlers
from app.routers import health


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_settings()  # .env에 빠진 값이 있으면 첫 요청이 아니라 서버 시작 시 실패합니다.
    yield


def create_app() -> FastAPI:
    # CORS 설정은 두지 않습니다. 브라우저는 Next.js 프록시를 통해 같은 출처로 호출합니다.
    app = FastAPI(title="microSNS API", lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(health.router)
    return app


app = create_app()

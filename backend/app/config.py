"""환경 변수(.env)를 읽어 설정 객체로 제공합니다."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str = "microsns"
    db_time_zone: str = Field(default="+09:00", pattern=r"^[+-]\d{2}:\d{2}$")

    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=1440, gt=0)

    cookie_secure: bool = False

    # 브라우저가 백엔드를 직접 호출할 수 있는 출처. .env에서는 JSON 배열로 씁니다.
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

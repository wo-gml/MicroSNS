from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, UploadFile

from app.config import get_settings
from app.errors import BadRequestError
from app.mock.deps import LoginUser
from app.schemas.error import errors
from app.schemas.post import UploadOut

router = APIRouter(tags=["파일"])

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _image_extension(head: bytes) -> Optional[str]:
    """파일 이름이나 Content-Type은 믿을 수 없으므로 내용으로 형식을 확인합니다."""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


@router.post(
    "/uploads",
    status_code=201,
    response_model=UploadOut,
    summary="사진 업로드",
    description="JPEG, PNG, GIF, WebP를 5MB까지 받습니다. 돌려준 `url`을 글 작성의 `image_urls`에 넣습니다.",
    responses=errors(400, 401, 422),
)
def upload_image(file: UploadFile, _: LoginUser):
    content = file.file.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise BadRequestError("사진은 5MB까지 올릴 수 있습니다.")
    extension = _image_extension(content[:12])
    if extension is None:
        raise BadRequestError("JPEG, PNG, GIF, WebP 사진만 올릴 수 있습니다.")

    upload_dir = get_settings().upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}.{extension}"
    (upload_dir / name).write_bytes(content)
    # 브라우저는 Next.js 프록시(/api)를 거쳐 사진을 받습니다.
    return {"url": f"/api/uploads/{name}"}

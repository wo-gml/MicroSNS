# microSNS 백엔드

FastAPI + MySQL. ORM 없이 `repositories/`에 SQL을 직접 작성합니다.

> **현재 상태:** 스키마가 나오기 전이라 API는 `app/mock/`의 메모리 저장소로 동작합니다. 서버를 끄면 데이터가 처음 상태로 돌아가고, 업로드한 사진만 `backend/uploads/`에 남습니다. MySQL이 없으면 `/health`만 503을 돌려줍니다. [DB로 바꾸는 방법](#db로-바꾸는-방법)을 참고하세요.

## 실행

1. MySQL에서 DB를 만듭니다. DB로 바꾸기 전까지는 건너뛰어도 됩니다.

   ```sql
   CREATE DATABASE microsns CHARACTER SET utf8mb4;
   ```

   레포 루트에서 ERD의 11개 테이블을 만듭니다. 기존 테이블을 지우고 다시 만드므로 데이터도 사라집니다.

   ```bash
   mysql -u root -p microsns < db/01_schema.sql
   ```

2. 패키지를 설치합니다. (Windows는 `.venv\Scripts\activate`)

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. `.env.example`을 `.env`로 복사하고 `JWT_SECRET`을 채웁니다. `DB_PASSWORD`는 DB를 쓸 때 채웁니다.

   ```bash
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. 서버를 실행합니다.

   ```bash
   uvicorn app.main:app --reload
   ```

   - API 문서(Swagger): http://localhost:8000/docs
   - 연결 확인: http://localhost:8000/health (MySQL 필요)

   Swagger에서 `POST /auth/login`을 실행하면 쿠키가 심어져, 로그인이 필요한 API도 바로 실행해 볼 수 있습니다.

## 예시 계정

비밀번호는 모두 `test1234`입니다. 프론트엔드의 `npm run dev:mock`과 같은 예시 데이터입니다.

| 이메일 | 이름 |
| --- | --- |
| `admin@test.com` | 김민준 (회원 2) |
| `user1@test.com` ~ `user8@test.com` | 다른 예시 회원. 번호가 회원 id입니다. 2번은 위 계정을 씁니다. |

## DB로 바꾸는 방법

1. `repositories/`에 `app/mock/store.py`와 같은 이름의 함수를 SQL로 작성합니다. 첫 인자로 `db`를 받습니다.
2. 라우터에서 `store.xxx(...)`를 `xxx_repo.xxx(db, ...)`로 바꾸고, `db: DbConn`을 추가합니다.
3. 라우터의 `app.mock.deps` import를 `app.deps`로 바꿉니다.
4. 모든 라우터를 바꾸면 `app/mock/`과 `app/main.py`의 `serialize_requests`, `/mock-photos` 설정을 지웁니다.

`db/01_schema.sql`의 enum 값은 API와 같은 소문자(`pending`, `accepted`, `rejected` 등)입니다. 지원 취소는 상태를 바꾸지 않고 행을 지웁니다. 글을 지우면 딸린 행이 DB에서 함께 지워지므로(ON DELETE CASCADE) `delete_post`는 `DELETE FROM post` 한 줄이면 됩니다.

## 테스트

DB 없이 실행하면 MySQL 테스트는 건너뜁니다.

```bash
pytest
```

실제 MySQL 테스트까지 실행합니다. `.env`의 DB는 쓰지 않고, `microsns_test` DB를 만들었다가 지웁니다.

```bash
TEST_DB_USER=root TEST_DB_PASSWORD=비밀번호 pytest
```

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| `app/db.py` | DB 연결, `transaction()` |
| `app/deps.py` | 라우터에 주입하는 `DbConn`, `LoginUser` |
| `app/security.py` | 비밀번호 해싱, JWT, 인증 쿠키 |
| `app/errors.py` | `NotFoundError` 등 공통 에러, MySQL 에러 변환 |
| `app/pagination.py` | `PageQuery`, `PageResponse` |
| `app/routers/` | API 주소. SQL을 쓰지 않습니다. |
| `app/mock/` | DB 연결 전까지 쓰는 예시 데이터와 메모리 저장소 |
| `app/repositories/` | SQL 쿼리 |
| `app/schemas/` | 요청/응답 형식 |

새 라우터는 `app/main.py`의 `create_app()`에 `include_router`로 등록합니다.

## 작성 규칙

- 라우터는 `async def`가 아니라 `def`로 작성합니다. PyMySQL이 동기 방식이기 때문입니다.
- SQL 값은 `%s` 파라미터로 전달하고 문자열로 이어 붙이지 않습니다.
- 쿼리 하나는 자동으로 저장됩니다. 여러 쿼리를 묶을 때만 `with transaction(db):`를 씁니다.
- `SELECT ... FOR UPDATE`는 트랜잭션의 첫 쿼리로 실행합니다. 이유는 `app/db.py`에 있습니다.
- 샘플 계정의 비밀번호 해시는 아래 명령으로 만듭니다.

  ```bash
  python -c "from app.security import hash_password; print(hash_password('test1234'))"
  ```

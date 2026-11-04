# microSNS 백엔드

FastAPI + MySQL. ORM 없이 `repositories/`에 SQL을 직접 작성합니다.

## 실행

1. MySQL에서 DB를 만듭니다.

   ```sql
   CREATE DATABASE microsns CHARACTER SET utf8mb4;
   ```

2. 패키지를 설치합니다. (Windows는 `.venv\Scripts\activate`)

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. `.env.example`을 `.env`로 복사하고 `DB_PASSWORD`, `JWT_SECRET`을 채웁니다.

   ```bash
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. 서버를 실행합니다.

   ```bash
   uvicorn app.main:app --reload
   ```

   - 연결 확인: http://localhost:8000/health
   - API 문서: http://localhost:8000/docs

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

# microSNS 백엔드

FastAPI + MySQL. ORM 없이 `repositories/`에 SQL을 직접 작성합니다.

모든 API가 MySQL에 데이터를 저장합니다. MySQL에 연결할 수 없으면 API는 503(`DB_UNAVAILABLE`)을 돌려줍니다. 업로드한 사진 파일은 `backend/uploads/`에 저장합니다.

## 실행

1. MySQL에서 DB를 만듭니다.

   ```sql
   CREATE DATABASE microsns CHARACTER SET utf8mb4;
   ```

   레포 루트에서 ERD의 11개 테이블을 만듭니다. 기존 테이블을 지우고 다시 만드므로 데이터도 사라집니다.

   ```bash
   mysql -u root -p microsns < db/01_schema.sql
   ```

   예시 데이터는 테이블 담당자가 `db/seed/`에 파일을 나눠 관리합니다. 참조 순서대로 회원부터 넣습니다.

   ```bash
   mysql -u root -p microsns < db/seed/members.sql
   mysql -u root -p microsns < db/seed/posts.sql
   mysql -u root -p microsns < db/seed/hashtags.sql
   ```

   게시글 시드는 회원 id 1~5를 작성자로 씁니다. 빈 테이블에 회원 시드를 먼저 넣어야 id가 맞습니다.
   앱에서 쓴 글은 API가 내용의 `#태그`를 저장하지만, 시드는 SQL로 바로 넣으므로 `hashtags.sql`로 따로 넣습니다. 게시글 시드의 태그를 바꾸면 이 파일도 함께 고칩니다.

   시드의 회원은 비밀번호 해시가 예시 문자열이라 로그인할 수 없습니다. 화면을 확인할 때는 회원가입으로 계정을 만듭니다.

2. 패키지를 설치합니다. (Windows는 `.venv\Scripts\activate`)

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. `.env.example`을 `.env`로 복사하고 `DB_PASSWORD`와 `JWT_SECRET`을 채웁니다.

   ```bash
   cp .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. 서버를 실행합니다.

   ```bash
   uvicorn app.main:app --reload
   ```

   - API 문서(Swagger): http://localhost:8000/docs
   - 연결 확인: http://localhost:8000/health

   Swagger에서 `POST /auth/signup`이나 `POST /auth/login`을 실행하면 쿠키가 심어져, 로그인이 필요한 API도 바로 실행해 볼 수 있습니다.

## DB 사용 방식

- 라우터는 `repositories/`의 함수만 부르고 SQL을 쓰지 않습니다. 리포지토리 함수는 첫 인자로 `db`를 받습니다.
- 함께 성공하거나 실패해야 하는 쓰기는 `with transaction(db):`로 묶습니다. 예: 좋아요와 알림, 글과 사진·해시태그·모집.
- 지원 수락은 모집 행을 `SELECT ... FOR UPDATE`로 잠근 뒤 정원을 확인합니다. 동시에 수락해도 정원을 넘지 않습니다.
- 좋아요, 팔로우, 지원의 중복은 DB의 PK/UNIQUE가 막습니다. 동시에 두 번 요청해도 한 번만 저장됩니다.
- 글을 지우면 딸린 댓글, 사진, 좋아요, 해시태그 연결, 모집, 지원, 알림은 DB가 지웁니다(ON DELETE CASCADE).
- 해시태그는 글을 쓸 때 내용의 `#단어`를 `hashtag`, `post_hashtag`에 저장합니다. 대소문자를 구분하지 않습니다(`#SQL` = `#sql`).
- DATETIME에는 시간대가 없으므로 `app/db.py`가 연결 시간대(`DB_TIME_ZONE`, 기본 +09:00) 기준으로 읽고 씁니다. API는 시간대가 붙은 시각을 주고받습니다.
- enum 값은 API와 같은 소문자(`pending`, `accepted`, `rejected` 등)입니다. 지원 취소는 상태를 바꾸지 않고 행을 지웁니다.

## 테스트

DB 없이 실행하면 MySQL이 필요한 테스트(API 테스트 포함)는 건너뜁니다.

```bash
pytest
```

MySQL 테스트까지 실행합니다. `.env`의 DB는 쓰지 않고, `microsns_test` DB에 `db/01_schema.sql`로 테이블을 만들었다가 지웁니다.

```bash
TEST_DB_USER=root TEST_DB_PASSWORD=비밀번호 pytest
```

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| `app/db.py` | DB 연결, `transaction()`, 시간대 변환, 쿼리 도우미 |
| `app/deps.py` | 라우터에 주입하는 `DbConn`, `LoginUser`, `OptionalUser` |
| `app/security.py` | 비밀번호 해싱, JWT, 인증 쿠키 |
| `app/errors.py` | `NotFoundError` 등 공통 에러, MySQL 에러 변환 |
| `app/pagination.py` | `PageQuery`, `PageResponse` |
| `app/routers/` | API 주소. SQL을 쓰지 않습니다. |
| `app/repositories/` | SQL 쿼리. 테이블 영역별 파일(`post_repo.py`, `recruitment_repo.py` 등) |
| `app/schemas/` | 요청/응답 형식 |

새 라우터는 `app/main.py`의 `create_app()`에 `include_router`로 등록합니다.

## 작성 규칙

- 라우터는 `async def`가 아니라 `def`로 작성합니다. PyMySQL이 동기 방식이기 때문입니다.
- SQL 값은 `%s` 파라미터로 전달하고 문자열로 이어 붙이지 않습니다.
- 쿼리 하나는 자동으로 저장됩니다. 여러 쿼리를 묶을 때만 `with transaction(db):`를 씁니다.
- `SELECT ... FOR UPDATE`는 트랜잭션의 첫 쿼리로 실행합니다. 이유는 `app/db.py`에 있습니다.
- 시드 회원의 비밀번호 해시는 아래 명령으로 만듭니다.

  ```bash
  python -c "from app.security import hash_password; print(hash_password('test1234'))"
  ```

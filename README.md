# Mini Twitter

팀 프로젝트로 만든 미니 트위터다. 글 쓰기(사진, 해시태그), 댓글, 좋아요, 팔로우, 알림이 있고 글에 모집 글을 달아 지원을 받을 수도 있다.

## 기술 스택

- Frontend: Next.js 16, React 19, TypeScript
- Backend: FastAPI (Python), PyMySQL
- DB: MySQL 8.0.16 이상
- 인증: JWT 쿠키, 비밀번호는 Argon2로 해싱
- 테스트: pytest

ORM은 쓰지 않고 SQL을 `backend/app/repositories/`에 직접 작성했다. 프론트에서 `/api/*`로 보내는 요청은 Next.js가 FastAPI로 넘겨주기 때문에 CORS 설정은 따로 하지 않아도 된다.

## 실행 방법

MySQL(8.0.16 이상), Python 3, Node.js가 설치되어 있어야 한다.

### 1. DB

```bash
mysql -u root -p
```

`Enter password:`가 뜨면 MySQL 설치할 때 정한 root 비밀번호를 입력한다. 입력해도 화면에 아무것도 안 보이는데 정상이다. 들어가서 DB를 만들고 `exit`로 나온다.

```sql
CREATE DATABASE microsns CHARACTER SET utf8mb4;
```

레포 루트에서 스키마와 시드를 넣는다. 시드는 회원 → 게시글 → 해시태그 순서로 넣어야 한다.

```bash
mysql -u root -p microsns < db/01_schema.sql
mysql -u root -p microsns < db/seed/members.sql
mysql -u root -p microsns < db/seed/posts.sql
mysql -u root -p microsns < db/seed/hashtags.sql
```

명령마다 비밀번호를 다시 물어본다. `-p1234`처럼 붙여 쓰면 묻지 않지만 터미널 기록에 비밀번호가 남으므로 권장하지 않는다.

`01_schema.sql`은 테이블을 지우고 새로 만들기 때문에 다시 실행하면 데이터가 사라진다. 시드 회원으로는 로그인할 수 없으니 화면을 볼 때는 회원가입해서 쓴다.

### 2. 백엔드

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows는 .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에서 `DB_PASSWORD`, `JWT_SECRET` 두 개는 꼭 채워야 한다. `DB_PASSWORD`는 위에서 `mysql -p` 할 때 넣은 비밀번호와 같다.

```env
DB_USER=root
DB_PASSWORD=MySQL_root_비밀번호
JWT_SECRET=아래_명령으로_만든_값
```

`JWT_SECRET`은 아래 명령으로 만든다.

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
uvicorn app.main:app --reload
```

http://localhost:8000/docs 에서 Swagger로 API를 볼 수 있고, http://localhost:8000/health 로 DB 연결을 확인할 수 있다. 비밀번호가 틀리면 API가 503(`DB_UNAVAILABLE`)을 돌려준다.

`.env`는 git에 올리지 않는다.

### 3. 프론트엔드

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

http://localhost:3000 에 접속해서 회원가입하면 된다.

테스트 실행 방법과 백엔드 코드 규칙은 [`backend/README.md`](backend/README.md)에 정리했다.

## 폴더 구조

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py          # 앱 생성, 라우터 등록
│   │   ├── db.py            # DB 연결, 트랜잭션
│   │   ├── security.py      # 비밀번호 해싱, JWT
│   │   ├── routers/         # API
│   │   ├── repositories/    # SQL 쿼리
│   │   └── schemas/         # 요청/응답 모델
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/      # 로그인, 회원가입
│       │   └── (main)/      # 피드, 글 상세, 프로필, 해시태그, 알림
│       ├── api/             # 백엔드 호출
│       ├── components/
│       └── hooks/
├── db/
│   ├── 01_schema.sql        # 테이블 생성
│   └── seed/                # 예시 데이터 (테이블 담당자별로 파일 분리)
└── docs/
    ├── erd/erd.png
    ├── requirements.md      # 기능 명세
    ├── normalization.md     # 정규화
    └── presentation/        # 발표 자료
```

`backend/app`에는 이 밖에 `config.py`, `deps.py`, `errors.py`, `pagination.py`가 있다. 파일별 역할은 `backend/README.md`에 있다.

## 팀원 역할

| 이름 | 역할 |
| --- | --- |
|  |  |

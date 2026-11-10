# Mini Twitter

MySQL 기반 미니 트위터 프로젝트입니다.

- 프론트엔드: Next.js (TypeScript)
- 백엔드: FastAPI
- DB: MySQL

## 실행 방법

1. DB와 백엔드: [`backend/README.md`](backend/README.md)를 따라 MySQL에 테이블을 만들고 서버를 실행합니다.
2. 프론트엔드:

   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

   http://localhost:3000 에서 회원가입한 뒤 사용합니다.

API 문서(Swagger)는 백엔드를 실행한 뒤 http://localhost:8000/docs 에서 봅니다.

## DB 파일

SQL은 모두 `db/`에 둡니다.

| 위치 | 내용 |
| --- | --- |
| `db/01_schema.sql` | 테이블, 제약 조건, 인덱스 (ERD: [`docs/erd/erd.png`](docs/erd/erd.png)) |
| `db/seed/<테이블 영역>.sql` | 예시 데이터. 테이블 담당자가 파일을 나눠 관리합니다. 예: `db/seed/members.sql`, `db/seed/posts.sql` |

실행 순서는 [`backend/README.md`](backend/README.md)의 실행 1단계를 따릅니다.

## 팀원 역할

| 이름 | 역할 |
| --- | --- |
|  |  |

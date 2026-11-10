# Mini Twitter

MySQL 기반 미니 트위터 프로젝트입니다.

- 프론트엔드: Next.js (TypeScript)
- 백엔드: FastAPI
- DB: MySQL

## 실행 방법

1. 백엔드: [`backend/README.md`](backend/README.md)를 따라 서버를 실행합니다. DB 연결 전까지 API는 메모리의 예시 데이터를 쓰므로 MySQL이 없어도 됩니다.
2. 프론트엔드:

   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

   http://localhost:3000 에서 `admin@test.com` / `test1234` 로 로그인합니다.

API 문서(Swagger)는 백엔드를 실행한 뒤 http://localhost:8000/docs 에서 봅니다.

## 팀원 역할

| 이름 | 역할 |
| --- | --- |
|  |  |

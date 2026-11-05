# Mini Twitter

MySQL 기반 미니 트위터 프로젝트입니다.

- 프론트엔드: Next.js (TypeScript)
- 백엔드: FastAPI
- DB: MySQL

## 실행 방법

1. DB: `db/`의 SQL을 실행합니다. (작성 예정)
2. 백엔드: [`backend/README.md`](backend/README.md)를 따라 서버를 실행합니다.
3. 프론트엔드:

   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   npm run dev
   ```

   http://localhost:3000 에서 확인합니다.

### 백엔드 없이 화면 확인하기

MySQL과 FastAPI 없이 예시 데이터로 프론트엔드를 실행합니다.

```bash
cd frontend
npm install
npm run dev:mock
```

http://localhost:3000 에서 `minjun@example.com` / `test1234` 로 로그인합니다.

- 데이터는 메모리에만 있어 서버를 끄면 처음 상태로 돌아갑니다.
- API 형식은 `frontend/src/api`의 임시 형식이며, 실제 백엔드와 다를 수 있습니다.
- 다른 포트를 쓰려면 `npm run dev:mock -- -p 3001`처럼 실행합니다. 목 API 포트(기본 8765)는 `MOCK_PORT`로 바꿉니다.

## 팀원 역할

| 이름 | 역할 |
| --- | --- |
|  |  |

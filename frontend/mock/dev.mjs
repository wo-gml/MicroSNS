// npm run dev:mock: 목 API와 Next.js 개발 서버를 함께 실행합니다.
// .env.local보다 여기서 넘기는 API_URL이 우선하므로 설정 파일을 바꿀 필요가 없습니다.
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SAMPLE_ACCOUNT, startMockServer } from "./server.mjs";

const PORT = Number(process.env.MOCK_PORT ?? 8765);
const FRONTEND_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const NEXT_BIN = path.join(FRONTEND_DIR, "node_modules", "next", "dist", "bin", "next");

let server;
try {
  server = await startMockServer(PORT);
} catch (error) {
  if (error.code !== "EADDRINUSE") throw error;
  console.error(`목 API 포트 ${PORT}을 이미 사용 중입니다. MOCK_PORT로 다른 포트를 지정해 주세요.`);
  process.exit(1);
}

console.log(`목 API: http://127.0.0.1:${PORT}`);
console.log(`샘플 계정: ${SAMPLE_ACCOUNT.email} / ${SAMPLE_ACCOUNT.password}\n`);

// npm run dev:mock -- -p 3001 처럼 넘긴 옵션은 next dev로 전달합니다.
const next = spawn(process.execPath, [NEXT_BIN, "dev", ...process.argv.slice(2)], {
  cwd: FRONTEND_DIR,
  stdio: "inherit",
  env: { ...process.env, API_URL: `http://127.0.0.1:${PORT}` },
});

next.on("exit", (code) => {
  server.close();
  process.exit(code ?? 0);
});
next.on("error", (error) => {
  console.error(error);
  server.close();
  process.exit(1);
});

// 터미널의 Ctrl+C는 next에도 전달되므로, 여기서는 next가 끝나기를 기다립니다.
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => next.kill(signal));
}

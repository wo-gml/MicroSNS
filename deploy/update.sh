#!/usr/bin/env bash
# main에 올라온 최신 코드를 서버에 반영한다: bash deploy/update.sh
# DB 스키마 변경은 반영하지 않는다. 필요하면 SQL을 직접 실행한다.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

git pull --ff-only
backend/.venv/bin/pip install -r backend/requirements.txt -q
(cd frontend && npm ci --no-audit --no-fund && npm run build)
sudo systemctl restart microsns-backend microsns-frontend
echo "반영했다. 상태 확인: systemctl status microsns-backend microsns-frontend"

#!/usr/bin/env bash
# 오라클 클라우드 Ubuntu 서버에 microSNS를 설치하고 실행한다.
# 레포를 받은 뒤 레포 루트에서 일반 사용자(ubuntu)로 실행한다: bash deploy/setup.sh
# 다시 실행해도 된다. 이미 있는 DB 데이터와 backend/.env는 건드리지 않는다.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_USER="$(id -un)"
NODE_MAJOR=24
DB_NAME=microsns
DB_USER=microsns

log() { printf '\n==> %s\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then
  echo "root가 아니라 일반 사용자(ubuntu)로 실행한다. 필요한 곳에서 sudo를 쓴다."
  exit 1
fi

log "1/8 메모리가 작으면 스왑 2GB 만들기"
mem_mb=$(free -m | awk '/^Mem:/{print $2}')
if [ "$mem_mb" -lt 3000 ] && [ -z "$(swapon --show)" ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

log "2/8 패키지 설치 (MySQL, nginx, Python, Node.js)"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  mysql-server nginx python3-venv python3-pip git curl ca-certificates iptables-persistent
node_major=0
if command -v node >/dev/null; then
  node_major=$(node -p 'process.versions.node.split(".")[0]')
fi
if [ "$node_major" -lt 20 ]; then
  # Next.js 16은 Node.js 20.9 이상이 필요하다. Ubuntu 기본 패키지는 버전이 낮을 수 있다.
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | sudo -E bash -
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
fi

log "3/8 서버 방화벽에서 80, 443 포트 열기"
# 오라클 Ubuntu 이미지는 iptables가 22번 말고는 막아 둔다. 콘솔의 보안 목록과 별개로 열어야 한다.
for port in 80 443; do
  if ! sudo iptables -C INPUT -p tcp -m state --state NEW --dport "$port" -j ACCEPT 2>/dev/null; then
    sudo iptables -I INPUT -p tcp -m state --state NEW --dport "$port" -j ACCEPT
  fi
done
sudo netfilter-persistent save

log "4/8 MySQL DB와 계정 만들기"
sudo systemctl enable --now mysql
ENV_FILE="$APP_DIR/backend/.env"
if [ -f "$ENV_FILE" ]; then
  DB_PASSWORD=$(grep '^DB_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)
else
  DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
fi
sudo mysql <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
SQL
table_count=$(sudo mysql -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${DB_NAME}'")
if [ "$table_count" -eq 0 ]; then
  cat "$APP_DIR/db/01_schema.sql" "$APP_DIR/db/seed/members.sql" \
      "$APP_DIR/db/seed/posts.sql" "$APP_DIR/db/seed/hashtags.sql" | sudo mysql "$DB_NAME"
else
  echo "테이블이 이미 있어서 스키마와 시드는 건너뛴다."
fi

log "5/8 백엔드 설치"
cd "$APP_DIR/backend"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
if [ ! -f .env ]; then
  JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  (
    umask 077
    cat > .env <<ENV
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_TIME_ZONE=+09:00
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRE_MINUTES=1440
# HTTPS를 붙이면 true로 바꾼다.
COOKIE_SECURE=false
ENV
  )
fi
mkdir -p uploads

log "6/8 프론트엔드 빌드"
cd "$APP_DIR/frontend"
# localhost는 IPv6(::1)로 먼저 붙을 수 있어서 127.0.0.1로 적는다.
echo "API_URL=http://127.0.0.1:8000" > .env.local
npm ci --no-audit --no-fund
npm run build

log "7/8 백엔드와 프론트를 서비스로 등록"
for svc in microsns-backend microsns-frontend; do
  sed -e "s|__APP_DIR__|${APP_DIR}|g" -e "s|__APP_USER__|${APP_USER}|g" \
    "$APP_DIR/deploy/${svc}.service" | sudo tee "/etc/systemd/system/${svc}.service" >/dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable microsns-backend microsns-frontend
sudo systemctl restart microsns-backend microsns-frontend

log "8/8 nginx 설정"
SITE=/etc/nginx/sites-available/microsns
if [ -f "$SITE" ] && grep -q "managed by Certbot" "$SITE"; then
  echo "HTTPS 설정이 들어간 nginx 파일이 있어서 덮어쓰지 않는다."
else
  sudo cp "$APP_DIR/deploy/nginx.conf" "$SITE"
fi
sudo ln -sf "$SITE" /etc/nginx/sites-enabled/microsns
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx

log "확인"
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null http://127.0.0.1/ && curl -fsS -o /dev/null http://127.0.0.1/api/health; then
    echo "프론트와 백엔드가 모두 응답한다. 브라우저에서 http://<서버 공인 IP>/ 로 접속한다."
    exit 0
  fi
  sleep 2
done
echo "60초 안에 응답이 없다. deploy/README.md의 '문제가 생겼을 때'를 본다."
exit 1

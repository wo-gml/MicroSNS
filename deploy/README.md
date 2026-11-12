# 배포 (오라클 클라우드 무료 서버)

오라클 클라우드 Always Free 서버 한 대에 MySQL, 백엔드, 프론트를 모두 올린다. 로컬과 같은 구조라 코드를 고치지 않아도 된다.

```text
브라우저 ──80/443──> nginx ─┬─ /api/* ──> FastAPI (127.0.0.1:8000) ──> MySQL
                            └─ 나머지 ──> Next.js (127.0.0.1:3000)
```

| 파일 | 내용 |
| --- | --- |
| `setup.sh` | 패키지 설치, 방화벽, DB, 백엔드, 프론트 빌드, 서비스 등록, nginx까지 한 번에 한다 |
| `update.sh` | main의 최신 코드를 받아 다시 빌드하고 재시작한다 |
| `microsns-backend.service`, `microsns-frontend.service` | 서버가 켜질 때 자동으로 실행되게 하는 systemd 설정 |
| `nginx.conf` | 80 포트로 들어온 요청을 백엔드와 프론트로 나눈다 |

## 1. 오라클 클라우드에서 서버 만들기

이 단계는 오라클 콘솔(웹)에서 직접 한다.

1. https://www.oracle.com/kr/cloud/free/ 에서 가입한다.
   - 본인 확인용으로 신용카드를 등록한다. Always Free 자원만 쓰면 요금이 나가지 않는다.
   - 홈 리전은 나중에 바꿀 수 없다. **South Korea Central (Seoul)** 또는 **South Korea North (Chuncheon)** 을 고른다.
2. 메뉴 → **Compute** → **Instances** → **Create instance**
   - **Image**: Canonical Ubuntu (최신 LTS)
   - **Shape**: Ampere `VM.Standard.A1.Flex`, OCPU 2, 메모리 12GB. `Always Free-eligible` 표시가 있는지 확인한다.
     - `Out of capacity`가 뜨면 다른 Availability Domain을 고르거나 AMD `VM.Standard.E2.1.Micro`(메모리 1GB)를 쓴다. 메모리가 작아도 `setup.sh`가 스왑을 만들어 빌드할 수 있다.
   - **Networking**: 새 VCN과 공개 서브넷을 만들고 **Assign a public IPv4 address**를 켠다.
   - **SSH keys**: **Generate a key pair for me** → **Save private key**로 키 파일을 받아 둔다. 잃어버리면 서버에 접속할 수 없다.
3. 만든 인스턴스의 **Public IP address**를 적어 둔다.
4. 80, 443 포트를 연다. 인스턴스 화면 → **Subnet** 링크 → **Security Lists** → `Default Security List` → **Add Ingress Rules**
   - Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `80`
   - 같은 방법으로 `443`도 추가한다.

## 2. 서버에 접속하기

macOS / Linux

```bash
chmod 400 ~/Downloads/ssh-key-*.key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@서버_공인_IP
```

Windows (PowerShell, Windows 10 이상은 ssh가 기본으로 있다)

```powershell
ssh -i $HOME\Downloads\ssh-key-파일이름.key ubuntu@서버_공인_IP
```

처음 접속할 때 `Are you sure you want to continue connecting`이 나오면 `yes`를 입력한다.

## 3. 설치 스크립트 실행

서버에 접속한 상태에서 실행한다. 처음에는 10분쯤 걸린다.

```bash
git clone https://github.com/wo-gml/MicroSNS.git
cd MicroSNS
bash deploy/setup.sh
```

- 중간에 서비스 재시작을 묻는 보라색 화면이 나오면 Enter를 누른다.
- DB 비밀번호와 `JWT_SECRET`은 스크립트가 만들어 서버의 `backend/.env`에만 저장한다.
- 시드 데이터도 같이 들어간다. 시드 회원으로는 로그인할 수 없으니 회원가입해서 쓴다.
- 마지막에 `프론트와 백엔드가 모두 응답한다`가 나오면 끝이다.

브라우저에서 `http://서버_공인_IP/` 로 접속해서 회원가입이 되는지 확인한다.

## 4. (선택) 도메인과 HTTPS

IP 대신 주소로 접속하고 싶을 때만 한다.

1. https://www.duckdns.org 에 로그인해서 서브도메인(예: `microsns-team`)을 만들고 서버 공인 IP를 넣는다.
2. 서버에서 실행한다. `microsns-team`은 만든 이름으로 바꾼다.

```bash
sudo sed -i 's/server_name _;/server_name microsns-team.duckdns.org;/' /etc/nginx/sites-available/microsns
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d microsns-team.duckdns.org
sed -i 's/^COOKIE_SECURE=.*/COOKIE_SECURE=true/' ~/MicroSNS/backend/.env
sudo systemctl restart microsns-backend
```

certbot이 이메일과 약관 동의를 묻는다. 이후 `https://microsns-team.duckdns.org` 로 접속한다. `COOKIE_SECURE=true`로 바꾼 뒤에는 http로 접속하면 로그인이 유지되지 않는다.

## 코드 수정 반영하기

main에 푸시한 뒤 서버에서 실행한다.

```bash
cd ~/MicroSNS
bash deploy/update.sh
```

DB 스키마를 바꿨다면 `update.sh`가 반영하지 않으니 SQL을 직접 실행한다. `01_schema.sql`을 다시 실행하면 데이터가 모두 지워진다.

## 문제가 생겼을 때

```bash
systemctl status microsns-backend microsns-frontend nginx   # 서비스 상태
journalctl -u microsns-backend -n 50                        # 백엔드 로그
journalctl -u microsns-frontend -n 50                       # 프론트 로그
curl http://127.0.0.1/api/health                            # 백엔드와 DB 연결 확인
```

| 증상 | 확인할 것 |
| --- | --- |
| 브라우저에서 접속이 안 된다 | 1단계 4번의 보안 목록에 80 포트를 열었는지 |
| `502 Bad Gateway` | 백엔드나 프론트 서비스가 꺼져 있다. 위 로그를 본다 |
| `/api/health`가 503 | MySQL이 꺼졌거나 `backend/.env`의 DB 비밀번호가 틀렸다 |
| 사진 업로드가 413 | `nginx.conf`의 `client_max_body_size` |

## 종료하기 (12월 1일 전)

1. 메뉴 → **Compute** → **Instances** → 인스턴스 → **Terminate**
   - **Permanently delete the attached boot volume**에 체크한다. DB와 업로드한 사진도 함께 지워진다.
2. 메뉴 → **Networking** → **Virtual cloud networks**에서 만든 VCN을 지운다.
3. 메뉴 → **Billing & Cost Management** → **Cost Analysis**에서 비용이 0인지 확인한다.
4. DuckDNS를 썼다면 서브도메인을 지운다.

계정을 Pay As You Go로 업그레이드하지 않았다면 무료 체험 기간이 끝나도 요금이 청구되지 않는다.

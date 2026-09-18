#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
REPO_URL="${REPO_URL:-https://github.com/crepus4256/legado-tts.git}"
PORT="${PORT:-}"
LOG="${INSTALL_LOG:-/var/log/legado-tts-install.log}"
mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1
on_error(){ code=$?; trap - ERR; echo; echo "安装失败，退出码=$code，请查看：$LOG"; docker compose ps 2>/dev/null || true; docker compose logs --tail=40 2>/dev/null || true; exit "$code"; }
trap on_error ERR
if [ "$(id -u)" -ne 0 ]; then echo '请使用 root 或 sudo 运行'; exit 1; fi
if ! command -v docker >/dev/null 2>&1; then echo '未检测到 Docker，开始安装...'; curl -fsSL https://get.docker.com | sh; fi
if ! docker compose version >/dev/null 2>&1; then echo '需要 Docker Compose v2'; exit 1; fi
if [ ! -d "$INSTALL_DIR/.git" ]; then git clone "$REPO_URL" "$INSTALL_DIR"; else git -C "$INSTALL_DIR" pull --ff-only; fi
cd "$INSTALL_DIR"
if [ -z "$PORT" ] && [ -f .env ]; then PORT=$(sed -n 's/^PORT=//p' .env | head -1); fi
PORT="${PORT:-8765}"
case "$PORT" in *[!0-9]*|'') echo 'PORT 必须是 1 到 65535 之间的整数'; exit 1;; esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then echo 'PORT 必须是 1 到 65535 之间的整数'; exit 1; fi
mkdir -p data cache
touch cache/.gitkeep
# data/access_key is authoritative because app/auth.py reads it before .env.
if [ -s data/access_key ]; then
  KEY=$(cat data/access_key)
elif [ -s .env ]; then
  KEY=$(sed -n 's/^TTS_ACCESS_KEY=//p' .env | head -1)
else
  KEY=$(openssl rand -hex 24)
fi
KEY=$(printf '%s' "$KEY" | tr -d '\r\n')
if [ "${#KEY}" -lt 12 ]; then echo '密钥长度不足 12 位，无法继续安装'; exit 1; fi
printf '%s' "$KEY" > data/access_key
chmod 600 data/access_key
printf 'TTS_ACCESS_KEY=%s\nPORT=%s\n' "$KEY" "$PORT" > .env
chmod 600 .env
if [ ! -f data/config.json ] && [ -f data/config.example.json ]; then cp data/config.example.json data/config.json; fi
chmod +x manage.sh update.sh uninstall.sh
echo '开始构建，完整日志会保存到安装日志...'
docker compose up -d --build
docker compose ps
healthy=false
for _ in $(seq 1 15); do
  if curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/health" >/dev/null && curl -fsS --max-time 5 -H "X-TTS-Key: $KEY" "http://127.0.0.1:${PORT}/status" >/dev/null; then healthy=true; break; fi
  sleep 2
done
$healthy || { echo '服务启动后 30 秒内未通过健康检查或密钥验证'; false; }
install -m 755 manage.sh /usr/local/bin/legado-tts
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
echo '安装成功'
echo "日志：$LOG"
echo '管理命令：legado-tts'
echo "管理页面：http://${IP:-服务器IP}:${PORT}/admin"
echo "访问密钥：$KEY"
echo "Legado URL：http://${IP:-服务器IP}:${PORT}/tts,{\"method\":\"POST\",\"body\":\"tex={{java.encodeURI(java.encodeURI(speakText))}}&speed={{speakSpeed}}\"}"
echo '请求头：{"X-TTS-Key":"你的访问密钥"}'
echo 'Content-Type：audio/mp3'

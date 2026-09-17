#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
REPO_URL="${REPO_URL:-https://github.com/crepus4256/legado-tts.git}"
PORT="${PORT:-8765}"
LOG="${INSTALL_LOG:-/var/log/legado-tts-install.log}"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
on_error(){ echo; echo "安装失败，退出码=$?，请查看：$LOG"; echo '最后 80 行诊断：'; tail -n 80 "$LOG"; }
trap on_error ERR
if [ "$(id -u)" -ne 0 ]; then echo '请使用 root 或 sudo 运行'; exit 1; fi
if ! command -v docker >/dev/null 2>&1; then
  echo '未检测到 Docker，开始安装...'
  curl -fsSL https://get.docker.com | sh
fi
if ! docker compose version >/dev/null 2>&1; then echo '需要 Docker Compose v2'; exit 1; fi
if [ ! -d "$INSTALL_DIR/.git" ]; then git clone "$REPO_URL" "$INSTALL_DIR"; else git -C "$INSTALL_DIR" pull --ff-only; fi
cd "$INSTALL_DIR"
mkdir -p data cache
touch cache/.gitkeep
if [ ! -f .env ]; then
  KEY=$(openssl rand -hex 24)
  printf 'TTS_ACCESS_KEY=%s\n' "$KEY" > .env
  chmod 600 .env
else
  KEY=$(sed -n 's/^TTS_ACCESS_KEY=//p' .env | head -1)
fi
if [ ! -f data/config.json ] && [ -f data/config.example.json ]; then cp data/config.example.json data/config.json; fi
chmod +x manage.sh update.sh uninstall.sh
echo '开始构建，完整日志会保存到安装日志...'
docker compose up -d --build
docker compose ps
sleep 3
curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null
install -m 755 manage.sh /usr/local/bin/legado-tts
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
echo '安装成功'
echo "日志：$LOG"
echo "管理命令：legado-tts"
echo "管理页面：http://${IP:-服务器IP}:${PORT}/admin"
echo "访问密钥：$KEY"
echo "Legado URL：http://${IP:-服务器IP}:${PORT}/tts,{\"method\":\"POST\",\"body\":\"tex={{java.encodeURI(java.encodeURI(speakText))}}&speed={{speakSpeed}}\"}"
echo '请求头：{"X-TTS-Key":"你的访问密钥"}'
echo 'Content-Type：audio/mp3'

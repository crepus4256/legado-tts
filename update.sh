#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
PORT="${PORT:-}"
LOG="${UPDATE_LOG:-/var/log/legado-tts-update.log}"
mkdir -p "$(dirname "$LOG")"
exec > >(tee "$LOG") 2>&1
on_error(){ code=$?; trap - ERR; echo; echo "更新失败，退出码=$code，日志：$LOG"; docker compose ps || true; docker compose logs --tail=40 || true; exit "$code"; }
trap on_error ERR
cd "$INSTALL_DIR"
if [ -z "$PORT" ] && [ -f .env ]; then PORT=$(sed -n 's/^PORT=//p' .env | head -1); fi
PORT="${PORT:-8765}"
case "$PORT" in *[!0-9]*|'') echo 'PORT 必须是 1 到 65535 之间的整数'; exit 1;; esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then echo 'PORT 必须是 1 到 65535 之间的整数'; exit 1; fi
if [ -d .git ]; then git pull --ff-only; else echo '当前目录不是 Git 工作区，无法自动更新'; exit 1; fi
docker compose up -d --build
install -m 755 manage.sh /usr/local/bin/legado-tts
healthy=false
for _ in $(seq 1 15); do
  if curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/health"; then healthy=true; break; fi
  sleep 2
done
$healthy || { echo '服务启动后 30 秒内未通过健康检查'; false; }
echo
echo '更新完成；.env、data 和 cache 已保留。'
echo "日志：$LOG"

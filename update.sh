#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
LOG="${UPDATE_LOG:-/var/log/legado-tts-update.log}"
mkdir -p "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
on_error(){ echo; echo "更新失败，退出码=$?，日志：$LOG"; tail -n 80 "$LOG"; }
trap on_error ERR
cd "$INSTALL_DIR"
if [ -d .git ]; then git pull --ff-only; else echo '当前目录不是 Git 工作区，无法自动更新'; exit 1; fi
docker compose up -d --build
install -m 755 manage.sh /usr/local/bin/legado-tts
curl -fsS http://127.0.0.1:8765/health
echo
echo "更新完成；.env、data 和 cache 已保留。"
echo "日志：$LOG"

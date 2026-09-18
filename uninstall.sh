#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
YES=false
INTERNAL=false
for arg in "$@"; do
  case "$arg" in
    --yes) YES=true;;
    --internal-confirmed) INTERNAL=true;;
    -h|--help) echo '用法：bash uninstall.sh [--yes]'; echo '删除 legado-tts 的容器、镜像、网络、卷、源码、配置、缓存和管理命令；不会删除 Docker 或其他项目。'; exit 0;;
    *) echo "未知参数：$arg"; exit 2;;
  esac
done
if ! $INTERNAL; then
  if ! $YES; then
    echo '警告：此操作将删除 legado-tts 的容器、镜像、网络、卷、源码、.env、data、cache 和管理命令。'
    echo '不会删除 Docker、Docker Compose 或其他项目。此操作不可恢复。'
    read -r -p '如确认，请输入 DELETE：' answer
    [ "$answer" = DELETE ] || { echo '已取消'; exit 0; }
  fi
  SELF=$(readlink -f "$0")
  TMP="/tmp/legado-tts-uninstall-$$.sh"
  cp "$SELF" "$TMP"
  chmod 700 "$TMP"
  exec "$TMP" --internal-confirmed
fi
LOG=/tmp/legado-tts-uninstall.log
exec > >(tee "$LOG") 2>&1
echo '正在卸载 legado-tts...'
if command -v docker >/dev/null 2>&1 && [ -f "$INSTALL_DIR/compose.yaml" ]; then
  docker compose --project-directory "$INSTALL_DIR" down --rmi local --volumes --remove-orphans || true
fi
rm -f /usr/local/bin/legado-tts
rm -rf "$INSTALL_DIR"
rm -f /var/log/legado-tts-install.log /var/log/legado-tts-update.log /var/log/legado-tts-uninstall.log
rm -rf /opt/legado-tts-backup-*
echo 'legado-tts 已完全卸载。Docker 和其他 Docker 项目未被删除。'
echo "本次临时日志：$LOG"

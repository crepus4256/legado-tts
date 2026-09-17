#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
PURGE=false
YES=false
for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=true;;
    --yes) YES=true;;
    -h|--help)
      echo "用法：bash uninstall.sh [--purge] [--yes]"
      echo "默认：删除服务和程序，备份 .env/data/cache，不删除数据"
      echo "--purge：连同 .env/data/cache 一并删除"
      echo "--yes：跳过确认，供自动化使用"
      exit 0;;
    *) echo "未知参数：$arg"; exit 2;;
  esac
done

if [ ! -d "$INSTALL_DIR" ]; then
  echo "项目目录不存在：$INSTALL_DIR"
  rm -f /usr/local/bin/legado-tts
  exit 0
fi
cd "$INSTALL_DIR"

if ! $YES; then
  if $PURGE; then
    echo '警告：完全卸载会删除 .env、data、cache，无法恢复。'
    read -r -p '请输入 DELETE 确认：' answer
    [ "$answer" = DELETE ] || { echo '已取消'; exit 0; }
  else
    read -r -p '确认停止并删除程序，但保留数据备份？输入 YES：' answer
    [ "$answer" = YES ] || { echo '已取消'; exit 0; }
  fi
fi

LOG=/var/log/legado-tts-uninstall.log
{
  echo "[$(date -Is)] uninstall purge=$PURGE"
  if command -v docker >/dev/null 2>&1 && [ -f compose.yaml ]; then
    docker compose down --remove-orphans || true
    IMAGE=$(docker compose config --images 2>/dev/null | head -1 || true)
    [ -n "$IMAGE" ] && docker image rm "$IMAGE" 2>/dev/null || true
  fi
  rm -f /usr/local/bin/legado-tts
  if $PURGE; then
    rm -rf "$INSTALL_DIR"
    echo '完全卸载完成'
  else
    BACKUP="/opt/legado-tts-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP"
    [ -f .env ] && cp -a .env "$BACKUP/"
    [ -d data ] && cp -a data "$BACKUP/"
    [ -d cache ] && cp -a cache "$BACKUP/"
    rm -rf "$INSTALL_DIR"
    echo "程序已卸载，数据备份：$BACKUP"
  fi
} 2>&1 | tee "$LOG"

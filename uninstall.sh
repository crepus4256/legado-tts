#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose down
echo "服务已停止。项目目录和 data/cache 没有删除。"

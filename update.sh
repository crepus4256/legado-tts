#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
git pull --ff-only
docker compose up -d --build
curl -fsS http://127.0.0.1:8765/health
echo
echo "更新完成；.env、data 和 cache 已保留。"

#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR="${INSTALL_DIR:-/opt/legado-tts}"
cd "$INSTALL_DIR"
log(){ printf '\033[36m%s\033[0m\n' "$*"; }
ok(){ printf '\033[32m✓ %s\033[0m\n' "$*"; }
fail(){ printf '\033[31m✗ %s\033[0m\n' "$*"; }
compose(){ docker compose --project-directory "$INSTALL_DIR" "$@"; }
status(){ echo; echo '========== legado-tts 服务状态 =========='; compose ps; echo; if curl -fsS --max-time 5 http://127.0.0.1:8765/health >/tmp/legado-tts-health.$$ 2>/dev/null; then ok "HTTP 健康检查通过：$(cat /tmp/legado-tts-health.$$)"; rm -f /tmp/legado-tts-health.$$; else fail 'HTTP 健康检查失败，服务可能尚未启动或端口不可用'; rm -f /tmp/legado-tts-health.$$ || true; fi; }
start_service(){ log '正在启动服务...'; compose up -d; ok '服务已启动'; status; }
stop_service(){ log '正在停止服务...'; compose stop; ok '服务已停止'; }
restart_service(){ log '正在重启服务...'; compose restart; ok '服务已重启'; status; }
logs(){ compose logs -f --tail=100; }
update(){ log '正在更新代码并重建镜像，详细日志：/var/log/legado-tts-update.log'; if bash "$INSTALL_DIR/update.sh"; then ok '更新完成'; else fail '更新失败，请查看 /var/log/legado-tts-update.log 最后 80 行'; return 1; fi; }
show_info(){ echo; echo '========== legado-tts 连接信息 =========='; echo "管理页面：http://$(hostname -I 2>/dev/null | awk '{print $1}') :8765/admin" | sed 's/ :/:/'; echo '项目目录：/opt/legado-tts'; echo '密钥文件：/opt/legado-tts/.env 或 /opt/legado-tts/data/access_key'; echo '注意：为安全起见，不在终端菜单中显示真实密钥。'; }
uninstall(){ echo; echo '警告：将删除 legado-tts 的容器、镜像、网络、卷、源码、配置、密钥、缓存和管理命令。'; echo '不会删除 Docker、Docker Compose 或其他 Docker 项目。此操作不可恢复。'; read -r -p '如确认，请输入 DELETE：' answer; [ "$answer" = DELETE ] || { echo '已取消'; return; }; bash "$INSTALL_DIR/uninstall.sh" --yes; }
while true; do echo; echo '╔════════════════════════════════════╗'; echo '║       legado-tts SSH 管理面板      ║'; echo '╠════════════════════════════════════╣'; echo '║  1. 查询运行状态                   ║'; echo '║  2. 启动服务                       ║'; echo '║  3. 停止服务                       ║'; echo '║  4. 重启服务                       ║'; echo '║  5. 查看实时日志                   ║'; echo '║  6. 更新并重建                     ║'; echo '║  7. 显示连接信息                   ║'; echo '║  8. 卸载 legado-tts                ║'; echo '║  0. 退出                           ║'; echo '╚════════════════════════════════════╝'; read -r -p '请选择 [0-8]：' choice; case "$choice" in 1) status;; 2) start_service;; 3) stop_service;; 4) restart_service;; 5) logs;; 6) update;; 7) show_info;; 8) uninstall;; 0) exit 0;; *) echo '请输入 0 到 8';; esac; read -r -p '按回车返回菜单...' _; done

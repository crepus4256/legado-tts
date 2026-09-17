# Legado Microsoft TTS Proxy

为 Legado（阅读）提供微软官方在线朗读服务，包含 Web 管理页面和 SSH 终端管理面板。

## 功能

- Microsoft 官方区域 TTS 与故障切换
- 默认支持晓晓多语言
- 动态音色、风格、角色目录
- Token 缓存、音频缓存和区域统计
- `X-TTS-Key` 请求头鉴权
- Legado GET/POST 在线朗读规则兼容
- Web 管理页面：音色、语速、缓存、区域和试听
- SSH 管理命令：状态、启动、停止、重启、日志、更新、卸载
- Docker Compose 一键安装

## 一键安装

把 `install.sh` 中的 `REPO_URL` 默认值改成你的 GitHub 仓库后，可直接执行：

```bash
curl -fsSL https://raw.githubusercontent.com/crepus4256/legado-tts/main/install.sh | bash
```

如果不想修改脚本默认仓库，也可以临时指定：

```bash
curl -fsSL https://raw.githubusercontent.com/crepus4256/legado-tts/main/install.sh | REPO_URL=https://github.com/crepus4256/legado-tts.git bash
```

脚本会：

1. 检查并安装 Docker；
2. 下载项目；
3. 自动生成访问密钥；
4. 创建 data 和 cache；
5. 构建并启动服务；
6. 安装 `legado-tts` 管理命令；
7. 输出管理页面、密钥和 Legado 配置。

构建和安装日志：

```text
/var/log/legado-tts-install.log
```

SSH 断线后可重新连接查看最后 80 行：

```bash
tail -n 80 /var/log/legado-tts-install.log
```

长时间安装建议使用：

```bash
tmux new -s legado-install
```

## SSH 管理面板

安装完成后执行：

```bash
legado-tts
```

菜单包括：

```text
1 查询运行状态
2 启动服务
3 停止服务
4 重启服务
5 查看实时日志
6 更新并重建
7 显示连接信息
8 卸载服务
0 退出
```

也可以直接执行：

```bash
cd /opt/legado-tts
bash update.sh
bash uninstall.sh
bash uninstall.sh --purge --yes
```

## 卸载说明

普通卸载：

```bash
bash uninstall.sh
```

会删除：

- 容器；
- 项目镜像；
- `/usr/local/bin/legado-tts`；
- 项目程序目录。

但会先备份并保留：

- `.env`；
- `data/`；
- `cache/`。

备份目录类似：

```text
/opt/legado-tts-backup-20260915-120000
```

完全卸载：

```bash
bash uninstall.sh --purge
```

需要输入 `DELETE` 二次确认。自动化完全卸载：

```bash
bash uninstall.sh --purge --yes
```

完全卸载会删除访问密钥、配置、统计和音频缓存，无法恢复，请谨慎使用。

## Legado 配置

URL：

```text
http://服务器IP:8765/tts,{"method":"POST","body":"tex={{java.encodeURI(java.encodeURI(speakText))}}&speed={{speakSpeed}}"}
```

请求头：

```json
{"X-TTS-Key":"你的访问密钥"}
```

Content-Type：

```text
audio/mp3
```

推荐并发率：`2`。

## 安全设计

启动、停止、重启、更新和卸载只存在于 SSH 管理面板，不放进 Web 管理页面。项目容器不挂载 Docker Socket，避免公网 Web 页面获得宿主机 root 级控制能力。

不要把以下文件提交到 GitHub：

```text
.env
data/access_key
data/config.json
data/regions.json
data/voices.json
cache/*.mp3
```

## 项目目录

```text
app/                 Python 后端和 admin.html
manage.sh            SSH 中文管理面板
Dockerfile           Docker 镜像
compose.yaml         Docker Compose
install.sh           一键安装
update.sh            一键更新
uninstall.sh         安全卸载
.env.example         环境变量示例
data/config.example.json 默认配置
```

## License

MIT

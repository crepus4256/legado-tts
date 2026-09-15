# Legado Microsoft TTS Proxy

为 Legado（阅读）提供可直接使用的微软官方在线朗读服务。

## 功能

- Microsoft Translator / Azure 官方区域 TTS
- 默认支持 `zh-CN-XiaoxiaoMultilingualNeural`（晓晓多语言）
- `eastus`、`westus` 等官方区域故障切换与延迟统计
- Edge 官方公共接口故障回退
- Microsoft 临时授权缓存与 401 自动刷新
- 动态音色目录、风格与角色校验
- MP3 磁盘缓存
- `X-TTS-Key` 请求头鉴权
- Legado GET/POST 在线朗读规则兼容
- 可视化中文管理页面
- Docker Compose 一键安装

> 本项目不使用第三方 TTS 转发服务器。当前 Translator 客户端授权接口并非微软承诺长期兼容的公开服务，微软可能随时调整。正式商业部署建议使用自己的 Azure Speech 订阅。

## 系统要求

- Debian / Ubuntu 等主流 Linux
- root 或 sudo
- 公网端口 `8765/tcp`
- Docker 与 Docker Compose v2（安装脚本可自动安装 Docker）

## 一键安装

先将 `install.sh` 中的仓库地址替换为你的 GitHub 仓库，或者安装时传入：

```bash
sudo REPO_URL=https://github.com/你的用户名/legado-tts.git bash -c "$(curl -fsSL https://raw.githubusercontent.com/你的用户名/legado-tts/main/install.sh)"
```

也可以常规安装：

```bash
git clone https://github.com/你的用户名/legado-tts.git
cd legado-tts
sudo REPO_URL=https://github.com/你的用户名/legado-tts.git bash install.sh
```

安装成功后脚本会显示：

- 管理页面地址
- 随机访问密钥
- Legado URL 规则
- Legado 请求头

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

推荐并发率：

```text
2
```

管理页面：

```text
http://服务器IP:8765/admin
```

## 速度模式

- 勾选“跟随阅读 App 的朗读速度”：采用 Legado 的 `speakSpeed`。
- 取消勾选：忽略 Legado 速度，使用管理页保存的默认语速。
- 管理页试听永远使用滑块当前值，不受上述开关影响。

微软可能会对极端 SSML 语速进行钳制。例如某些音色的 `+200%` 与 `+300%` 最终音频时长可能完全相同，这是上游限制，不是页面参数未传递。

## 更新

```bash
cd /opt/legado-tts
sudo bash update.sh
```

`.env`、`data` 与 `cache` 会保留。

## 停止服务

```bash
cd /opt/legado-tts
sudo bash uninstall.sh
```

该脚本只停止容器，不删除项目、设置或缓存。

## 目录

```text
app/                 后端模块与管理页面
Dockerfile           镜像定义
compose.yaml         容器编排
requirements.txt     Python 依赖
install.sh            一键安装
update.sh             一键更新
uninstall.sh          停止服务
.env.example          环境变量示例
data/config.example.json 默认配置示例
```

运行时敏感文件不会提交：

```text
.env
data/access_key
```

音频缓存、运行统计、备份和 Python 缓存也不会提交。

## 手动启动

```bash
cp .env.example .env
# 修改 .env，设置至少 12 位访问密钥
mkdir -p data cache
cp data/config.example.json data/config.json
docker compose up -d --build
```

健康检查：

```bash
curl http://127.0.0.1:8765/health
```

## 安全建议

- 不要提交 `.env` 或 `data/access_key`。
- 公网部署建议配置 HTTPS。
- 不要将访问密钥放在 URL 中，优先使用 `X-TTS-Key` 请求头。
- 不要将管理页面密钥分享给他人。

## License

MIT

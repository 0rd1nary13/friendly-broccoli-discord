# Telegram -> AI 翻译 -> Discord Relay

## 技术栈

- `Telethon`: 监听 Telegram 新消息
- `google-genai` (Python SDK): 调用 Gemini 模型进行翻译
- `requests`: 发送 Discord Webhook
- `uv`: 管理依赖与虚拟环境
- `pytest` + `ruff`: 测试与代码质量

## 目录结构

```text
src/goob_ai/
  config.py
  translator.py
  discord_sender.py
  telegram_listener.py
  main.py
tests/
deploy/systemd/
```

## 1) 准备 Telegram 凭据

1. 登录 https://my.telegram.org
2. 进入 API Development Tools
3. 拿到 `api_id` 和 `api_hash`
4. 频道 ID 可以用负数 ID（如 `-100...`）或频道用户名（如 `my_channel`）

## 2) 本地运行

```bash
uv venv
source .venv/bin/activate
uv sync --extra dev
cp .env.example .env
python -m goob_ai.main
```

首次运行 Telethon 会要求登录 Telegram（输入手机号和验证码），会生成本地 session 文件。

## 3) 环境变量

复制 `.env.example` 为 `.env`，并填写：

- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_SOURCE_CHATS`（支持多个，用逗号分隔）
- `GEMINI_API_KEY`
- `GEMINI_MODEL`（默认 `gemini-2.5-flash`）
- `TARGET_LANGUAGE`（默认 `English`）
- `DISCORD_WEBHOOK_URL`（在目标频道创建 Webhook，并填入该 URL）

## 4) Oracle Ampere 服务器常驻运行（systemd）

假设项目放在 `/opt/friendly-broccoli-discord`。

```bash
cd /opt
git clone <your_repo_url> friendly-broccoli-discord
cd friendly-broccoli-discord
uv venv
source .venv/bin/activate
uv sync --extra dev
cp .env.example .env
```

先手动启动一次完成 Telethon 登录：

```bash
source .venv/bin/activate
python -m goob_ai.main
```

确认能收到并转发后，安装 systemd 服务：

```bash
sudo cp deploy/systemd/telegram-relay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-relay
sudo systemctl start telegram-relay
sudo systemctl status telegram-relay
```

查看日志：

```bash
journalctl -u telegram-relay -f
```

## 4.1) 关掉 Terminal 也继续运行（relayctl）

如果你当前先在本机或普通 Linux 环境运行，不想依赖 systemd，可用项目内置脚本。

```bash
chmod +x scripts/relayctl.sh
./scripts/relayctl.sh start
./scripts/relayctl.sh status
./scripts/relayctl.sh logs
./scripts/relayctl.sh stop
```

说明：

- `start`: 后台启动，关闭 terminal 后进程继续运行
- `status`: 查看是否在运行
- `logs`: 实时查看日志
- `stop`: 停止后台进程
- 日志文件在 `var/log/relay.log`

## 5) 运行测试与检查

```bash
pytest -q
ruff check .
```

## 设计说明

- 配置、翻译、发送、监听分层，便于后续替换组件
- 仅处理包含中文的消息，并输出英文正文译文
- 完整日志与异常捕获，避免单条消息导致进程退出
- Discord 消息按 2000 字限制自动分段发送

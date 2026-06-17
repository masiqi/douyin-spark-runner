# douyin-spark-runner

本项目是在 macOS 本机运行的 Playwright 抖音网页版续火花 runner。它不使用 Android、手机自动化、GitHub Actions cookie，也不会要求安装抖音移动端。设计目标是每天由 Hermes/cron 启动一次浏览器，读取网页版聊天列表，给符合规则的可见/近期联系人发送随机自然消息，保存日志和截图后退出。

默认策略偏保守：每天最多发送 20 人、跳过疑似群聊、支持排除名单、支持 include 白名单、记录当天已发送联系人，重复运行时不会再次发送，除非显式使用 `--force`。

## 安装

需要 Python 3.11+ 和 `uv`。

```bash
uv sync --extra dev
```

如果本机已经安装 Chrome，Playwright 会优先使用系统 Chrome，不需要安装浏览器二进制。只有在本机没有可用 Chrome 或 Playwright 提示缺浏览器时，再运行：

```bash
uv run playwright install chromium
```

## 配置

复制示例配置到本地配置文件：

```bash
cp config.example.yaml config.yaml
```

`config.yaml` 已被 `.gitignore` 忽略，不要提交真实配置。常用字段：

- `max_recipients`: 单次最多发送人数，建议保持 20 或更低。
- `include`: 非空时只发送名称命中这些字符串或正则的联系人。
- `exclude`: 名称命中这些字符串或正则的联系人会跳过。
- `aliases`: 抖音昵称到日常称呼的映射；消息里使用映射后的称呼，未配置时使用抖音昵称。
- `skip_groups`: 是否跳过疑似群聊，默认 `true`。
- `random_sleep`: 每次发送后的随机等待秒数。
- `messages.templates`: 随机消息模板，支持 `{name}`、`{date}`、`{emoji}`、`{phrase}`。

浏览器登录态保存在 `state/browser-profile`，当天发送记录保存在 `state/daily/YYYY-MM-DD.json`，日志和截图分别在 `logs/`、`screenshots/`。

## 登录

首次运行需要手动扫码登录：

```bash
uv run douyin-spark login
```

命令会打开非 headless Chrome 并进入抖音聊天页。手动扫码登录完成后，回到终端按 Enter，浏览器 profile 会保存到本机 `state/browser-profile`。

## 查看联系人

只发现聊天列表中的可见/近期联系人，不发送消息：

```bash
uv run douyin-spark contacts
uv run douyin-spark contacts --output json
```

该命令会打开网页版抖音聊天页，读取当前聊天列表，并保存一张截图。

##  dry-run 计划

发送前先看计划，推荐每天实际发送前都跑一次：

```bash
uv run douyin-spark send-once --dry-run
```

dry-run 会输出本次计划：联系人、是否发送、跳过原因、为每个 eligible 联系人生成的随机消息。dry-run 不会点击发送，不会写入当天已发送记录。

## 发送一次

确认 dry-run 输出无误后再运行：

```bash
uv run douyin-spark send-once
```

发送逻辑会：

1. 打开 `https://www.douyin.com/chat`，失败时回退到 `https://www.douyin.com/im`。
2. 发现聊天列表联系人。
3. 根据 include/exclude、群聊判断、当天已发送记录和 `max_recipients` 过滤。
4. 为每个联系人生成不同消息。
5. 逐个点击联系人、输入消息、按 Enter。
6. 每次发送后随机等待，并写入日志和 `state/daily/YYYY-MM-DD.json`。
7. 失败或结束时保存截图。

如果确实需要忽略当天记录，可以使用：

```bash
uv run douyin-spark send-once --force
```

谨慎使用 `--force`，它可能让同一天重复发送给同一联系人。

## Hermes/cron 示例

建议定时任务先跑 dry-run 一段时间观察日志，再切到真实发送。

```cron
15 9 * * * cd /Users/siqi/projects/douyin-spark-runner && UV_CACHE_DIR=.uv-cache uv run douyin-spark send-once >> logs/cron.log 2>&1
```

如果 Hermes 支持环境变量，也建议设置：

```bash
UV_CACHE_DIR=/Users/siqi/projects/douyin-spark-runner/.uv-cache
```

## 安全提醒

- 本工具只面向本机个人使用，不保证抖音网页版 DOM 长期稳定。
- 不要在测试或 CI 中运行真实发送命令。
- `send-once --dry-run` 是离线计划模式中的安全检查，但仍会打开浏览器访问抖音网页版。
- 单次发送人数和等待时间应保持保守，避免高频自动化行为。
- 群聊识别是启发式规则，发送前请用 `contacts` 和 dry-run 检查。

## 测试

单元测试不访问抖音，也不会发送消息：

```bash
UV_CACHE_DIR=.uv-cache uv run pytest
```

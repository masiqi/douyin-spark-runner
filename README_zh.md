# 抖音续火花本机 Runner

[English README](README.md)

这是一个在本机桌面浏览器里运行的 Playwright 抖音网页版“续火花 / 保持每日互动”工具。

它不使用 Android 自动化、不控制手机、不依赖 GitHub Actions Cookie，也不需要安装抖音手机 App。它会在本机打开抖音网页版聊天页，读取最近/可见联系人，给符合规则的联系人发送随机自然问候，记录当天发送状态，保存日志和截图，然后退出。

> 安全原则：默认策略偏保守。真实发送前一定先运行 `send-once --dry-run` 检查计划。

## Agent 快速开始

如果你是 AI coding/ops agent，用户把这个仓库地址发给你，请按下面步骤操作：

```bash
git clone https://github.com/masiqi/douyin-spark-runner.git
cd douyin-spark-runner
uv sync --extra dev
cp config.example.yaml config.yaml
```

然后协助用户编辑 `config.yaml`：

1. `max_recipients` 保守设置，比如 `10`。
2. 除非用户明确需要群聊，否则保持 `skip_groups: true`。
3. 在 `exclude` 里加入不应该发送的人或账号，例如商家、课程、客服、官方号等。
4. 如果抖音昵称和日常称呼不同，在 `aliases` 里配置映射。
5. 真实发送前必须先运行 `contacts` 和 `send-once --dry-run`。

常用命令：

```bash
uv run douyin-spark login                 # 首次扫码登录
uv run douyin-spark check-login           # 检查保存的登录态是否有效
uv run douyin-spark logout                # 切换账号：清空/移走本地登录 profile
uv run douyin-spark contacts              # 列出最近/可见联系人
uv run douyin-spark contacts --output json
uv run douyin-spark send-once --dry-run   # 只生成计划，不发送
uv run douyin-spark send-once             # 真实发送
```

在用户确认 dry-run 计划之前，不要运行真实 `send-once`。

## 这是 skill 吗？

这个仓库本身主要是一个 **CLI 自动化工具**，不是 Hermes / Claude / OpenAI skill。

不过它的 README 已经按 agent-friendly 的方式编写，所以 agent 只拿到 GitHub URL 也能安装、配置和执行。后续可以再做一个很薄的 skill，只负责告诉 agent：

- clone 到哪里；
- 如何运行 `login`、`contacts`、`send-once --dry-run`、`send-once`；
- 如何配置 Hermes cron 定时任务。

也就是说：

- **本仓库** = 可执行实现；
- **可选 skill** = 操作流程说明包装层。

## 功能概览

1. 用 Playwright 打开抖音网页版聊天页。
2. 使用本地持久化浏览器 profile：`state/browser-profile`。
3. 读取最近/可见聊天联系人。
4. 按规则过滤联系人：
   - include 白名单；
   - exclude 排除名单；
   - 疑似群聊过滤；
   - 当天已发送记录；
   - `max_recipients` 人数上限。
5. 用模板生成随机自然消息。
6. 支持昵称映射：抖音昵称可以映射成日常称呼。
7. 逐个发送，并在联系人之间随机等待。
8. 保存 JSONL 日志、截图、当天发送记录。

## 环境要求

- macOS / Linux 桌面环境，能打开浏览器。
- Python 3.11+。
- [`uv`](https://github.com/astral-sh/uv)。
- 推荐安装 Chrome。

安装依赖：

```bash
uv sync --extra dev
```

如果本机没有可用 Chrome，或 Playwright 提示缺少浏览器：

```bash
uv run playwright install chromium
```

## 配置

创建本地配置：

```bash
cp config.example.yaml config.yaml
```

`config.yaml` 已被 git 忽略，不要提交真实配置。

常用字段示例：

```yaml
max_recipients: 10
include: []
exclude:
  - "群"
  - "老师"
  - "家长"
  - "工作"
  - "客服"
  - "官方"
skip_groups: true

# 抖音昵称 -> 日常称呼。
# 如果没有配置，就默认使用抖音昵称。
aliases:
  "疯狂的兔子": "三儿"
  "张三的抖音昵称": "张三"

random_sleep:
  min_seconds: 4
  max_seconds: 12

messages:
  templates:
    - "早呀 {name}，今天也顺顺利利 {emoji}"
    - "{name}，路过打个招呼，续一下火花 {emoji}"
    - "给 {name} 补个火花，{phrase}"
```

模板变量：

- `{name}`：如果配置了 alias，则使用 alias；否则使用抖音昵称。
- `{date}`：当前日期。
- `{emoji}`：从配置里随机选择一个 emoji。
- `{phrase}`：从配置里随机选择一个短语。

运行时目录：

- 浏览器 profile：`state/browser-profile`
- 当天发送记录：`state/daily/YYYY-MM-DD.json`
- 日志：`logs/*.jsonl`
- 截图：`screenshots/*.png`

## 首次登录

```bash
uv run douyin-spark login
```

命令会打开非 headless 浏览器并进入抖音网页版聊天页。用户完成扫码登录后，回到终端按 Enter，本地浏览器 profile 会保存下来。

如果 agent 是远程通过微信/聊天窗口服务用户，命令会保存一张二维码截图，例如：

```text
screenshots/YYYYMMDD-HHMMSS-login-qr.png
```

agent 可以把这张图片发给用户，等待用户扫码完成后，再向等待中的进程提交 Enter。

## 检查登录态

```bash
uv run douyin-spark check-login
```

退出码含义：

- `0`：已登录；
- `2`：未登录；
- `1`：命令异常。

`send-once` 会在发送前自动检查登录态。如果登录态缺失或过期，会输出 `not_logged_in` 并退出，不会发送消息。

## 切换账号 / logout

```bash
uv run douyin-spark logout
uv run douyin-spark login
```

`logout` 不会点击抖音网页里的退出登录按钮，而是把本地持久化浏览器 profile 移到一个带时间戳的备份目录，例如：

```text
state/browser-profile-logout-YYYYMMDD-HHMMSS
```

下一次 `login` 会使用新的空 profile，因此可以扫码登录另一个账号。

## 查看联系人

```bash
uv run douyin-spark contacts
uv run douyin-spark contacts --output json
```

这个命令会打开抖音网页版聊天页，读取最近/可见联系人，并保存截图。可以根据联系人结果调整 `include`、`exclude` 和 `aliases`。

## dry-run 计划

```bash
uv run douyin-spark send-once --dry-run
```

dry-run 会打开聊天页并输出本次发送计划，但不会真的发送消息，也不会写入当天已发送记录。

示例输出：

```json
{
  "name": "疯狂的兔子",
  "display_name": "三儿",
  "selector_index": 0,
  "is_group": false,
  "should_send": true,
  "reason": "eligible",
  "message": "三儿，路过打个招呼，续一下火花 ✨"
}
```

字段含义：

- `name`：抖音实际显示昵称，用于定位聊天。
- `display_name`：配置后的日常称呼，用于生成消息。
- `reason`：为什么发送或跳过。

## 真实发送一次

确认 dry-run 没问题后再执行：

```bash
uv run douyin-spark send-once
```

执行流程：

1. 打开 `https://www.douyin.com/chat`，失败时回退到 `https://www.douyin.com/im`。
2. 读取联系人。
3. 按 include/exclude、群聊判断、当天已发送记录和 `max_recipients` 过滤。
4. 为每个联系人生成随机消息。
5. 点击联系人、输入消息、按 Enter。
6. 每次发送后随机等待。
7. 写入日志和 `state/daily/YYYY-MM-DD.json`。
8. 保存截图。

如果确实要忽略当天已发送记录：

```bash
uv run douyin-spark send-once --force
```

谨慎使用 `--force`，它可能导致同一天给同一联系人重复发送。

## Hermes cron 示例

手动 dry-run 稳定后，可以用 Hermes cron 或普通 cron 每天运行。

普通 cron 示例：

```cron
15 9 * * * cd /Users/siqi/projects/douyin-spark-runner && UV_CACHE_DIR=.uv-cache uv run douyin-spark send-once >> logs/cron.log 2>&1
```

对于 Hermes Agent，可以创建一个计划任务，在仓库目录下运行命令。试运行阶段建议先定时 dry-run，确认没有误发风险后再切到真实发送。

如果希望未登录时不报错，可以在脚本里先执行：

```bash
uv run douyin-spark check-login
```

如果返回码是 `2`，说明未登录，可以直接跳过当天任务并返回成功。

## 安全提醒

- 这是针对抖音网页版的浏览器自动化，抖音 DOM 改动可能导致选择器失效。
- 自动化行为可能不符合平台预期，请只用于个人低频场景。
- `max_recipients` 建议保持较低。
- `random_sleep` 不要设置成 0。
- 改配置后先看 `contacts` 和 `send-once --dry-run`。
- 群聊识别是启发式规则，重要联系人请用 `exclude` 兜底。
- 不要提交 `config.yaml`、`state/`、`logs/`、`screenshots/`。

## 开发

运行测试：

```bash
uv run pytest
```

测试是离线的，不访问抖音，也不会发送消息。

语法检查：

```bash
python -m compileall -q src tests
```

## Public repository

https://github.com/masiqi/douyin-spark-runner

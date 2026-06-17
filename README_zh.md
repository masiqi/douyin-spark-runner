# 抖音续火花本机 Runner

[English](README.md) | 中文

这是一个运行在本机浏览器里的抖音网页版“续火花 / streak”自动化工具。

它不会使用 Android 自动化、手机控制、GitHub Actions Cookie，也不需要安装抖音手机 App。它会在本机打开抖音网页版聊天，读取最近/可见联系人，按配置筛选联系人，给符合条件的人发送随机自然问候，记录当天已发送状态，保存日志和截图，然后退出。

> 安全优先：真实发送前一定先跑 `send-once --dry-run` 检查计划。

## 给 Agent 的快速安装步骤

如果你是 AI coding/ops agent，用户把这个 GitHub 地址给你后，请按下面步骤执行：

```bash
git clone https://github.com/masiqi/douyin-spark-runner.git
cd douyin-spark-runner
uv sync --extra dev
cp config.example.yaml config.yaml
```

然后帮用户编辑 `config.yaml`：

1. `max_recipients` 保守设置，比如 `10`。
2. 除非用户明确要求发群聊，否则保持 `skip_groups: true`。
3. 给课程、商家、客服、官方号、不该打扰的人加入 `exclude`。
4. 如果抖音昵称和日常称呼不同，配置 `aliases`。
5. 先跑 `contacts` 和 `send-once --dry-run`，用户确认后才能真实发送。

常用命令：

```bash
uv run douyin-spark login                 # 首次扫码登录
uv run douyin-spark check-login           # 检查登录态
uv run douyin-spark logout                # 清掉本地登录态，用于切换账号
uv run douyin-spark contacts              # 列出最近/可见联系人
uv run douyin-spark contacts --output json
uv run douyin-spark send-once --dry-run   # 只生成发送计划，不真实发送
uv run douyin-spark send-once             # 真实发送
```

**不要在用户检查 dry-run 计划前执行真实发送。**

## 这是不是 Skill？

这个仓库本身是一个 **CLI 自动化工具**，不是 Hermes/Claude/OpenAI skill。

但 README 按 agent-friendly 方式编写，所以 agent 只拿到 GitHub URL 也能安装和操作。后续可以再做一个很薄的 skill，只负责告诉 agent：

- clone 到哪里；
- 如何安装依赖；
- 如何运行 `login`、`contacts`、`send-once --dry-run`、`send-once`；
- 如何配置 Hermes cron。

也就是说：

- **本仓库**：真正执行代码。
- **可选 skill**：给 agent 的流程说明包装层。

## 功能说明

1. 用 Playwright 打开抖音网页版聊天。
2. 使用本地持久化浏览器 profile：`state/browser-profile`。
3. 读取最近/可见聊天联系人。
4. 根据以下规则过滤：
   - `include` 白名单；
   - `exclude` 排除列表；
   - 群聊启发式判断；
   - 当天已发送记录；
   - `max_recipients` 人数上限。
5. 根据模板生成随机自然消息。
6. 支持昵称别名：抖音昵称用于定位联系人，日常称呼用于消息内容。
7. 逐个发送，中间随机等待。
8. 保存 JSONL 日志、截图、当天发送记录。

## 环境要求

- macOS/Linux 桌面环境，能打开浏览器。
- Python 3.11+。
- [`uv`](https://github.com/astral-sh/uv)。
- 推荐安装 Chrome。

安装依赖：

```bash
uv sync --extra dev
```

如果本机没有可用 Chrome，或者 Playwright 提示缺少浏览器：

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
# 如果没配置，就用抖音昵称。
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

- `{name}`：如果配置了 alias，则用 alias；否则用抖音昵称。
- `{date}`：当前日期。
- `{emoji}`：随机 emoji。
- `{phrase}`：随机短语。

运行时文件：

- 浏览器登录态：`state/browser-profile`
- 当天发送记录：`state/daily/YYYY-MM-DD.json`
- 日志：`logs/*.jsonl`
- 截图：`screenshots/*.png`

## 首次登录

```bash
uv run douyin-spark login
```

命令会打开非 headless 浏览器并进入抖音网页版聊天。扫码登录成功后，回到终端按 Enter，浏览器 profile 会保存在本机。

如果 agent 在远程 Mac 上运行、用户看不到屏幕，命令会保存二维码截图，例如：

```text
screenshots/YYYYMMDD-HHMMSS-login-qr.png
```

agent 可以把这张图发给用户，等用户扫码后，再向等待中的进程输入 Enter。

## 检查登录态

```bash
uv run douyin-spark check-login
```

退出码含义：

- `0`：已登录。
- `2`：未登录。
- `1`：命令异常。

`send-once` 在发送前会自动检查登录态。如果未登录或登录态失效，它会输出 `not_logged_in` 并退出，不会发送消息。

## 切换账号 / logout

```bash
uv run douyin-spark logout
uv run douyin-spark login
```

`logout` 不会点击抖音网页里的退出按钮，而是把本地浏览器 profile 移到带时间戳的备份目录，例如：

```text
state/browser-profile-logout-YYYYMMDD-HHMMSS
```

下一次 `login` 会从新的空 profile 开始，因此可以扫码登录另一个账号。

## 读取联系人

```bash
uv run douyin-spark contacts
uv run douyin-spark contacts --output json
```

这个命令会打开抖音网页版聊天，读取最近/可见联系人，并保存截图。根据输出调整 `include`、`exclude`、`aliases`。

## Dry-run 计划

```bash
uv run douyin-spark send-once --dry-run
```

dry-run 会打开聊天页并输出计划，但不会发送消息，也不会记录为“当天已发送”。

示例：

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

- `name`：抖音聊天列表里的真实昵称，用来定位聊天。
- `display_name`：配置后的日常称呼，用来生成消息。
- `reason`：为什么发送或跳过。

## 真实发送一次

确认 dry-run 没问题后执行：

```bash
uv run douyin-spark send-once
```

执行流程：

1. 打开 `https://www.douyin.com/chat`，失败则回退到 `https://www.douyin.com/im`。
2. 检查登录态。
3. 读取联系人。
4. 过滤收件人。
5. 生成随机消息。
6. 点击联系人，输入消息，按 Enter。
7. 每次发送后随机等待。
8. 记录当天已发送状态并保存日志/截图。

如果确实需要忽略当天已发送记录：

```bash
uv run douyin-spark send-once --force
```

谨慎使用 `--force`，它可能导致同一天重复给同一联系人发送。

## Hermes / cron 示例

稳定 dry-run 后，可以用普通 cron 或 Hermes 定时任务每天运行。

普通 cron 示例：

```cron
15 9 * * * cd /Users/siqi/projects/douyin-spark-runner && UV_CACHE_DIR=.uv-cache uv run douyin-spark send-once >> logs/cron.log 2>&1
```

Hermes Agent 也可以创建 no-agent 脚本型定时任务。建议前期先跑 dry-run，确认无误后再真实发送。

## 安全提醒

- 这是基于抖音网页版的浏览器自动化，DOM 改动可能导致失效。
- 仅建议个人低频使用。
- 保持 `max_recipients` 较低。
- 保持随机等待，不要高频群发。
- 改配置后先跑 `contacts` 和 `send-once --dry-run`。
- 群聊识别是启发式规则，重要联系人请用 `exclude` 明确保护。
- 不要提交 `config.yaml`、`state/`、`logs/`、`screenshots/`。

## 开发

运行测试：

```bash
uv run pytest
```

测试不访问抖音，也不会发送消息。

语法检查：

```bash
python -m compileall -q src tests
```

## Public repository

https://github.com/masiqi/douyin-spark-runner

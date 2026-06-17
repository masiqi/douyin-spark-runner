# douyin-spark-runner

Local Playwright runner for maintaining Douyin chat “spark / streak” interactions from a desktop browser.

It does **not** use Android automation, mobile-device control, GitHub Actions cookies, or the Douyin mobile app. It opens Douyin Web on the local machine, discovers recent chat contacts, sends randomized natural messages to eligible contacts, records daily send state, saves logs/screenshots, then exits.

> Safety first: default behavior is conservative. Always run `send-once --dry-run` before real sending.

## Agent Quick Start

If you are an AI coding/ops agent and the user gives you this repository URL, follow these steps exactly.

```bash
git clone https://github.com/masiqi/douyin-spark-runner.git
cd douyin-spark-runner
uv sync --extra dev
cp config.example.yaml config.yaml
```

Then help the user edit `config.yaml`:

1. Set `max_recipients` conservatively, e.g. `10`.
2. Keep `skip_groups: true` unless the user explicitly wants groups.
3. Add exclusions for shops, courses, customer service, official accounts, or any contact that should never receive messages.
4. Add `aliases` when Douyin nicknames differ from real-life names.
5. Run `contacts` and `send-once --dry-run` before any real send.

- `login` saves a local browser profile after the user scans the QR code.
- `check-login` verifies whether that saved profile is still logged in.
- `logout` moves the saved browser profile aside so a different Douyin account can log in.
- `contacts` lists visible/recent chat contacts.
- `send-once` checks login state first; if not logged in, it prints `not_logged_in` and exits without sending.

Commands:

```bash
uv run douyin-spark login                 # first-time browser login
uv run douyin-spark check-login           # verify saved login state
uv run douyin-spark logout                # switch accounts by clearing saved profile
uv run douyin-spark contacts              # list visible/recent contacts
uv run douyin-spark contacts --output json
uv run douyin-spark send-once --dry-run   # plan only, do not send
uv run douyin-spark send-once             # real send
```

Never run `send-once` until the user has reviewed a dry-run plan.

## Is this a skill?

This repository is primarily a **CLI automation tool**, not a Hermes/Claude/OpenAI skill by itself.

However, it is intentionally documented in an agent-friendly way so an agent can install and operate it from the GitHub URL alone. A separate thin skill can be created later that simply teaches an agent:

- where to clone/install this repo,
- how to run `login`, `contacts`, `send-once --dry-run`, and `send-once`,
- how to configure a Hermes cron job.

In other words:

- **This repo** = executable implementation.
- **Optional skill** = procedural wrapper/instructions for agents.

## What it does

1. Opens Douyin Web chat using Playwright.
2. Uses a persistent local browser profile under `state/browser-profile`.
3. Discovers visible/recent chat contacts.
4. Filters contacts by:
   - include list,
   - exclude list,
   - group heuristic,
   - daily already-sent state,
   - `max_recipients` cap.
5. Generates varied natural messages using templates.
6. Supports nickname aliases so messages use real-life names instead of Douyin display names.
7. Sends messages one by one with random pauses.
8. Saves JSONL logs, screenshots, and daily send records.

## Requirements

- macOS/Linux desktop environment with a browser available.
- Python 3.11+.
- [`uv`](https://github.com/astral-sh/uv).
- Chrome is recommended.

Install dependencies:

```bash
uv sync --extra dev
```

If local Chrome is unavailable or Playwright complains about a missing browser:

```bash
uv run playwright install chromium
```

## Configuration

Create local config:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` is ignored by git. Do not commit real local configuration.

Important fields:

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

# Douyin nickname -> everyday name used in messages.
# If absent, the Douyin nickname is used.
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

Template variables:

- `{name}`: alias value if configured, otherwise Douyin nickname.
- `{date}`: current date.
- `{emoji}`: random emoji from config.
- `{phrase}`: random phrase from config.

Runtime paths:

- Browser profile: `state/browser-profile`
- Daily sent state: `state/daily/YYYY-MM-DD.json`
- Logs: `logs/*.jsonl`
- Screenshots: `screenshots/*.png`

## First login

```bash
uv run douyin-spark login
```

The command opens a non-headless browser and navigates to Douyin Web chat. Complete QR/login in the browser, then return to the terminal and press Enter. The browser profile is saved locally.

For remote/macOS-headless-by-chat scenarios, the command saves a screenshot such as:

```text
screenshots/YYYYMMDD-HHMMSS-login-qr.png
```

An agent can send that image to the user through the chat platform, wait for the user to scan it, then press Enter / submit newline to the waiting process.

## Check login

```bash
uv run douyin-spark check-login
```

Exit code meanings:

- `0`: logged in.
- `2`: not logged in.
- `1`: command error.

`send-once` runs this check internally before sending. If login state is missing/expired, it exits without sending and writes a `not_logged_in` log entry.

## Switch accounts / logout

```bash
uv run douyin-spark logout
uv run douyin-spark login
```

`logout` does not call Douyin's website logout button. It safely moves the local persistent browser profile to a timestamped backup such as `state/browser-profile-logout-YYYYMMDD-HHMMSS`. The next `login` starts with a fresh browser profile, so another account can scan the QR code.

## Discover contacts

```bash
uv run douyin-spark contacts
uv run douyin-spark contacts --output json
```

This opens Douyin Web chat, reads visible/recent contacts, and saves a screenshot. Use this output to adjust `include`, `exclude`, and `aliases`.

## Dry-run plan

```bash
uv run douyin-spark send-once --dry-run
```

Dry-run opens the chat page and prints a plan, but does not send messages and does not mark contacts as sent.

Example output item:

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

Meanings:

- `name`: actual Douyin display name, used for locating the chat.
- `display_name`: configured alias, used in the generated message.
- `reason`: why the contact is eligible or skipped.

## Send once

Only after reviewing dry-run:

```bash
uv run douyin-spark send-once
```

The runner will:

1. Open `https://www.douyin.com/chat` with fallback to `https://www.douyin.com/im`.
2. Discover contacts.
3. Filter recipients.
4. Generate unique-ish randomized messages.
5. Click each contact, type the message, press Enter.
6. Wait a random interval between sends.
7. Record sent contacts in daily state.
8. Save screenshots/logs.

To ignore today’s already-sent state:

```bash
uv run douyin-spark send-once --force
```

Use `--force` carefully. It can send multiple times to the same contact on the same day.

## Hermes cron example

After manual dry-runs are stable, a Hermes cron/no-agent shell job or ordinary cron can run it daily.

Ordinary cron example:

```cron
15 9 * * * cd /Users/siqi/projects/douyin-spark-runner && UV_CACHE_DIR=.uv-cache uv run douyin-spark send-once >> logs/cron.log 2>&1
```

For Hermes Agent, a scheduled job can run this command from the repo workdir. Keep the prompt/script self-contained and start with dry-run during trial periods.

## Safety notes

- This is browser automation against Douyin Web; DOM changes can break selectors.
- It may violate platform automation expectations; use only for personal, low-volume use.
- Keep `max_recipients` low.
- Keep `random_sleep` non-zero.
- Always review `contacts` and `send-once --dry-run` after changing config.
- Group detection is heuristic. Use `exclude` for important safeguards.
- Do not commit `config.yaml`, `state/`, `logs/`, or `screenshots/`.

## Development

Run tests:

```bash
uv run pytest
```

Tests are offline. They do not access Douyin and do not send messages.

Run syntax check:

```bash
python -m compileall -q src tests
```

## Public repository

https://github.com/masiqi/douyin-spark-runner

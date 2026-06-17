# Codex implementation task

Build a production-leaning local Playwright runner for Douyin "spark/streak" maintenance on macOS.

Context:
- User wants NO Android/phone automation and does not want to install the Douyin mobile app.
- Browser automation is acceptable.
- Target deployment is this machine, launched once per day by Hermes cron: start browser, send messages, save logs/screenshots, close browser.
- Prefer not specifying a single contact. The runner should discover visible/recent chat contacts and send to all eligible contacts by default, with safety limits/exclusions.
- Messages must be randomized/natural; never send exactly the same fixed text to everyone.
- We researched existing projects in /Users/siqi/projects/douyin-spark-research. Reuse ideas from:
  - xuhuohua-skill: Playwright login/session and simple send flow.
  - DouYinSparkFlow-dev: https://www.douyin.com/chat selectors: .conversationConversationItemwrapper, .conversationConversationItemtitle, .conversationConversationListwrapper, .messageEditorimChatEditorContainer.
  - ScriptCat-Douyin-Fire-Helper: retry/logging/random messages ideas.

Requirements:
1. Use Python 3.11+ and Playwright sync API or async API. Keep dependencies minimal.
2. Project should be installable/run with uv.
3. Provide config example, but do not commit real config or secrets.
4. Store browser session under state/browser-profile or state/session so login persists locally.
5. Provide commands:
   - login: opens non-headless browser for manual扫码登录 and saves login state/profile.
   - contacts: opens Douyin chat and prints discovered contacts as JSON/table.
   - send-once: sends randomized messages to eligible discovered contacts, saves log and screenshots.
   - maybe dry-run mode: discover and plan recipients/messages without sending.
6. All-friends behavior must be safe:
   - default max recipients cap, e.g. 20, configurable.
   - exclusion list by display name substring/regex.
   - optional include list; if include list is non-empty, only send those.
   - skip groups optionally by heuristic if possible.
   - random sleep between sends.
   - record daily sent contacts in state/daily/YYYY-MM-DD.json and skip already sent unless --force.
7. Random message generation:
   - built-in template pool in config.example.yaml.
   - support per-recipient variation using {name}, {date}, random emoji, short phrase.
   - avoid identical message in a single run.
8. Browser automation:
   - use persistent browser context if practical.
   - Navigate to https://www.douyin.com/chat first, with fallback to https://www.douyin.com/im if needed.
   - Use multiple selector fallbacks for contact items and input box.
   - Do not rely on GitHub Actions cookies.
   - Take screenshot on failure and after run summary.
9. Verification:
   - add unit tests for config loading, message randomization, filtering/daily state logic (no live Douyin needed).
   - run tests locally.
10. Documentation:
   - README in Chinese with setup, login, dry-run, send-once, Hermes cron suggestion, safety warnings.

Implementation constraints:
- Do not actually send any Douyin messages during tests.
- No network calls except Playwright when user runs commands manually.
- Do not install browser binaries if system Chrome is available; document playwright install fallback.
- Keep code readable and maintainable.

After implementation, run unit tests and report exact commands/results.

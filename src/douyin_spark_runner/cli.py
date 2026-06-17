from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .browser import DouyinBrowser, clear_browser_profile
from .config import RunnerConfig, load_config
from .logging_utils import JsonlLogger
from .messages import MessageGenerator
from .recipients import RecipientDecision, plan_recipients
from .state import DailyState


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "login":
            return login(config)
        if args.command == "check-login":
            return check_login(config)
        if args.command == "logout":
            return logout(config)
        if args.command == "contacts":
            return contacts(config, output=args.output)
        if args.command == "send-once":
            return send_once(config, dry_run=args.dry_run, force=args.force)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    parser.print_help()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="douyin-spark")
    parser.add_argument("-c", "--config", type=Path, default=Path("config.yaml"), help="config YAML path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("login", help="open browser for manual Douyin login")
    subparsers.add_parser("check-login", help="check whether the saved browser profile is logged in")
    subparsers.add_parser("logout", help="move the saved browser profile aside so another account can log in")

    contacts_parser = subparsers.add_parser("contacts", help="discover visible/recent chat contacts")
    contacts_parser.add_argument("--output", choices=("json", "table"), default="table")

    send_parser = subparsers.add_parser("send-once", help="send randomized messages once")
    send_parser.add_argument("--dry-run", action="store_true", help="plan recipients/messages without sending")
    send_parser.add_argument("--force", action="store_true", help="ignore today's sent-contact state")
    return parser


def login(config: RunnerConfig) -> int:
    with DouyinBrowser(config) as browser:
        browser.open_chat()
        screenshot = browser.screenshot("login-qr")
        print(f"Login page screenshot saved: {screenshot}")
        print("Browser opened. Scan/login manually, then press Enter here to close and save profile.")
        input()
    return 0


def check_login(config: RunnerConfig) -> int:
    with DouyinBrowser(config) as browser:
        logged_in = browser.ensure_logged_in()
        screenshot = browser.screenshot("check-login")
    if logged_in:
        print(f"logged_in=true screenshot={screenshot}")
        return 0
    print(f"logged_in=false screenshot={screenshot}")
    return 2


def logout(config: RunnerConfig) -> int:
    backup = clear_browser_profile(config)
    if backup is None:
        print(f"No browser profile found at {config.browser_profile_dir}; already logged out.")
        return 0
    print(f"Moved browser profile to {backup}. Run `douyin-spark login` to log in with another account.")
    return 0


def contacts(config: RunnerConfig, *, output: str) -> int:
    with DouyinBrowser(config) as browser:
        discovered = browser.discover_contacts()
        browser.screenshot("contacts")
    if output == "json":
        print(
            json.dumps(
                [asdict(contact) for contact in discovered],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_contacts_table(discovered)
    return 0


def send_once(config: RunnerConfig, *, dry_run: bool, force: bool) -> int:
    daily = DailyState(config.state_dir)
    logger = JsonlLogger(config.log_dir, "send-once-dry-run" if dry_run else "send-once")
    generator = MessageGenerator(config.messages)

    with DouyinBrowser(config) as browser:
        if not browser.ensure_logged_in():
            screenshot = browser.screenshot("not-logged-in")
            logger.write("not_logged_in", dry_run=dry_run, screenshot=str(screenshot))
            print(json.dumps({"status": "not_logged_in", "screenshot": str(screenshot)}, ensure_ascii=False, indent=2))
            return 0

        discovered = browser.discover_contacts()
        decisions = plan_recipients(
            discovered,
            config,
            already_sent=daily.sent_names(),
            today=date.today(),
            force=force,
        )
        plan = _message_plan(decisions, generator, config.aliases)
        logger.write("plan", dry_run=dry_run, force=force, plan=plan)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

        if dry_run:
            screenshot = browser.screenshot("dry-run-summary")
            logger.write("screenshot", path=str(screenshot))
            return 0

        for item in plan:
            if not item["should_send"]:
                continue
            contact = discovered[item["selector_index"]]
            try:
                browser.send_message(contact, item["message"])
                daily.record_sent(contact.name, item["message"])
                logger.write("sent", name=contact.name)
                _sleep(config)
            except Exception as exc:
                screenshot = browser.screenshot(f"failure-{contact.name}")
                logger.write("send_failed", name=contact.name, error=str(exc), screenshot=str(screenshot))
                raise
        screenshot = browser.screenshot("send-summary")
        logger.write("complete", screenshot=str(screenshot))
    return 0


def _message_plan(
    decisions: list[RecipientDecision],
    generator: MessageGenerator,
    aliases: dict[str, str],
) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for decision in decisions:
        display_name = aliases.get(decision.contact.name, decision.contact.name)
        message = generator.render(display_name) if decision.should_send else ""
        plan.append(
            {
                "name": decision.contact.name,
                "display_name": display_name,
                "selector_index": decision.contact.selector_index,
                "is_group": decision.contact.is_group,
                "should_send": decision.should_send,
                "reason": decision.reason,
                "message": message,
            }
        )
    return plan


def _sleep(config: RunnerConfig) -> None:
    seconds = random.uniform(config.random_sleep.min_seconds, config.random_sleep.max_seconds)
    time.sleep(seconds)


def _print_contacts_table(discovered) -> None:  # type: ignore[no-untyped-def]
    print(f"{'INDEX':>5}  {'GROUP':>5}  NAME")
    for contact in discovered:
        print(f"{contact.selector_index:>5}  {str(contact.is_group):>5}  {contact.name}")


if __name__ == "__main__":
    raise SystemExit(main())

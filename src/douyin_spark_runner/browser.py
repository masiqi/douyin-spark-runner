from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from pathlib import Path
import shutil

from playwright.sync_api import BrowserContext, Error, Page, sync_playwright

from .config import RunnerConfig
from .contacts import Contact, looks_like_group


CHAT_URLS = ("https://www.douyin.com/chat", "https://www.douyin.com/im")
CONTACT_SELECTORS = (
    ".conversationConversationItemwrapper",
    "[class*='conversationConversationItem']",
    "[role='listitem']",
)
TITLE_SELECTORS = (
    ".conversationConversationItemtitle",
    "[class*='conversationConversationItemtitle']",
    "[class*='conversation'] [class*='title']",
)
LIST_SELECTORS = (
    ".conversationConversationListwrapper",
    "[class*='conversationConversationList']",
    "[role='list']",
)
EDITOR_SELECTORS = (
    ".messageEditorimChatEditorContainer [contenteditable='true']",
    ".messageEditorimChatEditorContainer textarea",
    "[class*='messageEditor'] [contenteditable='true']",
    "[contenteditable='true']",
    "textarea",
)


class DouyinBrowser(AbstractContextManager["DouyinBrowser"]):
    def __init__(self, config: RunnerConfig) -> None:
        self.config = config
        self._playwright = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def __enter__(self) -> "DouyinBrowser":
        self.config.browser_profile_dir.mkdir(parents=True, exist_ok=True)
        self._playwright = sync_playwright().start()
        self.context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.browser_profile_dir),
            channel="chrome",
            headless=self.config.headless,
            slow_mo=self.config.slow_mo_ms,
            viewport={"width": 1380, "height": 900},
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        if self.context:
            self.context.close()
        if self._playwright:
            self._playwright.stop()

    def open_login_page(self) -> Page:
        """Open a Douyin page suitable for QR-code login without requiring chat to be loaded."""
        page = self._page()
        page.goto("https://www.douyin.com/chat", wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(3_000)
        for text in ("登录", "手机扫码登录", "扫码登录"):
            try:
                button = page.get_by_text(text, exact=False).first
                if button.is_visible(timeout=1_000):
                    button.click(timeout=2_000)
                    page.wait_for_timeout(2_000)
                    break
            except Error:
                continue
        return page

    def open_chat(self) -> Page:
        page = self._page()
        last_error: Exception | None = None
        for url in CHAT_URLS:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(2_000)
                if self.is_logged_in():
                    return page
                if _first_visible(page, LIST_SELECTORS + CONTACT_SELECTORS, timeout=8_000):
                    return page
            except Error as exc:
                last_error = exc
        if last_error:
            raise RuntimeError(f"Could not open Douyin chat: {last_error}") from last_error
        return page

    def is_logged_in(self) -> bool:
        page = self._page()
        try:
            if page.locator("text=登录").first.is_visible(timeout=1_000):
                return False
        except Error:
            pass
        if _first_visible(page, LIST_SELECTORS + CONTACT_SELECTORS, timeout=3_000):
            return True
        try:
            cookies = self.context.cookies() if self.context else []
        except Error:
            cookies = []
        return any(cookie.get("name") == "sessionid" and cookie.get("value") for cookie in cookies)

    def ensure_logged_in(self) -> bool:
        self.open_chat()
        return self.is_logged_in()

    def discover_contacts(self, *, limit: int = 80) -> list[Contact]:
        page = self._page()
        self.open_chat()
        contacts: list[Contact] = []
        seen: set[str] = set()

        for selector in CONTACT_SELECTORS:
            items = page.locator(selector)
            count = min(items.count(), limit)
            for index in range(count):
                item = items.nth(index)
                try:
                    if not item.is_visible(timeout=1_000):
                        continue
                    name = _contact_name(item)
                    if not name or name in seen:
                        continue
                    subtitle = item.inner_text(timeout=1_000)
                except Error:
                    continue
                seen.add(name)
                contacts.append(
                    Contact(
                        name=name,
                        selector_index=index,
                        subtitle=subtitle,
                        is_group=looks_like_group(name, subtitle),
                    )
                )
            if contacts:
                break
        return contacts

    def send_message(self, contact: Contact, message: str) -> None:
        page = self._page()
        clicked = False
        for selector in CONTACT_SELECTORS:
            items = page.locator(selector)
            if items.count() <= contact.selector_index:
                continue
            item = items.nth(contact.selector_index)
            if _contact_name(item) == contact.name:
                item.click(timeout=5_000)
                clicked = True
                break
        if not clicked:
            page.get_by_text(contact.name, exact=False).first.click(timeout=5_000)

        editor = _first_visible(page, EDITOR_SELECTORS, timeout=10_000)
        if editor is None:
            raise RuntimeError(f"Could not find message editor for {contact.name}")
        editor.click()
        page.keyboard.insert_text(message)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1_000)

    def screenshot(self, name: str) -> Path:
        self.config.screenshot_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name)
        path = self.config.screenshot_dir / f"{datetime.now():%Y%m%d-%H%M%S}-{safe_name}.png"
        self._page().screenshot(path=str(path), full_page=True)
        return path

    def _page(self) -> Page:
        if self.page is None:
            raise RuntimeError("Browser is not open")
        return self.page


def clear_browser_profile(config: RunnerConfig) -> Path | None:
    profile_dir = config.browser_profile_dir
    if not profile_dir.exists():
        return None
    backup = profile_dir.with_name(f"{profile_dir.name}-logout-{datetime.now():%Y%m%d-%H%M%S}")
    shutil.move(str(profile_dir), str(backup))
    return backup


def _first_visible(page: Page, selectors: tuple[str, ...], *, timeout: int):
    for selector in selectors:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return locator
        except Error:
            continue
    return None


def _contact_name(item) -> str:  # type: ignore[no-untyped-def]
    for selector in TITLE_SELECTORS:
        try:
            title = item.locator(selector).first
            if title.count() and title.is_visible(timeout=500):
                text = title.inner_text(timeout=1_000).strip()
                if text:
                    return text.splitlines()[0].strip()
        except Error:
            continue
    try:
        text = item.inner_text(timeout=1_000).strip()
    except Error:
        return ""
    return text.splitlines()[0].strip() if text else ""

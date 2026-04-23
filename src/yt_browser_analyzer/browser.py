from __future__ import annotations

import json
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Browser, Page

DEFAULT_CDP_ENDPOINT = "http://127.0.0.1:9222"
DEFAULT_PAGE_HINT = "youtube.com"


class BrowserError(RuntimeError):
    pass


def cdp_json_version(endpoint: str) -> dict | None:
    url = endpoint.rstrip("/") + "/json/version"
    try:
        with urlopen(url, timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError):
        return None


def wait_for_cdp(endpoint: str, timeout_ms: int) -> dict | None:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        payload = cdp_json_version(endpoint)
        if payload:
            return payload
        time.sleep(0.5)
    return None


def ensure_browser(endpoint: str, launcher: str, timeout_ms: int) -> dict:
    payload = cdp_json_version(endpoint)
    if payload:
        return payload
    if not launcher:
        raise BrowserError(f"CDP endpoint {endpoint} is not ready and no launcher was provided.")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", launcher],
        check=True,
    )
    payload = wait_for_cdp(endpoint, timeout_ms)
    if not payload:
        raise BrowserError(f"Browser did not become ready at {endpoint} within {timeout_ms} ms.")
    return payload


def choose_page(browser: Browser, page_hint: str = DEFAULT_PAGE_HINT) -> Page:
    hint = page_hint.lower()
    for context in browser.contexts:
        for page in context.pages:
            if hint and hint in (page.url or "").lower():
                return page
    for context in browser.contexts:
        for page in context.pages:
            if page.url:
                return page
    if browser.contexts:
        return browser.contexts[0].new_page()
    return browser.new_context().new_page()


def new_page(browser: Browser) -> Page:
    if browser.contexts:
        return browser.contexts[0].new_page()
    return browser.new_context().new_page()

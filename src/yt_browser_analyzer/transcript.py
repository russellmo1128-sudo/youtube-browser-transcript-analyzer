from __future__ import annotations

import time
import json
from html import unescape
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from xml.etree import ElementTree

from playwright.sync_api import Page

from .timeutil import format_timestamp, parse_timestamp

TRANSCRIPT_ROW_SELECTOR = "ytd-transcript-segment-renderer"


@dataclass
class TranscriptTrack:
    language_code: str
    kind: str | None
    name: str
    base_url: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "language_code": self.language_code,
            "kind": self.kind,
            "name": self.name,
            "base_url": self.base_url,
        }


def selected_track(page_payload: dict[str, Any]) -> TranscriptTrack | None:
    tracks = page_payload.get("tracks") or []
    if not tracks:
        return None
    track = tracks[0]
    return TranscriptTrack(
        language_code=track.get("languageCode") or "",
        kind=track.get("kind"),
        name=track.get("name") or "",
        base_url=track.get("baseUrl"),
    )


def invoke_transcript_commands(
    page: Page,
    show_endpoint: dict[str, Any] | None,
    continuation_endpoint: dict[str, Any] | None,
) -> dict[str, Any]:
    result = page.evaluate(
        """
        ({ showEndpoint, continuationEndpoint }) => {
          const app = document.querySelector('ytd-app');
          const outcome = {
            showInvoked: false,
            continuationInvoked: false,
            handlerAvailable: !!app,
            errors: []
          };
          if (!app) {
            outcome.errors.push('ytd-app not found');
            return outcome;
          }
          if (showEndpoint && typeof app.handleShowEngagementPanelEndpoint === 'function') {
            try {
              app.handleShowEngagementPanelEndpoint(showEndpoint);
              outcome.showInvoked = true;
            } catch (error) {
              outcome.errors.push(`show endpoint failed: ${String(error)}`);
            }
          }
          if (continuationEndpoint && typeof app.handleCommandWithCommandHandler === 'function') {
            try {
              app.handleCommandWithCommandHandler(continuationEndpoint);
              outcome.continuationInvoked = true;
            } catch (error) {
              outcome.errors.push(`continuation endpoint failed: ${String(error)}`);
            }
          }
          return outcome;
        }
        """,
        {"showEndpoint": show_endpoint, "continuationEndpoint": continuation_endpoint},
    )
    page.wait_for_timeout(1500)
    return result


def wait_for_transcript_rows(page: Page, timeout_ms: int = 20000) -> int:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        count = page.locator(TRANSCRIPT_ROW_SELECTOR).count()
        if count > 0:
            return count
        page.wait_for_timeout(500)
    return 0


def scroll_transcript_until_stable(page: Page, max_rounds: int = 30, settle_ms: int = 800) -> int:
    stable_rounds = 0
    last_count = -1
    current_count = page.locator(TRANSCRIPT_ROW_SELECTOR).count()
    for _ in range(max_rounds):
        page.evaluate(
            """
            () => {
              const rows = document.querySelectorAll('ytd-transcript-segment-renderer');
              if (rows.length) rows[rows.length - 1].scrollIntoView({ block: 'end' });
            }
            """
        )
        page.wait_for_timeout(settle_ms)
        current_count = page.locator(TRANSCRIPT_ROW_SELECTOR).count()
        if current_count == last_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
            last_count = current_count
        if stable_rounds >= 2:
            break
    return current_count


def extract_transcript_rows(page: Page) -> list[dict[str, Any]]:
    return page.evaluate(
        """
        () => {
          return [...document.querySelectorAll('ytd-transcript-segment-renderer')].map((row, index) => {
            const timeNode =
              row.querySelector('.segment-timestamp')
              || row.querySelector('#timestamp')
              || row.querySelector('[class*="timestamp"]');
            const textNode =
              row.querySelector('.segment-text')
              || row.querySelector('#segment-text')
              || row.querySelector('[class*="segment-text"]');
            return {
              index: index + 1,
              start_ts: (timeNode?.textContent || '').trim(),
              text: (textNode?.textContent || '').trim(),
            };
          }).filter(item => item.start_ts || item.text);
        }
        """
    )


def build_raw_entries(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for row in rows:
        start_ts = str(row.get("start_ts") or "").strip()
        start_sec = row.get("start_sec")
        if start_sec is None:
            start_sec = parse_timestamp(start_ts)
        elif not start_ts:
            start_ts = format_timestamp(float(start_sec)) or ""
        text = str(row.get("text") or "").strip()
        entries.append(
            {
                "index": int(row.get("index") or len(entries) + 1),
                "start_ts": start_ts,
                "start_sec": start_sec,
                "text": text,
            }
        )
    return entries


def build_cleaned_entries(entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    last_key: tuple[Any, ...] | None = None
    for item in entries:
        text = " ".join(str(item.get("text") or "").split()).strip()
        start_ts = str(item.get("start_ts") or "").strip()
        start_sec = item.get("start_sec")
        if not text or start_sec is None:
            continue
        key = (start_sec, text)
        if key == last_key:
            continue
        cleaned.append(
            {
                "index": len(cleaned) + 1,
                "source_index": item.get("index"),
                "start_ts": start_ts,
                "start_sec": start_sec,
                "text": text,
            }
        )
        last_key = key
    return cleaned


def validate_cleaned_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    regressions: list[dict[str, Any]] = []
    previous_start: float | None = None
    for item in entries:
        start_sec = float(item["start_sec"])
        if previous_start is not None and start_sec < previous_start:
            regressions.append(
                {
                    "entry_index": item["index"],
                    "start_ts": item["start_ts"],
                    "start_sec": start_sec,
                    "previous_start_sec": previous_start,
                }
            )
        previous_start = start_sec

    return {
        "has_entries": bool(entries),
        "entry_count": len(entries),
        "monotonic_timestamps": not regressions,
        "timestamp_regression_count": len(regressions),
        "timestamp_regressions": regressions[:5],
        "first_start_sec": entries[0]["start_sec"] if entries else None,
        "last_start_sec": entries[-1]["start_sec"] if entries else None,
    }


def build_blocks(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not entries:
        return []
    blocks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_char_count = 0

    def flush() -> None:
        nonlocal current, current_char_count
        if not current:
            return
        blocks.append(
            {
                "id": len(blocks) + 1,
                "start_ts": current[0]["start_ts"],
                "end_ts": current[-1]["start_ts"],
                "start_sec": current[0]["start_sec"],
                "end_sec": current[-1]["start_sec"],
                "text": " ".join(item["text"] for item in current).strip(),
                "source_entry_range": [current[0]["index"], current[-1]["index"]],
            }
        )
        current = []
        current_char_count = 0

    for item in entries:
        if not current:
            current = [item]
            current_char_count = len(item["text"])
            continue
        gap = float(item["start_sec"]) - float(current[-1]["start_sec"])
        duration = float(item["start_sec"]) - float(current[0]["start_sec"])
        projected_chars = current_char_count + 1 + len(item["text"])
        should_flush = gap >= 15 or (duration >= 110 and len(current) >= 4)
        should_flush = should_flush or (projected_chars >= 1000 and len(current) >= 3)
        if should_flush:
            flush()
            current = [item]
            current_char_count = len(item["text"])
            continue
        current.append(item)
        current_char_count = projected_chars

    flush()
    return blocks


def build_transcript_text(entries: Iterable[dict[str, Any]]) -> str:
    lines = [f"[{item['start_ts']}] {item['text']}" for item in entries]
    return "\n".join(lines) + ("\n" if lines else "")


def _with_query_param(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[key] = value
    return urlunparse(parsed._replace(query=urlencode(query)))


def _parse_json3_rows(text: str) -> list[dict[str, Any]]:
    payload = json.loads(text)
    rows: list[dict[str, Any]] = []
    for event in payload.get("events", []):
        if "tStartMs" not in event:
            continue
        row_text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
        row_text = " ".join(row_text.split()).strip()
        if not row_text:
            continue
        start_sec = float(event["tStartMs"]) / 1000
        rows.append(
            {
                "index": len(rows) + 1,
                "start_ts": format_timestamp(start_sec),
                "start_sec": start_sec,
                "text": row_text,
            }
        )
    return rows


def _parse_xml_rows(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    root = ElementTree.fromstring(text)
    rows = []
    for node in root.findall(".//text"):
        start_raw = node.attrib.get("start")
        if start_raw is None:
            continue
        try:
            start_sec = float(start_raw)
        except ValueError:
            continue
        row_text = " ".join(unescape("".join(node.itertext())).split()).strip()
        if not row_text:
            continue
        rows.append(
            {
                "index": len(rows) + 1,
                "start_ts": format_timestamp(start_sec),
                "start_sec": start_sec,
                "text": row_text,
            }
        )
    return rows


def _page_fetch_text(page: Page, url: str) -> dict[str, Any]:
    return page.evaluate(
        """
        async (url) => {
          try {
            const response = await fetch(url, { credentials: 'include' });
            return {
              ok: response.ok,
              status: response.status,
              contentType: response.headers.get('content-type'),
              text: await response.text()
            };
          } catch (error) {
            return { ok: false, status: null, contentType: null, text: '', error: String(error) };
          }
        }
        """,
        url,
    )


def fetch_timedtext_rows(page: Page, base_url: str) -> list[dict[str, Any]]:
    """Fetch rows from YouTube's signed caption track URL as a validated fallback."""

    json_url = _with_query_param(base_url, "fmt", "json3")
    json_response = _page_fetch_text(page, json_url)
    if json_response.get("text"):
        try:
            rows = _parse_json3_rows(json_response["text"])
            if rows:
                return rows
        except Exception:
            pass

    xml_response = _page_fetch_text(page, base_url)
    if not xml_response.get("text"):
        return []
    try:
        return _parse_xml_rows(xml_response["text"])
    except Exception:
        return []

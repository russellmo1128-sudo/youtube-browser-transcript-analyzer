from __future__ import annotations

import re
from typing import Any


DEFAULT_KEYWORDS = [
    "AFK",
    "auto",
    "cloud",
    "download",
    "link",
    "code",
    "discount",
    "subscribe",
    "Roblox",
    "UGPhone",
    "Phone",
    "server",
    "package",
    "MVP",
    "VIP",
    "บอท",
    "โค้ด",
    "ลิงก์",
    "ส่วนลด",
    "แพ็คเกจ",
    "เซิร์ฟ",
    "ดาวน์โหลด",
]


def _clip(text: str, limit: int = 360) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    hits: list[str] = []
    for keyword in keywords:
        if keyword.lower() in lower and keyword not in hits:
            hits.append(keyword)
    return hits


def _ascii_terms(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_+-]{2,}", text)
    stop = {"the", "and", "for", "you", "this", "that", "with", "from"}
    result: list[str] = []
    for token in tokens:
        normalized = token.strip()
        if normalized.lower() in stop:
            continue
        if normalized not in result:
            result.append(normalized)
    return result[:12]


def build_content_analysis(
    metadata: dict[str, Any],
    public_metrics: dict[str, Any],
    blocks_payload: dict[str, Any],
    keywords: list[str] | None = None,
) -> dict[str, Any]:
    keywords = keywords or DEFAULT_KEYWORDS
    segments = []
    for block in blocks_payload.get("blocks", []):
        text = str(block.get("text") or "")
        hits = _keyword_hits(text, keywords)
        segments.append(
            {
                "id": block["id"],
                "start_ts": block["start_ts"],
                "end_ts": block["end_ts"],
                "start_sec": block["start_sec"],
                "end_sec": block["end_sec"],
                "source_entry_range": block["source_entry_range"],
                "keyword_hits": hits,
                "ascii_terms": _ascii_terms(text),
                "extractive_summary": _clip(text),
            }
        )

    return {
        "schema_version": "1.0",
        "analysis_type": "deterministic_timestamped_content_analysis",
        "video_id": metadata["video_id"],
        "title": metadata.get("title"),
        "channel": metadata.get("channel"),
        "duration_seconds": metadata.get("duration_seconds"),
        "public_metrics": {
            "view_count": public_metrics.get("video", {}).get("view_count"),
            "subscriber_count": public_metrics.get("channel", {}).get("subscriber_count"),
            "comment_count": public_metrics.get("engagement", {}).get("comment_count"),
            "like_count": public_metrics.get("engagement", {}).get("like_count"),
        },
        "segments": segments,
        "notes": [
            "This V0.1 analysis is deterministic and extractive, not an LLM summary.",
            "Use transcript blocks and keyword hits as evidence for later human or model-based scoring.",
        ],
    }


def render_content_analysis_markdown(analysis: dict[str, Any]) -> str:
    metrics = analysis.get("public_metrics", {})
    lines = [
        f"# {analysis.get('title') or analysis.get('video_id')}",
        "",
        f"Video ID: `{analysis.get('video_id')}`",
        f"Channel: {analysis.get('channel') or 'unknown'}",
        f"Duration: {analysis.get('duration_seconds') or 'unknown'} seconds",
        "",
        "## Public Metrics",
        "",
    ]
    for name in ["view_count", "subscriber_count", "comment_count", "like_count"]:
        item = metrics.get(name) or {}
        raw = item.get("raw")
        value = item.get("value", item.get("approx_value"))
        lines.append(f"- {name}: raw={raw!r}, value={value!r}")
    lines.extend(["", "## Timeline", ""])
    for segment in analysis.get("segments", []):
        keyword_text = ", ".join(segment.get("keyword_hits") or []) or "none"
        lines.extend(
            [
                f"### {segment['start_ts']}-{segment['end_ts']}",
                "",
                f"Keywords: {keyword_text}",
                "",
                segment["extractive_summary"],
                "",
                f"Source entries: {segment['source_entry_range']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"

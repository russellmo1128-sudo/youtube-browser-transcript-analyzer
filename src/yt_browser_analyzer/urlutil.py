from __future__ import annotations

from urllib.parse import parse_qs, urlparse


class WorkflowError(RuntimeError):
    pass


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith("youtu.be"):
        value = parsed.path.strip("/").split("/")[0]
        if value:
            return value
    if "youtube.com" in host:
        if parsed.path == "/watch":
            value = parse_qs(parsed.query).get("v", [""])[0]
            if value:
                return value
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]
    raise WorkflowError(f"Unsupported YouTube URL: {url}")

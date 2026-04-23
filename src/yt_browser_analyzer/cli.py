from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .artifacts import write_json
from .browser import DEFAULT_CDP_ENDPOINT, DEFAULT_PAGE_HINT, cdp_json_version, ensure_browser
from .capture import capture_single
from .timeutil import utc_now
from .urlutil import WorkflowError

DEFAULT_OUTPUT_ROOT = Path("outputs/youtube-browser-transcript")


def resolve_url_inputs(urls: list[str], urls_file: Path | None) -> list[str]:
    items = list(urls)
    if urls_file:
        items.extend(
            line.strip()
            for line in urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    deduped: list[str] = []
    seen = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def write_batch_report(output_root: Path, runs: list[dict[str, Any]]) -> Path:
    report_dir = output_root / "_batch_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"batch-{utc_now().strftime('%Y%m%dT%H%M%SZ')}.json"
    write_json(
        report_path,
        {
            "schema_version": "1.0",
            "created_at": utc_now().isoformat(timespec="seconds"),
            "run_count": len(runs),
            "ready_run_count": sum(1 for run in runs if run.get("status") == "ready"),
            "blocked_run_count": sum(1 for run in runs if run.get("status") != "ready"),
            "runs": runs,
        },
    )
    return report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture YouTube transcript artifacts from a fixed CDP browser."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    common.add_argument("--cdp-endpoint", default=DEFAULT_CDP_ENDPOINT)
    common.add_argument("--page-hint", default=DEFAULT_PAGE_HINT)
    common.add_argument("--launcher", default=str(Path("scripts/start_edge_cdp.ps1")))
    common.add_argument("--connect-timeout-ms", type=int, default=30000)
    common.add_argument("--settle-ms", type=int, default=2500)
    common.add_argument("--ensure-browser", action="store_true")
    common.add_argument(
        "--restart-on-connect-failure",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Restart the fixed CDP browser once if Playwright cannot connect.",
    )

    capture = subparsers.add_parser("capture", parents=[common])
    capture.add_argument("url")

    batch = subparsers.add_parser("batch-capture", parents=[common])
    batch.add_argument("urls", nargs="*")
    batch.add_argument("--urls-file")

    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "capture":
        urls = [args.url]
    else:
        urls = resolve_url_inputs(args.urls, Path(args.urls_file) if args.urls_file else None)
    if not urls:
        raise WorkflowError("No YouTube URLs were provided.")

    output_root = Path(args.output_root)
    if args.ensure_browser:
        version_payload = ensure_browser(args.cdp_endpoint, args.launcher, args.connect_timeout_ms)
    else:
        version_payload = cdp_json_version(args.cdp_endpoint)
        if not version_payload:
            raise WorkflowError(
                f"CDP endpoint {args.cdp_endpoint} is not ready. "
                "Start the fixed browser first or pass --ensure-browser."
            )

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(
                args.cdp_endpoint,
                timeout=args.connect_timeout_ms,
            )
        except (PlaywrightTimeoutError, PlaywrightError):
            if not (args.ensure_browser and args.restart_on_connect_failure):
                raise
            version_payload = ensure_browser(
                args.cdp_endpoint,
                args.launcher,
                args.connect_timeout_ms,
                force_new=True,
            )
            browser = playwright.chromium.connect_over_cdp(
                args.cdp_endpoint,
                timeout=args.connect_timeout_ms,
            )
        runs = [
            capture_single(
                browser=browser,
                url=url,
                output_root=output_root,
                page_hint=args.page_hint,
                settle_ms=args.settle_ms,
            )
            for url in urls
        ]

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "browser": version_payload.get("Browser", ""),
        "endpoint": args.cdp_endpoint,
        "run_count": len(runs),
        "runs": runs,
    }
    if args.command == "batch-capture":
        payload["batch_report"] = str(write_batch_report(output_root, runs).resolve())
    return payload


def main() -> int:
    try:
        payload = run(parse_args())
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

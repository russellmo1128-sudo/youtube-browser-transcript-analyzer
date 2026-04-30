from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Browser

from .artifacts import build_run_dir, write_json
from .browser import new_page
from .content_analysis import build_content_analysis, render_content_analysis_markdown
from .timeutil import utc_now
from .transcript import (
    build_blocks,
    build_cleaned_entries,
    build_raw_entries,
    build_transcript_text,
    capture_cc_timedtext_rows,
    extract_transcript_rows,
    fetch_timedtext_rows,
    invoke_transcript_commands,
    scroll_transcript_until_stable,
    selected_track,
    validate_coverage,
    validate_cleaned_entries,
    wait_for_transcript_rows,
)
from .urlutil import extract_video_id
from .youtube_page import build_metadata, collect_public_metrics, extract_page_payload


def _build_run_manifest(
    run_dir: Path,
    url: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "pending",
        "created_at": utc_now().isoformat(timespec="seconds"),
        "input_url": url,
        "requested_video_id": metadata["requested_video_id"],
        "video_id": metadata["video_id"],
        "output_dir": str(run_dir.resolve()),
        "pipeline": {
            "mode": "browser_transcript",
            "source": "fixed_cdp_browser",
            "fallbacks": [
                "CC-triggered timedtext json3",
                "live transcript command path",
                "page-exposed signed caption track URL",
            ],
        },
        "artifacts": {
            "metadata": "metadata.json",
            "public_metrics": "video_public_metrics.json",
            "transcript_raw": "transcript.browser.raw.json",
            "transcript_cleaned": "transcript.browser.cleaned.json",
            "transcript_blocks": "transcript.browser.blocks.json",
            "transcript_text": "transcript.browser.txt",
            "content_analysis_json": "content_analysis.json",
            "content_analysis_md": "content_analysis.md",
        },
        "validation": {},
        "notes": [],
    }


def capture_single(
    browser: Browser,
    url: str,
    output_root: Path,
    page_hint: str,
    settle_ms: int,
) -> dict[str, Any]:
    _ = page_hint
    page = new_page(browser)
    requested_video_id = extract_video_id(url)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(settle_ms)

    page_payload = extract_page_payload(page)
    metadata = build_metadata(url, requested_video_id, page_payload)
    video_id = metadata["video_id"]
    run_dir = build_run_dir(output_root, video_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    run_manifest = _build_run_manifest(run_dir, url, metadata)
    write_json(run_dir / "run.json", run_manifest)
    write_json(run_dir / "metadata.json", metadata)

    track = selected_track(page_payload)
    cc_timedtext_result = capture_cc_timedtext_rows(page, requested_video_id)
    invoke_result: dict[str, Any] = {
        "skipped": cc_timedtext_result.get("status") == "ready",
        "reason": "CC-triggered timedtext json3 returned usable caption rows.",
    }
    initial_rows = 0
    final_rows = 0
    if cc_timedtext_result.get("status") == "ready":
        transcript_source = "youtube_cc_timedtext_json3"
        rows = list(cc_timedtext_result.get("rows") or [])
    else:
        invoke_result = invoke_transcript_commands(
            page,
            page_payload.get("showEndpoint"),
            page_payload.get("continuationEndpoint"),
        )
        initial_rows = wait_for_transcript_rows(page)
        final_rows = scroll_transcript_until_stable(page) if initial_rows else 0
        transcript_source = "youtube_live_transcript_browser"
        rows = extract_transcript_rows(page)
    if not rows and track and track.base_url:
        rows = fetch_timedtext_rows(page, track.base_url)
        transcript_source = "youtube_timedtext_caption_track_fallback"
    raw_entries = build_raw_entries(rows)
    cleaned_entries = build_cleaned_entries(raw_entries)
    blocks = build_blocks(cleaned_entries)
    cleaned_validation = validate_cleaned_entries(cleaned_entries)
    coverage_validation = validate_coverage(cleaned_entries, metadata.get("duration_seconds"))
    video_id_match = requested_video_id == video_id
    usable = (
        bool(cleaned_entries)
        and cleaned_validation["monotonic_timestamps"]
        and coverage_validation["sufficient_for_full_video_summary"]
        and video_id_match
    )
    status = "ready" if usable else "blocked"

    notes = []
    if track:
        notes.append(f"Selected transcript track: {track.language_code} ({track.kind or 'unknown'}).")
    else:
        notes.append("No caption track metadata was exposed in the player response.")
    if cleaned_entries and transcript_source == "youtube_cc_timedtext_json3":
        notes.append("Transcript rows were loaded from the player CC-triggered timedtext json3 response.")
    elif cleaned_entries and transcript_source == "youtube_live_transcript_browser":
        notes.append("Transcript rows were loaded through the live browser transcript command path.")
    elif cleaned_entries:
        notes.append("Transcript rows were loaded through the page-exposed signed caption track URL.")
    else:
        notes.append("Transcript command path did not produce readable rows.")
    if not video_id_match:
        notes.append(f"Requested video_id {requested_video_id} but page exposed {video_id}.")
    if cleaned_entries and not cleaned_validation["monotonic_timestamps"]:
        notes.append("Transcript timestamps are not monotonic after cleaning.")
    if invoke_result.get("errors"):
        notes.extend(str(item) for item in invoke_result["errors"])
    if cc_timedtext_result.get("errors"):
        notes.extend(f"CC timedtext: {item}" for item in cc_timedtext_result["errors"])
    if cleaned_entries and not coverage_validation["sufficient_for_full_video_summary"]:
        notes.append("Transcript coverage is too short for a full-video summary.")

    validation = {
        "requested_video_id": requested_video_id,
        "page_video_id": video_id,
        "video_id_match": video_id_match,
        "has_caption_track_metadata": bool(track),
        "transcript_source": transcript_source if cleaned_entries else None,
        "raw_row_count": len(raw_entries),
        "cleaned_entry_count": len(cleaned_entries),
        "block_count": len(blocks),
        "cleaned_entries": cleaned_validation,
        "coverage": coverage_validation,
        "cc_timedtext": {
            key: value
            for key, value in cc_timedtext_result.items()
            if key != "rows"
        },
        "usable_for_summary": usable,
    }

    transcript_common = {
        "schema_version": "1.0",
        "status": status,
        "video_id": video_id,
        "requested_video_id": requested_video_id,
        "title": metadata["title"],
        "page_url": metadata["page_url"],
        "track": track.to_dict() if track else None,
        "validation": validation,
        "notes": notes,
    }
    transcript_raw = {
        **transcript_common,
        "source": transcript_source,
        "command_invocation": invoke_result,
        "cc_timedtext_capture": {
            key: value
            for key, value in cc_timedtext_result.items()
            if key != "rows"
        },
        "row_count": len(raw_entries),
        "entries": raw_entries,
    }
    transcript_cleaned = {
        **transcript_common,
        "entry_count": len(cleaned_entries),
        "entries": cleaned_entries,
    }
    transcript_blocks = {
        **transcript_common,
        "block_count": len(blocks),
        "blocks": blocks,
    }

    write_json(run_dir / "transcript.browser.raw.json", transcript_raw)
    write_json(run_dir / "transcript.browser.cleaned.json", transcript_cleaned)
    write_json(run_dir / "transcript.browser.blocks.json", transcript_blocks)
    (run_dir / "transcript.browser.txt").write_text(
        build_transcript_text(cleaned_entries),
        encoding="utf-8",
    )

    public_metrics = collect_public_metrics(page, page_payload, settle_ms=max(750, settle_ms // 2))
    write_json(run_dir / "video_public_metrics.json", public_metrics)

    if usable:
        analysis = build_content_analysis(metadata, public_metrics, transcript_blocks)
        write_json(run_dir / "content_analysis.json", analysis)
        (run_dir / "content_analysis.md").write_text(
            render_content_analysis_markdown(analysis),
            encoding="utf-8",
        )

    run_manifest["status"] = status
    run_manifest["validation"] = validation
    run_manifest["notes"] = notes
    write_json(run_dir / "run.json", run_manifest)

    return {
        "input_url": url,
        "video_id": video_id,
        "run_dir": str(run_dir.resolve()),
        "status": status,
        "title": metadata["title"],
        "public_metrics": public_metrics,
        "raw_row_count": len(raw_entries),
        "cleaned_entry_count": len(cleaned_entries),
        "block_count": len(blocks),
        "validation": validation,
        "artifacts": {
            key: str((run_dir / filename).resolve())
            for key, filename in run_manifest["artifacts"].items()
        },
        "notes": notes,
        "transcript_debug": {
            "initial_row_count": initial_rows,
            "final_row_count": final_rows,
            "invoke_result": invoke_result,
            "cc_timedtext_result": {
                key: value
                for key, value in cc_timedtext_result.items()
                if key != "rows"
            },
        },
    }

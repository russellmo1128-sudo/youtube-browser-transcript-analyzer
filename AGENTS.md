# Codex Instructions

This repository is a local YouTube video evidence collector and timestamped analyzer.

When the user asks to summarize, analyze, or extract information from a YouTube URL:

1. Use this repository's CLI instead of web search.
2. Start or reuse the fixed Edge CDP browser. Do not manually start a separate debug browser if port `9222` is already available. The CLI can restart the fixed debug browser automatically if the existing CDP connection is stale.
3. Run the capture command for the provided YouTube URL. If the user provides multiple YouTube URLs in one message, use `batch-capture` once instead of running multiple separate `capture` commands.
4. Read the latest generated run directory under `outputs/youtube-browser-transcript/<video_id>/`.
5. Check `run.json` before summarizing.
6. Only summarize when:
   - `status` is `ready`
   - `validation.video_id_match` is `true`
   - `validation.usable_for_summary` is `true`
   - `validation.cleaned_entries.monotonic_timestamps` is `true`
7. Read these files:
   - `video_public_metrics.json`
   - `transcript.browser.blocks.json`
   - `content_analysis.md`
8. Produce a timestamped summary grounded in the transcript blocks.
9. Include public metrics when available:
   - view count
   - channel subscriber count
   - comment count
   - like count
   - duration
   - publish date
10. If the run is blocked, do not summarize from title or description alone. Report Known, Unverified, and Next Step.

Default command:

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture "<YOUTUBE_URL>" --ensure-browser
```

The CLI defaults to `--restart-on-connect-failure`, so a stale debug browser should be restarted once automatically.

Multiple URLs:

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli batch-capture "<YOUTUBE_URL_1>" "<YOUTUBE_URL_2>" --ensure-browser
```

If `.venv` does not exist, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

If the fixed browser is not running, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1
```

Do not commit or share `outputs/`, `.browser-profile/`, `.venv/`, or generated transcript artifacts unless the user explicitly asks.

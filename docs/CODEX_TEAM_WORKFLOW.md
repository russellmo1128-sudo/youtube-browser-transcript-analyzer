# Codex Teammate Workflow

This guide is for teammates using Codex with their own GPT Plus accounts.

## Goal

After setup, a teammate should be able to ask Codex:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

Codex should then run this repo's CLI, control the fixed browser through Playwright/CDP, capture transcript artifacts, read the local output files, and summarize the video.

## One-time Setup

Recommended:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Manual equivalent:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
$site = .\.venv\Scripts\python.exe -c "import site; print(site.getsitepackages()[0])"
Set-Content -LiteralPath (Join-Path $site "yt_browser_analyzer_local.pth") -Value (Join-Path (Get-Location) "src") -Encoding ASCII
```

The fixed browser uses a persistent local profile:

```text
%LOCALAPPDATA%\youtube-browser-transcript-analyzer\edge-cdp-profile
```

After the first setup, later captures reuse the same browser/profile. If the browser is already running on port `9222`, the launcher will not open another debug browser.

If an old debug browser is stale, the CLI restarts it once automatically. Manual fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1 -ForceNew
```

## One-sentence Codex Usage

Ask Codex from inside this repository:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

The repository-level `AGENTS.md` tells Codex how to handle this request.

For multiple links in one message, Codex should use one batch command:

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli batch-capture "URL1" "URL2" "URL3" --ensure-browser
```

This reuses the same fixed browser and opens new tabs for each video.

## Single Video Capture

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture "https://www.youtube.com/watch?v=VIDEO_ID" --ensure-browser
```

## Batch Capture

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli batch-capture "URL1" "URL2" "URL3" --ensure-browser
```

Or put URLs in a file:

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli batch-capture --urls-file .\examples\urls.txt --ensure-browser
```

## Output Files To Read

Each run writes:

```text
outputs/youtube-browser-transcript/<video_id>/<run_id>/
```

Most useful files:

```text
video_public_metrics.json
transcript.browser.blocks.json
content_analysis.md
content_analysis.json
run.json
```

Use `run.json` first. Only trust the analysis when:

```text
status = ready
validation.video_id_match = true
validation.usable_for_summary = true
validation.cleaned_entries.monotonic_timestamps = true
```

## Suggested Codex Prompt

After capturing a video, ask Codex:

```text
Read the latest run directory under outputs/youtube-browser-transcript.
Use run.json to verify the capture is ready.
Then read video_public_metrics.json, transcript.browser.blocks.json, and content_analysis.md.

Summarize the video by timestamp.
Extract:
- video topic
- channel name
- public metrics
- main content sections
- any sponsor or product mention time
- useful evidence for later manual scoring

Do not invent conversion performance. If something is missing, mark it unverified.
```

For multiple videos:

```text
Read all ready run directories from the latest batch.
Create a comparison table with:
- video_id
- title
- channel
- duration
- view_count
- subscriber_count
- comment_count
- like_count
- transcript block count
- main content summary
- sponsor/product mention windows
- evidence gaps
```

## Troubleshooting

If setup fails:

- copy the exact setup error into Codex
- make sure Python 3.10+ is installed
- make sure the computer can access Python package downloads
- if Codex reports `PermissionError`, `WinError 5`, or Python temp directory access errors, approve rerunning the same command outside the sandbox

If capture is blocked:

- confirm the fixed Edge browser is still open
- rerun with `--ensure-browser`
- try the URL in a fresh browser tab
- check `run.json` and `transcript_debug`
- do not summarize a blocked transcript as final

If Playwright cannot connect:

- if Codex reports `WinError 5` while starting Playwright, approve rerunning the same capture command outside the sandbox
- make sure port `9222` is not occupied by another browser profile
- restart the Edge CDP browser using `scripts/start_edge_cdp.ps1`

If public comment count is missing:

- YouTube may not have rendered comments
- comments may be disabled
- treat the comment count as unverified

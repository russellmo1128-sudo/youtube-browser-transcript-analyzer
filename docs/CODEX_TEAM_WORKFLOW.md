# Codex Teammate Workflow

This guide is for teammates using Codex with their own GPT Plus accounts.

## Goal

After setup, a teammate should be able to ask Codex:

```text
帮我总结这个 YouTube 视频：https://www.youtube.com/watch?v=VIDEO_ID
```

Codex should then run this repo's CLI, control the fixed browser through Playwright/CDP, capture transcript artifacts, read the local output files, and summarize the video.

## One-time Setup

Clone the repository:

```powershell
git clone https://github.com/YOUR_NAME/youtube-browser-transcript-analyzer.git
cd youtube-browser-transcript-analyzer
```

Create the Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
```

Start the fixed Edge browser:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1
```

Keep that browser open while running captures.

## One-sentence Codex Usage

Ask Codex from inside this repository:

```text
帮我总结这个 YouTube 视频：https://www.youtube.com/watch?v=VIDEO_ID

请使用本仓库的 yt_browser_analyzer CLI 抓取字幕和公开视频指标。
运行完成后读取最新 outputs 目录，先检查 run.json 是否 ready，再基于 transcript.browser.blocks.json、video_public_metrics.json 和 content_analysis.md 按时间戳总结。
```

Short version:

```text
帮我总结这个视频：https://www.youtube.com/watch?v=VIDEO_ID
```

The repository-level `AGENTS.md` tells Codex how to handle this request.

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

If capture is blocked:

- confirm the fixed Edge browser is still open
- rerun with `--ensure-browser`
- try the URL in a fresh browser tab
- check `run.json` and `transcript_debug`
- do not summarize a blocked transcript as final

If Playwright cannot launch or connect:

- run `.\.venv\Scripts\python.exe -m playwright install chromium`
- make sure port `9222` is not occupied by another browser profile
- restart the Edge CDP browser using `scripts/start_edge_cdp.ps1`

If public comment count is missing:

- YouTube may not have rendered comments
- comments may be disabled
- treat the comment count as unverified

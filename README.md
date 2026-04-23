# YouTube Browser Transcript Analyzer

V0.1 is a browser-first workflow for collecting evidence from YouTube videos:

- connect to a fixed local Chrome/Edge CDP browser
- open a user-provided YouTube watch URL
- capture transcript rows from the live YouTube page
- fall back to the page-exposed signed caption track URL when the live transcript panel does not render rows
- validate video ID, non-empty transcript rows, and monotonic timestamps
- collect public page metrics such as views, comments, likes when visible, channel name, and subscriber text when visible
- write timestamped transcript artifacts and a content analysis report

The project does not include conversion scoring or business-specific templates. It only produces reliable source artifacts that downstream analysis can use.

## Codex One-sentence Usage

This repository includes `AGENTS.md` so Codex can use the local CLI when a teammate asks for a YouTube summary.

After setup, open this repository in Codex and ask:

```text
帮我总结这个 YouTube 视频：https://www.youtube.com/watch?v=VIDEO_ID
```

Codex should run the capture command, read the generated local artifacts, and summarize from the transcript evidence.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m playwright install chromium
```

Windows one-command setup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

## Start A Fixed Browser

Windows Edge example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1
```

By default this starts Edge on `http://127.0.0.1:9222` with a local `.browser-profile/edge-cdp` profile.

## Capture One Video

```powershell
yt-browser-analyzer capture "https://www.youtube.com/watch?v=VIDEO_ID" --ensure-browser
```

If the console cannot find `yt-browser-analyzer`, use the module form:

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture "https://www.youtube.com/watch?v=VIDEO_ID" --ensure-browser
```

## Capture Multiple Videos

```powershell
yt-browser-analyzer batch-capture "https://www.youtube.com/watch?v=AAA" "https://youtu.be/BBB" --ensure-browser
```

## Output Artifacts

Artifacts are written under:

```text
outputs/youtube-browser-transcript/<video_id>/<video_id>-<timestamp>/
```

Files:

```text
run.json
metadata.json
video_public_metrics.json
transcript.browser.raw.json
transcript.browser.cleaned.json
transcript.browser.blocks.json
transcript.browser.txt
content_analysis.json
content_analysis.md
```

## Reliability Policy

A capture is usable only when:

- requested video ID equals the page video ID
- cleaned transcript entries are non-empty
- cleaned transcript timestamps are monotonic
- the transcript source is recorded (`youtube_live_transcript_browser` or `youtube_timedtext_caption_track_fallback`)

If those checks fail, the run is marked `blocked`. Do not treat blocked output as a final summary.

## Public Metrics Caveat

YouTube page metrics are public, locale-dependent, and sometimes lazy-loaded. The analyzer stores both raw visible text and best-effort parsed numeric values. Parsed subscriber, like, and comment counts should be treated as approximate unless verified against an official source.

## Compliance

Use this tool only for videos you are allowed to analyze. Do not redistribute full transcript text unless you have the right to do so.

## Team Guides

- [Open-source publishing guide](docs/OPEN_SOURCE_GUIDE.md)
- [Codex teammate workflow](docs/CODEX_TEAM_WORKFLOW.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

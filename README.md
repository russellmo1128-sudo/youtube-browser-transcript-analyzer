# YouTube Browser Transcript Analyzer

V0.1 is a browser-first workflow for collecting evidence from YouTube videos:

- connect to a fixed local Microsoft Edge CDP browser
- open a user-provided YouTube watch URL
- capture transcript rows from the live YouTube page
- fall back to the page-exposed signed caption track URL when available
- validate video ID, non-empty transcript rows, and monotonic timestamps
- collect public page metrics such as views, comments, likes, channel name, subscriber text, duration, and publish date when visible
- write timestamped transcript artifacts and a content analysis report

The project does not include conversion scoring or business-specific templates. It only produces source artifacts that downstream analysis can use.

## Easiest Windows Usage

For non-technical teammates:

1. Download this repo as a ZIP from GitHub.
2. Unzip it.
3. Double-click `START_HERE.bat` once.
4. Open the unzipped folder in Codex.
5. Ask Codex:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

See [Non-technical quickstart](docs/NON_TECHNICAL_QUICKSTART.md).

## Codex One-sentence Usage

This repository includes `AGENTS.md` so Codex can use the local CLI when a teammate asks for a YouTube summary.

After setup, open this repository in Codex and ask:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

Codex should run the capture command, read the generated local artifacts, and summarize from transcript evidence.

## Install

Windows one-command setup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

The setup script:

- creates `.venv`
- uses workspace-local `.tmp` for Python temporary files
- installs the Python package dependencies
- verifies that `playwright` and `yt_browser_analyzer` can be imported before printing `Setup complete`

Manual equivalent:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
$site = .\.venv\Scripts\python.exe -c "import site; print(site.getsitepackages()[0])"
Set-Content -LiteralPath (Join-Path $site "yt_browser_analyzer_local.pth") -Value (Join-Path (Get-Location) "src") -Encoding ASCII
```

The default Edge/CDP workflow does not require `playwright install chromium` because it connects to the installed Microsoft Edge browser.

## Start A Fixed Browser

Windows Edge example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1
```

By default this starts Edge on `http://127.0.0.1:9222` with a persistent user-local profile:

```text
%LOCALAPPDATA%\youtube-browser-transcript-analyzer\edge-cdp-profile
```

If a CDP browser is already running on port `9222`, the script reuses it instead of opening another debug browser. Later video captures open new tabs in the same browser.

If the old debug browser becomes stale, the CLI restarts it once automatically by default. Manual restart:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_edge_cdp.ps1 -ForceNew
```

## Capture One Video

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture "https://www.youtube.com/watch?v=VIDEO_ID" --ensure-browser
```

## Capture Multiple Videos

```powershell
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli batch-capture "https://www.youtube.com/watch?v=AAA" "https://youtu.be/BBB" --ensure-browser
```

Use `batch-capture` when the user provides multiple links. It keeps one browser connection and opens one new tab per video.

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
- the transcript source is recorded

If those checks fail, the run is marked `blocked`. Do not treat blocked output as a final summary.

## Public Metrics Caveat

YouTube page metrics are public, locale-dependent, and sometimes lazy-loaded. Parsed subscriber, like, and comment counts should be treated as approximate unless verified against an official source.

## Compliance

Use this tool only for videos you are allowed to analyze. Do not redistribute full transcript text unless you have the right to do so.

## Team Guides

- [Open-source publishing guide](docs/OPEN_SOURCE_GUIDE.md)
- [Codex teammate workflow](docs/CODEX_TEAM_WORKFLOW.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

# Non-technical Quickstart

This is the simplest workflow for teammates who do not want to type many commands.

## First Time

1. Open the GitHub repo:

```text
https://github.com/russellmo1128-sudo/youtube-browser-transcript-analyzer
```

2. Click **Code**.
3. Click **Download ZIP**.
4. Unzip the file.
5. Open the unzipped folder.
6. Double-click:

```text
START_HERE.bat
```

This creates the local Python environment and installs the automation dependency.

The tool uses one persistent Edge browser environment on your computer. After the first run, later videos reuse the same browser and open new tabs.

If the browser gets stuck, close the debug Edge window and run `OPEN_BROWSER.bat` again. The CLI also tries one automatic restart when the CDP connection is stale.

## Use With Codex

1. Open Codex.
2. Open or select the unzipped `youtube-browser-transcript-analyzer` folder as the workspace.
3. Ask Codex:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID
```

Codex should read `AGENTS.md`, run the local capture tool, then summarize from the generated evidence files.

If you send multiple YouTube links in one message, Codex should process them in one batch and reuse the same browser.

If Codex asks for permission to run setup or Playwright outside the sandbox, approve it. The tool needs local browser access.

## If Codex Does Not Automatically Run The Tool

Paste this fuller prompt:

```text
Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID

Follow this repository's AGENTS.md workflow. Run:
.\.venv\Scripts\python.exe -m yt_browser_analyzer.cli capture "<URL_ABOVE>" --ensure-browser

Then read the latest outputs folder. Check run.json first. Only summarize if status=ready.
```

## No-Codex Fallback

If you only want to capture data:

1. Double-click:

```text
ANALYZE_VIDEO.bat
```

2. Paste a YouTube URL.
3. Wait for the capture to finish.
4. The output folder opens automatically.
5. Copy the generated folder path into Codex and ask it to summarize that folder.

## What Gets Generated Locally

Outputs are created on your own computer:

```text
outputs/youtube-browser-transcript/<video_id>/<run_id>/
```

Important files:

```text
run.json
video_public_metrics.json
transcript.browser.blocks.json
content_analysis.md
```

Do not upload `outputs/` unless you intentionally want to share generated transcript artifacts.

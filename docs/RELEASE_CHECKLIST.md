# Release Checklist

Use this checklist before pushing or tagging a release.

## Local Checks

```powershell
cd "C:\Users\Og\Documents\New project\youtube-browser-transcript-analyzer"
python -m compileall src
$env:PYTHONPATH='src'
python -X utf8 -m yt_browser_analyzer.cli --help
```

Run one real capture:

```powershell
$env:PYTHONPATH='src'
python -X utf8 -m yt_browser_analyzer.cli capture "https://www.youtube.com/watch?v=5d9UFv3YMvU" --ensure-browser --settle-ms 2000
```

Verify the latest `run.json`:

```text
status = ready
video_id_match = true
usable_for_summary = true
cleaned_entry_count > 0
block_count > 0
```

Verify public metrics:

```text
video_public_metrics.json exists
view_count.raw exists
channel.name exists
subscriber_count.raw is present when YouTube renders it
comment_count.raw is present when YouTube renders comments
```

## Git Checks

```powershell
git status --short
```

Expected tracked content:

```text
.gitignore
LICENSE
README.md
pyproject.toml
docs/
examples/
scripts/
src/
```

Do not commit:

```text
outputs/
.browser-profile/
.venv/
__pycache__/
.env
```

## Tagging

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## Release Notes

V0.1 includes:

- YouTube URL capture through fixed CDP browser
- live transcript command path
- validated transcript artifacts
- public metrics extraction
- deterministic timestamped content analysis
- team usage docs

V0.1 does not include:

- conversion scoring
- OpenAI API integration
- private backend metrics
- video frame OCR

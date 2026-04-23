# Open-source Publishing Guide

This guide turns the local V0.1 tool into a GitHub repository.

## Current Local Stage

The project is ready as a standalone directory:

```text
youtube-browser-transcript-analyzer/
```

It contains source code, packaging metadata, a license, a README, and team usage docs. Generated outputs are ignored by `.gitignore`.

## What You Need To Do In GitHub

Codex can prepare the local repository, but you need to create or authorize the GitHub repository because it depends on your GitHub account.

1. Open GitHub.
2. Click **New repository**.
3. Repository name: `youtube-browser-transcript-analyzer`.
4. Choose **Public** if you want it open-source, or **Private** if you only want internal sharing first.
5. Do not initialize with README, `.gitignore`, or license. This project already has them.
6. Create the repository.
7. Copy the remote URL, for example:

```text
https://github.com/YOUR_NAME/youtube-browser-transcript-analyzer.git
```

## Push From Local

Run these commands from the project directory:

```powershell
cd "C:\Users\Og\Documents\New project\youtube-browser-transcript-analyzer"
git remote add origin https://github.com/YOUR_NAME/youtube-browser-transcript-analyzer.git
git push -u origin main
git tag v0.1.0
git push origin v0.1.0
```

If `git push` asks you to log in, authenticate with GitHub in the browser or use a personal access token.

## What Should Not Be Published

These paths are ignored and should stay local:

```text
outputs/
.browser-profile/
.venv/
.env
```

The repository should not include browser cookies, YouTube login sessions, company backend data, private invite links, registration data, or GMV data.

## What V0.1 Publishes

V0.1 publishes only the generic tool:

- fixed browser CDP connection
- YouTube page opening
- live transcript row capture
- transcript validation artifacts
- public page metrics capture
- deterministic timestamped content analysis

It does not publish UgPhone scoring models or company conversion logic.

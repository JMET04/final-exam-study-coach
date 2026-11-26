# GitHub Web Upload Guide

Use this guide if GitHub CLI or a local token is not available.

## 1. Create the repository

Create a new GitHub repository with these settings:

- Repository name: `final-exam-study-coach`
- Visibility: public if you want to publish it broadly; private if you want to review first.
- Description: `A Codex skill that turns course materials, exam scope, past papers, and remaining time into a procrastination-aware final exam study plan and coaching workflow.`
- Do not initialize with README, license, or `.gitignore`; this package already contains them where needed.

## 2. Upload the files

Option A: Git push

Run from `github_release`:

```powershell
.\scripts\publish_to_github.ps1 -RemoteUrl "https://github.com/<owner>/final-exam-study-coach.git"
```

Option B: Web upload

Upload the contents of the `github_release` folder, not the parent folder. Do not upload `.git`.

## 3. Create the first release

After the repository is online:

- Tag: `v0.1.0`
- Release title: `v0.1.0 - Final Exam Study Coach`
- Release body: paste `docs/release-notes-v0.1.0.md`

## 4. Repository topics

Recommended topics:

- `codex-skill`
- `study-coach`
- `exam-prep`
- `spaced-repetition`
- `education`
- `learning-assistant`
- `chinese`

## 5. Privacy check

Before uploading, confirm the repository does not include:

- Private textbooks.
- Lecture slides.
- Past exam papers.
- Screenshots from personal accounts.
- Personal study checkpoints.
- Local absolute paths containing personal data.

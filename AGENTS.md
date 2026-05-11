# Agent Instructions

This repository is a Codex and Claude Code skill for low-frequency, read-only China Railway 12306 lookups.

## Scope

- Keep `SKILL.md` concise and focused on agent behavior.
- Keep detailed endpoint notes in `references/endpoints.md`.
- Keep deterministic helper logic in `scripts/rail12306.py`.
- Do not add login, captcha, ticket booking, order submission, scraping, or polling features.
- Prefer Python standard library code so the client works on Windows, macOS, and Linux without dependency installation.

## Validation

Run these checks after changing the skill or client:

```bash
python3 -m py_compile scripts/rail12306.py
python3 scripts/rail12306.py stations 北京南 --json
python3 scripts/rail12306.py stops G1 --date 2026-05-20 --json
```

If available, also run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## Documentation

- Update both `README.md` and `README_zh.md` for user-facing behavior changes.
- Keep the two README files linked to each other.
- If the demo GIF changes, keep it at `assets/codex-demo.gif` unless the README links are updated.

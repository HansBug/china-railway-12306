# Agent Instructions

This repository is a Codex and Claude Code skill for low-frequency, read-only China Railway 12306 lookups.

When a user asks a normal mainland China railway travel question, such as
checking tomorrow's trains, tickets, fares, times, or stops, use this skill even
from an arbitrary local working directory. The user does not need to name the
skill, mention 12306, or know station telecodes.
Resolve the helper script from the installed skill directory instead of assuming
the current directory is this repo:

```bash
RAIL12306_SCRIPT="${RAIL12306_SCRIPT:-$HOME/.codex/skills/china-railway-12306/scripts/rail12306.py}"
[ -f "$RAIL12306_SCRIPT" ] || RAIL12306_SCRIPT="$HOME/.claude/skills/china-railway-12306/scripts/rail12306.py"
```

For station-to-station train, ticket, time, and fare questions, run one command
like `python3 "$RAIL12306_SCRIPT" tickets 北京 杭州 --date YYYY-MM-DD --limit 3`.
The `tickets` output already includes parsed fares; call `price` only when the
user asks about a specific train or the ticket row lacks fares. Do not run
`--help` as part of a normal travel answer.

For user-facing answers, prefer concise natural language with train number,
departure/arrival time, remaining seats, fare, and practical booking advice when
useful. Use JSON only when the user explicitly asks for structured output or
another tool needs it. Every answer based on live 12306 data must state the
second-level query timestamp captured immediately before the API/script call.
When using `scripts/rail12306.py`, copy the script's `查询时间` value into the
final answer. For Chinese answers, include this exact source caveat once:
`数据来自当前 12306 公开网页端点，非官方开发者 API。` End Chinese live-data
answers with this exact sentence: `以上为本次实时查询结果。`

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

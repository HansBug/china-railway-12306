# China Railway 12306 Skill

[中文说明](README_zh.md)

A Codex and Claude Code compatible skill for personal, read-only lookups against the current China Railway 12306 public web endpoints. It helps agents resolve station telecodes, query trains and remaining tickets, fetch fares, and list train stops without login or booking flows.

> This is not an official 12306 developer API. Use it for low-frequency personal/agent lookups only. Do not use it for ticket booking, login, captcha handling, order submission, bypassing controls, scraping, or monitoring.

## Demo

The GIF below shows a real interactive `codex` session started from `/tmp`, not from this repository. The user asks a normal travel question, Codex discovers the installed skill, calls the bundled 12306 client, and returns train times, remaining seats, fares, and a second-level query timestamp.

![Codex uses the China Railway 12306 skill](assets/codex-demo.gif)

MP4 version: [assets/codex-demo.mp4](assets/codex-demo.mp4)

## What It Provides

- `SKILL.md` for Codex and Claude Code skill discovery.
- `scripts/rail12306.py`, a dependency-free Python client that works on Linux, macOS, and Windows.
- `references/endpoints.md`, notes on the current 12306 read-only endpoints and response fields.
- `AGENTS.md` plus `CLAUDE.md -> AGENTS.md` so both agent systems receive the same repo guidance.

Supported lookup tasks:

- Station lookup: station name, city name, pinyin, short pinyin, or telecode.
- Ticket/train lookup: station-to-station train rows and seat availability.
- Fare lookup: fares for a train segment.
- Stop lookup: full stop list for a train on a date.

## Install

For Codex:

```bash
git clone git@github.com:HansBug/china-railway-12306.git \
  ~/.codex/skills/china-railway-12306
```

For Claude Code:

```bash
git clone git@github.com:HansBug/china-railway-12306.git \
  ~/.claude/skills/china-railway-12306
```

You can also clone anywhere and point Codex/Claude Code at that directory during a run.

## Direct CLI Usage

The bundled script uses only Python's standard library:

```bash
python3 scripts/rail12306.py stations 北京南
python3 scripts/rail12306.py tickets 北京 杭州 --date 2026-05-20 --limit 3
python3 scripts/rail12306.py tickets --date 2026-05-20 --from 北京南 --to 上海虹桥 --limit 5
python3 scripts/rail12306.py price --date 2026-05-20 --from 北京南 --to 上海虹桥 --train G1
python3 scripts/rail12306.py stops G1 --date 2026-05-20
```

Human-readable output includes `查询时间` captured immediately before the live endpoint call. JSON output wraps results with top-level `query_time`, `source_caveat`, and `data` fields.

Use `--json` for structured output:

```bash
python3 scripts/rail12306.py tickets \
  --date 2026-05-20 \
  --from 北京南 \
  --to 上海虹桥 \
  --train-prefix G \
  --limit 3 \
  --json
```

Windows PowerShell:

```powershell
py scripts\rail12306.py stops G1 --date 2026-05-20 --json
```

## Agent Usage

Once installed under `~/.codex/skills/china-railway-12306` or `~/.claude/skills/china-railway-12306`, the skill is intended to trigger from any local working directory. Users do not need to mention 12306, telecodes, or this repository.

Example prompt:

```text
Tomorrow, what are three Beijing to Hangzhou trains with times, remaining seats, and fares?
```

For one-off interactive Codex testing from this repo:

```bash
codex -C . --dangerously-bypass-approvals-and-sandbox --no-alt-screen
```

Then ask:

```text
Check three Beijing to Hangzhou trains tomorrow, and tell me the time, tickets, and price.
```

For one-off Claude Code testing from this repo:

```bash
claude -p --add-dir . -- \
  "Use the skill in this directory to query G1 stops on 2026-05-20. Do not modify files."
```

## Data Sources

The skill was verified on 2026-05-11 against these public 12306 web endpoints:

- Station dictionary: `https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`
- Ticket query: `https://kyfw.12306.cn/otn/leftTicket/queryG`
- Fare query: `https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice`
- Stop list: `https://kyfw.12306.cn/otn/czxx/queryByTrainNo`
- Train search: `https://search.12306.cn/search/v1/train/search`

See [references/endpoints.md](references/endpoints.md) for request parameters, field notes, and curl examples.

## Validation

```bash
python3 -m py_compile scripts/rail12306.py
python3 scripts/rail12306.py stations 北京南 --json
python3 scripts/rail12306.py stops G1 --date 2026-05-20 --json
```

If you have the Codex skill validator available:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## License And Terms

This repository contains a skill and a small read-only client. The live railway data belongs to China Railway/12306 and is accessed through current public web endpoints. Keep usage low-frequency and user-driven, and respect 12306 service controls and terms.

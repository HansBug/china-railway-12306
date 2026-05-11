---
name: china-railway-12306
description: >-
  Query mainland China Railway 12306 read-only web data for normal travel
  questions and agent lookups, including train times, tickets, remaining seats,
  fares, route options, station codes, and train stop lists. Use for
  natural-language questions such as "tomorrow Beijing to Hangzhou trains and
  prices" even when the user does not mention 12306 or this skill. Not for
  booking, login, captcha handling, scraping, monitoring, or ticket purchasing.
---

# China Railway 12306

## Quick Start

Use the bundled standard-library Python client first. Do not assume the current
working directory is this skill repository; normal users may ask from any local
project directory.

Resolve the script path before running commands:

```bash
RAIL12306_SCRIPT="${RAIL12306_SCRIPT:-$HOME/.codex/skills/china-railway-12306/scripts/rail12306.py}"
[ -f "$RAIL12306_SCRIPT" ] || RAIL12306_SCRIPT="$HOME/.claude/skills/china-railway-12306/scripts/rail12306.py"
```

Then call it with an absolute path:

```bash
python "$RAIL12306_SCRIPT" stations 北京南
python "$RAIL12306_SCRIPT" tickets --date 2026-05-20 --from 北京南 --to 上海虹桥 --limit 5
python "$RAIL12306_SCRIPT" tickets 北京 杭州 --date 2026-05-12 --limit 3
python "$RAIL12306_SCRIPT" price --date 2026-05-20 --from 北京南 --to 上海虹桥 --train G1
python "$RAIL12306_SCRIPT" stops G1 --date 2026-05-20
```

Add `--json` when the caller needs structured data for another tool or LLM step.
For normal human travel questions, keep the final answer in natural language
instead of JSON.
The CLI captures a `查询时间` value immediately before it starts live endpoint
calls. Copy that second-level timestamp into user-facing answers.

## Operating Rules

- Treat these as unofficial, read-only 12306 web endpoints. Do not log in, buy tickets, submit orders, solve captchas, bypass controls, or build high-frequency polling.
- Trigger on ordinary mainland China rail travel questions about times, tickets, remaining seats, fares, routes, or stops, even if the user does not say "12306" or "skill".
- Run the bundled script by absolute path from the installed skill directory; never rely on the current working directory being the skill repo.
- Refresh the 12306 ticket page cookie before ticket and fare queries. The script does this by visiting `/otn/leftTicket/init?linktypeid=dc`.
- Query low-frequency, user-driven lookups only. If an endpoint returns HTML, 302, empty data, or `c_url`, refresh the session once and retry.
- Resolve station names to telecodes before querying tickets. City names often work because 12306 performs city-level searches, but exact station names reduce ambiguity.
- Use dates inside the current 12306 sale window. If the requested date is outside the sale window, report that the endpoint may return no data.
- Always state the second-level query timestamp captured immediately before the live API/script call, because seat availability and fares are time-sensitive.
- Include a short source caveat in user-facing answers: data is from current 12306 public web endpoints and is not a stable official developer API. For Chinese answers, use: `数据来自当前 12306 公开网页端点，非官方开发者 API。`
- End Chinese live-data answers with: `以上为本次实时查询结果。`
- For travel-planning answers, summarize train number, departure/arrival time, remaining seats, fare, and practical purchase advice when useful.

## Tasks

**Station lookup**

Run `stations` for station names, city names, pinyin, short pinyin, or telecodes. Use this before ticket lookups when a station is ambiguous.

**Ticket and train lookup**

Run `tickets` with `--date`, `--from`, and `--to`. Filter with `--train-prefix GDC` or `--limit`. The output includes `train_no`, station numbers, and `seat_types`, which are needed for fare lookups.
For normal station-to-station questions, the positional form `tickets FROM TO --date YYYY-MM-DD --limit 3` is concise and the natural-language output already includes parsed fares. Do not run `--help` unless debugging the CLI.

**Fare lookup**

Use `price --date --from --to --train TRAIN_CODE` only for a specific train fare follow-up or when a ticket row lacks fares. It finds the matching ticket row and calls `/otn/leftTicket/queryTicketPrice`. If you already have raw ticket metadata, call `price` with `--train-no`, `--from-station-no`, `--to-station-no`, and `--seat-types`.

**Stop list lookup**

Run `stops TRAIN_CODE --date YYYY-MM-DD`. The script resolves 12306's internal `train_no` through the train search endpoint, then calls `/otn/czxx/queryByTrainNo`.

## References

Read [references/endpoints.md](references/endpoints.md) when implementing a custom curl/wget/Python client, debugging endpoint changes, or explaining field meanings.

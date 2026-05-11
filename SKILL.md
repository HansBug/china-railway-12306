---
name: china-railway-12306
description: Query mainland China Railway 12306 read-only web data for station codes, train schedules, remaining tickets, fares, and train stop lists. Use when Codex or Claude Code needs personal/agent lookup of Chinese mainland railway information through public 12306 page endpoints, not for booking, login, captcha handling, scraping, monitoring, or ticket purchasing.
---

# China Railway 12306

## Quick Start

Use the bundled standard-library Python client first:

```bash
python scripts/rail12306.py stations 北京南
python scripts/rail12306.py tickets --date 2026-05-20 --from 北京南 --to 上海虹桥 --limit 5
python scripts/rail12306.py price --date 2026-05-20 --from 北京南 --to 上海虹桥 --train G1
python scripts/rail12306.py stops G1 --date 2026-05-20
```

Add `--json` when the caller needs structured data for another tool or LLM step.

## Operating Rules

- Treat these as unofficial, read-only 12306 web endpoints. Do not log in, buy tickets, submit orders, solve captchas, bypass controls, or build high-frequency polling.
- Refresh the 12306 ticket page cookie before ticket and fare queries. The script does this by visiting `/otn/leftTicket/init?linktypeid=dc`.
- Query low-frequency, user-driven lookups only. If an endpoint returns HTML, 302, empty data, or `c_url`, refresh the session once and retry.
- Resolve station names to telecodes before querying tickets. City names often work because 12306 performs city-level searches, but exact station names reduce ambiguity.
- Use dates inside the current 12306 sale window. If the requested date is outside the sale window, report that the endpoint may return no data.
- Include a short source caveat in user-facing answers: data is from current 12306 public web endpoints and is not a stable official developer API.

## Tasks

**Station lookup**

Run `stations` for station names, city names, pinyin, short pinyin, or telecodes. Use this before ticket lookups when a station is ambiguous.

**Ticket and train lookup**

Run `tickets` with `--date`, `--from`, and `--to`. Filter with `--train-prefix GDC` or `--limit`. The output includes `train_no`, station numbers, and `seat_types`, which are needed for fare lookups.

**Fare lookup**

Prefer `price --date --from --to --train TRAIN_CODE`; it finds the matching ticket row and calls `/otn/leftTicket/queryTicketPrice`. If you already have raw ticket metadata, call `price` with `--train-no`, `--from-station-no`, `--to-station-no`, and `--seat-types`.

**Stop list lookup**

Run `stops TRAIN_CODE --date YYYY-MM-DD`. The script resolves 12306's internal `train_no` through the train search endpoint, then calls `/otn/czxx/queryByTrainNo`.

## References

Read [references/endpoints.md](references/endpoints.md) when implementing a custom curl/wget/Python client, debugging endpoint changes, or explaining field meanings.

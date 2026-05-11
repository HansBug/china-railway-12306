# 12306 Read-Only Endpoint Notes

These endpoints were verified on 2026-05-11 with low-frequency unauthenticated requests. They are public web endpoints used by the 12306 site, not a supported developer API.

## Evidence

- The current 12306 ticket query page sets `var CLeftTicketUrl = 'leftTicket/queryG';`.
- The same page loads `/otn/resources/js/framework/station_name.js?station_version=...` for station data.
- The current 12306 merged ticket-query JavaScript calls `ctx+"leftTicket/queryTicketPrice"` with `train_no`, `from_station_no`, `to_station_no`, `seat_types`, and `train_date`.
- The same JavaScript configures stop lookup with `url: ctx+"czxx/queryByTrainNo"`.
- The current 12306 page says the railway has not authorized other websites or apps to provide similar service content.
- `py12306` 0.1.1, a public Python client, uses the same station, ticket, stop, init, and train-search endpoints.

Source links:

- 12306 ticket query page: `https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc`
- Station dictionary: `https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`
- py12306 package: `https://pypi.org/project/py12306/`
- Claude Code skills documentation: `https://docs.claude.com/en/docs/claude-code/skills`

## Session Setup

Ticket and fare endpoints often redirect or return an error page unless the client first initializes a 12306 session cookie:

```bash
curl -sS -A "Mozilla/5.0" -c 12306.cookie \
  "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc" >/dev/null
```

Reuse that cookie and set a 12306 referer:

```bash
curl -sS -A "Mozilla/5.0" -b 12306.cookie \
  -e "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc" \
  "https://kyfw.12306.cn/otn/leftTicket/queryG?leftTicketDTO.train_date=2026-05-20&leftTicketDTO.from_station=VNP&leftTicketDTO.to_station=AOH&purpose_codes=ADULT"
```

## Endpoints

### Station Dictionary

`GET https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`

The response is JavaScript containing `@`-separated station records. Useful fields after splitting a record by `|`:

| Index | Meaning | Example |
|---:|---|---|
| 1 | station name | 北京南 |
| 2 | telecode | VNP |
| 3 | pinyin | beijingnan |
| 4 | pinyin short | bjn |
| 5 | order index | 3 |
| 6 | city code | 0357 |
| 7 | city name | 北京 |

### Ticket Query

`GET https://kyfw.12306.cn/otn/leftTicket/queryG`

Parameters:

| Parameter | Meaning |
|---|---|
| `leftTicketDTO.train_date` | `YYYY-MM-DD` travel date |
| `leftTicketDTO.from_station` | origin telecode, e.g. `VNP` |
| `leftTicketDTO.to_station` | destination telecode, e.g. `AOH` |
| `purpose_codes` | usually `ADULT` |

The JSON response shape is typically:

```json
{
  "status": true,
  "httpstatus": 200,
  "data": {
    "result": ["pipe|separated|ticket|rows"],
    "map": {"VNP": "北京南", "AOH": "上海虹桥"}
  }
}
```

Important pipe-separated row indexes:

| Index | Meaning |
|---:|---|
| 2 | internal `train_no` |
| 3 | public train code, e.g. `G1` |
| 6 | actual origin telecode for this row |
| 7 | actual destination telecode for this row |
| 8 | departure time |
| 9 | arrival time |
| 10 | duration |
| 11 | bookable flag (`Y` means bookable on the web page) |
| 16 | origin station number for this segment |
| 17 | destination station number for this segment |
| 30 | second-class seat availability |
| 31 | first-class seat availability |
| 32 | business/special seat availability |
| 35 | seat type string needed by fare query |
| 39 | compact fare/availability info used by the page |

Seat availability indexes used by the bundled script:

| Seat code | Name | Row index |
|---|---|---:|
| `9` | 商务座 | 32 |
| `P` | 特等座 | 25 |
| `M` | 一等座 | 31 |
| `D` | 优选一等座 | 31 |
| `O` | 二等座 | 30 |
| `6` | 高级软卧 | 21 |
| `4` | 软卧 | 23 |
| `F` | 动卧 | 33 |
| `J` | 二等卧 | 28 |
| `3` | 硬卧 | 28 |
| `2` | 软座 | 24 |
| `1` | 硬座 | 29 |
| `W` | 无座 | 26 |

If the first response has `status: false` and a `c_url`, call `https://kyfw.12306.cn/otn/{c_url}` with the same parameters.

### Fare Query

`GET https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice`

Parameters:

| Parameter | Meaning |
|---|---|
| `train_no` | internal train number from ticket row index 2 |
| `from_station_no` | row index 16 |
| `to_station_no` | row index 17 |
| `seat_types` | row index 35 |
| `train_date` | `YYYY-MM-DD` |

Example:

```bash
curl -sS -A "Mozilla/5.0" -b 12306.cookie \
  -e "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc" \
  "https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no=24000000G10L&from_station_no=01&to_station_no=07&seat_types=9MOO&train_date=2026-05-20"
```

The response `data` object uses seat codes as keys, plus display values such as `M: "¥1060.0"` and compact numeric values such as `9: "23180"`.

### Train Search

`GET https://search.12306.cn/search/v1/train/search`

Parameters:

| Parameter | Meaning |
|---|---|
| `keyword` | train code such as `G1` |
| `date` | `YYYYMMDD` |

Use this to resolve public train codes to internal `train_no` before calling the stop-list endpoint.

### Stop List

`GET https://kyfw.12306.cn/otn/czxx/queryByTrainNo`

Parameters:

| Parameter | Meaning |
|---|---|
| `train_no` | internal train number |
| `from_station_telecode` | segment origin telecode; `BBB` also works for whole-route lookup |
| `to_station_telecode` | segment destination telecode; `BBB` also works for whole-route lookup |
| `depart_date` | `YYYY-MM-DD` |

The response usually stores stop objects under `data.data`, with fields such as `station_name`, `station_no`, `arrive_time`, `start_time`, and `stopover_time`.

## Windows Notes

Use the Python script for cross-platform use:

```powershell
py scripts\rail12306.py tickets --date 2026-05-20 --from 北京南 --to 上海虹桥 --json
```

PowerShell aliases `curl` to `Invoke-WebRequest` on some Windows installations. Use `curl.exe` explicitly if testing raw curl recipes.

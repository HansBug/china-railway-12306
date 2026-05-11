#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only China Railway 12306 web endpoint client.

This script intentionally uses only Python's standard library so it runs on
Windows, macOS, and Linux without installing dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API = {
    "ticket_init": "https://kyfw.12306.cn/otn/leftTicket/init",
    "stations": "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js",
    "ticket_query": "https://kyfw.12306.cn/otn/leftTicket/queryG",
    "ticket_price": "https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice",
    "train_search": "https://search.12306.cn/search/v1/train/search",
    "train_stops": "https://kyfw.12306.cn/otn/czxx/queryByTrainNo",
}

DEFAULT_REFERER = "https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/javascript,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

SEAT_NAMES = {
    "9": "商务座",
    "P": "特等座",
    "M": "一等座",
    "D": "优选一等座",
    "O": "二等座",
    "S": "二等包座",
    "6": "高级软卧",
    "A": "高级动卧",
    "4": "软卧",
    "F": "动卧",
    "I": "一等卧",
    "J": "二等卧",
    "3": "硬卧",
    "2": "软座",
    "1": "硬座",
    "W": "无座",
    "H": "其他",
}

SEAT_FIELD = {
    "9": 32,
    "P": 25,
    "M": 31,
    "D": 31,
    "O": 30,
    "S": 30,
    "6": 21,
    "A": 21,
    "4": 23,
    "F": 33,
    "I": 23,
    "J": 28,
    "3": 28,
    "2": 24,
    "1": 29,
    "W": 26,
    "H": 22,
}


@dataclass(frozen=True)
class Station:
    name: str
    code: str
    pinyin: str
    short: str
    city: str
    city_code: str
    index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "code": self.code,
            "pinyin": self.pinyin,
            "short": self.short,
            "city": self.city,
            "city_code": self.city_code,
            "index": self.index,
        }


class Rail12306Client:
    def __init__(self) -> None:
        jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self._stations: list[Station] | None = None

    def get_text(
        self,
        url: str,
        params: dict[str, str] | None = None,
        *,
        referer: str | None = DEFAULT_REFERER,
        timeout: int = 30,
    ) -> str:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        headers = dict(HEADERS)
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers)
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
                if charset.lower().replace("_", "-") == "utf-8":
                    charset = "utf-8-sig"
                return raw.decode(charset, errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from {url}: {body[:200]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    def get_json(
        self,
        url: str,
        params: dict[str, str] | None = None,
        *,
        referer: str | None = DEFAULT_REFERER,
        timeout: int = 30,
    ) -> dict[str, Any]:
        text = self.get_text(url, params, referer=referer, timeout=timeout)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            prefix = text[:160].replace("\n", " ")
            raise RuntimeError(f"Expected JSON from {url}, got: {prefix}") from exc

    def init_ticket_session(self) -> None:
        self.get_text(API["ticket_init"], {"linktypeid": "dc"}, referer=None)

    def load_stations(self) -> list[Station]:
        if self._stations is not None:
            return self._stations

        text = self.get_text(API["stations"], referer="https://www.12306.cn/index/")
        stations: list[Station] = []
        for item in text.split("@")[1:]:
            parts = item.strip().strip("';").split("|")
            if len(parts) < 8:
                continue
            try:
                order = int(parts[5])
            except ValueError:
                order = 0
            stations.append(
                Station(
                    name=parts[1],
                    code=parts[2],
                    pinyin=parts[3],
                    short=parts[4],
                    city=parts[7],
                    city_code=parts[6],
                    index=order,
                )
            )
        self._stations = stations
        return stations

    def station_indexes(self) -> tuple[dict[str, Station], dict[str, Station], dict[str, list[Station]]]:
        by_code: dict[str, Station] = {}
        by_name: dict[str, Station] = {}
        by_city: dict[str, list[Station]] = {}
        for station in self.load_stations():
            by_code[station.code.upper()] = station
            by_name[station.name] = station
            by_city.setdefault(station.city, []).append(station)
        for stations in by_city.values():
            stations.sort(key=lambda s: s.index)
        return by_code, by_name, by_city

    def resolve_station(self, query: str) -> Station:
        query = query.strip()
        if not query:
            raise ValueError("station query is empty")
        by_code, by_name, by_city = self.station_indexes()

        upper = query.upper()
        if upper in by_code:
            return by_code[upper]
        if query in by_name:
            return by_name[query]
        if query in by_city:
            return by_city[query][0]

        matches = [
            s
            for s in self.load_stations()
            if query in s.name
            or query in s.city
            or query.lower() in s.pinyin.lower()
            or query.lower() == s.short.lower()
        ]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValueError(f"no station matched {query!r}")
        preview = ", ".join(f"{s.name}({s.code})" for s in matches[:12])
        raise ValueError(f"ambiguous station {query!r}; candidates: {preview}")

    def search_stations(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return [s.to_dict() for s in self.load_stations()[:limit]]
        q_lower = query.lower()
        matches = [
            s
            for s in self.load_stations()
            if query in s.name
            or query in s.city
            or q_lower in s.pinyin.lower()
            or q_lower in s.short.lower()
            or query.upper() == s.code.upper()
        ]
        return [s.to_dict() for s in matches[:limit]]

    def query_tickets(self, date: str, from_query: str, to_query: str) -> list[dict[str, Any]]:
        validate_date(date)
        src = self.resolve_station(from_query)
        dst = self.resolve_station(to_query)
        params = {
            "leftTicketDTO.train_date": date,
            "leftTicketDTO.from_station": src.code,
            "leftTicketDTO.to_station": dst.code,
            "purpose_codes": "ADULT",
        }

        self.init_ticket_session()
        data = self.get_json(API["ticket_query"], params)
        if not data.get("status") and data.get("c_url"):
            data = self.get_json(f"https://kyfw.12306.cn/otn/{data['c_url']}", params)

        result_data = data.get("data") or {}
        rows = result_data.get("result") or []
        station_map = result_data.get("map") or {}
        parsed = [parse_ticket_row(row, station_map) for row in rows]
        return [ticket for ticket in parsed if ticket is not None]

    def query_price_by_meta(
        self,
        date: str,
        train_no: str,
        from_station_no: str,
        to_station_no: str,
        seat_types: str,
    ) -> dict[str, Any]:
        validate_date(date)
        self.init_ticket_session()
        params = {
            "train_no": train_no,
            "from_station_no": from_station_no,
            "to_station_no": to_station_no,
            "seat_types": seat_types,
            "train_date": date,
        }
        data = self.get_json(API["ticket_price"], params)
        if not data.get("status"):
            raise RuntimeError(f"price query failed: {data}")
        return data.get("data") or {}

    def query_price_by_train(self, date: str, from_query: str, to_query: str, train: str) -> dict[str, Any]:
        tickets = self.query_tickets(date, from_query, to_query)
        train_upper = train.strip().upper()
        for ticket in tickets:
            if ticket["train"].upper() == train_upper:
                meta = ticket["meta"]
                prices = self.query_price_by_meta(
                    date,
                    meta["train_no"],
                    meta["from_station_no"],
                    meta["to_station_no"],
                    meta["seat_types"],
                )
                return {"ticket": ticket, "prices": prices}
        raise ValueError(f"train {train!r} not found for {from_query}->{to_query} on {date}")

    def find_train_no(self, train: str, date: str) -> str:
        validate_date(date)
        params = {"keyword": train.strip().upper(), "date": date.replace("-", "")}
        data = self.get_json(API["train_search"], params, referer="https://www.12306.cn/index/")
        rows = data.get("data") or []
        for row in rows:
            if row.get("station_train_code", "").upper() == train.strip().upper():
                return str(row.get("train_no") or "")
        if rows and rows[0].get("train_no"):
            return str(rows[0]["train_no"])
        raise ValueError(f"could not resolve internal train_no for {train!r} on {date}")

    def query_stops(self, train: str, date: str, train_no: str | None = None) -> dict[str, Any]:
        validate_date(date)
        train_no = train_no or self.find_train_no(train, date)
        params = {
            "train_no": train_no,
            "from_station_telecode": "BBB",
            "to_station_telecode": "BBB",
            "depart_date": date,
        }
        data = self.get_json(API["train_stops"], params)
        rows = ((data.get("data") or {}).get("data")) or []
        return {
            "train": train.strip().upper(),
            "train_no": train_no,
            "date": date,
            "stops": [
                {
                    "station_no": row.get("station_no"),
                    "station": row.get("station_name"),
                    "arrive": row.get("arrive_time"),
                    "depart": row.get("start_time"),
                    "stopover": row.get("stopover_time"),
                    "start_station": row.get("start_station_name"),
                    "end_station": row.get("end_station_name"),
                    "train_class": row.get("train_class_name"),
                }
                for row in rows
            ],
        }


def validate_date(value: str) -> None:
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"date must be YYYY-MM-DD, got {value!r}") from exc


def parse_minutes(duration: str) -> int | None:
    if not duration or ":" not in duration:
        return None
    try:
        hours, minutes = duration.split(":", 1)
        return int(hours) * 60 + int(minutes)
    except ValueError:
        return None


def normalize_availability(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value in {"", "--", "*"}:
        return None
    return value


def parse_price_info(value: str) -> dict[str, float]:
    """Parse compact 12306 fare info from a ticket row.

    The page currently uses 11-char chunks for many G/D trains and 10-char
    chunks for many conventional trains. Use the most plausible parse.
    """
    known = set(SEAT_NAMES)
    candidates: list[list[tuple[str, float]]] = []

    for step, count_width in ((11, 5), (10, 4)):
        matches: list[tuple[str, float]] = []
        for i in range(0, len(value), step):
            chunk = value[i : i + step]
            if len(chunk) != step:
                continue
            seat, price, count = chunk[0], chunk[1:6], chunk[6 : 6 + count_width]
            if seat in known and price.isdigit() and count.isdigit():
                if int(count) >= 3000:
                    seat = "W"
                matches.append((seat, int(price) / 10))
        candidates.append(matches)

    regex_matches: list[tuple[str, float]] = []
    for match in re.finditer(r"([0-9A-Z])(\d{5})(\d{4,5})", value):
        seat, price, count = match.groups()
        if seat in known:
            if int(count) >= 3000:
                seat = "W"
            regex_matches.append((seat, int(price) / 10))
    candidates.append(regex_matches)

    best = max(candidates, key=len, default=[])
    prices: dict[str, float] = {}
    for seat, price in best:
        prices.setdefault(seat, price)
    return prices


def ordered_seat_codes(seat_types: str, fields: list[str], prices: dict[str, float]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in seat_types:
        if code in SEAT_NAMES and code not in seen:
            seen.add(code)
            ordered.append(code)
    for code in prices:
        if code in SEAT_NAMES and code not in seen:
            seen.add(code)
            ordered.append(code)
    if ordered:
        return ordered

    for code in ("9", "P", "M", "O", "6", "4", "F", "3", "2", "1", "W"):
        index = SEAT_FIELD[code]
        if code in seen:
            continue
        available = normalize_availability(fields[index] if len(fields) > index else None)
        if available is not None or code in prices:
            seen.add(code)
            ordered.append(code)
    return ordered


def parse_ticket_row(row: str, station_map: dict[str, str]) -> dict[str, Any] | None:
    fields = row.split("|")
    if len(fields) < 36:
        return None

    def field(index: int) -> str:
        return fields[index] if len(fields) > index else ""

    price_info = field(39)
    prices = parse_price_info(price_info) if price_info else {}
    seat_types = field(35)
    seats: list[dict[str, Any]] = []
    for code in ordered_seat_codes(seat_types, fields, prices):
        available = normalize_availability(fields[SEAT_FIELD[code]] if len(fields) > SEAT_FIELD[code] else None)
        seat: dict[str, Any] = {
            "code": code,
            "name": SEAT_NAMES.get(code, code),
            "available": available,
        }
        if code in prices:
            seat["price"] = prices[code]
        seats.append(seat)

    duration = field(10)
    origin_code = field(6)
    dest_code = field(7)
    return {
        "train": field(3),
        "origin": {"name": station_map.get(origin_code, origin_code), "code": origin_code},
        "dest": {"name": station_map.get(dest_code, dest_code), "code": dest_code},
        "depart": field(8),
        "arrive": field(9),
        "duration": duration,
        "duration_min": parse_minutes(duration),
        "bookable": field(11) == "Y",
        "seats": seats,
        "meta": {
            "train_no": field(2),
            "from_station_no": field(16),
            "to_station_no": field(17),
            "seat_types": seat_types,
        },
    }


def dump_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_stations(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No stations found.")
        return
    for row in rows:
        print(f"{row['name']:<10} {row['code']:<4} {row['city']:<8} {row['pinyin']:<24} {row['short']}")


def format_seats(seats: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for seat in seats[:6]:
        availability = seat.get("available") or "-"
        if "price" in seat:
            parts.append(f"{seat['name']}:{availability}/¥{seat['price']}")
        else:
            parts.append(f"{seat['name']}:{availability}")
    return " ".join(parts)


def print_tickets(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No tickets found.")
        return
    for row in rows:
        print(
            f"{row['train']:<8} {row['origin']['name']}({row['origin']['code']}) -> "
            f"{row['dest']['name']}({row['dest']['code']})  "
            f"{row['depart']}-{row['arrive']} {row['duration']:<6}  {format_seats(row['seats'])}"
        )


def print_price(data: dict[str, Any]) -> None:
    prices = data.get("prices", data)
    ticket = data.get("ticket")
    if ticket:
        print(
            f"{ticket['train']} {ticket['origin']['name']} -> {ticket['dest']['name']} "
            f"{ticket['depart']}-{ticket['arrive']}"
        )
    for key in sorted(prices):
        value = prices[key]
        if isinstance(value, str) and value.startswith("¥"):
            print(f"{SEAT_NAMES.get(key, key):<8} {value}")


def print_stops(data: dict[str, Any]) -> None:
    stops = data.get("stops") or []
    if not stops:
        print("No stops found.")
        return
    print(f"{data['train']} {data['date']} train_no={data['train_no']}")
    for stop in stops:
        print(
            f"{str(stop.get('station_no') or ''):>2}  {stop.get('station'):<10} "
            f"arr {stop.get('arrive') or '----':<5} dep {stop.get('depart') or '----':<5} "
            f"stop {stop.get('stopover') or '----'}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query read-only China Railway 12306 web data.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_stations = sub.add_parser("stations", help="Search station dictionary.")
    p_stations.add_argument("query", nargs="?", default="", help="Station/city/pinyin/telecode query.")
    p_stations.add_argument("--limit", type=int, default=20)
    p_stations.add_argument("--json", action="store_true")

    p_tickets = sub.add_parser("tickets", help="Query ticket rows between stations.")
    p_tickets.add_argument("--date", required=True)
    p_tickets.add_argument("--from", dest="from_station", required=True)
    p_tickets.add_argument("--to", dest="to_station", required=True)
    p_tickets.add_argument("--train-prefix", default="", help="Filter by train prefix, e.g. G, GD, DCK.")
    p_tickets.add_argument("--sort", choices=["depart", "arrive", "duration"], default="depart")
    p_tickets.add_argument("--limit", type=int, default=20)
    p_tickets.add_argument("--json", action="store_true")

    p_price = sub.add_parser("price", help="Query fares via queryTicketPrice.")
    p_price.add_argument("--date", required=True)
    p_price.add_argument("--from", dest="from_station")
    p_price.add_argument("--to", dest="to_station")
    p_price.add_argument("--train")
    p_price.add_argument("--train-no")
    p_price.add_argument("--from-station-no")
    p_price.add_argument("--to-station-no")
    p_price.add_argument("--seat-types")
    p_price.add_argument("--json", action="store_true")

    p_stops = sub.add_parser("stops", help="Query stop list for a train.")
    p_stops.add_argument("train")
    p_stops.add_argument("--date", required=True)
    p_stops.add_argument("--train-no", help="Internal train_no if already known.")
    p_stops.add_argument("--json", action="store_true")

    return parser


def run(args: argparse.Namespace) -> int:
    client = Rail12306Client()

    if args.command == "stations":
        rows = client.search_stations(args.query, limit=max(args.limit, 1))
        dump_json(rows) if args.json else print_stations(rows)
        return 0

    if args.command == "tickets":
        rows = client.query_tickets(args.date, args.from_station, args.to_station)
        if args.train_prefix:
            prefixes = tuple(args.train_prefix.upper())
            rows = [row for row in rows if row["train"].upper().startswith(prefixes)]
        if args.sort == "duration":
            rows.sort(key=lambda row: row.get("duration_min") if row.get("duration_min") is not None else 99999)
        else:
            rows.sort(key=lambda row: row.get(args.sort) or "")
        if args.limit:
            rows = rows[: max(args.limit, 0)]
        dump_json(rows) if args.json else print_tickets(rows)
        return 0

    if args.command == "price":
        if args.train and args.from_station and args.to_station:
            result = client.query_price_by_train(args.date, args.from_station, args.to_station, args.train)
        elif args.train_no and args.from_station_no and args.to_station_no and args.seat_types:
            result = client.query_price_by_meta(
                args.date, args.train_no, args.from_station_no, args.to_station_no, args.seat_types
            )
        else:
            raise ValueError(
                "price requires either --train with --from/--to, or --train-no with "
                "--from-station-no/--to-station-no/--seat-types"
            )
        dump_json(result) if args.json else print_price(result)
        return 0

    if args.command == "stops":
        result = client.query_stops(args.train, args.date, train_no=args.train_no)
        dump_json(result) if args.json else print_stops(result)
        return 0

    raise ValueError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001 - CLI should show concise failures.
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

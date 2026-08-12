#!/usr/bin/env python3
"""Build the resilient live-data snapshot consumed by Password Panic VRChat."""

from __future__ import annotations

import html
import json
import random
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "live-data.txt"
UA = "PasswordPanicLiveData/1.0"
STOCKS = ("AAPL", "NVDA", "GOOGL", "META", "AMZN")
CITIES = (
    ("NEW_YORK", "NEW YORK", 40.7128, -74.0060, "America/New_York"),
    ("LONDON", "LONDON", 51.5072, -0.1276, "Europe/London"),
    ("TOKYO", "TOKYO", 35.6762, 139.6503, "Asia/Tokyo"),
    ("SYDNEY", "SYDNEY", -33.8688, 151.2093, "Australia/Sydney"),
    ("SAO_PAULO", "SAO PAULO", -23.5505, -46.6333, "America/Sao_Paulo"),
)


def fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.load(response)


def clean(value: object, limit: int = 180) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text).replace("|", "/").replace("=", "-")
    return re.sub(r"\s+", " ", text).strip()[:limit]


def existing() -> dict[str, str]:
    values: dict[str, str] = {}
    if OUTPUT.exists():
        for line in OUTPUT.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def stocks(values: dict[str, str]) -> None:
    changes: dict[str, float] = {}
    dates: list[str] = []
    for symbol in STOCKS:
        result = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d")["chart"]["result"][0]
        points = [(int(t), float(c)) for t, c in zip(result.get("timestamp") or [], result["indicators"]["quote"][0].get("close") or []) if c is not None]
        if len(points) < 2:
            raise ValueError(f"not enough closes for {symbol}")
        latest, prior = points[-1][1], points[-2][1]
        change = (latest - prior) / prior * 100
        values[f"STOCK_{symbol}_PRICE"] = f"{latest:.2f}"
        values[f"STOCK_{symbol}_CHANGE"] = f"{change:+.2f}"
        changes[symbol] = change
        dates.append(datetime.fromtimestamp(points[-1][0], timezone.utc).strftime("%Y-%m-%d"))
    values["MARKET_DATE"] = max(dates)
    values["STOCK_LEADER"] = max(changes, key=changes.get)


def weather_name(code: int) -> str:
    if code == 0: return "CLEAR"
    if code in (1, 2): return "PARTLY CLOUDY"
    if code == 3: return "CLOUDY"
    if code in (45, 48): return "FOG"
    if 51 <= code <= 57: return "DRIZZLE"
    if 61 <= code <= 67 or 80 <= code <= 82: return "RAIN"
    if 71 <= code <= 77 or 85 <= code <= 86: return "SNOW"
    if 95 <= code <= 99: return "STORM"
    return "MIXED"


def weather(values: dict[str, str]) -> None:
    temperatures: dict[str, int] = {}
    for key, label, lat, lon, zone in CITIES:
        query = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code", "temperature_unit": "fahrenheit", "timezone": zone})
        current = fetch(f"https://api.open-meteo.com/v1/forecast?{query}")["current"]
        temperature = int(round(float(current["temperature_2m"])))
        values[f"WEATHER_{key}_TEMP"] = str(temperature)
        values[f"WEATHER_{key}_CONDITION"] = weather_name(int(current["weather_code"]))
        temperatures[label] = temperature
    values["WEATHER_WARMEST"] = max(temperatures, key=temperatures.get)


def fx(values: dict[str, str]) -> None:
    payload = fetch("https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CAD,AUD")
    values["FX_DATE"] = clean(payload.get("date"), 20)
    for symbol in ("EUR", "GBP", "JPY", "CAD", "AUD"):
        values[f"FX_{symbol}"] = f"{float(payload['rates'][symbol]):.4f}"


def quake(values: dict[str, str]) -> None:
    features = [f for f in fetch("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson").get("features", []) if f.get("properties", {}).get("mag") is not None]
    strongest = max(features, key=lambda item: float(item["properties"]["mag"]))
    values["QUAKE_MAG"] = f"{float(strongest['properties']['mag']):.1f}"
    values["QUAKE_PLACE"] = clean(strongest["properties"].get("place", "UNKNOWN REGION"), 72).upper()


def history(values: dict[str, str], month: int, day: int) -> None:
    payload = fetch(f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{month:02d}/{day:02d}")
    events = [(item.get("year"), clean(item.get("text"), 150)) for item in payload.get("events", [])]
    events = [(year, text) for year, text in events if isinstance(year, int) and 1000 <= year <= 2099 and len(text) >= 45]
    year, text = events[(month * 31 + day) % len(events)]
    values["HISTORY_YEAR"], values["HISTORY_TEXT"] = str(year), text


def trivia(values: dict[str, str], seed: int) -> None:
    result = fetch("https://opentdb.com/api.php?amount=1&type=multiple")["results"][0]
    correct = clean(result["correct_answer"], 52).upper()
    choices = [correct] + [clean(item, 52).upper() for item in result["incorrect_answers"]]
    random.Random(seed).shuffle(choices)
    values["TRIVIA_QUESTION"] = clean(result["question"], 150).upper()
    for index, choice in enumerate(choices): values[f"TRIVIA_{chr(65 + index)}"] = choice
    values["TRIVIA_ANSWER"] = correct


def main() -> None:
    now = datetime.now(timezone.utc)
    values = existing()
    failures: list[str] = []
    for name, task in (("stocks", lambda: stocks(values)), ("weather", lambda: weather(values)), ("fx", lambda: fx(values)), ("quake", lambda: quake(values)), ("history", lambda: history(values, now.month, now.day)), ("trivia", lambda: trivia(values, int(now.strftime("%Y%m%d"))))):
        try: task()
        except Exception as exc: failures.append(f"{name}: {exc}")

    values["VERSION"] = "1"
    values["WORDLE"] = (ROOT / "current.txt").read_text(encoding="ascii").strip()
    seed = int(now.strftime("%Y%m%d"))
    stock = STOCKS[seed % 5]
    city = CITIES[(seed // 3) % 5]
    currency = ("EUR", "GBP", "JPY", "CAD", "AUD")[(seed // 7) % 5]
    values["STOCK_TARGET"], values["STOCK_TARGET_PRICE"] = stock, values.get(f"STOCK_{stock}_PRICE", "200.00")
    values["WEATHER_TARGET_CITY"], values["WEATHER_TARGET_TEMP"] = city[1], values.get(f"WEATHER_{city[0]}_TEMP", "70")
    values["FX_TARGET"], values["FX_TARGET_RATE"] = currency, values.get(f"FX_{currency}", "1.0000")
    values["UPDATED_UTC"] = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    values["SOURCE_STATUS"] = "PARTIAL" if failures else "LIVE"

    required = ("STOCK_TARGET_PRICE", "STOCK_LEADER", "WEATHER_TARGET_TEMP", "WEATHER_WARMEST", "FX_TARGET_RATE", "QUAKE_MAG", "HISTORY_YEAR", "TRIVIA_ANSWER")
    missing = [key for key in required if not values.get(key)]
    if missing: raise RuntimeError("no live or cached value for " + ", ".join(missing))

    order = ["VERSION", "UPDATED_UTC", "SOURCE_STATUS", "WORDLE", "MARKET_DATE"]
    order += [f"STOCK_{symbol}_{field}" for symbol in STOCKS for field in ("PRICE", "CHANGE")]
    order += ["STOCK_TARGET", "STOCK_TARGET_PRICE", "STOCK_LEADER"]
    order += [f"WEATHER_{key}_{field}" for key, _, _, _, _ in CITIES for field in ("TEMP", "CONDITION")]
    order += ["WEATHER_TARGET_CITY", "WEATHER_TARGET_TEMP", "WEATHER_WARMEST", "FX_DATE"]
    order += [f"FX_{symbol}" for symbol in ("EUR", "GBP", "JPY", "CAD", "AUD")]
    order += ["FX_TARGET", "FX_TARGET_RATE", "QUAKE_MAG", "QUAKE_PLACE", "HISTORY_YEAR", "HISTORY_TEXT", "TRIVIA_QUESTION", "TRIVIA_A", "TRIVIA_B", "TRIVIA_C", "TRIVIA_D", "TRIVIA_ANSWER"]
    OUTPUT.write_text("\n".join(f"{key}={values.get(key, '')}" for key in order) + "\n", encoding="utf-8")
    print("complete snapshot" if not failures else "cached sections: " + " | ".join(failures))


if __name__ == "__main__": main()

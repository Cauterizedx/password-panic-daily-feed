#!/usr/bin/env python3
"""Publish a tiny, validated daily Wordle feed for the VRChat world."""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def eastern_today() -> date:
    """Return the New York calendar date without requiring a timezone package."""
    now_utc = datetime.now(timezone.utc)
    year = now_utc.year

    march_first = date(year, 3, 1)
    second_sunday_march = 8 + ((6 - march_first.weekday()) % 7)
    dst_start = datetime.combine(
        date(year, 3, second_sunday_march), time(7), tzinfo=timezone.utc
    )

    november_first = date(year, 11, 1)
    first_sunday_november = 1 + ((6 - november_first.weekday()) % 7)
    dst_end = datetime.combine(
        date(year, 11, first_sunday_november), time(6), tzinfo=timezone.utc
    )

    offset = -4 if dst_start <= now_utc < dst_end else -5
    return (now_utc + timedelta(hours=offset)).date()


TODAY = eastern_today()
SOURCE_URL = f"https://www.nytimes.com/svc/wordle/v2/{TODAY.isoformat()}.json"


def fetch() -> dict:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "PasswordPanicDailyFeed/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"Wordle endpoint returned HTTP {response.status}")
        return json.load(response)


def validate(payload: dict) -> tuple[str, int | None]:
    answer = str(payload.get("solution", "")).strip().upper()
    if re.fullmatch(r"[A-Z]{5}", answer) is None:
        raise ValueError("The downloaded solution is not exactly five ASCII letters")

    returned_date = str(payload.get("print_date", ""))
    if returned_date and returned_date != TODAY.isoformat():
        raise ValueError(
            f"The endpoint returned {returned_date}, expected {TODAY.isoformat()}"
        )

    puzzle = payload.get("days_since_launch")
    if puzzle is not None and not isinstance(puzzle, int):
        raise ValueError("The downloaded puzzle identifier is malformed")
    return answer, puzzle


def main() -> None:
    payload = fetch()
    answer, puzzle = validate(payload)

    current_path = ROOT / "current.txt"
    metadata_path = ROOT / "meta.json"
    existing_answer = ""
    existing_metadata: dict = {}
    if current_path.exists():
        existing_answer = current_path.read_text(encoding="ascii").strip()
    if metadata_path.exists():
        try:
            existing_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing_metadata = {}

    unchanged = (
        existing_answer == answer
        and existing_metadata.get("date") == TODAY.isoformat()
        and existing_metadata.get("puzzle") == puzzle
        and existing_metadata.get("source") == "New York Times Wordle endpoint"
    )
    if unchanged:
        print(f"Feed is already current for {TODAY.isoformat()} (puzzle {puzzle}).")
        return

    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )

    current_path.write_text(answer + "\n", encoding="ascii")
    metadata = {
        "date": TODAY.isoformat(),
        "puzzle": puzzle,
        "updated_at_utc": updated_at,
        "source": "New York Times Wordle endpoint",
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Validated Wordle feed for {TODAY.isoformat()} (puzzle {puzzle}).")


if __name__ == "__main__":
    main()

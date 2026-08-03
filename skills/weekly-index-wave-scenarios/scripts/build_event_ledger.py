#!/usr/bin/env python3
"""Validate an event ledger and calculate bounded, auditable event scores."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED = {
    "event_id", "published_at", "effective_from", "effective_to", "event_type", "title", "status",
    "source_level", "source_url", "market_scope", "channel", "direction", "confidence",
}
STATUS_WEIGHT = {"rumour": 0.0, "filing": 0.25, "accepted": 0.25, "registered": 0.5, "priced": 0.8, "listed": 1.0, "post_listing": 1.0, "confirmed": 1.0}
SOURCE_WEIGHT = {"official": 1.0, "reputable_media": 0.5, "unverified": 0.0}
EVENT_TYPES = {"policy", "liquidity", "macro", "ipo", "external_risk", "earnings", "market_structure"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    ledger = pd.read_csv(args.input)
    missing = REQUIRED.difference(ledger.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")
    if ledger.event_id.duplicated().any():
        raise SystemExit("event_id must be unique")
    if not set(ledger.event_type.dropna()).issubset(EVENT_TYPES):
        raise SystemExit(f"event_type must be one of: {sorted(EVENT_TYPES)}")
    if not set(ledger.status.dropna()).issubset(STATUS_WEIGHT):
        raise SystemExit(f"status must be one of: {sorted(STATUS_WEIGHT)}")
    if not set(ledger.source_level.dropna()).issubset(SOURCE_WEIGHT):
        raise SystemExit(f"source_level must be one of: {sorted(SOURCE_WEIGHT)}")

    ledger["published_at"] = pd.to_datetime(ledger["published_at"], errors="raise")
    for column in ("effective_from", "effective_to"):
        ledger[column] = pd.to_datetime(ledger[column], errors="raise").dt.date.astype(str)
    if (ledger.effective_from > ledger.effective_to).any():
        raise SystemExit("effective_from must not be later than effective_to")
    ledger["direction"] = pd.to_numeric(ledger.direction, errors="raise")
    ledger["confidence"] = pd.to_numeric(ledger.confidence, errors="raise")
    if not ledger.direction.isin([-1, 0, 1]).all():
        raise SystemExit("direction must be -1, 0, or 1")
    if not ledger.confidence.between(0, 1).all():
        raise SystemExit("confidence must be between 0 and 1")

    ledger["status_weight"] = ledger.status.map(STATUS_WEIGHT)
    ledger["source_weight"] = ledger.source_level.map(SOURCE_WEIGHT)
    ledger["event_score"] = (ledger.direction * ledger.confidence * ledger.status_weight * ledger.source_weight).round(3)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ledger.sort_values(["published_at", "event_id"]).to_csv(output, index=False)
    print(f"Validated {len(ledger)} events; wrote {output}")


if __name__ == "__main__":
    main()

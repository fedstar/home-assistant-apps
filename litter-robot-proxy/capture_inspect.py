#!/usr/bin/env python3
"""Inspect LR3 JSONL captures or LR3_CAPTURE lines copied from app logs."""

import argparse
import csv
import datetime
import json
import sys


def parse_timestamp(value):
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        datetime.timezone.utc
    )


def read_records(paths):
    for path in paths:
        with open(path, encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                marker = "LR3_CAPTURE "
                if marker in line:
                    line = line.split(marker, 1)[1]
                elif not line.lstrip().startswith("{"):
                    continue
                try:
                    record = json.loads(line)
                    raw = bytes.fromhex(record["raw_hex"])
                    if len(raw) != record["length"]:
                        raise ValueError("raw payload length mismatch")
                    record["timestamp"] = parse_timestamp(record["timestamp_utc"])
                except (KeyError, ValueError, json.JSONDecodeError) as exc:
                    print("%s:%d: skipped invalid capture: %s" % (path, line_number, exc), file=sys.stderr)
                    continue
                yield record


def read_annotations(path):
    with open(path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            yield parse_timestamp(row["timestamp"]), row["label"]


def describe(record):
    fields = record["fields"]
    return "%s %-16s %-8s %-16s %-8s %-8s %s" % (
        record["timestamp_utc"],
        record["direction"],
        fields.get("kind", "unknown"),
        fields.get("device_id", ""),
        fields.get("command", ""),
        fields.get("sequence", ""),
        fields.get("checksum", ""),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", help="JSONL files or copied app logs")
    parser.add_argument("--annotations", help="CSV with timestamp,label columns (ISO 8601 with timezone)")
    parser.add_argument("--window-seconds", type=float, default=10.0)
    args = parser.parse_args()

    records = sorted(read_records(args.captures), key=lambda record: record["timestamp"])
    print("%d valid packets" % len(records))
    for record in records:
        print(describe(record))

    if args.annotations:
        print("\nCommands within %.1f seconds after each annotation:" % args.window_seconds)
        for timestamp, label in read_annotations(args.annotations):
            matches = [
                record for record in records
                if record["direction"] == "server_to_robot"
                and record["fields"].get("kind") == "command"
                and 0 <= (record["timestamp"] - timestamp).total_seconds() <= args.window_seconds
            ]
            print("%s  %s" % (timestamp.isoformat(), label))
            for record in matches:
                print("  " + describe(record))
            if not matches:
                print("  (no command packet in window)")


if __name__ == "__main__":
    main()

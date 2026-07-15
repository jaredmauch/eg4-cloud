#!/usr/bin/env python3
"""Fetch inverter configuration registers from EG4 Monitor Center."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

from eg4_config_fetch import fetch_inverter_config
from eg4_config_lib import (
    build_diff_report,
    compare_configs,
    format_comparison_report,
    save_config_snapshot,
)
from xls_to_influxdb import authenticate_eg4, get_inverter_list, read_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch EG4 inverter configuration registers for comparison."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for JSON snapshots (default: configs/<timestamp>)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Print differences across fetched inverters after saving",
    )
    parser.add_argument(
        "--flags-only",
        action="store_true",
        help="With --compare: only show FUNC_* and BIT_* differences",
    )
    parser.add_argument(
        "--serial",
        action="append",
        dest="serials",
        help="Fetch only this inverter serial (repeatable; default: config.yaml)",
    )
    args = parser.parse_args()

    config = read_config()
    session = authenticate_eg4(
        config["eg4_monitor"]["username"],
        config["eg4_monitor"]["password"],
    )
    if not session:
        print("Authentication failed", file=sys.stderr)
        sys.exit(1)

    if args.serials:
        inverters = [{"id": serial} for serial in args.serials]
    else:
        inverters = get_inverter_list(session, config)

    if not inverters:
        print("No inverters to fetch", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or Path("configs") / timestamp

    fetched: List[Dict[str, Any]] = []
    for inverter in inverters:
        inverter_sn = inverter["id"]
        print(f"Fetching config for inverter {inverter_sn}...")
        try:
            config_data = fetch_inverter_config(
                session,
                inverter_sn,
                plant_id=inverter.get("plant_id"),
                plant_name=inverter.get("plant_name"),
                model=inverter.get("model"),
            )
        except (requests.RequestException, RuntimeError) as exc:
            print(f"  Failed: {exc}", file=sys.stderr)
            continue

        path = save_config_snapshot(config_data, output_dir)
        print(f"  Saved {config_data['field_count']} settings to {path}")
        fetched.append(config_data)

    if not fetched:
        print("No configs were fetched successfully", file=sys.stderr)
        sys.exit(1)

    summary_path = output_dir / "summary.json"
    differences = compare_configs(fetched, flags_only=args.flags_only)
    summary: Dict[str, Any] = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "inverters": [
            {
                "inverter_sn": item["inverter_sn"],
                "plant_name": item.get("plant_name"),
                "plant_id": item.get("plant_id"),
                "model": item.get("model"),
            }
            for item in fetched
        ],
        "field_count": fetched[0]["field_count"] if fetched else 0,
    }
    if len(fetched) > 1:
        summary["diff_summary"] = build_diff_report(
            fetched, differences, flags_only=args.flags_only
        )["summary"]

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote summary to {summary_path}")

    if args.compare or len(fetched) > 1:
        print()
        print(format_comparison_report(fetched, differences, flags_only=args.flags_only))
        if len(fetched) > 1:
            diff_path = output_dir / "diff-report.json"
            with diff_path.open("w", encoding="utf-8") as handle:
                json.dump(
                    build_diff_report(fetched, differences, flags_only=args.flags_only),
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
            print(f"Wrote diff report to {diff_path}")


if __name__ == "__main__":
    main()

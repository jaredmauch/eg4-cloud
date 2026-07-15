#!/usr/bin/env python3
"""Compare EG4 inverter configs across sites and highlight flag differences."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from eg4_config_lib import (
    build_diff_report,
    compare_configs,
    format_comparison_report,
    load_config_dir,
    load_config_snapshot,
    save_config_snapshot,
)
from eg4_config_fetch import fetch_inverter_config
from xls_to_influxdb import authenticate_eg4, get_inverter_list, read_config


def _fetch_configs(
    serials: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    *,
    all_sites: bool = False,
) -> List[Dict[str, Any]]:
    config = read_config()
    session = authenticate_eg4(
        config["eg4_monitor"]["username"],
        config["eg4_monitor"]["password"],
    )
    if not session:
        raise RuntimeError("Authentication failed")

    if serials:
        inverters = [{"id": serial, "plant_name": "unknown", "model": "unknown"} for serial in serials]
    else:
        inverters = get_inverter_list(session, config, all_sites=all_sites)

    if not inverters:
        raise RuntimeError("No inverters to fetch")

    fetched: List[Dict[str, Any]] = []
    for inverter in inverters:
        inverter_sn = inverter["id"]
        print(f"Fetching config for {inverter_sn}...", file=sys.stderr)
        config_data = fetch_inverter_config(
            session,
            inverter_sn,
            plant_id=inverter.get("plant_id"),
            plant_name=inverter.get("plant_name"),
            model=inverter.get("model"),
        )
        if output_dir:
            save_config_snapshot(config_data, output_dir)
        fetched.append(config_data)

    return fetched


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diff EG4 inverter configs and highlight flag differences."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "config_dir",
        nargs="?",
        type=Path,
        help="Directory of config snapshots from eg4-config-fetch.py",
    )
    source.add_argument(
        "--config",
        action="append",
        dest="config_files",
        type=Path,
        help="Individual config JSON file (repeatable, at least two)",
    )
    source.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch live configs for configured inverters, then diff",
    )

    parser.add_argument(
        "--serial",
        action="append",
        dest="serials",
        help="With --fetch: limit to these serial numbers",
    )
    parser.add_argument(
        "--flags-only",
        action="store_true",
        help="Only show FUNC_* and BIT_* flag differences",
    )
    parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include device identity fields (serial, firmware, clock, etc.)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON diff report to this file",
    )
    parser.add_argument(
        "--all-sites",
        action="store_true",
        help="With --fetch: include every inverter on every site, not just config.yaml",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="With --fetch: save snapshots to this directory",
    )
    args = parser.parse_args()

    try:
        if args.fetch:
            configs = _fetch_configs(args.serials, args.save_dir, all_sites=args.all_sites)
        elif args.config_files:
            if len(args.config_files) < 2:
                parser.error("Provide at least two --config files")
            configs = [load_config_snapshot(path) for path in args.config_files]
        else:
            if not args.config_dir:
                parser.error("Provide a config directory, --config files, or --fetch")
            configs = load_config_dir(args.config_dir)
    except (ValueError, RuntimeError, requests.RequestException) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    ignore_fields = frozenset() if args.include_ignored else None
    differences = compare_configs(
        configs,
        ignore_fields=ignore_fields,
        flags_only=args.flags_only,
    )

    report = build_diff_report(configs, differences, flags_only=args.flags_only)
    print(format_comparison_report(configs, differences, flags_only=args.flags_only))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"Wrote JSON report to {args.output}", file=sys.stderr)

    if args.save_dir and args.fetch:
        summary_path = args.save_dir / "summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "inverters": report["inverters"],
                    "diff_summary": report["summary"],
                },
                handle,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
        diff_path = args.save_dir / "diff-report.json"
        with diff_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"Wrote snapshots and diff report to {args.save_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()

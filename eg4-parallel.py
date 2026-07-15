#!/usr/bin/env python3
"""Inspect EG4 inverter parallel mode status across sites."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import requests

from xls_to_influxdb import (
    EG4_BASE_URL,
    authenticate_eg4,
    get_inverter_list,
    get_inverters_for_plant,
    get_plant_list,
    read_config,
)

MONITOR_REFERER = f"{EG4_BASE_URL}/WManage/web/monitor/inverter"
PARALLEL_GROUP_URL = f"{EG4_BASE_URL}/WManage/api/inverterOverview/getParallelGroupDetails"
RUNTIME_URL = f"{EG4_BASE_URL}/WManage/api/inverter/getInverterRuntime"


def _api_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": EG4_BASE_URL,
        "Referer": MONITOR_REFERER,
        "X-Requested-With": "XMLHttpRequest",
    }


def _post_json(session: requests.Session, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    response = session.post(url, headers=_api_headers(), data=data)
    response.raise_for_status()
    return response.json()


def fetch_parallel_status(
    session: requests.Session,
    *,
    all_sites: bool = False,
    serials: List[str] | None = None,
) -> List[Dict[str, Any]]:
    config = read_config()
    if serials:
        targets = [
            {"id": serial, "plant_name": "unknown", "model": "unknown"}
            for serial in serials
        ]
    elif all_sites:
        targets = []
        for plant in get_plant_list(session):
            for row in get_inverters_for_plant(session, plant["plantId"]):
                targets.append(
                    {
                        "id": row["serialNum"],
                        "plant_id": plant["plantId"],
                        "plant_name": plant["name"],
                        "model": row.get("deviceTypeText", "unknown"),
                        "parallel_enabled": row.get("parallelEnabled"),
                    }
                )
    else:
        targets = get_inverter_list(session, config)

    seen_groups: Dict[str, Dict[str, Any]] = {}
    results: List[Dict[str, Any]] = []

    for inverter in targets:
        serial = inverter["id"]
        runtime = _post_json(session, RUNTIME_URL, {"serialNum": serial})
        group = _post_json(session, PARALLEL_GROUP_URL, {"serialNum": serial})
        group_key = ",".join(
            device["serialNum"]
            for device in sorted(group.get("devices", []), key=lambda item: item["serialNum"])
        ) or f"solo:{serial}"

        if group_key not in seen_groups:
            seen_groups[group_key] = {
                "group_key": group_key,
                "inverter_count": group.get("inverterCount"),
                "devices": group.get("devices", []),
                "success": group.get("success"),
                "message": group.get("msg"),
            }

        results.append(
            {
                "serial": serial,
                "plant_name": inverter.get("plant_name", "unknown"),
                "model": inverter.get("model", "unknown"),
                "parallel_enabled": inverter.get("parallel_enabled"),
                "is_parallel_enabled": runtime.get("isParallelEnabled"),
                "status_text": runtime.get("statusText"),
                "group_key": group_key,
                "group": seen_groups[group_key],
            }
        )

    return results


def format_status_report(results: List[Dict[str, Any]]) -> str:
    lines = ["EG4 parallel status", "=" * 60]
    printed_groups: set[str] = set()

    for item in results:
        lines.append(
            f"\n{item['plant_name']} / {item['serial']} ({item['model']})"
        )
        lines.append(
            f"  parallelEnabled: {item['parallel_enabled']}  "
            f"runtime isParallelEnabled: {item['is_parallel_enabled']}  "
            f"status: {item['status_text']}"
        )

        group_key = item["group_key"]
        if group_key in printed_groups:
            continue
        printed_groups.add(group_key)

        group = item["group"]
        if not group.get("success"):
            lines.append(f"  parallel group: {group.get('message', 'not in a group')}")
            continue

        lines.append(f"  parallel group ({group.get('inverter_count')} inverter(s)):")
        for device in group.get("devices", []):
            lines.append(
                f"    - {device['serialNum']}: {device.get('roleText', '?')} "
                f"(index {device.get('parallelIndex', '?')})"
            )

    lines.extend(
        [
            "",
            "Notes:",
            "  - Sites are grouped via POST /api/inverter/autoParallel (Monitor Center Auto Parallel).",
            "  - No disableParallel API is exposed in the web UI/JS.",
            "  - Per-inverter HOLD_SET_MASTER_OR_SLAVE changes require standby/fault on the unit.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all-sites",
        action="store_true",
        help="Include every inverter on every site",
    )
    parser.add_argument(
        "--serial",
        action="append",
        dest="serials",
        help="Limit to specific inverter serial(s)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON",
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

    try:
        results = fetch_parallel_status(
            session,
            all_sites=args.all_sites,
            serials=args.serials,
        )
    except requests.RequestException as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_status_report(results))


if __name__ == "__main__":
    main()

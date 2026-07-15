#!/usr/bin/env python3
"""Push inverter configuration settings to EG4 Monitor Center."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from xls_to_influxdb import EG4_BASE_URL, authenticate_eg4, read_config

REMOTE_SET_BASE = f"{EG4_BASE_URL}/WManage/web/maintain/remoteSet"
MAINTAIN_REFERER = f"{EG4_BASE_URL}/WManage/web/maintain/remoteSet"

DEFAULT_CLIENT_TYPE = "WEB"
DEFAULT_REMOTE_SET_TYPE = "NORMAL"

# Fields that identify the device — never push these.
IMMUTABLE_FIELDS = frozenset({
    "HOLD_SERIAL_NUM",
    "HOLD_FW_CODE",
    "HOLD_TIME",
    "HOLD_MODEL",
})


def _api_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": EG4_BASE_URL,
        "Referer": MAINTAIN_REFERER,
        "X-Requested-With": "XMLHttpRequest",
    }


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return True
    if text in {"0", "false", "no", "off", "disabled"}:
        return False
    raise ValueError(f"Expected boolean value, got {value!r}")


def _field_kind(field: str) -> str:
    if field.startswith("FUNC_"):
        return "function"
    if field.startswith("BIT_"):
        return "bit"
    if (
        field.startswith("HOLD_")
        or field.startswith("LSP_HOLD_")
        or field.startswith("_12K_HOLD_")
    ):
        return "hold"
    raise ValueError(
        f"Unsupported field {field!r}; expected FUNC_*, BIT_*, or HOLD_* prefix"
    )


def _build_request(field: str, value: Any) -> Tuple[str, Dict[str, Any]]:
    kind = _field_kind(field)
    if kind == "function":
        return "functionControl", {
            "functionParam": field,
            "enable": str(_parse_bool(value)).lower(),
        }
    if kind == "bit":
        return "bitParamControl", {
            "bitParam": field,
            "value": str(value),
        }
    return "write", {
        "holdParam": field,
        "valueText": str(value),
    }


def push_setting(
    session: requests.Session,
    inverter_sn: str,
    field: str,
    value: Any,
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Push one named setting to an inverter."""
    endpoint, payload = _build_request(field, value)
    data = {
        "inverterSn": inverter_sn,
        "clientType": DEFAULT_CLIENT_TYPE,
        "remoteSetType": DEFAULT_REMOTE_SET_TYPE,
        **payload,
    }
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "endpoint": endpoint,
            "data": data,
        }

    response = session.post(
        f"{REMOTE_SET_BASE}/{endpoint}",
        headers=_api_headers(),
        data=data,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get("success"):
        message = result.get("msg") or result.get("message") or result
        raise RuntimeError(f"{field} -> {value!r} failed: {message}")
    return result


def load_settings_from_config(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        raise ValueError(f"{path} does not contain a 'settings' object")
    return settings


def parse_set_args(values: Iterable[str]) -> Dict[str, Any]:
    settings: Dict[str, Any] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Expected FIELD=VALUE, got {item!r}")
        field, value = item.split("=", 1)
        field = field.strip()
        value = value.strip()
        if not field:
            raise ValueError(f"Empty field name in {item!r}")
        settings[field] = value
    return settings


def filter_settings(
    settings: Dict[str, Any],
    only: Optional[List[str]] = None,
    skip_immutable: bool = True,
) -> Dict[str, Any]:
    filtered = dict(settings)
    if skip_immutable:
        for field in IMMUTABLE_FIELDS:
            filtered.pop(field, None)
    if only:
        allowed = set(only)
        filtered = {key: value for key, value in filtered.items() if key in allowed}
    return filtered


def diff_settings(
    source: Dict[str, Any],
    current: Dict[str, Any],
) -> Dict[str, Any]:
    changes: Dict[str, Any] = {}
    for field, value in source.items():
        if field in IMMUTABLE_FIELDS:
            continue
        if current.get(field) != value:
            changes[field] = value
    return changes


def confirm_push(inverter_sn: str, settings: Dict[str, Any]) -> bool:
    print(f"\nAbout to push {len(settings)} setting(s) to inverter {inverter_sn}:")
    for field in sorted(settings):
        print(f"  {field} = {settings[field]!r}")
    answer = input("\nProceed? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Push EG4 inverter configuration settings via remoteSet API."
    )
    parser.add_argument(
        "--serial",
        action="append",
        dest="serials",
        required=True,
        help="Target inverter serial number (repeatable)",
    )
    parser.add_argument(
        "--set",
        action="append",
        dest="sets",
        default=[],
        metavar="FIELD=VALUE",
        help="Set one field, e.g. FUNC_CHARGE_LAST=true",
    )
    parser.add_argument(
        "--from-config",
        type=Path,
        help="JSON config snapshot (from eg4-config-fetch.py) to apply",
    )
    parser.add_argument(
        "--only",
        help="Comma-separated list of fields to apply from --from-config",
    )
    parser.add_argument(
        "--diff-against",
        type=Path,
        metavar="CONFIG_JSON",
        help="Only push fields that differ from this inverter config snapshot",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned writes without sending them",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    settings: Dict[str, Any] = {}
    if args.from_config:
        settings.update(load_settings_from_config(args.from_config))
    if args.sets:
        settings.update(parse_set_args(args.sets))
    if not settings:
        parser.error("Provide at least one --set FIELD=VALUE or --from-config")

    only_fields = [field.strip() for field in args.only.split(",")] if args.only else None
    settings = filter_settings(settings, only=only_fields)

    if args.diff_against:
        baseline = load_settings_from_config(args.diff_against)
        settings = diff_settings(settings, baseline)
        if not settings:
            print("No differences to push after --diff-against filtering.")
            return

    config = read_config()
    session = authenticate_eg4(
        config["eg4_monitor"]["username"],
        config["eg4_monitor"]["password"],
    )
    if not session:
        print("Authentication failed", file=sys.stderr)
        sys.exit(1)

    failures = 0
    for inverter_sn in args.serials:
        to_push = settings
        if not args.yes and not args.dry_run:
            if not confirm_push(inverter_sn, to_push):
                print(f"Skipped {inverter_sn}")
                continue

        print(f"\nPushing to {inverter_sn}...")
        for field, value in sorted(to_push.items()):
            try:
                result = push_setting(
                    session,
                    inverter_sn,
                    field,
                    value,
                    dry_run=args.dry_run,
                )
                if args.dry_run:
                    endpoint = result["endpoint"]
                    print(f"  [dry-run] {endpoint}: {field} = {value!r}")
                else:
                    print(f"  OK {field} = {value!r}")
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                print(f"  FAIL {field}: {exc}", file=sys.stderr)
                failures += 1

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()

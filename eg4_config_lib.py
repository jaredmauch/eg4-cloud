"""Shared helpers for EG4 inverter config fetch, load, and compare."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from eg4_config_labels import (
    format_field_heading,
    peak_shaving_window_from_settings,
    summarize_hold_model,
    value_description,
)

# Device identity / runtime — not meaningful for config alignment diffs.
IGNORE_FIELDS = frozenset({
    "HOLD_SERIAL_NUM",
    "HOLD_FW_CODE",
    "HOLD_TIME",
    "HOLD_COM_ADDR",
    "HOLD_MAINTENANCE_COUNT",
})

FIELD_CATEGORIES: Tuple[Tuple[str, str], ...] = (
    ("FUNC_", "function flags (FUNC_)"),
    ("BIT_", "bit flags (BIT_)"),
    ("LSP_", "load-shedule (LSP_)"),
    ("_12K_", "12K-specific (_12K_)"),
    ("HOLD_", "hold registers (HOLD_)"),
)


def field_category(field: str) -> str:
    for prefix, label in FIELD_CATEGORIES:
        if field.startswith(prefix):
            return label
    return "other"


def is_lsp_hold_time_field(field: str) -> bool:
    return field.startswith("LSP_HOLD_DIS_CHG_POWER_TIME_")


def is_hold_model_field(field: str) -> bool:
    return field == "HOLD_MODEL" or field.startswith("HOLD_MODEL_")


def summarize_peak_shaving_windows(settings: Dict[str, Any]) -> List[str]:
    """Decode Peak Shaving time windows from LSP_HOLD_DIS_CHG_POWER_TIME_37–44."""
    windows: List[str] = []
    for window in (1, 2):
        text = peak_shaving_window_from_settings(settings, window)
        if text:
            windows.append(f"window {window}: {text}")
    return windows


def is_flag_field(field: str) -> bool:
    return field.startswith("FUNC_") or field.startswith("BIT_")


def inverter_label(config: Dict[str, Any]) -> str:
    site = config.get("plant_name") or config.get("site") or "unknown site"
    serial = config.get("inverter_sn", "?")
    model = config.get("model")
    if model:
        return f"{site} / {serial} ({model})"
    return f"{site} / {serial}"


def load_config_snapshot(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if "settings" not in payload:
        raise ValueError(f"{path} is not an inverter config snapshot (missing 'settings')")
    return payload


def save_config_snapshot(config_data: Dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{config_data['inverter_sn']}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(config_data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def load_config_dir(directory: Path) -> List[Dict[str, Any]]:
    configs: List[Dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        if path.name in {"summary.json", "diff-report.json"}:
            continue
        try:
            configs.append(load_config_snapshot(path))
        except ValueError:
            continue
    if len(configs) < 2:
        raise ValueError(
            f"Need at least two inverter snapshots in {directory}, found {len(configs)}"
        )
    return configs


def compare_configs(
    configs: List[Dict[str, Any]],
    *,
    ignore_fields: Optional[frozenset] = None,
    flags_only: bool = False,
) -> List[Dict[str, Any]]:
    """Return setting-level differences across inverter configs."""
    if len(configs) < 2:
        return []

    ignored = ignore_fields if ignore_fields is not None else IGNORE_FIELDS
    all_fields: set[str] = set()
    for config in configs:
        all_fields.update(config["settings"])

    differences: List[Dict[str, Any]] = []
    for field in sorted(all_fields):
        if field in ignored:
            continue
        if flags_only and not is_flag_field(field):
            continue

        values = {
            config["inverter_sn"]: config["settings"].get(field)
            for config in configs
        }
        unique = {json.dumps(value, sort_keys=True) for value in values.values()}
        if len(unique) <= 1:
            continue

        differences.append({
            "field": field,
            "category": field_category(field),
            "is_flag": is_flag_field(field),
            "values": values,
            "labels": {
                config["inverter_sn"]: inverter_label(config)
                for config in configs
            },
        })

    return differences


def group_differences(
    differences: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for diff in differences:
        grouped.setdefault(diff["category"], []).append(diff)
    return grouped


def summarize_differences(differences: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped = group_differences(differences)
    flag_count = sum(1 for diff in differences if diff["is_flag"])
    return {
        "total_differences": len(differences),
        "flag_differences": flag_count,
        "hold_differences": len(differences) - flag_count,
        "by_category": {category: len(items) for category, items in grouped.items()},
    }


def format_value(
    value: Any,
    field: str,
    *,
    model: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    return value_description(
        field,
        value,
        model=model,
        settings=settings,
    )


def format_comparison_report(
    configs: List[Dict[str, Any]],
    differences: List[Dict[str, Any]],
    *,
    flags_only: bool = False,
) -> str:
    lines: List[str] = []
    inverters = [inverter_label(config) for config in configs]
    summary = summarize_differences(differences)

    lines.append("EG4 inverter config comparison")
    lines.append("=" * 60)
    lines.append(f"Inverters ({len(configs)}):")
    for label in inverters:
        lines.append(f"  - {label}")
    lines.append("")

    if not differences:
        scope = "flag settings" if flags_only else "settings"
        lines.append(f"All compared inverters have identical {scope}.")
        return "\n".join(lines)

    lines.append(
        f"Differences: {summary['total_differences']} total "
        f"({summary['flag_differences']} flags, {summary['hold_differences']} other)"
    )
    lines.append("")

    grouped = group_differences(differences)
    category_order = [label for _, label in FIELD_CATEGORIES] + ["other"]
    for category in category_order:
        items = grouped.get(category)
        if not items:
            continue
        lines.append(f"--- {category} ({len(items)}) ---")
        for diff in items:
            lines.append(format_field_heading(diff["field"]))
            for config in configs:
                value = diff["values"].get(config["inverter_sn"])
                formatted = format_value(
                    value,
                    diff["field"],
                    model=config.get("model"),
                    settings=config.get("settings"),
                )
                lines.append(f"  {inverter_label(config)}: {formatted}")
            lines.append("")
        if category == "hold registers (HOLD_)":
            model_diffs = [
                diff for diff in items if is_hold_model_field(diff["field"])
            ]
            if model_diffs:
                lines.append("HOLD_MODEL (decoded):")
                for config in configs:
                    summary = summarize_hold_model(
                        config.get("settings", {}),
                        model=config.get("model"),
                    )
                    if summary:
                        lines.append(f"  {inverter_label(config)}: {summary}")
                lines.append("")
        if category == "load-shedule (LSP_)":
            peak_diffs = [
                diff for diff in items
                if is_lsp_hold_time_field(diff["field"])
            ]
            if peak_diffs:
                lines.append("Peak Shaving windows (decoded):")
                for config in configs:
                    windows = summarize_peak_shaving_windows(config["settings"])
                    if windows:
                        lines.append(
                            f"  {inverter_label(config)}: {', '.join(windows)}"
                        )
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_diff_report(
    configs: List[Dict[str, Any]],
    differences: List[Dict[str, Any]],
    *,
    flags_only: bool = False,
) -> Dict[str, Any]:
    return {
        "inverters": [
            {
                "inverter_sn": config.get("inverter_sn"),
                "plant_name": config.get("plant_name"),
                "plant_id": config.get("plant_id"),
                "model": config.get("model"),
                "fetched_at": config.get("fetched_at"),
            }
            for config in configs
        ],
        "summary": summarize_differences(differences),
        "flags_only": flags_only,
        "differences": differences,
    }

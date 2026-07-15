"""Load human-readable EG4 field labels scraped from Monitor Center HTML."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_LABELS_PATH = Path(__file__).resolve().parent / "eg4-field-labels.json"
DEFAULT_DESCRIPTIONS_PATH = Path(__file__).resolve().parent / "eg4-field-descriptions.json"

_LSP_SLOT_RE = re.compile(
    r"^FUNC_LSP_(BAT_FIRST|BYPASS|OUTPUT)_(\d+)_EN$"
)
_LSP_HOLD_TIME_RE = re.compile(r"^LSP_HOLD_DIS_CHG_POWER_TIME_(\d+)$")
_POWER_RATING_UI_RE = re.compile(r"^powerRating(\d+)_(.+?)Text$")


@lru_cache(maxsize=1)
def load_labels(path: Optional[Path] = None) -> Dict[str, Any]:
    labels_path = path or DEFAULT_LABELS_PATH
    if not labels_path.exists():
        return {}
    with labels_path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_field_descriptions(path: Optional[Path] = None) -> Dict[str, Any]:
    descriptions_path = path or DEFAULT_DESCRIPTIONS_PATH
    if not descriptions_path.exists():
        return {}
    with descriptions_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def lsp_slot_time_range(slot: int) -> str:
    """Return HH:MM–HH:MM for LSP scheduler slot 1–48 (30-minute slots)."""
    if not 1 <= slot <= 48:
        raise ValueError(f"LSP slot must be 1–48, got {slot}")
    start_minutes = (slot - 1) * 30
    end_minutes = slot * 30
    start_h, start_m = divmod(start_minutes, 60)
    if end_minutes >= 1440:
        return f"{start_h:02d}:{start_m:02d}–24:00"
    end_h, end_m = divmod(end_minutes, 60)
    return f"{start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d}"


def _lsp_hold_time_component(register: int) -> Optional[str]:
    """Return hour|minute for Peak Shaving time registers 37–44."""
    parts = {
        37: "hour",
        38: "minute",
        39: "hour",
        40: "minute",
        41: "hour",
        42: "minute",
        43: "hour",
        44: "minute",
    }
    return parts.get(register)


def format_lsp_hold_time_value(field: str, value: Any) -> str:
    """Format a single LSP_HOLD_DIS_CHG_POWER_TIME_* component for display."""
    match = _LSP_HOLD_TIME_RE.match(field)
    if not match:
        return str(value)
    component = _lsp_hold_time_component(int(match.group(1)))
    if component is None:
        return str(value)
    text = str(value).strip()
    if text.isdigit():
        return f"{int(text):02d} ({component})"
    return str(value)


def peak_shaving_window_from_settings(
    settings: Dict[str, Any],
    window: int = 1,
) -> Optional[str]:
    """Return HH:MM–HH:MM for Peak Shaving window 1 or 2, or None if unset."""
    if window not in (1, 2):
        raise ValueError("Peak Shaving window must be 1 or 2")
    base = 37 if window == 1 else 41
    keys = [f"LSP_HOLD_DIS_CHG_POWER_TIME_{base + offset}" for offset in range(4)]
    raw = [settings.get(key) for key in keys]
    if not any(raw):
        return None
    parts = [str(v or "0").strip() for v in raw]
    if not any(part not in ("", "0", "00") for part in parts):
        return None
    sh, sm, eh, em = (int(p) if p.isdigit() else 0 for p in parts)
    return f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d}"


@lru_cache(maxsize=1)
def _power_rating_tables(labels_path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """Parse powerRating{N}_{Profile}Text entries from scraped UI strings."""
    data = load_labels(labels_path)
    tables: Dict[str, Dict[str, str]] = {}
    for key, text in data.get("ui_strings", {}).items():
        match = _POWER_RATING_UI_RE.match(key)
        if not match:
            continue
        index, profile = match.group(1), match.group(2)
        tables.setdefault(profile, {})[index] = text
    return tables


def _enum_display_text(mapped: str) -> str:
    """Extract short label from value_description output like '2 (2: Lithium)'."""
    text = mapped.strip()
    if "(" in text and text.endswith(")"):
        inner = text.split("(", 1)[1][:-1]
        if ":" in inner:
            return inner.split(":", 1)[1].strip()
        return inner.strip()
    return text


def power_rating_profile(model: Optional[str] = None) -> str:
    profiles = load_field_descriptions().get("power_rating_profiles", {})
    if model and model in profiles:
        return profiles[model]
    return profiles.get("default", "Default")


def power_rating_label(
    value: Any,
    *,
    model: Optional[str] = None,
    labels: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Return human kW label for HOLD_MODEL_powerRating, e.g. '8 kW'."""
    text = str(value).strip()
    if not text.isdigit():
        return None
    profile = power_rating_profile(model)
    tables = _power_rating_tables()
    entry = tables.get(profile, {}).get(text)
    if not entry:
        entry = tables.get("Default", {}).get(text)
    if not entry:
        return None
    # UI strings look like "2: 8kW" — keep the kW portion for display.
    if ":" in entry:
        return entry.split(":", 1)[1].strip().replace("kW", " kW")
    return entry


def _hold_model_subfield_value_key(field: str) -> Optional[str]:
    return load_field_descriptions().get("hold_model_subfield_value_keys", {}).get(field)


def _parse_hold_model_hex(value: Any) -> Optional[int]:
    text = str(value).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    if text.isdigit():
        return int(text)
    return None


def summarize_hold_model(
    settings: Dict[str, Any],
    *,
    model: Optional[str] = None,
    labels: Optional[Dict[str, Any]] = None,
) -> str:
    """One-line summary of exploded HOLD_MODEL subfields."""
    parts: List[str] = []
    raw = settings.get("HOLD_MODEL")
    if raw:
        parts.append(str(raw))

    rating = settings.get("HOLD_MODEL_powerRating")
    if rating is not None:
        kw = power_rating_label(rating, model=model, labels=labels)
        parts.append(kw or f"powerRating {rating}")

    for field, bit_key in load_field_descriptions().get(
        "hold_model_subfield_value_keys", {}
    ).items():
        value = settings.get(field)
        if value is None:
            continue
        label = value_description(
            bit_key,
            value,
            labels=labels,
            model=model,
            settings=settings,
        )
        parts.append(_enum_display_text(label))

    if settings.get("HOLD_MODEL_usVersion"):
        parts.append("US")

    return " · ".join(parts)


def describe_lsp_slot_field(field: str) -> Optional[str]:
    """Human description for FUNC_LSP_{BAT_FIRST,BYPASS,OUTPUT}_{N}_EN fields."""
    match = _LSP_SLOT_RE.match(field)
    if not match:
        return None
    family_key, slot_text = match.group(1), match.group(2)
    slot = int(slot_text)
    time_range = lsp_slot_time_range(slot)
    family_names = {
        "BAT_FIRST": "PV Charge Priority / Charge Priority",
        "BYPASS": "Bypass Mode",
        "OUTPUT": "Output priority",
    }
    return (
        f"LSP slot {slot} ({time_range}) — {family_names[family_key]}"
    )


def field_description(
    field: str,
    labels: Optional[Dict[str, Any]] = None,
    descriptions: Optional[Dict[str, Any]] = None,
) -> str:
    lsp_text = describe_lsp_slot_field(field)
    if lsp_text:
        return lsp_text

    desc_data = descriptions if descriptions is not None else load_field_descriptions()
    explicit = desc_data.get("fields", {}).get(field)
    if explicit:
        return explicit

    for entry in desc_data.get("field_patterns", []):
        pattern = entry.get("pattern")
        template = entry.get("description")
        if not pattern or not template:
            continue
        match = re.match(pattern, field)
        if match:
            slot = int(match.group(1))
            return template.format(slot=slot, time=lsp_slot_time_range(slot))

    data = labels if labels is not None else load_labels()
    if not data:
        return field

    for section in ("FUNC_", "BIT_", "HOLD_", "modelBitParam"):
        name = data.get("field_labels", {}).get(section, {}).get(field)
        if name:
            return name
    return field


def value_description(
    field: str,
    value: Any,
    labels: Optional[Dict[str, Any]] = None,
    *,
    model: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    data = labels if labels is not None else load_labels()
    if isinstance(value, bool):
        return "enabled" if value else "disabled"

    if field == "HOLD_MODEL":
        parsed = _parse_hold_model_hex(value)
        detail_parts: List[str] = []
        if settings:
            rating = settings.get("HOLD_MODEL_powerRating")
            kw = power_rating_label(rating, model=model, labels=data)
            if kw:
                detail_parts.append(kw)
            for subfield, bit_key in load_field_descriptions().get(
                "hold_model_subfield_value_keys", {}
            ).items():
                sub_value = settings.get(subfield)
                if sub_value is None:
                    continue
                label = value_description(
                    bit_key,
                    sub_value,
                    labels=data,
                    model=model,
                    settings=settings,
                )
                detail_parts.append(_enum_display_text(label))
        if parsed is not None:
            if detail_parts:
                return f"{value} ({parsed}; {' · '.join(detail_parts)})"
            return f"{value} ({parsed})"
        return str(value)

    if field == "HOLD_MODEL_powerRating":
        kw = power_rating_label(value, model=model, labels=data)
        if kw:
            return f"{value} ({kw})"
        return str(value)

    subfield_key = _hold_model_subfield_value_key(field)
    if subfield_key:
        mapped = value_description(
            subfield_key,
            value,
            labels=data,
            model=model,
            settings=settings,
        )
        if mapped != str(value):
            return mapped

    value_labels = data.get("value_labels", {})
    field_values = value_labels.get(field, {})
    text = field_values.get(str(value))
    if text:
        return f"{value} ({text})"
    if _LSP_HOLD_TIME_RE.match(field):
        return format_lsp_hold_time_value(field, value)
    return str(value)


def format_field_heading(field: str, labels: Optional[Dict[str, Any]] = None) -> str:
    description = field_description(field, labels)
    if description == field:
        return field
    return f"{field} — {description}"

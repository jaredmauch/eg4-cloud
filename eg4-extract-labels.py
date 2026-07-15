#!/usr/bin/env python3
"""Extract field labels and value mappings from EG4 Monitor Center remoteSet HTML."""

from __future__ import annotations

import argparse
import html as htmlmod
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

import requests

from xls_to_influxdb import EG4_BASE_URL, authenticate_eg4, read_config

DEFAULT_OUTPUT = Path("eg4-field-labels.json")
API_SPEC = Path("eg4-field-labels.json").parent / "eg4-api.json"


def _load_page_text(session: requests.Session) -> tuple[str, str]:
    page_url = f"{EG4_BASE_URL}/WManage/web/maintain/remoteSet"
    page = session.get(page_url).text
    text = page
    for url in re.findall(r'<script[^>]+src="([^"]+)"', page):
        if url.startswith("http"):
            text += "\n" + requests.get(url, timeout=30).text
    return page, text


def _extract_ui_strings(text: str) -> Dict[str, str]:
    return dict(re.findall(r"var (\w+)\s*=\s*'([^']*)'", text))


def _extract_enum_groups(strings: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    groups: Dict[str, Dict[int, str]] = defaultdict(dict)
    for name, value in strings.items():
        match = re.match(r"^(.+)_(\d+)$", name)
        if match:
            groups[match.group(1)][int(match.group(2))] = value
    return {
        prefix: {str(index): label for index, label in sorted(values.items())}
        for prefix, values in groups.items()
        if len(values) >= 2
    }


def _nearest_label(page: str, index: int) -> str | None:
    before = page[max(0, index - 1200) : index]
    labels = list(re.finditer(r"<label[^>]*>(.*?)</label>", before, re.S))
    if not labels:
        return None
    text = re.sub(r"<[^>]+>", "", labels[-1].group(1))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*\(\?\)\s*$", "", text)
    return htmlmod.unescape(text) if text else None


def _label_after_param(page: str, attr: str) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    pattern = rf'{attr}="([^"]+)"'
    for match in re.finditer(pattern, page):
        param = match.group(1)
        if param in labels:
            continue
        label = _nearest_label(page, match.start())
        if label:
            labels[param] = label
            continue
        after = page[match.start() : match.start() + 800]
        title_match = re.search(
            r'class="remoteSetTitle[^"]*"[^>]*>\s*([^<]+?)\s*<', after
        )
        if title_match:
            labels[param] = htmlmod.unescape(title_match.group(1).strip())
    return labels


def _extract_select_values(page: str, strings: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    selects: Dict[str, Dict[str, Any]] = {}
    for match in re.finditer(
        r'<select[^>]*\s(bitParam|holdParam|modelBitParam)="([^"]+)"[^>]*>(.*?)</select>',
        page,
        re.S,
    ):
        control, param = match.group(1), match.group(2)
        options: Dict[str, str] = {}
        for option in re.finditer(
            r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>',
            match.group(3),
            re.S,
        ):
            raw = htmlmod.unescape(re.sub(r"<[^>]+>", "", option.group(2)).strip())
            refs = re.findall(r"\+\s*(\w+)\s*\+", raw)
            if refs:
                label = " / ".join(strings.get(ref, ref) for ref in refs)
            else:
                label = raw
            options[option.group(1)] = label
        if param not in selects or len(options) > len(selects[param]["values"]):
            selects[param] = {"control": control, "values": options}
    return selects


def _known_param_enum_links() -> Dict[str, str]:
    return {
        "BIT_AC_CHARGE_TYPE": "acChargeBaseOn",
    }


def build_label_document(session: requests.Session) -> Dict[str, Any]:
    page, text = _load_page_text(session)
    ui_strings = _extract_ui_strings(text)
    enum_groups = _extract_enum_groups(ui_strings)
    selects = _extract_select_values(page, ui_strings)

    value_labels: Dict[str, Dict[str, str]] = {}
    for param, meta in selects.items():
        values = {
            key: label
            for key, label in meta["values"].items()
            if key != "-1" and label not in {"<Empty>", "&lt;Empty&gt;"}
        }
        if values:
            value_labels[param] = values

    for param, prefix in _known_param_enum_links().items():
        if prefix in enum_groups:
            value_labels[param] = enum_groups[prefix]

    for prefix, values in enum_groups.items():
        value_labels.setdefault(prefix, values)

    api_types: Dict[str, str] = {}
    if API_SPEC.exists():
        with API_SPEC.open(encoding="utf-8") as handle:
            api = json.load(handle)
        properties = api["components"]["schemas"]["InverterSettingsDTO"]["properties"]
        api_types = {
            name: field.get("type", "unknown") for name, field in properties.items()
        }

    return {
        "meta": {
            "source": "EG4 Monitor Center remoteSet HTML + linked JS",
            "source_url": f"{EG4_BASE_URL}/WManage/web/maintain/remoteSet",
            "ui_string_count": len(ui_strings),
            "notes": {
                "boolean_fields": "FUNC_* fields are boolean enable/disable toggles",
                "value_labels": "Numeric keys map to EG4 Monitor Center dropdown labels",
            },
        },
        "value_labels": dict(sorted(value_labels.items())),
        "enum_groups": dict(sorted(enum_groups.items())),
        "field_labels": {
            "FUNC_": dict(sorted(_label_after_param(page, "functionParam").items())),
            "BIT_": dict(sorted(_label_after_param(page, "bitParam").items())),
            "HOLD_": dict(sorted(_label_after_param(page, "holdParam").items())),
            "modelBitParam": dict(
                sorted(_label_after_param(page, "modelBitParam").items())
            ),
        },
        "select_controls": {
            param: meta["control"] for param, meta in sorted(selects.items())
        },
        "ui_strings": dict(sorted(ui_strings.items())),
        "api_types": api_types,
    }


def render_markdown(doc: Dict[str, Any]) -> str:
    lines = [
        "# EG4 Monitor Center Field Reference",
        "",
        f"Scraped from [{doc['meta']['source_url']}]({doc['meta']['source_url']}).",
        "",
        "Regenerate with:",
        "",
        "```bash",
        "python3 eg4-extract-labels.py --markdown docs/field-reference.md",
        "```",
        "",
        "## LSP internal schedule fields",
        "",
        "`FUNC_LSP_*` fields are firmware-internal Load Schedule Plan bitmaps. "
        "They are not exposed as labeled controls in Monitor Center. "
        "See [lsp-schedule-fields.md](lsp-schedule-fields.md) for the 48-slot model, "
        "`BAT_FIRST` / `BYPASS` / `OUTPUT` families, and Monitor Center mappings.",
        "",
        "## Value labels (dropdown / enum fields)",
        "",
        "These fields use numeric values in config snapshots. The labels below come "
        "from the Monitor Center UI.",
        "",
    ]

    for param, values in doc["value_labels"].items():
        lines.append(f"### `{param}`")
        lines.append("")
        for value, label in values.items():
            lines.append(f"- **{value}**: {label}")
        lines.append("")

    for section, title in [
        ("FUNC_", "Function flags (FUNC_*)"),
        ("BIT_", "Bit fields (BIT_*)"),
        ("HOLD_", "Hold registers (HOLD_*)"),
        ("modelBitParam", "Model bit fields"),
    ]:
        labels = doc["field_labels"].get(section, {})
        if not labels:
            continue
        lines.extend([f"## {title}", ""])
        for param, label in labels.items():
            api_type = doc.get("api_types", {}).get(param)
            type_note = f" (`{api_type}`)" if api_type else ""
            lines.append(f"- `{param}`: {label}{type_note}")
        lines.append("")

    lines.extend(
        [
            "## Boolean flags without dedicated UI labels",
            "",
            "Many `FUNC_*` toggles only show Enable/Disable buttons in the UI. "
            "When no label is listed above, refer to the field name or the "
            "[EG4 API documentation](https://eg4electronics.com/api-documentation/).",
            "",
        ]
    )

    func_in_api = sorted(
        name for name in doc.get("api_types", {}) if name.startswith("FUNC_")
    )
    documented = set(doc["field_labels"].get("FUNC_", {}))
    undocumented = [name for name in func_in_api if name not in documented]
    if undocumented:
        lines.append("### FUNC_* fields from official API schema")
        lines.append("")
        for name in undocumented:
            lines.append(f"- `{name}` ({doc['api_types'][name]})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"JSON output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        help="Also write a Markdown field reference to this path",
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

    document = build_label_document(session)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}", file=sys.stderr)
    print(
        f"  value_labels: {len(document['value_labels'])}, "
        f"FUNC labels: {len(document['field_labels']['FUNC_'])}, "
        f"HOLD labels: {len(document['field_labels']['HOLD_'])}",
        file=sys.stderr,
    )

    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(document), encoding="utf-8")
        print(f"Wrote {args.markdown}", file=sys.stderr)


if __name__ == "__main__":
    main()

"""Fetch inverter configuration from EG4 Monitor Center remoteRead API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests

from xls_to_influxdb import EG4_BASE_URL

REMOTE_READ_URL = f"{EG4_BASE_URL}/WManage/web/maintain/remoteRead/read"
MAINTAIN_REFERER = f"{EG4_BASE_URL}/WManage/web/maintain/remoteRead"

CONFIG_READS: List[Tuple[int, int]] = [
    (0, 127),
    (127, 127),
    (240, 127),
]

METADATA_KEYS = frozenset({
    "success",
    "valueFrame",
    "inverterSn",
    "deviceType",
    "startRegister",
    "pointNumber",
    "inverterRuntimeDeviceTime",
    "INPUT_BATTERY_VOLTAGE",
})


def _api_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": EG4_BASE_URL,
        "Referer": MAINTAIN_REFERER,
        "X-Requested-With": "XMLHttpRequest",
    }


def fetch_config_chunk(
    session: requests.Session,
    inverter_sn: str,
    start_register: int,
    point_number: int,
) -> Dict[str, Any]:
    response = session.post(
        REMOTE_READ_URL,
        headers=_api_headers(),
        data={
            "inverterSn": inverter_sn,
            "startRegister": start_register,
            "pointNumber": point_number,
        },
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success", True):
        raise RuntimeError(
            f"remoteRead failed for {inverter_sn} @ {start_register}: "
            f"{payload.get('message') or payload}"
        )
    return payload


def _extract_config_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in METADATA_KEYS
    }


def fetch_inverter_config(
    session: requests.Session,
    inverter_sn: str,
    *,
    plant_id: Any = None,
    plant_name: str | None = None,
    model: str | None = None,
) -> Dict[str, Any]:
    chunks: List[Dict[str, Any]] = []
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    for start_register, point_number in CONFIG_READS:
        payload = fetch_config_chunk(
            session, inverter_sn, start_register, point_number
        )
        fields = _extract_config_fields(payload)
        chunks.append(
            {
                "start_register": start_register,
                "point_number": point_number,
                "field_count": len(fields),
                "value_frame": payload.get("valueFrame"),
            }
        )
        settings.update(fields)
        if not metadata:
            metadata = {
                "device_type": payload.get("deviceType"),
                "inverter_runtime_device_time": payload.get(
                    "inverterRuntimeDeviceTime"
                ),
                "input_battery_voltage": payload.get("INPUT_BATTERY_VOLTAGE"),
            }

    result: Dict[str, Any] = {
        "inverter_sn": inverter_sn,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "field_count": len(settings),
        "metadata": metadata,
        "settings": dict(sorted(settings.items())),
        "chunks": chunks,
    }
    if plant_id is not None:
        result["plant_id"] = plant_id
    if plant_name is not None:
        result["plant_name"] = plant_name
    if model is not None:
        result["model"] = model
    return result

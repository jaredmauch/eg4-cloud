# LSP (Load Schedule Plan) Internal Fields

`FUNC_LSP_*` fields are **firmware-internal** flags for the inverter's 24-hour working-mode
scheduler. They appear in config snapshots from `remoteRead` but are **not** exposed as
labeled controls in Monitor Center's remoteSet HTML.

Sources for this document:

- EG4/LuxPower Monitor Center working-mode behavior
- [eg4-bridge/doc](../eg4-bridge/doc) (`eg2.portal.txt`, `LXP_REGISTERS.txt`, Modbus protocol)
- LuxPower [AC-Coupled Setting guide](https://luxpowertek.com/wp-content/uploads/2022/02/AC-Coupled-Setting.pdf)
- Fleet config analysis (`configs/latest/`)

## 48-slot day model

The scheduler divides the day into **48 half-hour slots** (30 minutes each).

| Slot | Time range | Formula |
|------|------------|---------|
| 1 | 00:00–00:30 | start = (N−1) × 30 min |
| 2 | 00:30–01:00 | end = N × 30 min |
| … | … | |
| 48 | 23:30–24:00 | |

Example: `FUNC_LSP_BAT_FIRST_17_EN = true` → slot 17 → **08:00–08:30**.

When comparing inverters, decode enabled slots to time ranges instead of diffing 48
individual booleans.

## Two layers: user settings vs firmware bitmap

Monitor Center exposes **working modes** and **time windows**. The firmware stores a
compiled **per-slot bitmap** in `FUNC_LSP_*` fields.

```
User-facing (Monitor Center)          Firmware internal (config snapshot)
─────────────────────────────         ───────────────────────────────────
PV Charge Priority Mode tab    →      FUNC_LSP_BAT_FIRST_1_EN … _48_EN
  FUNC_FORCED_CHG_EN (enable)         (one flag per 30-min slot)
  HOLD_FORCED_CHARGE_* (times)
  HOLD_FORCED_CHG_* (power/SOC)

Bypass / Self Consumption / etc. →    FUNC_LSP_BYPASS_* , FUNC_LSP_SELF_CONSUMPTION_EN , …
```

The bitmap can retain old slot assignments even when the master enable is off (e.g.
`FUNC_FORCED_CHG_EN=false` while `FUNC_LSP_BAT_FIRST_*` slots are still set).

## Per-slot mode families

Each slot can be assigned at most one primary mode via these flag families:

| Flag pattern | Working mode | Monitor Center / API |
|--------------|--------------|----------------------|
| `FUNC_LSP_BAT_FIRST_{N}_EN` | **PV Charge Priority** (battery/charge first) | PV Charge Priority Mode; `FUNC_FORCED_CHG_EN`; eg4-bridge "Charge Priority" |
| `FUNC_LSP_BYPASS_{N}_EN` | **Bypass Mode** | Not a dedicated tab; see `FUNC_LSP_BYPASS_MODE_EN` |
| `FUNC_LSP_OUTPUT_{N}_EN` | Timeline mode (export/output priority) | Partially documented; 12 slots in some models |
| *(unset)* | **Self Consumption** (default) | Self Consumption Mode; `FUNC_LSP_SELF_CONSUMPTION_EN` |

### `FUNC_LSP_BAT_FIRST_{1-48}_EN` — PV Charge Priority slots

**Meaning:** During slot N, route solar to **charge the battery first**, then serve
loads, then export surplus to grid.

Also called:

- **Charge Priority** (LuxPower monitor docs, eg4-bridge)
- **Battery first** (Modbus `OutputPrioConfig` value 0; `ChgFirstPowerCMD`)
- `chargeFirst` in Monitor Center working-mode JavaScript

**User-facing controls** (what you edit in the UI):

| Field | UI label (eg4-field-labels) |
|-------|----------------------------|
| `FUNC_FORCED_CHG_EN` | PV Charge Priority Mode enable |
| `HOLD_FORCED_CHARGE_START_HOUR` / `_MINUTE` | Window 1 start |
| `HOLD_FORCED_CHARGE_END_HOUR` / `_MINUTE` | Window 1 end |
| `HOLD_FORCED_CHARGE_START_HOUR_1` … `_2` | Windows 2–3 start |
| `HOLD_FORCED_CHARGE_END_HOUR_1` … `_2` | Windows 2–3 end |
| `HOLD_FORCED_CHG_POWER_CMD` | PV Charge Power (kW) |
| `HOLD_FORCED_CHG_SOC_LIMIT` | PV Charge Priority Stop SOC (%) |

**eg4-bridge cross-reference:**

- Register 21, charge-priority bit — `LXP_REGISTERS.txt`: *"charge priority (charge before supplying load)"*
- `eg2.portal.txt` — example `FUNC_LSP_BAT_FIRST_*` values for a live inverter

### `FUNC_LSP_BYPASS_{1-48}_EN` — Bypass Mode slots

**Meaning:** During slot N, **grid AC powers loads**; solar charges the battery only
(firmware mode `0×11` Bypass in EG4 manuals).

Related master flags:

| Field | Meaning |
|-------|---------|
| `FUNC_LSP_BYPASS_EN` | Bypass subsystem present/enabled in scheduler |
| `FUNC_LSP_BYPASS_MODE_EN` | Master enable for Bypass Mode profile |
| `FUNC_LSP_WHOLE_BYPASS_{1-3}_EN` | Which of 3 schedule bands use bypass |

Not the same as `FUNC_BATTERY_ECO_EN` (auto-bypass at On-Grid EOD).

### `FUNC_LSP_OUTPUT_{1-12}_EN` — Output priority slots

**Meaning:** Another timeline-assigned mode (fewer slots than the 48-slot families
above on some models). Modbus register 145 `OutputPrioConfig` documents output
priority as `0-bat first / 1-PV first / 2-AC first` at a different abstraction layer.

Treat as internal scheduler state; prefer user-facing hold/func fields for changes.

### `FUNC_LSP_SELF_CONSUMPTION_EN`

Master flag: self-consumption is the **default fill** for slots not marked
`BAT_FIRST`, `BYPASS`, or `OUTPUT`.

## Whole-day band flags (`FUNC_LSP_WHOLE_*`)

These select which of the **three configurable time windows** apply for a given mode:

| Field | Mode |
|-------|------|
| `FUNC_LSP_WHOLE_BAT_FIRST_{1-3}_EN` | PV Charge Priority windows 1–3 |
| `FUNC_LSP_WHOLE_BYPASS_{1-3}_EN` | Bypass windows 1–3 |
| `FUNC_LSP_WHOLE_SELF_CONSUMPTION_{1-3}_EN` | Self Consumption windows 1–3 |
| `FUNC_LSP_WHOLE_DAY_SCHEDULE_EN` | Use whole-day schedule mode |

## Other `FUNC_LSP_*` master flags

| Field | Notes |
|-------|-------|
| `FUNC_LSP_CHARGE_PRIORITY_EN` | LSP-level charge priority enable |
| `FUNC_LSP_AC_CHARGE` | AC charge in LSP context |
| `FUNC_LSP_BAT_ACTIVATION_EN` | Battery activation in scheduler |
| `FUNC_LSP_BATT_VOLT_OR_SOC` | SOC vs voltage for LSP thresholds |
| `FUNC_LSP_FAN_CHECK_EN` | Fan check |
| `FUNC_LSP_ISO_EN` | ISO / ground fault |
| `FUNC_LSP_LCD_REMOTE_DIS_CHG_EN` | LCD remote discharge disable |
| `FUNC_LSP_SET_TO_STANDBY` | Standby in LSP context |

## Decoding example

From `4362830287` config — enabled `FUNC_LSP_BAT_FIRST_*` slots:

| Slot | Time |
|------|------|
| 1 | 00:00–00:30 |
| 4–5 | 01:30–02:30 |
| 17 | 08:00–08:30 |
| 19 | 09:00–09:30 |
| 37, 39 | 18:00–18:30, 19:00–19:30 |

Enabled `FUNC_LSP_BYPASS_*` on the same unit includes 16:00–20:00 (slots 33–40) plus
scattered morning slots — overlapping slot flags reflect how the working-mode timeline
was painted in Monitor Center.

## Tips for config diffs

1. **Group by mode family** — compare decoded time ranges, not 48 raw booleans.
2. **Check master enables** — `FUNC_FORCED_CHG_EN`, `FUNC_LSP_BYPASS_MODE_EN`, etc.
   may disagree with slot bitmaps (stale compiled schedule).
3. **Use full diff** — `eg4-config-diff.py` without `--flags-only` includes `LSP_`
   fields; default reports group them under `load-shedule (LSP_)`.
4. **Slot labels in diff output** — `eg4_config_labels.py` expands
   `FUNC_LSP_BAT_FIRST_N_EN` to include the time range when descriptions are loaded.

## Python helpers

```python
from eg4_config_labels import lsp_slot_time_range, describe_lsp_slot_field

describe_lsp_slot_field("FUNC_LSP_BAT_FIRST_17_EN")
# → "LSP slot 17 (08:00–08:30) — PV Charge Priority"

lsp_slot_time_range(17)
# → "08:00–08:30"
```

Summarize all enabled slots for one mode from a config snapshot:

```python
from eg4_config_lib import summarize_lsp_slots

summarize_lsp_slots(settings, "FUNC_LSP_BAT_FIRST_")
# → ['00:00–00:30', '01:30–02:30', ...]
```

## Peak Shaving time windows (`LSP_HOLD_DIS_CHG_POWER_TIME_*`)

Despite the `LSP_` prefix and internal register names (`disChgPowerTime*`), registers
**37–44** are **Peak Shaving Mode** schedule times in Monitor Center’s working-mode tab
(`workingMode2Read.js`). They are **not** the 48-slot LSP bitmap scheduler.

Master enable: **`FUNC_GRID_PEAK_SHAVING`**.

| Register field | Monitor Center role |
|--------------|---------------------|
| `LSP_HOLD_DIS_CHG_POWER_TIME_37` | Window 1 **start hour** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_38` | Window 1 **start minute** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_39` | Window 1 **end hour** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_40` | Window 1 **end minute** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_41` | Window 2 **start hour** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_42` | Window 2 **start minute** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_43` | Window 2 **end hour** |
| `LSP_HOLD_DIS_CHG_POWER_TIME_44` | Window 2 **end minute** |

Related thresholds (12K hold namespace):

| Field | Role |
|-------|------|
| `_12K_HOLD_GRID_PEAK_SHAVING_SOC` / `_SOC_2` | Stop SOC (%) per window |
| `_12K_HOLD_GRID_PEAK_SHAVING_VOLT` / `_VOLT_2` | Stop voltage (V) per window |
| `_12K_HOLD_GRID_PEAK_SHAVING_POWER` / `_POWER_2` | Discharge power (kW) per window |

### Decoding example (fleet diff)

When only hours differ in a diff report:

| Field | Meaning | Example values |
|-------|---------|----------------|
| `_37` | Window 1 start **hour** | 11 vs 15 vs 12 |
| `_39` | Window 1 end **hour** | 19 vs 20 |

With minutes at `00` on all units, decoded window 1 times:

| Inverter | Window 1 |
|----------|----------|
| `4362830287` | 11:00–19:00 |
| `4372830125`, `4502670584`, `4372830102` | 15:00–19:00 or 15:00–20:00 |
| `4494830269` | 12:00–19:00 |

`eg4-config-diff.py` appends a **Peak Shaving windows (decoded)** block under the
LSP section when any of these fields differ.

```python
from eg4_config_labels import peak_shaving_window_from_settings
from eg4_config_lib import summarize_peak_shaving_windows

peak_shaving_window_from_settings(settings, 1)
# → "11:00–19:00"

summarize_peak_shaving_windows(settings)
# → ['window 1: 11:00–19:00', ...]
```

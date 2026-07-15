# HOLD_MODEL register (device identity)

`HOLD_MODEL` is the packed firmware **MODEL** word (LuxPower Modbus registers 0–1).
Monitor Center exposes it as a hex string plus exploded `HOLD_MODEL_*` subfields in
config snapshots.

**This is device identity, not a user tuning parameter.** `config-push.py` treats
`HOLD_MODEL` as immutable alongside serial number and firmware code.

Sources: `eg4-bridge/doc/LXP_REGISTERS.txt`, Monitor Center HAR/API responses, scraped
`powerRating{N}_*Text` UI strings in `eg4-field-labels.json`.

## Raw `HOLD_MODEL` hex

| Hex | Decimal | Fleet example |
|-----|---------|---------------|
| `0x98640` | 624192 | EG4 **12KPV** units |
| `0x986C0` | 624320 | EG4 **18KPV** unit |

The 12K vs 18K difference is `0x80` (128) in the packed word and correlates with
`HOLD_MODEL_powerRating` **2 → 6**. The exact bit layout is not fully documented in
eg4-bridge (`LXP_REGISTERS.txt` lists subfield names but says decoding is incomplete).

Prefer the exploded subfields (especially `HOLD_MODEL_powerRating`) over hand-decoding
the hex.

## Subfields

| Field | Role | Enum / notes |
|-------|------|--------------|
| `HOLD_MODEL_powerRating` | Rated AC output tier | Product-specific table; see below |
| `HOLD_MODEL_batteryType` | Battery chemistry | `0` none, `1` lead-acid, `2` lithium |
| `HOLD_MODEL_lithiumType` | Lithium BMS / brand profile | Monitor Center “Lithium Brand / No comms” |
| `HOLD_MODEL_leadAcidType` | Lead-acid profile | When `batteryType` is lead-acid |
| `HOLD_MODEL_measurement` | Export/limit measurement | `0` meter, `1` CT |
| `HOLD_MODEL_meterType` | Meter phase | `0` 1-phase, `1` 3-phase |
| `HOLD_MODEL_meterBrand` | External meter brand | Eastron, WattNode, etc. |
| `HOLD_MODEL_wirelessMeter` | Wireless meter option | |
| `HOLD_MODEL_usVersion` | US-market hardware variant | `1` on US fleet units |
| `HOLD_MODEL_rule` | Grid interconnection rule | Region-specific (UL1741, HECO, …) |
| `HOLD_MODEL_ruleMask` | Active rule bitmask | |

`HOLD_MODEL_batteryType`, `measurement`, and `meterType` share labels with Monitor Center
`MODEL_BIT_*` dropdowns (see `docs/field-reference.md`).

## `HOLD_MODEL_powerRating`

Numeric index into a **product-line-specific** power table in Monitor Center JavaScript.
The runtime API also returns `powerRatingText` (e.g. `"8kW"`).

### EG4 12KPV / 18KPV fleet (12K profile)

Monitor Center uses the `powerRating{N}_12KText` strings. Confirmed on fleet HAR for
12KPV (`powerRating: 2` → `powerRatingText: "8kW"`).

| `powerRating` | Label (12K profile) | Fleet |
|---------------|---------------------|-------|
| 2 | 8 kW | Four **12KPV** inverters |
| 6 | 12 kW | **18KPV** `4502670584` |

Other indices (examples from scraped UI):

| Index | Label |
|-------|-------|
| 0 | 5 kW |
| 1 | 7.6 kW |
| 3 | 11.4 kW |
| 4 | 10 kW |
| 5 | 9.6 kW |
| 7 | 7 kW |

Different hardware lines use different suffixes (`_Flex100Text`, `_GEN3_Text`,
`_DefaultText`, …). Pass the snapshot `model` field (e.g. `12KPV`, `18KPV`) when
decoding.

## Fleet diff example

```
HOLD_MODEL — Packed MODEL register (device identity; immutable)
  …/4362830287 (12KPV): 0x98640 (624192; 8 kW)
  …/4502670584 (18KPV): 0x986C0 (624320; 12 kW)

HOLD_MODEL_powerRating — Rated AC output power tier
  …/4362830287 (12KPV): 2 (8 kW)
  …/4502670584 (18KPV): 6 (12 kW)
```

These differences reflect **hardware class** (12 kW vs 18 kW nameplate), not
misconfiguration. Do not attempt to align them across unlike models.

## Python helpers

```python
from eg4_config_labels import (
    power_rating_label,
    summarize_hold_model,
    value_description,
)

power_rating_label(2, model="12KPV")
# → "8 kW"

summarize_hold_model(settings, model="12KPV")
# → "0x98640 · 8 kW · Lithium · CT · US"

value_description(
    "HOLD_MODEL_powerRating", 2, model="12KPV"
)
# → "2 (8 kW)"
```

`eg4-config-diff.py` decodes `HOLD_MODEL` / `HOLD_MODEL_powerRating` in text output
when those fields differ.

## Related

- [field-reference.md](field-reference.md) — `MODEL_BIT_*` enum labels
- [lsp-schedule-fields.md](lsp-schedule-fields.md) — unrelated `LSP_*` scheduler fields
- `eg4-bridge/doc/LXP_REGISTERS.txt` — Modbus register map
- `config-push.py` — `IMMUTABLE_FIELDS` includes `HOLD_MODEL`

# EG4 Cloud Tools

CLI tools for managing EG4 inverter configurations via the
[EG4 Monitor Center](https://monitor.eg4electronics.com) web API.

## Setup

```bash
pip install requests pyyaml pandas openpyxl influxdb
```

Copy the sample config and fill in your credentials:

```bash
cp config.sample.yaml config.yaml
```

```yaml
eg4_monitor:
  username: "you@example.com"
  password: "your-password"
  # Optional: limit to specific inverters (omit to use all on your account)
  # inverters:
  #   - id: "1111111111"
  #   - id: "2222222222"

influxdb:
  host: "localhost"
  port: 8086
  database: "eg4_data"
```

## Tools

### eg4-config-fetch.py — Snapshot inverter configuration

Reads all configuration registers from your inverters and saves JSON snapshots.

```bash
# Fetch all configured inverters, save to configs/<timestamp>/
python3 eg4-config-fetch.py

# Fetch specific serials
python3 eg4-config-fetch.py --serial 1111111111 --serial 2222222222

# Fetch and immediately show differences
python3 eg4-config-fetch.py --compare

# Only show flag (FUNC_*/BIT_*) differences
python3 eg4-config-fetch.py --compare --flags-only

# Save to a specific directory
python3 eg4-config-fetch.py --output-dir configs/baseline
```

### eg4-config-diff.py — Compare inverter configurations

Diff saved snapshots or fetch live configs for comparison.

```bash
# Diff a saved snapshot directory
python3 eg4-config-diff.py configs/20260701_161931/

# Diff two individual config files
python3 eg4-config-diff.py --config configs/baseline/1111111111.json \
                           --config configs/baseline/2222222222.json

# Fetch live and diff in one step
python3 eg4-config-diff.py --fetch

# Include all sites, not just config.yaml inverters
python3 eg4-config-diff.py --fetch --all-sites

# Only flag differences, write JSON report
python3 eg4-config-diff.py --fetch --flags-only --output report.json

# Save fetched snapshots while diffing
python3 eg4-config-diff.py --fetch --save-dir configs/latest
```

### config-push.py — Push settings to inverters

Write configuration values back to inverters via the remoteSet API.

```bash
# Set a single flag
python3 config-push.py --serial 1111111111 --set FUNC_CHARGE_LAST=true

# Set multiple values
python3 config-push.py --serial 1111111111 \
    --set FUNC_CHARGE_LAST=true \
    --set BIT_AC_CHARGE_TYPE=1

# Apply an entire config snapshot
python3 config-push.py --serial 1111111111 --from-config configs/baseline/2222222222.json

# Apply only specific fields from a snapshot
python3 config-push.py --serial 1111111111 \
    --from-config configs/baseline/2222222222.json \
    --only FUNC_CHARGE_LAST,BIT_AC_CHARGE_TYPE

# Only push fields that differ from current state
python3 config-push.py --serial 1111111111 \
    --from-config configs/target.json \
    --diff-against configs/current/1111111111.json

# Preview without writing
python3 config-push.py --serial 1111111111 --set FUNC_CHARGE_LAST=true --dry-run

# Skip confirmation prompt
python3 config-push.py --serial 1111111111 --set FUNC_CHARGE_LAST=true -y
```

### eg4-parallel.py — Inspect parallel mode status

Query parallel group membership and runtime status.

```bash
# Show configured inverters
python3 eg4-parallel.py

# Include every inverter on every site
python3 eg4-parallel.py --all-sites

# Specific serials
python3 eg4-parallel.py --serial 1111111111

# Machine-readable output
python3 eg4-parallel.py --json
```

### eg4-extract-labels.py — Scrape field labels from Monitor Center

Extracts human-readable field names and enum values from the remoteSet HTML.

```bash
# Write eg4-field-labels.json (default)
python3 eg4-extract-labels.py

# Also generate markdown reference
python3 eg4-extract-labels.py --markdown docs/field-reference.md
```

### xls_to_influxdb.py — Export inverter data to InfluxDB

Downloads today's data export for configured inverters and writes to InfluxDB.

```bash
python3 xls_to_influxdb.py
```

## Project layout

```
eg4-config-fetch.py      CLI: snapshot inverter configs
eg4-config-diff.py       CLI: diff configs across inverters
config-push.py           CLI: push settings to inverters
eg4-parallel.py          CLI: inspect parallel group status
eg4-extract-labels.py    CLI: scrape field labels/enums
xls_to_influxdb.py       CLI + shared lib: auth, plant/inverter discovery, InfluxDB pipeline

eg4_config_fetch.py      Library: remoteRead API client
eg4_config_lib.py        Library: config load/save/compare/report
eg4_config_labels.py     Library: field descriptions, value labels, LSP decoding

eg4-field-labels.json    Scraped UI labels and enum mappings
eg4-field-descriptions.json  Hand-maintained field documentation
eg4-api.json             EG4 API schema (OpenAPI-style)
docs/                    Reference documentation
config.sample.yaml       Example configuration (copy to config.yaml)
```

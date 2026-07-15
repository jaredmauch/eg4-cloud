# EG4 Monitor Center Field Reference

Scraped from [https://monitor.eg4electronics.com/WManage/web/maintain/remoteSet](https://monitor.eg4electronics.com/WManage/web/maintain/remoteSet).

Regenerate with:

```bash
python3 eg4-extract-labels.py --markdown docs/field-reference.md
```

## LSP internal schedule fields

`FUNC_LSP_*` fields are firmware-internal Load Schedule Plan bitmaps. They are not
exposed as labeled controls in Monitor Center. See
[lsp-schedule-fields.md](lsp-schedule-fields.md) for the 48-slot model, `BAT_FIRST` /
`BYPASS` / `OUTPUT` families, and Monitor Center mappings.

## HOLD_MODEL (device identity)

`HOLD_MODEL` is the packed firmware model register; exploded subfields include
`HOLD_MODEL_powerRating` (nameplate kW tier). See
[hold-model-fields.md](hold-model-fields.md) for decoding `0x98640` vs `0x986C0` and
power-rating tables.

## Value labels (dropdown / enum fields)

These fields use numeric values in config snapshots. The labels below come from the Monitor Center UI.

### `BIT_AC_CHARGE_TYPE`

- **0**: Time (According to)
- **1**: SOC/Volt (According to)
- **2**: Time+SOC/Volt (According to)

### `BIT_LCD_TYPE`

- **0**: 0: FlexBOSS External Display
- **1**: 1: LCD Screen Kit

### `BIT_METER_PORT_REUSE_TYPE`

- **0**: Default
- **1**: AC couple

### `MODEL_BIT_BATTERY_TYPE`

- **0**: 0: No battery
- **1**: 1: Lead-acid
- **2**: 2: Lithium

### `MODEL_BIT_MEASUREMENT`

- **0**: 0: Meter
- **1**: 1: CT

### `MODEL_BIT_METER_TYPE`

- **0**: 0: 1 Phase Meter
- **1**: 1: 3 Phase Meter

### `acChargeBaseOn`

- **0**: Time (According to)
- **1**: SOC/Volt (According to)
- **2**: Time+SOC/Volt (According to)

### `acChargeBaseOnGen3`

- **0**: Disable
- **1**: Time (According to)
- **2**: Battery Voltage (According to)
- **3**: Battery SOC (According to)
- **4**: Battery Voltage and Time (According to)
- **5**: Battery SOC and Time (According to)

### `meterBrand1`

- **1**: 1: Rsvd
- **2**: 1: WattNode

## Function flags (FUNC_*)

- `FUNC_BAT_SHARED`: Parallel Setting Data Sync (`boolean`)
- `FUNC_BUZZER_EN`: Off-Grid Mode (`boolean`)
- `FUNC_CT_DIRECTION_REVERSED`: Meter Port Reuse (`boolean`)
- `FUNC_FEED_IN_GRID_EN`: PV Arc Fault Clear (`boolean`)
- `FUNC_GREEN_EN`: Restart Inverter (`boolean`)
- `FUNC_PARALLEL_DATA_SYNC_EN`: Set System Type (`boolean`)
- `FUNC_PV_ARC`: RSD (`boolean`)
- `FUNC_PV_ARC_FAULT_CLEAR`: PV Arc (`boolean`)
- `FUNC_PV_GRID_OFF_EN`: Seamless EPS switching (`boolean`)
- `FUNC_PV_SELL_TO_GRID_EN`: Forced Discharge Enable (`boolean`)
- `FUNC_RSD_DISABLE`: No Batteries (`boolean`)
- `FUNC_RUN_WITHOUT_GRID`: Grid Sell Back Power(kW) (`boolean`)
- `FUNC_RUN_WITHOUT_GRID_12K`: Buzzer Enable (`boolean`)
- `FUNC_SPORADIC_CHARGE`: AC Charge Enable
- `FUNC_SW_SEAMLESSLY_EN`: Power Backup (`boolean`)
- `FUNC_WATT_NODE_CT_DIRECTION_A`: CT A Amps(A)
- `FUNC_WATT_NODE_CT_DIRECTION_B`: CT B Amps(A)
- `FUNC_WATT_NODE_CT_DIRECTION_C`: CT C Amps(A)

## Bit fields (BIT_*)

- `BIT_AC_CHARGE_TYPE`: AC Charge Based On (`integer`)
- `BIT_CT_SAMPLE_RATIO`: CT Sample Ratio (`integer`)
- `BIT_LCD_TYPE`: LCD Type
- `BIT_METER_PORT_REUSE_TYPE`: Meter Port Reuse

## Hold registers (HOLD_*)

- `ASC_HOLD_ACCUMULATED_UNCALIBRATED_COUNT_DAYS`: Accumulated Uncalibrated Count(Days)
- `ASC_HOLD_CALIBRATION_PERIOD_DAYS`: Calibration Period(Days)
- `HOLD_AC_CHARGE_BATTERY_CURRENT`: AC Charge Battery Current(A) (`integer`)
- `HOLD_AC_CHARGE_END_BATTERY_VOLTAGE`: Backup Volt(V) (`number`)
- `HOLD_AC_CHARGE_END_BATTERY_VOLTAGE_1`: Stop AC Charge Volt 1(V)
- `HOLD_AC_CHARGE_END_BATTERY_VOLTAGE_2`: Stop AC Charge Volt 2(V)
- `HOLD_AC_CHARGE_POWER_CMD`: AC Charge Power(kW) (`number`)
- `HOLD_AC_CHARGE_POWER_CMD_1`: AC Charge Power 1(kW)
- `HOLD_AC_CHARGE_POWER_CMD_2`: AC Charge Power 2(kW)
- `HOLD_AC_CHARGE_SOC_LIMIT`: Backup SOC(%) (`integer`)
- `HOLD_AC_CHARGE_SOC_LIMIT_1`: Stop AC Charge SOC 1(%)
- `HOLD_AC_CHARGE_SOC_LIMIT_2`: Stop AC Charge SOC 2(%)
- `HOLD_AC_CHARGE_START_BATTERY_SOC`: Start AC Charge SOC(%) (`integer`)
- `HOLD_AC_CHARGE_START_BATTERY_SOC_1`: Start AC Charge SOC 1(%)
- `HOLD_AC_CHARGE_START_BATTERY_SOC_2`: Start AC Charge SOC 2(%)
- `HOLD_AC_CHARGE_START_BATTERY_VOLTAGE`: Start AC Charge Volt(V) (`number`)
- `HOLD_AC_CHARGE_START_BATTERY_VOLTAGE_1`: Start AC Charge Volt 1(V)
- `HOLD_AC_CHARGE_START_BATTERY_VOLTAGE_2`: Start AC Charge Volt 2(V)
- `HOLD_CT_POWER_OFFSET`: CT Power Offset(W) (?) (`integer`)
- `HOLD_DISCHG_CUT_OFF_SOC_EOD`: On-Grid Cut-Off SOC(%) (`integer`)
- `HOLD_EQUALIZATION_PERIOD`: Equalization Period(Days) (`integer`)
- `HOLD_EQUALIZATION_TIME`: Equalization Time(Hours) (`integer`)
- `HOLD_EQUALIZATION_VOLTAGE`: Equalization Voltage(V) (`number`)
- `HOLD_FEED_IN_GRID_POWER_PERCENT`: Grid Sell Back Power(kW) (`integer`)
- `HOLD_FLOATING_VOLTAGE`: Float Voltage(V) (`number`)
- `HOLD_FORCED_CHG_POWER_CMD`: PV Charge Power(kW) (`number`)
- `HOLD_FORCED_CHG_POWER_CMD_1`: PV Charge Power 1(kW)
- `HOLD_FORCED_CHG_POWER_CMD_2`: PV Charge Power 2(kW)
- `HOLD_FORCED_CHG_SOC_LIMIT`: PV Charge Priority Stop SOC(%) (`integer`)
- `HOLD_FORCED_CHG_SOC_LIMIT_1`: PV Charge Priority Stop SOC 1(%)
- `HOLD_FORCED_CHG_SOC_LIMIT_2`: PV Charge Priority Stop SOC 2(%)
- `HOLD_FORCED_DISCHARGE_START_HOUR`: Stop Discharge Volt 1(V) (`integer`)
- `HOLD_FORCED_DISCHG_POWER_CMD`: Forced Discharge Power 1(kW) (`number`)
- `HOLD_FORCED_DISCHG_SOC_LIMIT`: Stop Discharge SOC 1(%) (`integer`)
- `HOLD_FW_CODE`: LCD Version (`string`)
- `HOLD_GEN_START_HOUR_1`: Gen Time
- `HOLD_GEN_START_MINUTE_1`: Gen Time
- `HOLD_LCD_VERSION`: LCD Version
- `HOLD_LEAD_ACID_CHARGE_RATE`: Charge Current Limit(Adc) (`integer`)
- `HOLD_LEAD_ACID_CHARGE_VOLT_REF`: Absorb Voltage(V) (`number`)
- `HOLD_LEAD_ACID_DISCHARGE_CUT_OFF_VOLT`: Off-Grid Cut-Off Volt(V) (`number`)
- `HOLD_LEAD_ACID_DISCHARGE_RATE`: Discharge Current Limit(Adc) (`integer`)
- `HOLD_MAX_AC_INPUT_POWER`: Max. AC Input Power(kW) (`number`)
- `HOLD_MAX_GENERATOR_INPUT_POWER`: Gen Rated Power(kW) (`integer`)
- `HOLD_OFF_GRID_START_HOUR_1`: Off-Grid Mode
- `HOLD_ON_GRID_EOD_VOLTAGE`: On-Grid Cut-Off Volt(V) (`number`)
- `HOLD_PV_INPUT_MODE`: PV Input Mode (`integer`)
- `HOLD_P_TO_USER_START_DISCHG`: Start Discharge P_import(W)
- `HOLD_SET_COMPOSED_PHASE`: Set Composed Phase (`integer`)
- `HOLD_SET_MASTER_OR_SLAVE`: Set System Type (`integer`)
- `HOLD_SMART_LOAD_START_HOUR_1`: Start PV Power(kW)
- `HOLD_SOC_LOW_LIMIT_EPS_DISCHG`: Off-Grid Cut-Off SOC(%) (`integer`)
- `HOLD_START_PV_VOLT`: Start PV Volt(V) (`number`)
- `HOLD_SYSTEM_CHARGE_SOC_LIMIT`: System Charge SOC Limit(%) (`integer`)
- `HOLD_SYSTEM_CHARGE_VOLT_LIMIT`: System Charge Volt Limit(V) (`number`)
- `HOLD_TIME`: Time (`string`)
- `HOLD_VBAT_START_DERATING`: On Grid Discharge Derate Vbatt(V) (`integer`)
- `OFF_GRID_HOLD_GEN_CHG_END_SOC`: Charge End SOC(%) (`integer`)
- `OFF_GRID_HOLD_GEN_CHG_END_VOLT`: Charge End Volt(V) (`number`)
- `OFF_GRID_HOLD_GEN_CHG_START_SOC`: Charge Start SOC(%) (`integer`)
- `OFF_GRID_HOLD_GEN_CHG_START_VOLT`: Charge Start Volt(V) (`number`)
- `OFF_GRID_HOLD_MAX_GEN_CHG_BAT_CURR`: Batt Charge Current Limit(Adc) (`integer`)
- `_12K_HOLD_AC_COUPLE_END_SOC`: AC Couple End SOC(%) (`integer`)
- `_12K_HOLD_AC_COUPLE_END_VOLT`: AC Couple End Volt(V) (`number`)
- `_12K_HOLD_AC_COUPLE_START_SOC`: AC Couple Start SOC(%) (`integer`)
- `_12K_HOLD_AC_COUPLE_START_VOLT`: AC Couple Start Volt(V) (`number`)
- `_12K_HOLD_CHARGE_FIRST_VOLT`: PV Charge Priority Stop Volt(V)
- `_12K_HOLD_CHARGE_FIRST_VOLT_1`: PV Charge Priority Stop Volt 2(V)
- `_12K_HOLD_CHARGE_FIRST_VOLT_2`: PV Charge Priority Stop Volt 1(V)
- `_12K_HOLD_GEN_COOL_DOWN_TIME`: Generator Cool-Down Time(Min)
- `_12K_HOLD_GRID_TYPE`: Grid Type
- `_12K_HOLD_LEAD_CAPACITY`: Lead-acid Capacity(Ah)
- `_12K_HOLD_SMART_LOAD_END_SOC`: Smart Load End SOC(%) (`integer`)
- `_12K_HOLD_SMART_LOAD_END_VOLT`: Smart Load End Volt(V) (`number`)
- `_12K_HOLD_SMART_LOAD_START_SOC`: Smart Load Start SOC(%) (`integer`)
- `_12K_HOLD_SMART_LOAD_START_VOLT`: Smart Load Start Volt(V) (`number`)
- `_12K_HOLD_START_PV_POWER`: Start PV Power(kW) (`number`)
- `_12K_HOLD_STOP_DISCHG_VOLT`: Stop Discharge Volt 1(V)
- `_12K_HOLD_WATT_NODE_CT_AMPS_A`: CT A Amps(A)
- `_12K_HOLD_WATT_NODE_CT_AMPS_B`: CT B Amps(A)
- `_12K_HOLD_WATT_NODE_CT_AMPS_C`: CT C Amps(A)

## Model bit fields

- `MODEL_BIT_BATTERY_TYPE`: Battery Type
- `MODEL_BIT_LITHIUM_TYPE`: Lithium Brand / No comms
- `MODEL_BIT_MEASUREMENT`: Measurement
- `MODEL_BIT_METER_BRAND`: Meter Brand
- `MODEL_BIT_METER_TYPE`: Meter Type

## Boolean flags without dedicated UI labels

Many `FUNC_*` toggles only show Enable/Disable buttons in the UI. When no label is listed above, refer to the field name or the [EG4 API documentation](https://eg4electronics.com/api-documentation/).

### FUNC_* fields from official API schema

- `FUNC_ACTIVE_POWER_LIMIT_MODE` (boolean)
- `FUNC_AC_CHARGE` (boolean)
- `FUNC_AC_COUPLE_DARK_START_EN` (boolean)
- `FUNC_AC_COUPLE_EN_1` (boolean)
- `FUNC_AC_COUPLE_EN_2` (boolean)
- `FUNC_AC_COUPLE_EN_3` (boolean)
- `FUNC_AC_COUPLE_EN_4` (boolean)
- `FUNC_AC_COUPLING_FUNCTION` (boolean)
- `FUNC_ANTI_ISLAND_EN` (boolean)
- `FUNC_BATTERY_BACKUP_CTRL` (boolean)
- `FUNC_BATTERY_CALIBRATION_EN` (boolean)
- `FUNC_BATTERY_ECO_EN` (boolean)
- `FUNC_BAT_CHARGE_CONTROL` (boolean)
- `FUNC_BAT_DISCHARGE_CONTROL` (boolean)
- `FUNC_CHARGE_LAST` (boolean)
- `FUNC_DCI_EN` (boolean)
- `FUNC_DRMS_EN` (boolean)
- `FUNC_ENERTEK_WORKING_MODE` (boolean)
- `FUNC_EPS_EN` (boolean)
- `FUNC_FAN_SPEED_SLOPE_CTRL_1` (boolean)
- `FUNC_FAN_SPEED_SLOPE_CTRL_2` (boolean)
- `FUNC_FAN_SPEED_SLOPE_CTRL_3` (boolean)
- `FUNC_FAN_SPEED_SLOPE_CTRL_4` (boolean)
- `FUNC_FAN_SPEED_SLOPE_CTRL_5` (boolean)
- `FUNC_FORCED_CHG_EN` (boolean)
- `FUNC_FORCED_DISCHG_EN` (boolean)
- `FUNC_GEN_PEAK_SHAVING` (boolean)
- `FUNC_GFCI_EN` (boolean)
- `FUNC_GO_TO_OFFGRID` (boolean)
- `FUNC_GRID_CT_CONNECTION_EN` (boolean)
- `FUNC_GRID_ON_POWER_SS_EN` (boolean)
- `FUNC_GRID_PEAK_SHAVING` (boolean)
- `FUNC_HALF_HOUR_AC_CHG_START_EN` (boolean)
- `FUNC_ISO_EN` (boolean)
- `FUNC_LSP_AC_CHARGE` (boolean)
- `FUNC_LSP_BATT_VOLT_OR_SOC` (boolean)
- `FUNC_LSP_BAT_ACTIVATION_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_10_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_11_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_12_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_13_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_14_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_15_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_16_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_17_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_18_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_19_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_1_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_20_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_21_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_22_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_23_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_24_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_25_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_26_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_27_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_28_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_29_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_2_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_30_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_31_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_32_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_33_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_34_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_35_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_36_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_37_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_38_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_39_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_3_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_40_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_41_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_42_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_43_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_44_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_45_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_46_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_47_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_48_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_4_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_5_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_6_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_7_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_8_EN` (boolean)
- `FUNC_LSP_BAT_FIRST_9_EN` (boolean)
- `FUNC_LSP_BYPASS_10_EN` (boolean)
- `FUNC_LSP_BYPASS_11_EN` (boolean)
- `FUNC_LSP_BYPASS_12_EN` (boolean)
- `FUNC_LSP_BYPASS_13_EN` (boolean)
- `FUNC_LSP_BYPASS_14_EN` (boolean)
- `FUNC_LSP_BYPASS_15_EN` (boolean)
- `FUNC_LSP_BYPASS_16_EN` (boolean)
- `FUNC_LSP_BYPASS_17_EN` (boolean)
- `FUNC_LSP_BYPASS_18_EN` (boolean)
- `FUNC_LSP_BYPASS_19_EN` (boolean)
- `FUNC_LSP_BYPASS_1_EN` (boolean)
- `FUNC_LSP_BYPASS_20_EN` (boolean)
- `FUNC_LSP_BYPASS_21_EN` (boolean)
- `FUNC_LSP_BYPASS_22_EN` (boolean)
- `FUNC_LSP_BYPASS_23_EN` (boolean)
- `FUNC_LSP_BYPASS_24_EN` (boolean)
- `FUNC_LSP_BYPASS_25_EN` (boolean)
- `FUNC_LSP_BYPASS_26_EN` (boolean)
- `FUNC_LSP_BYPASS_27_EN` (boolean)
- `FUNC_LSP_BYPASS_28_EN` (boolean)
- `FUNC_LSP_BYPASS_29_EN` (boolean)
- `FUNC_LSP_BYPASS_2_EN` (boolean)
- `FUNC_LSP_BYPASS_30_EN` (boolean)
- `FUNC_LSP_BYPASS_31_EN` (boolean)
- `FUNC_LSP_BYPASS_32_EN` (boolean)
- `FUNC_LSP_BYPASS_33_EN` (boolean)
- `FUNC_LSP_BYPASS_34_EN` (boolean)
- `FUNC_LSP_BYPASS_35_EN` (boolean)
- `FUNC_LSP_BYPASS_36_EN` (boolean)
- `FUNC_LSP_BYPASS_37_EN` (boolean)
- `FUNC_LSP_BYPASS_38_EN` (boolean)
- `FUNC_LSP_BYPASS_39_EN` (boolean)
- `FUNC_LSP_BYPASS_3_EN` (boolean)
- `FUNC_LSP_BYPASS_40_EN` (boolean)
- `FUNC_LSP_BYPASS_41_EN` (boolean)
- `FUNC_LSP_BYPASS_42_EN` (boolean)
- `FUNC_LSP_BYPASS_43_EN` (boolean)
- `FUNC_LSP_BYPASS_44_EN` (boolean)
- `FUNC_LSP_BYPASS_45_EN` (boolean)
- `FUNC_LSP_BYPASS_46_EN` (boolean)
- `FUNC_LSP_BYPASS_47_EN` (boolean)
- `FUNC_LSP_BYPASS_48_EN` (boolean)
- `FUNC_LSP_BYPASS_4_EN` (boolean)
- `FUNC_LSP_BYPASS_5_EN` (boolean)
- `FUNC_LSP_BYPASS_6_EN` (boolean)
- `FUNC_LSP_BYPASS_7_EN` (boolean)
- `FUNC_LSP_BYPASS_8_EN` (boolean)
- `FUNC_LSP_BYPASS_9_EN` (boolean)
- `FUNC_LSP_BYPASS_EN` (boolean)
- `FUNC_LSP_BYPASS_MODE_EN` (boolean)
- `FUNC_LSP_CHARGE_PRIORITY_EN` (boolean)
- `FUNC_LSP_FAN_CHECK_EN` (boolean)
- `FUNC_LSP_ISO_EN` (boolean)
- `FUNC_LSP_LCD_REMOTE_DIS_CHG_EN` (boolean)
- `FUNC_LSP_OUTPUT_10_EN` (boolean)
- `FUNC_LSP_OUTPUT_11_EN` (boolean)
- `FUNC_LSP_OUTPUT_12_EN` (boolean)
- `FUNC_LSP_OUTPUT_1_EN` (boolean)
- `FUNC_LSP_OUTPUT_2_EN` (boolean)
- `FUNC_LSP_OUTPUT_3_EN` (boolean)
- `FUNC_LSP_OUTPUT_4_EN` (boolean)
- `FUNC_LSP_OUTPUT_5_EN` (boolean)
- `FUNC_LSP_OUTPUT_6_EN` (boolean)
- `FUNC_LSP_OUTPUT_7_EN` (boolean)
- `FUNC_LSP_OUTPUT_8_EN` (boolean)
- `FUNC_LSP_OUTPUT_9_EN` (boolean)
- `FUNC_LSP_SELF_CONSUMPTION_EN` (boolean)
- `FUNC_LSP_SET_TO_STANDBY` (boolean)
- `FUNC_LSP_WHOLE_BAT_FIRST_1_EN` (boolean)
- `FUNC_LSP_WHOLE_BAT_FIRST_2_EN` (boolean)
- `FUNC_LSP_WHOLE_BAT_FIRST_3_EN` (boolean)
- `FUNC_LSP_WHOLE_BYPASS_1_EN` (boolean)
- `FUNC_LSP_WHOLE_BYPASS_2_EN` (boolean)
- `FUNC_LSP_WHOLE_BYPASS_3_EN` (boolean)
- `FUNC_LSP_WHOLE_DAY_SCHEDULE_EN` (boolean)
- `FUNC_LSP_WHOLE_SELF_CONSUMPTION_1_EN` (boolean)
- `FUNC_LSP_WHOLE_SELF_CONSUMPTION_2_EN` (boolean)
- `FUNC_LSP_WHOLE_SELF_CONSUMPTION_3_EN` (boolean)
- `FUNC_LVRT_EN` (boolean)
- `FUNC_MICRO_GRID_EN` (boolean)
- `FUNC_MIDBOX_EN` (boolean)
- `FUNC_NEUTRAL_DETECT_EN` (boolean)
- `FUNC_N_PE_CONNECT_INNER_EN` (boolean)
- `FUNC_ON_GRID_ALWAYS_ON` (boolean)
- `FUNC_OVF_LOAD_DERATE_EN` (boolean)
- `FUNC_QUICK_CHARGE_CTRL` (boolean)
- `FUNC_RETAIN_SHUTDOWN` (boolean)
- `FUNC_RETAIN_STANDBY` (boolean)
- `FUNC_SET_TO_STANDBY` (boolean)
- `FUNC_SHEDDING_MODE_EN_1` (boolean)
- `FUNC_SHEDDING_MODE_EN_2` (boolean)
- `FUNC_SHEDDING_MODE_EN_3` (boolean)
- `FUNC_SHEDDING_MODE_EN_4` (boolean)
- `FUNC_SMART_LOAD_ENABLE` (boolean)
- `FUNC_SMART_LOAD_EN_1` (boolean)
- `FUNC_SMART_LOAD_EN_2` (boolean)
- `FUNC_SMART_LOAD_EN_3` (boolean)
- `FUNC_SMART_LOAD_EN_4` (boolean)
- `FUNC_SMART_LOAD_GRID_ON_1` (boolean)
- `FUNC_SMART_LOAD_GRID_ON_2` (boolean)
- `FUNC_SMART_LOAD_GRID_ON_3` (boolean)
- `FUNC_SMART_LOAD_GRID_ON_4` (boolean)
- `FUNC_TAKE_LOAD_TOGETHER` (boolean)
- `FUNC_TOTAL_LOAD_COMPENSATION_EN` (boolean)
- `FUNC_TRIP_TIME_UNIT` (boolean)
- `FUNC_WATT_VOLT_EN` (boolean)

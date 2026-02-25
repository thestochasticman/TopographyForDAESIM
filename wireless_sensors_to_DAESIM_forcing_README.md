# Wireless Sensors to DAESIM Forcing Conversion

Converts wireless sensor data (Phenode) to DAESIM forcing format.

## Usage

```python
from wireless_sensors_to_DAESIM_forcing import lux_to_srad_mj_per_day, convert_wireless_sensor_data_to_daesim_forcing

# Convert a sensor CSV file
convert_wireless_sensor_data_to_daesim_forcing('/path/to/wireless-sensor-data.csv')

# Or use the lux conversion function directly
from pandas import read_csv
df = read_csv('sensor-data.csv', encoding='latin-1')
df_daily_srad = lux_to_srad_mj_per_day(df)
```

## Functions

### `lux_to_srad_mj_per_day(df, lux_col, time_col)`

Converts instantaneous lux readings to daily solar radiation (SRAD) in MJ/m²/day.

**Parameters:**
- `df`: DataFrame with lux and time columns
- `lux_col`: Name of illuminance column (default: `'Illuminance (lux)'`)
- `time_col`: Name of timestamp column (default: `'Time'`)

**Returns:** DataFrame with `Date` and `SRAD` columns

**Conversion method:**
1. Lux → W/m²: divide by 120 (approximation for sunlight)
2. Integrate irradiance over time intervals
3. Sum daily to get MJ/m²/day

### `convert_wireless_sensor_data_to_daesim_forcing(sensor_file_path)`

Reads a wireless sensor CSV and extracts relevant columns for DAESIM forcing.

**Input columns used:**
- `Illuminance (lux)` - Light intensity
- `TEROS-12-Calibrated VWC 1 (%)` - Volumetric water content sensor 1
- `TEROS-12-Calibrated VWC 2 (%)` - Volumetric water content sensor 2

## Notes

- Input CSV files use Latin-1 encoding (contains degree symbols)
- Sensor readings are typically at 10-20 minute intervals
- SRAD output units match DAESIM forcing format (MJ/m²/day)

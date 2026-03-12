from pathlib import Path
import numpy as np
from pandas import read_csv, to_datetime


SOIL_DEPTH_MM = 100  # Each sensor represents 100mm of soil profile
WIRELESS_SENSORS_DIR = Path('/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/wireless-sensors')
PHENODE_DATA_PATH = '/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/phenode_sensor_data.csv'
OUTPUT_DIR = Path('/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/forcing')


def vwc_pct_to_mm(vwc_pct, depth_mm=SOIL_DEPTH_MM):
    """Convert VWC percentage to soil moisture in mm."""
    return vwc_pct * depth_mm / 100


def process_wireless_sensor(sensor_path):
    """
    Process a wireless sensor CSV to get daily soil moisture in mm.
    Returns a DataFrame with Date and Soil moisture columns.
    """
    df = read_csv(sensor_path, index_col=0, parse_dates=True)

    # Unify VWC columns (early data in %, later data as decimal)
    df['VWC_1_pct'] = df.get('Soil Moisture 1 (VWC)', np.nan)
    if 'Calibrated Counts VWC 1' in df.columns:
        df['VWC_1_pct'] = df['VWC_1_pct'].fillna(df['Calibrated Counts VWC 1'] * 100)

    df['VWC_2_pct'] = df.get('Soil Moisture 2 (VWC)', np.nan)
    if 'Calibrated Counts VWC 2' in df.columns:
        df['VWC_2_pct'] = df['VWC_2_pct'].fillna(df['Calibrated Counts VWC 2'] * 100)

    # Filter invalid values (VWC must be 0-100%)
    df.loc[df['VWC_1_pct'] > 100, 'VWC_1_pct'] = np.nan
    df.loc[df['VWC_2_pct'] > 100, 'VWC_2_pct'] = np.nan
    df.loc[df['VWC_1_pct'] < 0, 'VWC_1_pct'] = np.nan
    df.loc[df['VWC_2_pct'] < 0, 'VWC_2_pct'] = np.nan

    # Convert to mm
    df['SM_1_mm'] = vwc_pct_to_mm(df['VWC_1_pct'])
    df['SM_2_mm'] = vwc_pct_to_mm(df['VWC_2_pct'])

    # Total soil moisture (200mm profile)
    df['Soil moisture'] = df['SM_1_mm'] + df['SM_2_mm']

    # Extract date and aggregate to daily mean
    df['Date'] = df.index.date
    daily = df.groupby('Date').agg({'Soil moisture': 'mean'}).reset_index()

    return daily


def phenode_to_daesim_forcing(input_path, output_path=None, lat_filter=None, lon_filter=None):
    """
    Convert phenode sensor data to DAESIM forcing format.

    Aggregates sub-daily observations to daily values matching DAESIM format:
    - Date: YYYY-MM-DD
    - Precipitation: daily sum (mm)
    - Minimum temperature: daily min (°C)
    - Maximum temperature: daily max (°C)
    - VPeff: daily mean vapor pressure (kPa)
    - Uavg: daily mean wind speed (m/s)
    """
    df = read_csv(input_path, parse_dates=['Time'])

    # Filter by location if specified
    if lat_filter is not None and lon_filter is not None:
        df = df[(df['Latitude'].round(2) == round(lat_filter, 2)) &
                (df['Longitude'].round(2) == round(lon_filter, 2))]

    # Replace -9999 missing data flags with NaN
    df = df.replace(-9999, np.nan)

    # Extract date from timestamp
    df['Date'] = df['Time'].dt.date

    # Use Air Temperature Secondary, fall back to Primary if missing
    df['Temperature'] = df['Air Temperature Secondary (°C)'].fillna(
        df['Air Temperature Primary (°C)']
    )

    # Aggregate to daily values
    daily = df.groupby('Date').agg({
        'Calculated Fallen Rain (mm)': 'sum',
        'Temperature': ['min', 'max'],
        'Vapor Pressure (kPa)': 'mean',
        'Wind Speed (m/s)': 'mean',
    })

    # Flatten column names
    daily.columns = ['Precipitation', 'Minimum temperature', 'Maximum temperature',
                     'VPeff', 'Uavg']
    daily = daily.reset_index()

    # Add empty columns to match DAESIM format (Runoff calculated later per sensor)
    daily['Runoff'] = np.nan
    daily['Soil moisture'] = None
    daily['Vegetation growth'] = None
    daily['Vegetation leaf area'] = None
    daily['SRAD'] = None

    # Reorder columns to match DAESIM format
    daily = daily[['Date', 'Precipitation', 'Runoff', 'Minimum temperature',
                   'Maximum temperature', 'Soil moisture', 'Vegetation growth',
                   'Vegetation leaf area', 'VPeff', 'Uavg', 'SRAD']]

    if output_path:
        daily.to_csv(output_path)
        print(f"Saved to {output_path}")

    return daily


def create_forcing_per_sensor(phenode_path=PHENODE_DATA_PATH,
                               sensors_dir=WIRELESS_SENSORS_DIR,
                               output_dir=OUTPUT_DIR,
                               lat_filter=-35.12,
                               lon_filter=149.02):
    """
    Create a DAESIM forcing file for each wireless sensor.
    Combines common phenode data with sensor-specific soil moisture.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get common phenode data (without soil moisture)
    phenode_daily = phenode_to_daesim_forcing(
        phenode_path,
        lat_filter=lat_filter,
        lon_filter=lon_filter,
    )
    # Drop the empty soil moisture column - we'll add sensor-specific data
    phenode_daily = phenode_daily.drop(columns=['Soil moisture'])

    sensors_dir = Path(sensors_dir)
    sensor_files = list(sensors_dir.glob('WS-*.csv'))

    print(f"Processing {len(sensor_files)} sensors...")

    for sensor_file in sensor_files:
        sensor_id = sensor_file.stem  # e.g., 'WS-f575dcdea0dc'

        # Get soil moisture from this sensor
        try:
            soil_daily = process_wireless_sensor(sensor_file)
        except Exception as e:
            print(f"  {sensor_id}: Error processing - {e}")
            continue

        if soil_daily['Soil moisture'].isna().all():
            print(f"  {sensor_id}: No valid soil moisture data, skipping")
            continue

        # Merge phenode data with sensor soil moisture
        forcing = phenode_daily.merge(soil_daily, on='Date', how='left')

        # Calculate runoff: Precipitation - Gain in soil moisture
        # Gain = today's soil moisture - yesterday's soil moisture
        forcing['SM_gain'] = forcing['Soil moisture'].diff()
        # Runoff only occurs when there's rain and SM gain is less than rain
        # Runoff = max(0, Precipitation - SM_gain) on rainy days
        # If SM_gain is negative (drying), runoff = precipitation (no infiltration)
        forcing['Runoff'] = np.where(
            forcing['Precipitation'] > 0,
            np.maximum(0, forcing['Precipitation'] - forcing['SM_gain'].clip(lower=0)),
            np.nan  # No runoff calculation on dry days
        )
        forcing = forcing.drop(columns=['SM_gain'])

        # Reorder columns to match DAESIM format
        forcing = forcing[['Date', 'Precipitation', 'Runoff', 'Minimum temperature',
                           'Maximum temperature', 'Soil moisture', 'Vegetation growth',
                           'Vegetation leaf area', 'VPeff', 'Uavg', 'SRAD']]

        # Save to file
        output_path = output_dir / f'{sensor_id}_DAESim_forcing.csv'
        forcing.to_csv(output_path)

        # Report stats
        valid_sm = forcing['Soil moisture'].notna().sum()
        print(f"  {sensor_id}: {len(forcing)} days, {valid_sm} with soil moisture -> {output_path.name}")

    print("Done!")


if __name__ == '__main__':
    create_forcing_per_sensor()

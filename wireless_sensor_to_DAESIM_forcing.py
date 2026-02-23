from os.path import exists
from pandas import read_csv

SOIL_DEPTH_MM = 100  # Each sensor represents 100mm of soil profile


def vwc_pct_to_mm(vwc_pct, depth_mm=SOIL_DEPTH_MM):
    """Convert VWC percentage to soil moisture in mm."""
    return vwc_pct * depth_mm / 100


def unify_vwc_columns(df):
    """
    Unify soil moisture data from both column formats.
    Early data: 'Soil Moisture 1/2 (VWC)' in percentage (e.g., 20 = 20%)
    Later data: 'Calibrated Counts VWC 1/2' as decimal fraction (e.g., 0.20 = 20%)
    """
    # Convert calibrated counts (decimal) to percentage, use where VWC columns are missing
    df['VWC_1_pct'] = df['Soil Moisture 1 (VWC)'].fillna(
        df['Calibrated Counts VWC 1'] * 100
    )
    df['VWC_2_pct'] = df['Soil Moisture 2 (VWC)'].fillna(
        df['Calibrated Counts VWC 2'] * 100
    )

    # Filter out invalid values (VWC must be 0-100%)
    df.loc[df['VWC_1_pct'] > 100, 'VWC_1_pct'] = None
    df.loc[df['VWC_2_pct'] > 100, 'VWC_2_pct'] = None
    df.loc[df['VWC_1_pct'] < 0, 'VWC_1_pct'] = None
    df.loc[df['VWC_2_pct'] < 0, 'VWC_2_pct'] = None

    return df

if __name__ == '__main__':
    sensor_data = read_csv(
        '/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/wireless-sensors/WS-f575dcdea0dc.csv',
        index_col=0,
        parse_dates=True
    )

    sensor_data = unify_vwc_columns(sensor_data)

    # Convert VWC (%) to soil moisture (mm)
    sensor_data['Soil Moisture 1 (mm)'] = vwc_pct_to_mm(sensor_data['VWC_1_pct'])
    sensor_data['Soil Moisture 2 (mm)'] = vwc_pct_to_mm(sensor_data['VWC_2_pct'])

    # Total soil moisture for 200mm profile (both sensors combined)
    sensor_data['Soil Moisture Total (mm)'] = (
        sensor_data['Soil Moisture 1 (mm)'] + sensor_data['Soil Moisture 2 (mm)']
    )

    print(sensor_data[['Soil Moisture 1 (mm)', 'Soil Moisture 2 (mm)', 'Soil Moisture Total (mm)']].describe())

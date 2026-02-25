from pandas import read_csv, to_datetime, DataFrame

def lux_to_mj_per_m2_per_day(df: DataFrame, lux_col: str = 'Illuminance (lux)', time_col: str = 'Time') -> DataFrame:
    """
    Convert instantaneous lux readings to daily SRAD in MJ/m²/day.

    Conversion: lux -> W/m² (÷120 for sunlight) -> integrate over time -> MJ/m²/day
    """
    df = df.copy()
    df[time_col] = to_datetime(df[time_col])

    # Convert lux to W/m² (for sunlight: W/m² ≈ lux / 120)
    df['Irradiance (W/m2)'] = df[lux_col] / 120

    # Calculate time difference between readings in seconds
    df['dt_seconds'] = df[time_col].diff().dt.total_seconds().fillna(600)  # assume 10 min for first reading

    # Calculate energy per interval in MJ/m² (W/m² * seconds / 1e6)
    df['Energy (MJ/m2)'] = df['Irradiance (W/m2)'] * df['dt_seconds'] / 1e6

    # Group by date and sum to get daily SRAD in MJ/m²/day
    df['Date'] = df[time_col].dt.date
    df_daily = df.groupby('Date')['Energy (MJ/m2)'].sum().reset_index()
    df_daily.rename(columns={'Energy (MJ/m2)': 'SRAD'}, inplace=True)

    return df_daily

def convert_wireless_sensor_data_to_daesim_forcing(sensor_file_path: str):
    df_sensors = read_csv(sensor_file_path, encoding='latin-1')
    df_sensors = df_sensors[['Illuminance (lux)','TEROS-12-Calibrated VWC 1 (%)', 'TEROS-12-Calibrated VWC 2 (%)']]
    print(df_sensors)
    
if __name__ == '__main__':
    convert_wireless_sensor_data_to_daesim_forcing('/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/wireless-sensor-data.csv')
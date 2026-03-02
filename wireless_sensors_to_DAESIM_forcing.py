from pandas import read_csv, to_datetime, DataFrame

SOIL_DEPTH_MM = 100  # Each sensor represents 100mm of soil profile


def vwc_pct_to_mm(vwc_pct, depth_mm=SOIL_DEPTH_MM):
    """Convert VWC percentage to soil moisture in mm."""
    return vwc_pct * depth_mm / 100


def unify_vwc_columns(df):
    """
    Extract and validate VWC data from TEROS-12 calibrated columns.
    Data is already in percentage format (e.g., 12.56 = 12.56%).
    """
    df['VWC_1_pct'] = df['TEROS-12-Calibrated VWC 1 (%)'].copy()
    df['VWC_2_pct'] = df['TEROS-12-Calibrated VWC 2 (%)'].copy()

    # Filter out invalid values (VWC must be 0-100%)
    df.loc[df['VWC_1_pct'] > 100, 'VWC_1_pct'] = None
    df.loc[df['VWC_2_pct'] > 100, 'VWC_2_pct'] = None
    df.loc[df['VWC_1_pct'] < 0, 'VWC_1_pct'] = None
    df.loc[df['VWC_2_pct'] < 0, 'VWC_2_pct'] = None

    return df


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


    
if __name__ == '__main__':

    from matplotlib import pyplot as plt
    
    # df = convert_wireless_sensor_data_to_daesim_forcing('/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/wireless-sensor-data.csv')
    df = read_csv('/borevitz_projects/data/Phenode/ANU_4_All_Phenode_Data/wireless-sensor-data.csv', encoding='latin-1')
    sensors = df['Sensor'].unique().tolist()
    for sensor in sensors:
        sensor_df = df[df['Sensor'] == sensor]

        columns = [
            'Sensor',
            'Time',
            'TEROS-12-Calibrated VWC 1 (%)',
            'TEROS-12-Calibrated VWC 2 (%)',
            'Illuminance (lux)'
        ]
        sensor_df = sensor_df[columns]
        print(sensor_df)
        sensor_df = lux_to_mj_per_m2_per_day(sensor_df, lux_col='Illuminance (lux)', time_col='Time')
        # plt.hist(sensor_df['SRAD'], bins=range(0, int(sensor_df['SRAD'].max()) + 5, 5))
        # plt.show()
        plt.plot(sensor_df['Date'], sensor_df['SRAD'])
        plt.xlabel('Date')
        plt.ylabel('SRAD (MJ/m²/day)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        break
    # print(df)
    
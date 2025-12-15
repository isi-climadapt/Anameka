"""
Convert CMIP6 daily CSV files to APSIM MET format.
Combines tasmax, tasmin, and pr files into MET format.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime

# Configuration
INPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka"
LATITUDE = -31.75
LONGITUDE = 117.5999984741211

SCENARIOS = ['SSP585', 'SSP245']
BASE_NAME = "Anameka South_ACCESS CM2"


def calculate_tav_amp(df):
    """
    Calculate annual average temperature (tav) and annual amplitude (amp).
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'date' as index and 'maxt' and 'mint' columns
    
    Returns:
    --------
    tuple: (tav, amp)
        tav: Annual average ambient temperature
        amp: Annual amplitude in mean monthly temperature
    """
    # Calculate daily mean temperature
    df = df.copy()
    df['tmean'] = (df['maxt'] + df['mint']) / 2.0
    
    # Calculate monthly means
    df['year'] = df.index.year
    df['month'] = df.index.month
    monthly_means = df.groupby(['year', 'month'])['tmean'].mean()
    
    # Calculate overall annual average (tav)
    tav = df['tmean'].mean()
    
    # Calculate annual amplitude (amp)
    # Average of all January means minus average of all July means, divided by 2
    jan_means = monthly_means[monthly_means.index.get_level_values('month') == 1].mean()
    jul_means = monthly_means[monthly_means.index.get_level_values('month') == 7].mean()
    amp = (jan_means - jul_means) / 2.0
    
    return tav, amp


def create_met_file(tasmax_df, tasmin_df, pr_df, scenario, output_dir, latitude, longitude):
    """
    Create MET format file from tasmax, tasmin, and pr DataFrames.
    
    Parameters:
    -----------
    tasmax_df : pd.DataFrame
        DataFrame with date and value columns for maximum temperature
    tasmin_df : pd.DataFrame
        DataFrame with date and value columns for minimum temperature
    pr_df : pd.DataFrame
        DataFrame with date and value columns for precipitation
    scenario : str
        Scenario name (SSP585 or SSP245)
    output_dir : str
        Output directory path
    latitude : float
        Latitude in decimal degrees
    longitude : float
        Longitude in decimal degrees
    """
    # Merge all dataframes on date
    merged = tasmax_df.copy()
    merged = merged.rename(columns={'value': 'maxt'})
    merged['date'] = pd.to_datetime(merged['date'])
    
    # Merge tasmin
    tasmin_df['date'] = pd.to_datetime(tasmin_df['date'])
    merged = merged.merge(tasmin_df[['date', 'value']], on='date', how='outer')
    merged = merged.rename(columns={'value': 'mint'})
    
    # Merge pr (precipitation/rain)
    pr_df['date'] = pd.to_datetime(pr_df['date'])
    merged = merged.merge(pr_df[['date', 'value']], on='date', how='outer')
    merged = merged.rename(columns={'value': 'rain'})
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    # Calculate tav and amp
    merged_temp = merged[['date', 'maxt', 'mint']].copy()
    merged_temp = merged_temp.set_index('date')
    # Ensure date index is datetime
    merged_temp.index = pd.to_datetime(merged_temp.index)
    tav, amp = calculate_tav_amp(merged_temp)
    
    # Create year and day columns
    merged['year'] = merged['date'].dt.year
    merged['day'] = merged['date'].dt.dayofyear
    
    # Add empty columns for radn, evap, vp, code
    merged['radn'] = ''  # Will be filled later
    merged['evap'] = ''  # Leave blank
    merged['vp'] = ''    # Leave blank
    merged['code'] = ''  # Leave blank
    
    # Select and order columns for MET format
    met_data = merged[['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'evap', 'vp', 'code']].copy()
    
    # Prepare header
    current_date = datetime.now().strftime('%Y%m%d')
    
    header = f"""[weather.met.weather]
!Your Ref:  "
latitude = {latitude:.2f}  (DECIMAL DEGREES)
longitude =  {longitude:.2f}  (DECIMAL DEGREES)
tav = {tav:.2f} (oC) ! Annual average ambient temperature.
amp = {amp:.2f} (oC) ! Annual amplitude in mean monthly temperature.
!Data Extracted from CMIP6 ACCESS-CM2 {scenario} dataset on {current_date} for APSIM
!As evaporation is read at 9am, it has been shifted to day before
!ie The evaporation measured on 20 April is in row for 19 April
!The 6 digit code indicates the source of the 6 data columns
!0 actual observation, 1 actual observation composite station
!2 interpolated from daily observations
!3 interpolated from daily observations using anomaly interpolation method for CLIMARC data
!6 synthetic pan
!7 interpolated long term averages
!more detailed two digit codes are available in SILO's 'Standard' format files
!
!For further information see the documentation on the datadrill
!  http://www.longpaddock.qld.gov.au/silo
!
year  day radn  maxt   mint  rain  evap    vp   code
 ()   () (MJ/m^2) (oC)  (oC)  (mm)  (mm) (hPa)     ()
"""
    
    # Create output filename
    output_filename = f"{BASE_NAME}_{scenario}.met"
    output_path = os.path.join(output_dir, output_filename)
    
    # Write MET file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        # Write data rows
        for _, row in met_data.iterrows():
            # Format the row with proper spacing matching the example format
            # year  day radn  maxt   mint  rain  evap    vp   code
            # Example: 2000   1   26.8  33.7  16.4   0.0   9.8  12.7 222222
            # For empty values, use empty string with proper spacing
            radn_val = row['radn'] if row['radn'] != '' and pd.notna(row['radn']) else ''
            evap_val = row['evap'] if row['evap'] != '' and pd.notna(row['evap']) else ''
            vp_val = row['vp'] if row['vp'] != '' and pd.notna(row['vp']) else ''
            code_val = row['code'] if row['code'] != '' and pd.notna(row['code']) else ''
            
            # Format numbers with proper spacing (column widths from example)
            if radn_val != '':
                radn_str = f"{float(radn_val):6.1f}"
            else:
                radn_str = "      "  # 6 spaces
                
            if evap_val != '':
                evap_str = f"{float(evap_val):6.1f}"
            else:
                evap_str = "      "  # 6 spaces
                
            if vp_val != '':
                vp_str = f"{float(vp_val):6.1f}"
            else:
                vp_str = "      "  # 6 spaces
                
            if code_val != '':
                code_str = f"{str(code_val):>6s}"
            else:
                code_str = "      "  # 6 spaces
            
            # Format with proper column widths: year(4) day(4) radn(6) maxt(6) mint(6) rain(6) evap(6) vp(6) code(6)
            line = f"{int(row['year']):4d} {int(row['day']):4d} {radn_str} {row['maxt']:6.1f} {row['mint']:6.1f} {row['rain']:6.1f} {evap_str} {vp_str} {code_str}\n"
            f.write(line)
    
    print(f"  [OK] Created MET file: {output_filename}")
    
    # Also create CSV version with same structure
    csv_filename = f"{BASE_NAME}_{scenario}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    # Write CSV (without header comments, just data)
    met_data.to_csv(csv_path, index=False, encoding='utf-8', float_format='%.1f')
    print(f"  [OK] Created CSV file: {csv_filename}")
    
    return tav, amp, len(met_data)


def main():
    """Main execution function."""
    print("="*70)
    print("Converting CMIP6 Data to APSIM MET Format")
    print("="*70)
    print(f"\nInput directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Coordinates: ({LATITUDE}, {LONGITUDE})")
    print(f"Scenarios: {', '.join(SCENARIOS)}")
    print("="*70)
    
    for scenario in SCENARIOS:
        print(f"\n{'='*70}")
        print(f"Processing Scenario: {scenario}")
        print(f"{'='*70}")
        
        # Construct file paths
        tasmax_file = os.path.join(INPUT_DIR, f"{BASE_NAME}_tasmax_{scenario}.csv")
        tasmin_file = os.path.join(INPUT_DIR, f"{BASE_NAME}_tasmin_{scenario}.csv")
        pr_file = os.path.join(INPUT_DIR, f"{BASE_NAME}_pr_{scenario}.csv")
        
        # Check if files exist
        for fpath in [tasmax_file, tasmin_file, pr_file]:
            if not os.path.exists(fpath):
                print(f"  ERROR: File not found: {fpath}")
                continue
        
        # Load data
        print(f"  Loading data files...")
        tasmax_df = pd.read_csv(tasmax_file)
        tasmin_df = pd.read_csv(tasmin_file)
        pr_df = pd.read_csv(pr_file)
        
        print(f"    tasmax: {len(tasmax_df)} rows")
        print(f"    tasmin: {len(tasmin_df)} rows")
        print(f"    pr: {len(pr_df)} rows")
        
        # Create MET file
        tav, amp, num_rows = create_met_file(
            tasmax_df, tasmin_df, pr_df, scenario, 
            OUTPUT_DIR, LATITUDE, LONGITUDE
        )
        
        print(f"  Summary:")
        print(f"    Rows: {num_rows}")
        print(f"    tav (annual average temp): {tav:.2f} °C")
        print(f"    amp (annual amplitude): {amp:.2f} °C")
    
    print(f"\n{'='*70}")
    print("Conversion complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()


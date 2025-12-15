"""
Grid Point CMIP6 Retrieval and MET Conversion Script
=====================================================

This script extracts climate data from CMIP6 NetCDF files for a user-specified coordinate 
and converts it to APSIM MET format.

Variables processed:
- tasmax -> maxt (maximum temperature)
- tasmin -> mint (minimum temperature)  
- pr -> rain (precipitation)
- rsds -> radn (radiation, converted from W/m2 to MJ/m2)

Note: vp and code fields are left blank in MET format
"""

import pandas as pd
import numpy as np
import xarray as xr
import glob
import os
import time
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# ============================================================================
# CONFIGURATION
# ============================================================================

CMIP6_BASE_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\CMIP6"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"  # Output directory for MET files
COORD_TOLERANCE = 0.01  # degrees (approximately 1.1 km)

# Model and Scenario
MODEL = "ACCESS CM2"  # e.g., "ACCESS CM2"
SCENARIO = "SSP245"   # e.g., "SSP245" or "SSP585"

# Variables to process (4 variables)
# MET format mapping:
# - tasmax -> maxt (maximum temperature)
# - tasmin -> mint (minimum temperature)
# - pr -> rain (precipitation)
# - rsds -> radn (radiation, converted from W/m2 to MJ/m2)
# Note: vp and code are left blank in MET format
VARIABLES = ['tasmax', 'tasmin', 'pr', 'rsds']

# Coordinates
LATITUDE = -31.75   # Target latitude in decimal degrees (-90 to 90)
LONGITUDE = 117.5999984741211  # Target longitude in decimal degrees (-180 to 180)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================================
# FUNCTIONS
# ============================================================================

def extract_daily_data_from_netcdf(netcdf_dir, variable, target_lat, target_lon, tolerance=0.01):
    """
    Extract daily time series data for a specific coordinate from NetCDF files.
    
    Parameters:
    -----------
    netcdf_dir : str
        Directory containing NetCDF files for the variable
    variable : str
        Variable name (tasmax, tasmin, pr, rsds)
    target_lat : float
        Target latitude
    target_lon : float
        Target longitude
    tolerance : float
        Coordinate matching tolerance in degrees
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: date, value
    """
    start_time = time.time()
    
    # Find all NetCDF files in the directory
    # Pattern 1: Files directly in the directory matching *{variable}*.nc
    nc_files = sorted(glob.glob(os.path.join(netcdf_dir, f"*{variable}*.nc")))
    
    # Pattern 2: Files in subdirectories named {variable}_* (e.g., pr_ACCESS CM2 SSP245)
    if len(nc_files) == 0:
        var_subdirs = glob.glob(os.path.join(netcdf_dir, f"{variable}_*"))
        for var_subdir in var_subdirs:
            if os.path.isdir(var_subdir):
                found_files = sorted(glob.glob(os.path.join(var_subdir, "*.nc")))
                if found_files:
                    nc_files.extend(found_files)
                    print(f"  Found files in subdirectory: {os.path.basename(var_subdir)}/")
                    break
    
    # Pattern 3: Check subdirectory named exactly after the variable
    if len(nc_files) == 0:
        var_dir = os.path.join(netcdf_dir, variable)
        if os.path.exists(var_dir) and os.path.isdir(var_dir):
            nc_files = sorted(glob.glob(os.path.join(var_dir, "*.nc")))
            if len(nc_files) > 0:
                print(f"  Found files in subdirectory: {variable}/")
    
    if len(nc_files) == 0:
        print(f"  ERROR: No NetCDF files found in {netcdf_dir}")
        print(f"  Searched patterns:")
        print(f"    - {netcdf_dir}/*{variable}*.nc")
        print(f"    - {netcdf_dir}/{variable}_*/*.nc")
        print(f"    - {netcdf_dir}/{variable}/*.nc")
        return None
    
    print(f"  Found {len(nc_files)} NetCDF files")
    
    # Cache coordinate information from first file
    lat_name = None
    lon_name = None
    time_name = None
    lat_idx = None
    lon_idx = None
    actual_lat = None
    actual_lon = None
    var_name = None
    
    # List to store daily data
    all_data = []
    
    # Process first file to get coordinate structure
    if len(nc_files) > 0:
        try:
            ds_sample = xr.open_dataset(nc_files[0], decode_times=False)
            
            # Get variable name
            for v in ds_sample.data_vars:
                if variable in v.lower() or v.lower() in variable.lower():
                    var_name = v
                    break
            
            if var_name is None:
                possible_names = [variable, variable.upper(), f'{variable}_day']
                for name in possible_names:
                    if name in ds_sample.data_vars:
                        var_name = name
                        break
            
            # Get coordinate names
            for coord in ds_sample.coords:
                coord_lower = coord.lower()
                if 'lat' in coord_lower:
                    lat_name = coord
                elif 'lon' in coord_lower:
                    lon_name = coord
                elif 'time' in coord_lower:
                    time_name = coord
            
            if lat_name and lon_name:
                # Find nearest grid point (cache indices)
                lat_idx = np.abs(ds_sample[lat_name].values - target_lat).argmin()
                lon_idx = np.abs(ds_sample[lon_name].values - target_lon).argmin()
                
                actual_lat = float(ds_sample[lat_name].values[lat_idx])
                actual_lon = float(ds_sample[lon_name].values[lon_idx])
                
                # Check if within tolerance
                if abs(actual_lat - target_lat) > tolerance or abs(actual_lon - target_lon) > tolerance:
                    print(f"  Warning: Nearest point ({actual_lat:.4f}, {actual_lon:.4f}) is outside tolerance")
                else:
                    print(f"  Using grid point: ({actual_lat:.4f}, {actual_lon:.4f})")
            
            ds_sample.close()
            
        except Exception as e:
            print(f"  Warning: Could not read sample file: {e}")
    
    if var_name is None or lat_idx is None or lon_idx is None:
        print(f"  ERROR: Could not determine coordinate structure")
        return None
    
    # Process all files with progress bar
    print(f"  Processing files...")
    for nc_file in tqdm(nc_files, desc=f"  {variable}", unit="file"):
        try:
            # Open NetCDF file with minimal decoding for speed
            ds = xr.open_dataset(nc_file, decode_times=False)
            
            # Extract data using cached indices
            data = ds[var_name].isel({lat_name: lat_idx, lon_name: lon_idx})
            
            # Convert to numpy array (load into memory)
            values = data.values
            if values.ndim > 1:
                values = values.flatten()
            
            # Get time values - try multiple methods to ensure accuracy and handle leap years (366 days)
            time_values = None
            
            # Method 1: Try to use time coordinate from NetCDF file (most reliable)
            if time_name and time_name in ds.coords:
                try:
                    time_coord = ds[time_name]
                    if len(time_coord) == len(values):
                        # Try to decode times
                        try:
                            # Decode time coordinate
                            time_decoded = xr.decode_cf(ds[[time_name]])[time_name]
                            time_values = pd.to_datetime(time_decoded.values)
                            if len(time_values) == len(values):
                                pass  # Success - using decoded time coordinate
                        except:
                            # If decoding fails, try manual conversion
                            if hasattr(time_coord, 'units') and 'days since' in time_coord.units.lower():
                                base_date_str = time_coord.units.split('since')[1].strip().split()[0]
                                base_date = pd.to_datetime(base_date_str)
                                time_values = base_date + pd.to_timedelta(time_coord.values, unit='D')
                                if len(time_values) != len(values):
                                    time_values = None
                except Exception as e:
                    pass  # Fall back to other methods
            
            # Method 2: Extract year from filename and create date range
            # This method automatically handles leap years (366 days) correctly
            if time_values is None:
                year = None
                filename = os.path.basename(nc_file)
                all_years = re.findall(r'\d{4}', filename)
                for year_str in all_years:
                    year_candidate = int(year_str)
                    if 2000 <= year_candidate <= 2100:
                        year = year_candidate
                        break
                
                if year:
                    # Create dates based on ACTUAL data length
                    # pd.date_range with freq='D' automatically handles leap years
                    # For leap years (e.g., 2024, 2028), it will include Feb 29 (366 days)
                    # For non-leap years, it will have 365 days
                    time_values = pd.date_range(start=f'{year}-01-01', periods=len(values), freq='D')
                else:
                    # Fallback: use 2035 as default (start of typical CMIP6 data range)
                    time_values = pd.date_range(start='2035-01-01', periods=len(values), freq='D')
            
            # Ensure we have the correct number of dates matching the data
            # This handles edge cases where time coordinate might not match exactly
            if len(time_values) != len(values):
                if len(time_values) > len(values):
                    time_values = time_values[:len(values)]
                else:
                    # Extend if needed (shouldn't happen normally, but handle it)
                    additional_days = len(values) - len(time_values)
                    last_date = time_values[-1]
                    additional_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=additional_days, freq='D')
                    time_values = pd.concat([pd.Series(time_values), pd.Series(additional_dates)]).values
            
            # Create DataFrame for this file
            # Use actual data length to ensure all days are included (365 or 366 for leap years)
            if len(values) > 0:
                df_file = pd.DataFrame({
                    'date': time_values[:len(values)],
                    'value': values
                })
                all_data.append(df_file)
            
            ds.close()
            
        except Exception as e:
            tqdm.write(f"    Error processing {os.path.basename(nc_file)}: {e}")
            continue
    
    if len(all_data) == 0:
        print(f"  ERROR: No data extracted")
        return None
    
    # Combine all data
    print(f"  Combining data from {len(all_data)} files...")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    # Remove duplicate dates (keep first occurrence)
    combined_df = combined_df.drop_duplicates(subset='date', keep='first')
    
    elapsed_time = time.time() - start_time
    print(f"  [OK] Extracted {len(combined_df):,} daily records in {elapsed_time:.1f} seconds")
    print(f"  Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    
    return combined_df


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


def create_met_file(tasmax_df, tasmin_df, pr_df, rsds_df=None, scenario=None, 
                    output_dir=None, latitude=None, longitude=None, model=None):
    """
    Create MET format file from tasmax, tasmin, pr, and optional rsds DataFrames.
    
    Parameters:
    -----------
    tasmax_df : pd.DataFrame
        DataFrame with date and value columns for maximum temperature
    tasmin_df : pd.DataFrame
        DataFrame with date and value columns for minimum temperature
    pr_df : pd.DataFrame
        DataFrame with date and value columns for precipitation
    rsds_df : pd.DataFrame, optional
        DataFrame with date and value columns for surface downwelling shortwave radiation (W/m2)
    scenario : str
        Scenario name (e.g., SSP585 or SSP245)
    output_dir : str
        Output directory path
    latitude : float
        Latitude in decimal degrees
    longitude : float
        Longitude in decimal degrees
    model : str
        Model name (e.g., "ACCESS CM2")
    
    Returns:
    --------
    tuple: (tav, amp, num_rows)
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
    
    # Merge rsds (radiation) if available
    # rsds is in W/m2, convert to MJ/m2 by multiplying by 0.0864 (seconds per day / 1e6)
    if rsds_df is not None and len(rsds_df) > 0:
        rsds_df['date'] = pd.to_datetime(rsds_df['date'])
        # Convert W/m2 to MJ/m2 (multiply by seconds per day / 1e6)
        rsds_df['value_mj'] = rsds_df['value'] * 0.0864
        merged = merged.merge(rsds_df[['date', 'value_mj']], on='date', how='outer')
        merged = merged.rename(columns={'value_mj': 'radn'})
    else:
        merged['radn'] = ''
    
    # vp (vapor pressure) is left blank
    merged['vp'] = ''
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    # Calculate tav and amp
    merged_temp = merged[['date', 'maxt', 'mint']].copy()
    merged_temp = merged_temp.set_index('date')
    merged_temp.index = pd.to_datetime(merged_temp.index)
    tav, amp = calculate_tav_amp(merged_temp)
    
    # Create year and day columns
    merged['year'] = merged['date'].dt.year
    merged['day'] = merged['date'].dt.dayofyear
    
    # Add empty columns for evap and code
    merged['evap'] = ''  # Leave blank
    merged['code'] = ''  # Leave blank
    
    # Ensure radn and vp are strings if empty
    if 'radn' not in merged.columns:
        merged['radn'] = ''
    if 'vp' not in merged.columns:
        merged['vp'] = ''
    
    # Select and order columns for MET format
    met_data = merged[['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'evap', 'vp', 'code']].copy()
    
    # Prepare header
    current_date = datetime.now().strftime('%Y%m%d')
    model_scenario = f"{model.replace(' ', '_')}_{scenario}" if model and scenario else "CMIP6"
    
    header = f"""[weather.met.weather]
!Your Ref:  "
latitude = {latitude:.2f}  (DECIMAL DEGREES)
longitude =  {longitude:.2f}  (DECIMAL DEGREES)
tav = {tav:.2f} (oC) ! Annual average ambient temperature.
amp = {amp:.2f} (oC) ! Annual amplitude in mean monthly temperature.
!Data Extracted from CMIP6 {model} {scenario} dataset on {current_date} for APSIM
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
    
    # Create output filename with coordinate-based naming
    # Format: {Model}_{Scenario}_{Lat}_{Lon}.met (e.g., ACCESS_CM2_SSP245_-31.75_117.60.met)
    lat_str = f"{latitude:.2f}"
    lon_str = f"{longitude:.2f}"
    output_filename = f"{model_scenario}_{lat_str}_{lon_str}.met"
    output_path = os.path.join(output_dir, output_filename)
    
    # Write MET file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        # Write data rows
        for _, row in met_data.iterrows():
            # Format the row with proper spacing
            radn_val = row['radn'] if row['radn'] != '' and pd.notna(row['radn']) else ''
            evap_val = row['evap'] if row['evap'] != '' and pd.notna(row['evap']) else ''
            vp_val = row['vp'] if row['vp'] != '' and pd.notna(row['vp']) else ''
            code_val = row['code'] if row['code'] != '' and pd.notna(row['code']) else ''
            
            # Format numbers with proper spacing
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
            
            # Handle NaN values for maxt, mint, rain - use 0.0 as default
            maxt_val = row['maxt'] if pd.notna(row['maxt']) else 0.0
            mint_val = row['mint'] if pd.notna(row['mint']) else 0.0
            rain_val = row['rain'] if pd.notna(row['rain']) else 0.0
            
            # Format with proper column widths
            line = f"{int(row['year']):4d} {int(row['day']):4d} {radn_str} {maxt_val:6.1f} {mint_val:6.1f} {rain_val:6.1f} {evap_str} {vp_str} {code_str}\n"
            f.write(line)
    
    print(f"  [OK] Created MET file: {output_filename}")
    
    # Also create CSV version with same structure
    csv_filename = f"{model_scenario}_{lat_str}_{lon_str}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    # Write CSV (without header comments, just data)
    met_data.to_csv(csv_path, index=False, encoding='utf-8', float_format='%.1f')
    print(f"  [OK] Created CSV file: {csv_filename}")
    
    return tav, amp, len(met_data)


def process_coordinate(model, scenario, latitude, longitude, variables, cmip6_base_dir, output_dir, tolerance=0.01):
    """
    Main processing function for user-provided coordinate.
    Extract all variables from NC files and convert to MET format.
    
    Parameters:
    -----------
    model : str
        Model name (e.g., "ACCESS CM2")
    scenario : str
        Scenario name (e.g., "SSP245")
    latitude : float
        Target latitude
    longitude : float
        Target longitude
    variables : list
        List of variable names to extract
    cmip6_base_dir : str
        Base directory containing Model Scenario folders
    output_dir : str
        Output directory for results
    tolerance : float
        Coordinate matching tolerance
    
    Returns:
    --------
    dict: Summary statistics
    """
    print("="*70)
    print(f"Processing Coordinate: ({latitude:.6f}, {longitude:.6f})")
    print(f"Model: {model}, Scenario: {scenario}")
    print("="*70)
    
    # Construct data directory path
    data_dir = os.path.join(cmip6_base_dir, f"{model} {scenario}")
    
    if not os.path.exists(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        return None
    
    print(f"\nData directory: {data_dir}")
    
    # Extract data for all variables
    extracted_data = {}
    
    for variable in variables:
        print(f"\n{'='*70}")
        print(f"Processing variable: {variable}")
        print(f"{'='*70}")
        
        # Extract data from NetCDF files
        df = extract_daily_data_from_netcdf(
            data_dir, 
            variable, 
            latitude, 
            longitude, 
            tolerance=tolerance
        )
        
        if df is not None and len(df) > 0:
            extracted_data[variable] = df
            
            # Save individual variable CSV
            # Format: {Model}_{Scenario}_{Lat}_{Lon}_{variable}.csv
            lat_str = f"{latitude:.2f}"
            lon_str = f"{longitude:.2f}"
            model_scenario = f"{model.replace(' ', '_')}_{scenario}"
            csv_filename = f"{model_scenario}_{lat_str}_{lon_str}_{variable}.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            df.to_csv(csv_path, index=False, encoding='utf-8', float_format='%.6f')
            print(f"  [OK] Saved CSV: {csv_filename}")
        else:
            print(f"  WARNING: No data extracted for {variable}")
    
    # Check if required variables are available for MET conversion
    required_vars = ['tasmax', 'tasmin', 'pr']
    missing_vars = [v for v in required_vars if v not in extracted_data]
    
    if missing_vars:
        print(f"\nERROR: Missing required variables for MET conversion: {missing_vars}")
        return None
    
    # Create MET file
    print(f"\n{'='*70}")
    print("Creating MET file...")
    print(f"{'='*70}")
    
    # Get required variables
    tasmax_df = extracted_data['tasmax']
    tasmin_df = extracted_data['tasmin']
    pr_df = extracted_data['pr']
    
    # Get optional variable for MET format
    rsds_df = extracted_data.get('rsds', None)
    
    # Note: vp and code are left blank in MET format
    
    tav, amp, num_rows = create_met_file(
        tasmax_df=tasmax_df,
        tasmin_df=tasmin_df,
        pr_df=pr_df,
        rsds_df=rsds_df,
        scenario=scenario,
        output_dir=output_dir,
        latitude=latitude,
        longitude=longitude,
        model=model
    )
    
    # Summary
    summary = {
        'latitude': latitude,
        'longitude': longitude,
        'model': model,
        'scenario': scenario,
        'variables_extracted': list(extracted_data.keys()),
        'num_variables': len(extracted_data),
        'tav': tav,
        'amp': amp,
        'num_rows': num_rows,
        'date_range': {
            'start': tasmax_df['date'].min(),
            'end': tasmax_df['date'].max()
        }
    }
    
    print(f"\n{'='*70}")
    print("Processing Summary")
    print(f"{'='*70}")
    print(f"  Variables extracted: {len(extracted_data)}")
    print(f"    - {', '.join(extracted_data.keys())}")
    print(f"  MET file rows: {num_rows}")
    print(f"  Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
    print(f"  tav (annual average temp): {tav:.2f} °C")
    print(f"  amp (annual amplitude): {amp:.2f} °C")
    print(f"  Output directory: {output_dir}")
    print(f"{'='*70}")
    
    return summary


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Validate coordinates
    if not (-90 <= LATITUDE <= 90):
        raise ValueError(f"Latitude must be between -90 and 90. Provided: {LATITUDE}")
    if not (-180 <= LONGITUDE <= 180):
        raise ValueError(f"Longitude must be between -180 and 180. Provided: {LONGITUDE}")
    
    # Display configuration
    print("="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(f"\nModel: {MODEL}")
    print(f"Scenario: {SCENARIO}")
    print(f"\nCoordinates:")
    print(f"  Latitude: {LATITUDE:.6f}°")
    print(f"  Longitude: {LONGITUDE:.6f}°")
    print(f"  Tolerance: {COORD_TOLERANCE} degrees (~ {COORD_TOLERANCE * 111:.1f} km)")
    print(f"\nVariables to process ({len(VARIABLES)}):")
    for var in VARIABLES:
        if var == 'tasmax':
            print(f"  - {var} -> maxt (maximum temperature)")
        elif var == 'tasmin':
            print(f"  - {var} -> mint (minimum temperature)")
        elif var == 'pr':
            print(f"  - {var} -> rain (precipitation)")
        elif var == 'rsds':
            print(f"  - {var} -> radn (radiation, W/m2 -> MJ/m2)")
    print(f"\nDirectories:")
    print(f"  CMIP6 Base: {CMIP6_BASE_DIR}")
    print(f"  Data Directory: {os.path.join(CMIP6_BASE_DIR, f'{MODEL} {SCENARIO}')}")
    print(f"  Output Directory: {OUTPUT_DIR}")
    print(f"\nOutput Files:")
    print(f"  MET file: {MODEL.replace(' ', '_')}_{SCENARIO}_{LATITUDE:.2f}_{LONGITUDE:.2f}.met")
    print(f"  CSV file: {MODEL.replace(' ', '_')}_{SCENARIO}_{LATITUDE:.2f}_{LONGITUDE:.2f}.csv")
    print(f"  Variable CSVs: {len(VARIABLES)} files (one per variable)")
    print("="*70)
    
    # Execute main processing
    print("\n" + "="*70)
    print("STARTING PROCESSING")
    print("="*70)
    print(f"Model: {MODEL}")
    print(f"Scenario: {SCENARIO}")
    print(f"Coordinates: ({LATITUDE:.6f}, {LONGITUDE:.6f})")
    print(f"Variables to process: {len(VARIABLES)} ({', '.join(VARIABLES)})")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*70 + "\n")
    
    summary = process_coordinate(
        model=MODEL,
        scenario=SCENARIO,
        latitude=LATITUDE,
        longitude=LONGITUDE,
        variables=VARIABLES,
        cmip6_base_dir=CMIP6_BASE_DIR,
        output_dir=OUTPUT_DIR,
        tolerance=COORD_TOLERANCE
    )
    
    if summary:
        print("\n" + "="*70)
        print("[SUCCESS] PROCESSING COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\nOutput files created:")
        print(f"  - MET file: {MODEL.replace(' ', '_')}_{SCENARIO}_{LATITUDE:.2f}_{LONGITUDE:.2f}.met")
        print(f"  - CSV file: {MODEL.replace(' ', '_')}_{SCENARIO}_{LATITUDE:.2f}_{LONGITUDE:.2f}.csv")
        print(f"  - Individual variable CSVs: {len(summary['variables_extracted'])} files")
        print(f"\nAll files saved to: {OUTPUT_DIR}")
    else:
        print("\n" + "="*70)
        print("[ERROR] PROCESSING FAILED")
        print("="*70)
        print("Please check error messages above.")

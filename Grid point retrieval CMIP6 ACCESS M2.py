import pandas as pd
import numpy as np
import xarray as xr
import glob
import os
import time
import re
import calendar
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Configuration
CMIP6_BASE_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\CMIP6"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"  # Output directory for MET files
COORD_TOLERANCE = 0.01  # degrees (approximately 1.1 km)

# Model and Scenario - UPDATE THESE AS NEEDED
MODEL = "ACCESS CM2"  # e.g., "ACCESS CM2"
SCENARIO = "SSP585"   # e.g., "SSP245" or "SSP585"

# Variables to process (5 variables)
# MET format mapping:
# - tasmax -> maxt (maximum temperature)
# - tasmin -> mint (minimum temperature)
# - pr -> rain (precipitation)
# - rsds -> radn (radiation, converted from W/m2 to MJ/m2)
# - hurs -> vp (vapor pressure, calculated using SILO method)
# Note: code is hardcoded to '222222'
VARIABLES = ['tasmax', 'tasmin', 'pr', 'rsds', 'hurs']

# Coordinates
LATITUDE = -31.75   # Target latitude in decimal degrees (-90 to 90)
LONGITUDE = 117.5999984741211  # Target longitude in decimal degrees (-180 to 180)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    
    # Pattern 2b: For rsds, also check for "rad_" folder (folder named "rad_" but files contain "rsds")
    # Example: rad_ACCESS CM2 SSP245/ contains files named *rsds*.nc
    if len(nc_files) == 0 and variable == 'rsds':
        rad_subdirs = glob.glob(os.path.join(netcdf_dir, "rad_*"))
        for rad_subdir in rad_subdirs:
            if os.path.isdir(rad_subdir):
                # Search for files containing "rsds" in the rad_ folder
                found_files = sorted(glob.glob(os.path.join(rad_subdir, "*rsds*.nc")))
                if found_files:
                    nc_files.extend(found_files)
                    print(f"  Found files in subdirectory: {os.path.basename(rad_subdir)}/")
                    break
                # Fallback: if no rsds files found, try all .nc files
                if len(nc_files) == 0:
                    found_files = sorted(glob.glob(os.path.join(rad_subdir, "*.nc")))
                    if found_files:
                        nc_files.extend(found_files)
                        print(f"  Found files in subdirectory: {os.path.basename(rad_subdir)}/")
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
        if variable == 'rsds':
            print(f"    - {netcdf_dir}/rad_*/*rsds*.nc")
            print(f"    - {netcdf_dir}/rad_*/*.nc")
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
            
            # For rsds, also check for "rad" variable name (some datasets use "rad" instead of "rsds")
            if var_name is None and variable == 'rsds':
                for v in ds_sample.data_vars:
                    if 'rad' in v.lower() and 'rsds' not in v.lower():
                        var_name = v
                        break
            
            if var_name is None:
                possible_names = [variable, variable.upper(), f'{variable}_day']
                # For rsds, also try "rad" as variable name
                if variable == 'rsds':
                    possible_names.extend(['rad', 'RAD', 'rad_day'])
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

def calculate_saturation_vapor_pressure(temperature):
    """
    Calculate saturation vapor pressure (kPa) at a given temperature using SILO method.
    
    Parameters:
    -----------
    temperature : float or array
        Temperature in °C
    
    Returns:
    --------
    float or array
        Saturation vapor pressure in kPa
    """
    # SILO formula: e_s(T) = 0.611 × exp(17.27 × T / (T + 237.3))
    return 0.611 * np.exp(17.27 * temperature / (temperature + 237.3))


def calculate_vapor_pressure(hurs_df, tasmax_df, tasmin_df):
    """
    Calculate vapor pressure (hPa) from mean relative humidity and temperature using SILO method.
    
    Parameters:
    -----------
    hurs_df : pd.DataFrame
        DataFrame with date and value (mean relative humidity %) columns
    tasmax_df : pd.DataFrame
        DataFrame with date and value (maximum temperature °C) columns
    tasmin_df : pd.DataFrame
        DataFrame with date and value (minimum temperature °C) columns
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with date and value (vapor pressure hPa) columns
    """
    # Merge temperature dataframes
    temp_df = tasmax_df.merge(tasmin_df, on='date', suffixes=('_max', '_min'))
    temp_df['tmean'] = (temp_df['value_max'] + temp_df['value_min']) / 2.0
    
    # Merge with mean humidity
    merged = hurs_df.merge(temp_df[['date', 'tmean']], on='date')
    
    # Calculate saturation vapor pressure at mean temperature (in kPa)
    # SILO formula: e_s(T) = 0.611 × exp(17.27 × T / (T + 237.3))
    merged['es_kpa'] = calculate_saturation_vapor_pressure(merged['tmean'])
    
    # Calculate actual vapor pressure using mean relative humidity (in kPa)
    # e_a = (hurs/100) × e_s(T_mean)
    merged['ea_kpa'] = (merged['value'] / 100.0) * merged['es_kpa']
    
    # Convert to SILO VP units (hPa): VP(hPa) = 10 × e_a(kPa)
    merged['vp'] = 10.0 * merged['ea_kpa']
    
    # Return DataFrame with date and vp columns
    vp_df = merged[['date', 'vp']].copy()
    vp_df = vp_df.rename(columns={'vp': 'value'})
    
    return vp_df

def create_met_file(tasmax_df, tasmin_df, pr_df, rsds_df, hurs_df=None, scenario=None, 
                    output_dir=None, latitude=None, longitude=None, model=None):
    """
    Create MET format file from tasmax, tasmin, pr, rsds, and optional hurs DataFrames.
    
    Parameters:
    -----------
    tasmax_df : pd.DataFrame
        DataFrame with date and value columns for maximum temperature
    tasmin_df : pd.DataFrame
        DataFrame with date and value columns for minimum temperature
    pr_df : pd.DataFrame
        DataFrame with date and value columns for precipitation
    rsds_df : pd.DataFrame
        DataFrame with date and value columns for surface downwelling shortwave radiation (W/m2) - REQUIRED
    hurs_df : pd.DataFrame, optional
        DataFrame with date and value columns for relative humidity (%) - if provided, VP will be calculated
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
    
    # Merge rsds (radiation) - REQUIRED
    # rsds is in W/m2, convert to MJ/m2 by multiplying by 0.0864 (seconds per day / 1e6)
    if rsds_df is None or len(rsds_df) == 0:
        raise ValueError("rsds_df is required but is None or empty")
    
    rsds_df['date'] = pd.to_datetime(rsds_df['date'])
    # Convert W/m2 to MJ/m2 (multiply by seconds per day / 1e6)
    rsds_df['value_mj'] = rsds_df['value'] * 0.0864
    merged = merged.merge(rsds_df[['date', 'value_mj']], on='date', how='outer')
    merged = merged.rename(columns={'value_mj': 'radn'})
    
    # Calculate vp (vapor pressure) if hurs is provided, otherwise leave blank
    # NOTE: VP calculation will happen AFTER date range extension to ensure all days are included
    # We'll calculate VP later after forward-filling hurs data
    
    # Sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    # CRITICAL FIX: Create a complete date range to ensure all days are included
    # This ensures leap years have 366 days and non-leap years have 365 days
    min_date = merged['date'].min()
    max_date = merged['date'].max()
    original_count = len(merged)
    
    # Ensure the last year is complete - extend to end of year if needed
    last_year = max_date.year
    last_day_of_year = pd.Timestamp(year=last_year, month=12, day=31)
    if max_date < last_day_of_year:
        # Extend max_date to end of year to ensure complete year coverage
        max_date = last_day_of_year
    
    # Create complete date range (includes all days, including day 366 for leap years)
    complete_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # Set date as index for reindexing
    merged = merged.set_index('date')
    
    # Reindex to include all days in the complete range
    merged = merged.reindex(complete_date_range)
    
    # Report if days were added
    new_count = len(merged)
    if new_count > original_count:
        print(f"  [INFO] Added {new_count - original_count} missing days to ensure complete date range")
    
    # Fill missing values for numeric columns using forward fill then backward fill
    # This handles gaps in the data gracefully
    numeric_cols = ['maxt', 'mint', 'rain', 'radn']
    for col in numeric_cols:
        if col in merged.columns:
            # Forward fill first, then backward fill to handle gaps at start/end
            merged[col] = merged[col].ffill().bfill()
            # If still NaN, fill with 0 (shouldn't happen, but safety check)
            merged[col] = merged[col].fillna(0.0)
    
    # Calculate VP AFTER date range extension and forward-filling
    # This ensures VP can be calculated for all days, including day 366
    if hurs_df is not None and len(hurs_df) > 0:
        # Prepare hurs, tasmax, and tasmin dataframes with complete date range
        # Forward-fill missing values so VP can be calculated for all dates
        hurs_complete = pd.DataFrame({'date': complete_date_range})
        hurs_df_copy = hurs_df.copy()
        hurs_df_copy['date'] = pd.to_datetime(hurs_df_copy['date'])
        hurs_complete = hurs_complete.merge(hurs_df_copy[['date', 'value']], on='date', how='left')
        hurs_complete = hurs_complete.sort_values('date').reset_index(drop=True)
        hurs_complete['value'] = hurs_complete['value'].ffill().bfill()  # Forward/backward fill hurs
        
        tasmax_complete = pd.DataFrame({'date': complete_date_range})
        tasmax_df_copy = tasmax_df.copy()
        tasmax_df_copy['date'] = pd.to_datetime(tasmax_df_copy['date'])
        tasmax_complete = tasmax_complete.merge(tasmax_df_copy[['date', 'value']], on='date', how='left')
        tasmax_complete = tasmax_complete.sort_values('date').reset_index(drop=True)
        tasmax_complete['value'] = tasmax_complete['value'].ffill().bfill()  # Forward/backward fill tasmax
        
        tasmin_complete = pd.DataFrame({'date': complete_date_range})
        tasmin_df_copy = tasmin_df.copy()
        tasmin_df_copy['date'] = pd.to_datetime(tasmin_df_copy['date'])
        tasmin_complete = tasmin_complete.merge(tasmin_df_copy[['date', 'value']], on='date', how='left')
        tasmin_complete = tasmin_complete.sort_values('date').reset_index(drop=True)
        tasmin_complete['value'] = tasmin_complete['value'].ffill().bfill()  # Forward/backward fill tasmin
        
        # Calculate VP using SILO method with forward-filled data
        vp_df = calculate_vapor_pressure(hurs_complete, tasmax_complete, tasmin_complete)
        vp_df['date'] = pd.to_datetime(vp_df['date'])
        
        # Merge VP into merged dataframe (using index since merged is indexed by date)
        vp_df_indexed = vp_df.set_index('date')
        merged['vp'] = vp_df_indexed['value']
        # Ensure VP is numeric
        merged['vp'] = pd.to_numeric(merged['vp'], errors='coerce')
        
        # Count how many VP values were calculated
        vp_calculated = merged['vp'].notna().sum()
        print(f"  [OK] Calculated vapor pressure for {vp_calculated} days (including forward-filled hurs for missing dates)")
    else:
        # vp (vapor pressure) is left blank if hurs not available
        merged['vp'] = np.nan
        print(f"  [INFO] hurs not provided - VP left blank")
    
    # Reset index to get date back as a column
    merged = merged.reset_index()
    merged = merged.rename(columns={'index': 'date'})
    
    # Ensure VP column exists and handle any remaining NaN values
    if 'vp' not in merged.columns:
        merged['vp'] = np.nan
    
    # Calculate tav and amp (use only non-NaN values for calculation)
    merged_temp = merged[['date', 'maxt', 'mint']].copy()
    merged_temp = merged_temp.set_index('date')
    merged_temp.index = pd.to_datetime(merged_temp.index)
    tav, amp = calculate_tav_amp(merged_temp)
    
    # Create year and day columns
    merged['year'] = merged['date'].dt.year
    merged['day'] = merged['date'].dt.dayofyear
    
    # FIX: Copy VP value from day 365 to day 366 for leap years
    # This ensures day 366 has a VP value even if hurs data doesn't exist for that date
    if 'vp' in merged.columns:
        # Find all day 366 rows (leap year days)
        day366_mask = merged['day'] == 366
        day366_rows = merged[day366_mask].copy()
        
        if len(day366_rows) > 0:
            # For each day 366, copy VP from day 365 of the same year
            for idx in day366_rows.index:
                year = merged.loc[idx, 'year']
                # Find day 365 of the same year
                day365_mask = (merged['year'] == year) & (merged['day'] == 365)
                day365_rows = merged[day365_mask]
                
                if len(day365_rows) > 0:
                    # Copy VP value from day 365 to day 366
                    vp_day365 = merged.loc[day365_rows.index[0], 'vp']
                    # Only copy if day 366 VP is NaN or empty
                    vp_day366 = merged.loc[idx, 'vp']
                    if pd.isna(vp_day366) or vp_day366 == '':
                        merged.loc[idx, 'vp'] = vp_day365
                        print(f"  [INFO] Copied VP value from day 365 to day 366 for year {year}: {vp_day365:.2f} hPa")
    
    # Add empty columns for evap and code
    merged['evap'] = ''  # Leave blank
    merged['code'] = '222222'  # Hardcoded code value for all rows
    
    # Ensure vp column exists (should already be set above)
    if 'vp' not in merged.columns:
        merged['vp'] = ''
    
    # VP should now be calculated for all dates (including day 366)
    # No need to convert to empty string - VP should have numeric values
    # Only convert NaN to empty string if hurs was not provided at all
    if 'vp' in merged.columns:
        if hurs_df is None or len(hurs_df) == 0:
            # If hurs was not provided, VP should be empty string
            merged['vp'] = merged['vp'].astype(object)
            merged.loc[merged['vp'].isna(), 'vp'] = ''
        else:
            # VP should be numeric (calculated from forward-filled hurs)
            # Fill any remaining NaN with the last valid value (shouldn't happen, but safety check)
            merged['vp'] = merged['vp'].ffill().bfill()
            # If still NaN (shouldn't happen), convert to empty string
            if merged['vp'].isna().any():
                merged['vp'] = merged['vp'].astype(object)
                merged.loc[merged['vp'].isna(), 'vp'] = ''
    
    # Check for blank VP values and issue warning
    vp_blank_count = ((merged['vp'] == '') | (merged['vp'].isna())).sum()
    if vp_blank_count > 0:
        # Find which years have blank VP values
        blank_vp_dates = merged[((merged['vp'] == '') | (merged['vp'].isna())) & merged['date'].notna()]
        if len(blank_vp_dates) > 0:
            blank_years = sorted(blank_vp_dates['date'].dt.year.unique())
            years_str = ', '.join(map(str, blank_years))
            print(f"  [WARNING] Found {vp_blank_count} days with blank VP values (missing hurs data)")
            print(f"  [WARNING] Years affected: {years_str}")
            print(f"  [WARNING] These VP values will appear as blank spaces in the output files")
    
    # Create met_data - VP should now be numeric (calculated from forward-filled hurs)
    met_data = merged[['year', 'day', 'radn', 'maxt', 'mint', 'rain', 'evap', 'vp', 'code']].copy()
    # VP should be numeric if hurs was provided, otherwise empty string
    if 'vp' in met_data.columns:
        if hurs_df is None or len(hurs_df) == 0:
            # If hurs was not provided, VP should be empty string
            met_data['vp'] = met_data['vp'].astype(object)
            met_data.loc[met_data['vp'].isna(), 'vp'] = ''
        else:
            # VP should be numeric - ensure it's float
            met_data['vp'] = pd.to_numeric(met_data['vp'], errors='coerce')
            # Fill any remaining NaN (shouldn't happen after forward-fill)
            if met_data['vp'].isna().any():
                met_data['vp'] = met_data['vp'].ffill().bfill()
                # If still NaN, convert to empty string
                if met_data['vp'].isna().any():
                    met_data['vp'] = met_data['vp'].astype(object)
                    met_data.loc[met_data['vp'].isna(), 'vp'] = ''
    
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
            # Format numbers with proper spacing
            if radn_val != '':
                radn_str = f"{float(radn_val):6.1f}"
            else:
                radn_str = "      "  # 6 spaces
                
            if evap_val != '':
                evap_str = f"{float(evap_val):6.1f}"
            else:
                evap_str = "      "  # 6 spaces
                
            # Handle VP - should be numeric (calculated) or empty string (if hurs not provided)
            vp_val = row['vp']
            is_blank = (vp_val == '' or pd.isna(vp_val) or vp_val is None or 
                       (isinstance(vp_val, float) and np.isnan(vp_val)))
            
            if not is_blank:
                try:
                    vp_str = f"{float(vp_val):6.1f}"
                except (ValueError, TypeError):
                    vp_str = "      "  # 6 spaces
            else:
                vp_str = "      "  # 6 spaces
                
            # Code is hardcoded to '222222' for all rows
            code_str = "222222"
            
            # Handle NaN values for maxt, mint, rain - use 0.0 as default
            maxt_val = row['maxt'] if pd.notna(row['maxt']) else 0.0
            mint_val = row['mint'] if pd.notna(row['mint']) else 0.0
            rain_val = row['rain'] if pd.notna(row['rain']) else 0.0
            
            # Format with proper column widths
            line = f"{int(row['year']):4d} {int(row['day']):4d} {radn_str} {maxt_val:6.1f} {mint_val:6.1f} {rain_val:6.1f} {evap_str} {vp_str} {code_str}\n"
            f.write(line)
    
    # Count blank VP values in final output for warning (after file is written)
    final_blank_vp = ((met_data['vp'] == '') | (met_data['vp'].isna())).sum()
    
    # Verify complete date coverage
    years = met_data['year'].unique()
    total_days = len(met_data)
    # Calculate expected days: 366 for leap years, 365 for non-leap years
    expected_days = sum(366 if calendar.isleap(year) else 365 for year in years)
    
    print(f"  [OK] Created MET file: {output_filename}")
    print(f"  [INFO] Date range: {min_date.date()} to {max_date.date()}")
    print(f"  [INFO] Total days: {total_days} (expected: {expected_days} for {len(years)} years)")
    if total_days == expected_days:
        print(f"  [OK] All days present - leap years have 366 days, non-leap years have 365 days")
    else:
        print(f"  [WARNING] Day count mismatch - may need investigation")
    
    # Final warning about blank VP values
    if final_blank_vp > 0:
        blank_years_list = sorted(met_data[((met_data['vp'] == '') | (met_data['vp'].isna()))]['year'].unique())
        years_str = ', '.join(map(str, blank_years_list))
        print(f"  [WARNING] ========================================")
        print(f"  [WARNING] BLANK VP VALUES DETECTED!")
        print(f"  [WARNING] {final_blank_vp} days have blank VP values (missing hurs data)")
        print(f"  [WARNING] Affected years: {years_str}")
        print(f"  [WARNING] These will appear as blank spaces in MET/CSV files")
        print(f"  [WARNING] ========================================")
    
    # Also create CSV version with same structure
    csv_filename = f"{model_scenario}_{lat_str}_{lon_str}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    # Write CSV (without header comments, just data)
    csv_data = met_data.copy()
    # VP should be numeric if hurs was provided, otherwise empty string
    # Use na_rep='' to ensure empty strings/NaN are written as empty cells
    csv_data.to_csv(csv_path, index=False, encoding='utf-8', float_format='%.1f', na_rep='')
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
    # Note: rsds is now mandatory (required for radn in MET format)
    required_vars = ['tasmax', 'tasmin', 'pr', 'rsds']
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
    
    # Get rsds variable for MET format (now mandatory)
    rsds_df = extracted_data.get('rsds', None)
    if rsds_df is None:
        print(f"  ERROR: rsds is required but was not extracted")
        return None
    
    # Get hurs variable for VP calculation (optional but recommended)
    hurs_df = extracted_data.get('hurs', None)
    if hurs_df is not None:
        print(f"  [INFO] hurs data available - VP will be calculated using SILO method")
    else:
        print(f"  [INFO] hurs data not available - VP will be left blank")
    
    # Note: code is hardcoded to '222222'
    
    tav, amp, num_rows = create_met_file(
        tasmax_df=tasmax_df,
        tasmin_df=tasmin_df,
        pr_df=pr_df,
        rsds_df=rsds_df,
        hurs_df=hurs_df,
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
    print(f"  tav (annual average temp): {tav:.2f} degC")
    print(f"  amp (annual amplitude): {amp:.2f} degC")
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
    print(f"  Latitude: {LATITUDE:.6f} deg")
    print(f"  Longitude: {LONGITUDE:.6f} deg")
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
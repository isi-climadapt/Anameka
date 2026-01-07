import pandas as pd
import numpy as np
import os
from pathlib import Path

# Configuration - match your notebook settings
MODEL = "ACCESS_CM2"
PROXY_OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
LAT = -31.75
LON = 117.6

# Convert lat/lon to string format used in filenames
lat_str = f"neg{abs(LAT):.2f}".replace('.', '_')
lon_str = f"{LON:.2f}".replace('.', '_')

print("="*80)
print("ANALYSIS: Comparing ETO (Evap) Results for SSP245 vs SSP585")
print("="*80)

# Step 1: Check which files are being loaded
print("\n[STEP 1] Checking input files...")
print("-"*80)

scenarios = ['ssp245', 'ssp585']
evap_files = {}

for scenario in scenarios:
    # Check the file pattern used in the notebook
    evap_future_patterns = [
        f"{MODEL}_{scenario}_{lat_str}_{lon_str}_eto.csv",
        f"{MODEL}_{scenario}_{lat_str}_{lon_str}_eto"
    ]
    
    found_file = None
    for pattern in evap_future_patterns:
        file_path = os.path.join(PROXY_OUTPUT_DIR, pattern)
        if os.path.exists(file_path):
            found_file = file_path
            break
    
    if found_file:
        evap_files[scenario] = found_file
        file_size = os.path.getsize(found_file)
        print(f"  {scenario.upper()}: {os.path.basename(found_file)}")
        print(f"    Full path: {found_file}")
        print(f"    File size: {file_size:,} bytes")
        
        # Load and check basic info
        try:
            df = pd.read_csv(found_file)
            print(f"    Rows: {len(df):,}")
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                print(f"    Date range: {df['date'].min()} to {df['date'].max()}")
            if 'value' in df.columns:
                print(f"    Value range: {df['value'].min():.4f} to {df['value'].max():.4f} mm/day")
                print(f"    Mean: {df['value'].mean():.4f} mm/day")
        except Exception as e:
            print(f"    Error reading file: {e}")
    else:
        print(f"  {scenario.upper()}: FILE NOT FOUND")
        for pattern in evap_future_patterns:
            print(f"    Checked: {os.path.join(PROXY_OUTPUT_DIR, pattern)}")

# Check if files are the same
if len(evap_files) == 2:
    if evap_files['ssp245'] == evap_files['ssp585']:
        print("\n  ⚠️  WARNING: Both scenarios are using the SAME input file!")
    else:
        print("\n  ✓ Different input files for each scenario")

# Step 2: Load calibrated met files
print("\n[STEP 2] Loading calibrated .met files...")
print("-"*80)

calibrated_files = {}
for scenario in scenarios:
    met_filename = f"{MODEL}_{scenario}_{lat_str}_{lon_str}_calibrated.met"
    met_path = os.path.join(OUTPUT_DIR, met_filename)
    
    if os.path.exists(met_path):
        print(f"  {scenario.upper()}: {met_filename}")
        
        # Parse the met file
        try:
            with open(met_path, 'r') as f:
                lines = f.readlines()
            
            # Find data section (skip header)
            data_lines = []
            in_data = False
            for line in lines:
                if line.strip() and not line.strip().startswith('!'):
                    # Check if it's a data line (starts with year)
                    parts = line.strip().split()
                    if len(parts) >= 8 and parts[0].isdigit():
                        in_data = True
                        data_lines.append(line)
            
            # Parse data
            data = []
            for line in data_lines:
                parts = line.strip().split()
                if len(parts) >= 7:
                    year = int(parts[0])
                    day = int(parts[1])
                    evap = float(parts[6])  # evap is 7th column (index 6)
                    
                    # Convert year and day to date
                    date = pd.to_datetime(f"{year}-01-01") + pd.Timedelta(days=day-1)
                    data.append({'date': date, 'evap': evap, 'year': year, 'day': day})
            
            df_met = pd.DataFrame(data)
            df_met['date'] = pd.to_datetime(df_met['date'])
            calibrated_files[scenario] = df_met
            
            print(f"    Rows: {len(df_met):,}")
            print(f"    Date range: {df_met['date'].min().date()} to {df_met['date'].max().date()}")
            print(f"    ETO range: {df_met['evap'].min():.4f} to {df_met['evap'].max():.4f} mm/day")
            print(f"    Mean ETO: {df_met['evap'].mean():.4f} mm/day")
            print(f"    Std ETO: {df_met['evap'].std():.4f} mm/day")
            
        except Exception as e:
            print(f"    Error reading met file: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  {scenario.upper()}: FILE NOT FOUND - {met_path}")

# Step 3: Compare calibrated ETO values
print("\n[STEP 3] Comparing calibrated ETO values...")
print("-"*80)

if len(calibrated_files) == 2:
    df_245 = calibrated_files['ssp245'].copy()
    df_585 = calibrated_files['ssp585'].copy()
    
    # Merge on date for comparison
    comparison = df_245[['date', 'evap']].merge(
        df_585[['date', 'evap']], 
        on='date', 
        how='inner',
        suffixes=('_ssp245', '_ssp585')
    )
    
    if len(comparison) > 0:
        comparison['difference'] = comparison['evap_ssp585'] - comparison['evap_ssp245']
        comparison['abs_difference'] = comparison['difference'].abs()
        comparison['pct_difference'] = (comparison['difference'] / comparison['evap_ssp245'] * 100).replace([np.inf, -np.inf], np.nan)
        
        print(f"  Common dates: {len(comparison):,}")
        print(f"  Date range: {comparison['date'].min().date()} to {comparison['date'].max().date()}")
        print("\n  Statistical Comparison:")
        print(f"    SSP245 mean ETO: {comparison['evap_ssp245'].mean():.4f} mm/day")
        print(f"    SSP585 mean ETO: {comparison['evap_ssp585'].mean():.4f} mm/day")
        print(f"    Mean difference (SSP585 - SSP245): {comparison['difference'].mean():.4f} mm/day")
        print(f"    Std difference: {comparison['difference'].std():.4f} mm/day")
        print(f"    Max absolute difference: {comparison['abs_difference'].max():.4f} mm/day")
        print(f"    Mean absolute difference: {comparison['abs_difference'].mean():.4f} mm/day")
        
        # Check if values are identical
        identical_count = (comparison['evap_ssp245'] == comparison['evap_ssp585']).sum()
        identical_pct = (identical_count / len(comparison)) * 100
        
        print(f"\n  Identity Check:")
        print(f"    Identical values: {identical_count:,} ({identical_pct:.2f}%)")
        
        if identical_pct == 100:
            print("    ⚠️  WARNING: ALL VALUES ARE IDENTICAL!")
        elif identical_pct > 95:
            print("    ⚠️  WARNING: Most values are identical (>95%)")
        else:
            print("    ✓ Values differ between scenarios")
        
        # Monthly comparison
        comparison['month'] = comparison['date'].dt.month
        comparison['year'] = comparison['date'].dt.year
        
        print("\n  Monthly Statistics:")
        monthly_stats = comparison.groupby('month').agg({
            'evap_ssp245': 'mean',
            'evap_ssp585': 'mean',
            'difference': 'mean',
            'abs_difference': 'mean'
        }).round(4)
        monthly_stats.columns = ['SSP245_Mean', 'SSP585_Mean', 'Mean_Diff', 'Mean_Abs_Diff']
        print(monthly_stats.to_string())
        
        # Annual comparison
        print("\n  Annual Statistics:")
        annual_stats = comparison.groupby('year').agg({
            'evap_ssp245': 'mean',
            'evap_ssp585': 'mean',
            'difference': 'mean'
        }).round(4)
        annual_stats.columns = ['SSP245_Mean', 'SSP585_Mean', 'Mean_Diff']
        print(annual_stats.head(10).to_string())
        if len(annual_stats) > 10:
            print(f"    ... ({len(annual_stats) - 10} more years)")
        
        # Save comparison to CSV
        output_csv = os.path.join(OUTPUT_DIR, f"ETO_comparison_SSP245_vs_SSP585_{lat_str}_{lon_str}.csv")
        comparison.to_csv(output_csv, index=False)
        print(f"\n  ✓ Comparison saved to: {os.path.basename(output_csv)}")
        
    else:
        print("  ⚠️  No overlapping dates found between scenarios")
else:
    print("  ⚠️  Cannot compare - one or both calibrated files are missing")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
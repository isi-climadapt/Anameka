# CMIP6 VP & Evap Calibration Workflow Guide

## Overview

This document provides a comprehensive guide to the CMIP6 Vapor Pressure (VP) and Evaporation (Evap) calibration workflow. The workflow transforms raw CMIP6 climate model data into calibrated APSIM-compatible `.met` files through a two-phase process: proxy calculation and calibration.

**Purpose**: Generate calibrated climate data files that match SILO climatology while preserving CMIP6 projected trends for agricultural simulation modeling (APSIM).

---

## Workflow Architecture

The workflow consists of **two main phases**:

1. **Phase 1: Proxy Calculation** - Calculate VP and Evap proxies from CMIP6 NetCDF data
2. **Phase 2: Calibration** - Calibrate proxies to SILO observations using monthly mean-variance scaling

**Prerequisites**:
- CMIP6 NetCDF files organized by model and scenario
- SILO baseline `.met` files (1986-2014) created via SILO API Module_Workflow
- Python environment with required packages (see `requirements.txt`)

---

## Phase 1: Proxy Calculation

### Overview

Phase 1 calculates physically-based proxies for Vapor Pressure (VP) and Evaporation (Evap) from CMIP6 meteorological variables. These proxies serve as the foundation for calibration in Phase 2.

### Step 1.1: Data Preparation

**Notebook**: `Grid_point_CMIP6_retrieval.ipynb` (optional, if data not already extracted)

**Purpose**: Extract CMIP6 NetCDF data for specific grid points

**Inputs**:
- CMIP6 NetCDF files organized in: `{CMIP6_BASE_DIR}/{MODEL} {SCENARIO}/`
- Target coordinates (latitude, longitude)

**Outputs**:
- CSV files for individual variables:
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_tasmax.csv`
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_tasmin.csv`
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_pr.csv`
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_rsds.csv`
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_hurs.csv`
  - `{MODEL}_{SCENARIO}_{LAT}_{LON}_sfcWind.csv` (for Evap calculation)

**Configuration**:
```python
CMIP6_BASE_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\CMIP6"
MODEL = "ACCESS CM2"
SCENARIO = "SSP585"  # or "obs", "SSP245", etc.
LATITUDE = -31.75
LONGITUDE = 117.5999984741211
COORD_TOLERANCE = 0.01  # degrees (~1.1 km)
```

**Note**: This step can be skipped if CMIP6 data is already extracted or if the proxy calculation notebooks extract directly from NetCDF files.

---

### Step 1.2: Vapor Pressure (VP) Proxy Calculation

**Notebook**: `CMPI6_VP_Calculation.ipynb`

**Purpose**: Calculate daily vapor pressure proxy using the SILO method

**Input Variables** (from CMIP6 NetCDF):
- `hurs`: Mean relative humidity (%)
- `tasmax`: Daily maximum temperature (°C)
- `tasmin`: Daily minimum temperature (°C)

**Calculation Method (SILO)**:

1. **Calculate mean temperature**:
   ```
   T_mean = (tasmax + tasmin) / 2
   ```

2. **Calculate saturation vapor pressure** (kPa):
   ```
   e_s(T_mean) = 0.611 × exp(17.27 × T_mean / (T_mean + 237.3))
   ```

3. **Calculate actual vapor pressure** (hPa):
   ```
   VP(hPa) = (hurs/100) × e_s(T_mean) × 10
   ```

**Output**:
- CSV file: `{MODEL}_{SCENARIO}_{LAT}_{LON}_vp_proxy.csv`
- Format: `date, value` (value in hPa)
- One file per model/scenario/coordinate combination

**Configuration**:
```python
MODEL = "ACCESS CM2"
SCENARIO = "SSP585"  # Run for: "obs", "SSP245", "SSP585", etc.
LATITUDE = -31.75
LONGITUDE = 117.5999984741211
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
```

**Execution Notes**:
- Run once for each scenario (obs, SSP245, SSP585, etc.)
- Each run generates one VP proxy CSV file
- Files are saved in the specified output directory

---

### Step 1.3: Evaporation (Evap) Proxy Calculation

**Notebook**: `CMPI6_Evap_Calculation.ipynb`

**Purpose**: Calculate daily reference evapotranspiration (ET₀) using FAO-56 Penman-Monteith method

**Input Variables** (from CMIP6 NetCDF):
- `tasmax`: Daily maximum temperature (°C)
- `tasmin`: Daily minimum temperature (°C)
- `hurs`: Mean relative humidity (%)
- `rsds`: Surface downwelling shortwave radiation (W/m²)
- `sfcWind`: Wind speed at 10m (m/s)

**Calculation Method (FAO-56 Penman-Monteith)**:

1. **Calculate mean temperature**:
   ```
   T_mean = (tasmax + tasmin) / 2
   ```

2. **Convert radiation**: W/m² → MJ/m²/day
   ```
   Rs = rsds × 0.0864
   ```

3. **Convert wind speed**: 10m → 2m height
   ```
   u₂ = u₁₀ × ln(2/z₀) / ln(10/z₀)
   ```
   Where z₀ = 0.0002 m (roughness length for open water)

4. **Calculate vapor pressure**:
   - Saturation: `es = 0.611 × exp(17.27 × T_mean / (T_mean + 237.3))`
   - Actual: `ea = es × hurs / 100`

5. **Calculate ET₀** (mm/day):
   ```
   ET₀ = (0.408 × Δ × (Rn - G) + γ × (900/(T+273)) × u₂ × (es - ea)) / (Δ + γ × (1 + 0.34 × u₂))
   ```
   Where:
   - `Δ` = slope of vapor pressure curve (kPa/°C)
   - `Rn` = net radiation (MJ/m²/day) ≈ 0.77 × Rs
   - `G` = soil heat flux (assumed 0 for daily)
   - `γ` = psychrometric constant ≈ 0.0675 kPa/°C

**Output**:
- CSV file: `{MODEL}_{SCENARIO}_{LAT}_{LON}_eto.csv` or `{MODEL}_{SCENARIO}_{LAT}_{LON}_evap_proxy.csv`
- Format: `date, value` (value in mm/day)
- One file per model/scenario/coordinate combination

**Configuration**:
```python
MODEL = "ACCESS CM2"
SCENARIO = "SSP585"  # Run for: "obs", "SSP245", "SSP585", etc.
LATITUDE = -31.75
LONGITUDE = 117.5999984741211
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
```

**Execution Notes**:
- Run once for each scenario (obs, SSP245, SSP585, etc.)
- Each run generates one Evap/ET₀ proxy CSV file
- Files are saved in the specified output directory

---

### Step 1.4: Create CMIP6 .met Files

**Notebook**: `ACCESS met file creation.ipynb`

**Purpose**: Combine base CMIP6 variables with VP and Evap proxies to create complete `.met` files

**Inputs**:
1. **Base variables** (from CMIP6 NetCDF or cached CSV):
   - `tasmax` → `maxt` (maximum temperature, °C)
   - `tasmin` → `mint` (minimum temperature, °C)
   - `pr` → `rain` (precipitation, mm)
   - `rsds` → `radn` (radiation, MJ/m², converted from W/m²)

2. **VP proxy** (from Step 1.2):
   - CSV file: `{MODEL}_{SCENARIO}_{LAT}_{LON}_vp_proxy.csv`
   - Loaded as `vp` column (hPa)

3. **Evap proxy** (from Step 1.3):
   - CSV file: `{MODEL}_{SCENARIO}_{LAT}_{LON}_eto.csv`
   - Loaded as `evap` column (mm/day)

**Process**:
1. Extract or load base variables from NetCDF files (with caching)
2. Load VP and Evap from CSV files generated in Steps 1.2 and 1.3
3. Merge all variables on date
4. Calculate metadata:
   - `tav`: Annual average temperature (°C)
   - `amp`: Annual amplitude in mean monthly temperature (°C)
5. Create complete date range (handles leap years)
6. Format as APSIM `.met` file

**Output**:
- MET file: `{MODEL}_{SCENARIO}_{LAT}_{LON}.met`
- CSV file: `{MODEL}_{SCENARIO}_{LAT}_{LON}.csv` (same data)
- Format: APSIM MET format with all required columns

**Configuration**:
```python
MODEL = "ACCESS CM2"
SCENARIO = "obs"  # Run for: "obs", "SSP245", "SSP585", etc.
LATITUDE = -31.75
LONGITUDE = 117.5999984741211
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
```

**Execution Notes**:
- **CRITICAL**: Run Steps 1.2 and 1.3 first to generate VP and Evap CSV files
- Run once for each scenario (obs, SSP245, SSP585, etc.)
- Each run generates one complete `.met` file
- Base variables are cached to CSV for faster subsequent runs

**MET File Structure**:
```
[weather.met.weather]
latitude = -31.75  (DECIMAL DEGREES)
longitude = 117.60  (DECIMAL DEGREES)
tav = XX.XX (oC) ! Annual average ambient temperature.
amp = XX.XX (oC) ! Annual amplitude in mean monthly temperature.
...
year  day radn  maxt   mint  rain  evap    vp   code
```

---

## Phase 2: Calibration

### Overview

Phase 2 calibrates the CMIP6 VP and Evap proxies to match SILO climatology using monthly mean-variance scaling. The calibration parameters are derived from the historical baseline period (1986-2014) and applied to all time periods, including future scenarios.

### Step 2.1: Calibration Setup

**Notebook**: `CMPI6_VP_Evap_Calibration.ipynb`

**Purpose**: Calibrate VP and Evap to match SILO observations

**Required Inputs**:

1. **SILO baseline .met file** (1986-2014):
   - File: `SILO_1986-2014_{LAT}_{LON}.met`
   - Contains: SILO observed VP (hPa) and Evap (mm/day)
   - Created via: SILO API Module_Workflow (external process)

2. **CMIP6 obs baseline .met file** (1985-2014):
   - File: `{MODEL}_obs_{LAT}_{LON}.met`
   - Created in Step 1.4 with SCENARIO="obs"

3. **CMIP6 future scenario .met files**:
   - Files: `{MODEL}_{SCENARIO}_{LAT}_{LON}.met` (e.g., SSP245, SSP585)
   - Created in Step 1.4 for each scenario

4. **VP proxy CSV files** (from Step 1.2):
   - `{MODEL}_obs_{LAT}_{LON}_vp_proxy.csv`
   - `{MODEL}_{SCENARIO}_{LAT}_{LON}_vp_proxy.csv` (for each scenario)

5. **Evap proxy CSV files** (from Step 1.3):
   - `{MODEL}_obs_{LAT}_{LON}_eto.csv`
   - `{MODEL}_{SCENARIO}_{LAT}_{LON}_eto.csv` (for each scenario)

**Configuration**:
```python
MODEL = "ACCESS_CM2"
SCENARIOS = ["ssp245", "ssp585"]  # Future scenarios to calibrate
COORDINATES = [(-31.75, 117.60)]  # List of (lat, lon) tuples

BASELINE_START = "1986-01-01"
BASELINE_END = "2014-12-31"

INPUT_MET_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
PROXY_OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042\calibrated"
```

---

### Step 2.2: Calibration Process

**Calibration Method**: Monthly Mean-Variance Scaling

For each variable (VP and Evap) and each calendar month **m** (1-12):

1. **Extract baseline data** (1986-2014):
   - SILO observed values (target)
   - CMIP6 obs proxy values (source)

2. **Calculate monthly statistics**:
   - SILO: `μₛ(m)`, `σₛ(m)` (mean and std for month m)
   - CMIP6 obs: `μ꜀(m)`, `σ꜀(m)` (mean and std for month m)

3. **Apply calibration transformation**:
   ```
   x′ = μₛ(m) + (x − μ꜀(m)) × (σₛ(m) / σ꜀(m))
   ```
   Where:
   - `x` = original CMIP6 value
   - `x′` = calibrated value
   - `μₛ(m)` = SILO mean for month m (target anchor)
   - `μ꜀(m)` = CMIP6 obs mean for month m (source reference)
   - `σₛ(m)` = SILO std for month m (target scale)
   - `σ꜀(m)` = CMIP6 obs std for month m (source scale)

4. **Special cases**:
   - If `σ꜀(m) ≈ 0`: Apply mean shift only: `x′ = x + (μₛ(m) − μ꜀(m))`
   - Enforce physical bounds: `VP ≥ 0`, `Evap ≥ 0`

5. **Apply to all time periods**:
   - Calibration parameters (derived from 1986-2014) are held fixed
   - Applied to CMIP6 obs baseline (for QC validation)
   - Applied to all future scenarios (SSP245, SSP585, etc.)

**Key Properties**:
- ✅ Preserves CMIP6 projected trends and anomalies
- ✅ Matches SILO monthly climatology (mean and variance)
- ✅ Maintains temporal structure and variability
- ✅ Uses fixed calibration parameters (no future data leakage)

---

### Step 2.3: Generate Calibrated .met Files

**Process**:

1. **Read original CMIP6 .met file** (for each scenario)

2. **Replace columns**:
   - `vp` column → calibrated VP series
   - `evap` column → calibrated Evap series
   - All other columns remain unchanged

3. **Recalculate metadata**:
   - `tav`: Annual average temperature (from maxt/mint)
   - `amp`: Annual amplitude (from maxt/mint)

4. **Write calibrated .met file**:
   - Format: Matches template file structure exactly
   - Filename: `{MODEL}_{SCENARIO}_{LAT}_{LON}_calibrated.met`

**Output**:
- Calibrated `.met` files (one per scenario/coordinate)
- Format: APSIM MET format with calibrated VP and Evap

---

### Step 2.4: Generate Diagnostics and Reports

**Diagnostics Generated**:

**A) Baseline Validation (1986-2014)**:
- Monthly statistics tables (CSV): SILO vs raw CMIP6 vs corrected CMIP6
- Monthly climatology plots (PNG):
  - Mean comparison (SILO, raw, corrected)
  - Standard deviation comparison
- Daily time-series overlay (representative year)
- Distribution histograms

**B) Future Scenario Validation**:
- Trend sanity check plots (raw vs corrected)
- Variance preservation plots (rolling 30-day std)
- Scenario separation plots (if multiple scenarios)

**C) Physical Bounds Validation**:
- No NaNs, no negative values
- Date continuity and length matching

**D) Calibration Report** (Markdown):
- Model, coordinates, baseline period information
- VP calibration statistics (monthly mean/std comparison)
- Evap calibration statistics (monthly mean/std comparison)
- Summary statistics (min, mean, max) for all series
- Warnings and validation results

**Output Structure**:
```
OUTPUT_DIR/
├── {MODEL}_{SCENARIO}_{LAT}_{LON}_calibrated.met
├── calibration_report_{MODEL}_{LAT}_{LON}.md
└── diagnostics/
    └── {MODEL}/
        └── {LAT}_{LON}/
            ├── *_baseline_monthly_stats_*.csv
            ├── *_baseline_monthly_mean_*.png
            ├── *_baseline_monthly_std_*.png
            ├── *_baseline_daily_overlay_*.png
            ├── *_baseline_distribution_*.png
            ├── *_{SCENARIO}_trend_raw_vs_corrected_*.png
            └── *_{SCENARIO}_rolling_std_raw_vs_corrected_*.png
```

---

## Complete Workflow Execution Order

### Preparation Phase

1. **Obtain CMIP6 NetCDF files** (organized by model/scenario)
2. **Create SILO baseline .met files** (1986-2014) via SILO API Module_Workflow
3. **Set up output directories** and configure paths

### Phase 1: Proxy Calculation

**For each scenario** (obs, SSP245, SSP585, etc.):

1. **Run `CMPI6_VP_Calculation.ipynb`**
   - Input: CMIP6 NetCDF files (hurs, tasmax, tasmin)
   - Output: VP proxy CSV file

2. **Run `CMPI6_Evap_Calculation.ipynb`**
   - Input: CMIP6 NetCDF files (tasmax, tasmin, hurs, rsds, sfcWind)
   - Output: Evap/ET₀ proxy CSV file

3. **Run `ACCESS met file creation.ipynb`**
   - Input: CMIP6 NetCDF files + VP/Evap CSV files
   - Output: Complete CMIP6 .met file

**Result**: Complete CMIP6 .met files for obs baseline and all future scenarios

### Phase 2: Calibration

**Run once** (processes all scenarios and coordinates):

1. **Run `CMPI6_VP_Evap_Calibration.ipynb`**
   - Input: SILO .met files + CMIP6 .met files + VP/Evap proxy CSVs
   - Process:
     - Extract baseline data (1986-2014)
     - Calculate calibration parameters (monthly statistics)
     - Apply calibration to all scenarios
     - Generate calibrated .met files
     - Generate diagnostics and reports
   - Output: Calibrated .met files + diagnostics + reports

**Result**: Calibrated CMIP6 .met files ready for APSIM simulations

---

## Key Configuration Parameters

### Common Settings

```python
# Model and Scenario
MODEL = "ACCESS CM2"  # or "ACCESS_CM2" (format varies by notebook)
SCENARIOS = ["obs", "ssp245", "ssp585"]  # Scenarios to process

# Coordinates
LATITUDE = -31.75
LONGITUDE = 117.5999984741211
COORDINATES = [(-31.75, 117.60)]  # For calibration (list of tuples)

# Directories
CMIP6_BASE_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\CMIP6"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Anameka_South_16_226042"
INPUT_MET_DIR = OUTPUT_DIR  # Where CMIP6 .met files are located
PROXY_OUTPUT_DIR = OUTPUT_DIR  # Where VP/Evap CSV files are located

# Calibration Period
BASELINE_START = "1986-01-01"
BASELINE_END = "2014-12-31"
```

### Coordinate Formatting

**Note**: Different notebooks use different coordinate string formats:
- **Underscore format**: `neg31_75_117_60` (used in some CSV filenames)
- **Decimal format with neg prefix**: `neg31.75_117.60` (used in MET filenames)
- **Decimal format with negative sign**: `-31.75_117.60` (alternative format)

The notebooks handle format conversion automatically when searching for files.

---

## File Naming Conventions

### VP Proxy Files
- Format: `{MODEL}_{SCENARIO}_{LAT}_{LON}_vp_proxy.csv`
- Example: `ACCESS_CM2_SSP585_neg31.75_117.60_vp_proxy.csv`

### Evap Proxy Files
- Format: `{MODEL}_{SCENARIO}_{LAT}_{LON}_eto.csv` or `{MODEL}_{SCENARIO}_{LAT}_{LON}_evap_proxy.csv`
- Example: `ACCESS_CM2_SSP585_neg31.75_117.60_eto.csv`

### CMIP6 .met Files
- Format: `{MODEL}_{SCENARIO}_{LAT}_{LON}.met`
- Example: `ACCESS_CM2_SSP585_neg31.75_117.60.met`

### Calibrated .met Files
- Format: `{MODEL}_{SCENARIO}_{LAT}_{LON}_calibrated.met`
- Example: `ACCESS_CM2_SSP585_neg31.75_117.60_calibrated.met`

### SILO Baseline Files
- Format: `SILO_1986-2014_{LAT}_{LON}.met`
- Example: `SILO_1986-2014_-31.75_117.60.met`

---

## Troubleshooting

### Common Issues

1. **VP/Evap CSV files not found**:
   - Ensure Steps 1.2 and 1.3 have been executed
   - Check file naming matches expected format
   - Verify output directory paths

2. **SILO .met file not found**:
   - Create SILO baseline files via SILO API Module_Workflow
   - Verify file naming: `SILO_1986-2014_{LAT}_{LON}.met`
   - Check file location matches `INPUT_MET_DIR`

3. **Date range mismatches**:
   - Ensure CMIP6 obs data covers 1985-2014 (or at least 1986-2014)
   - Verify SILO data covers 1986-2014
   - Check for missing dates in source files

4. **Constant values warning**:
   - Indicates missing/corrupted source NetCDF data
   - Check original CMIP6 files for that year
   - May need to re-extract data

5. **Coordinate format issues**:
   - Notebooks handle multiple formats automatically
   - If files not found, check actual filenames match expected patterns
   - Verify coordinate string formatting (neg prefix vs negative sign)

---

## Output Summary

### Phase 1 Outputs (per scenario/coordinate)

- 1 VP proxy CSV file
- 1 Evap/ET₀ proxy CSV file
- 1 CMIP6 .met file

### Phase 2 Outputs (per scenario/coordinate)

- 1 Calibrated .met file
- 1 Calibration report (Markdown)
- 2 CSV diagnostic files (VP and Evap monthly stats)
- 12+ PNG diagnostic plots (baseline validation + future scenario validation)

**Total**: ~17 files per coordinate (1 report + 2 CSVs + 12+ plots + 1+ calibrated .met files)

---

## Best Practices

1. **Execute in order**: Complete Phase 1 before starting Phase 2
2. **Run all scenarios**: Process obs baseline and all future scenarios in Phase 1
3. **Verify inputs**: Check that all required files exist before running calibration
4. **Review diagnostics**: Always review calibration reports and diagnostic plots
5. **Validate outputs**: Check calibrated .met files for physical bounds and date continuity
6. **Keep backups**: Save original CMIP6 .met files before calibration
7. **Document configurations**: Record model, scenarios, and coordinates used for each run

---

## References

- **SILO Method**: Australian Bureau of Meteorology SILO data service
- **FAO-56 Penman-Monteith**: Allen et al. (1998) - Crop evapotranspiration guidelines
- **CMIP6**: Coupled Model Intercomparison Project Phase 6
- **APSIM**: Agricultural Production Systems sIMulator

---

*Last Updated: 2025-01-27*
*Workflow Version: 1.0*


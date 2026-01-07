# CMIP6 VP & Evap Calibration Workflow Diagram

## Complete Workflow: From CMIP6 Data to Calibrated .met Files

### Mermaid Flowchart (for Markdown viewers with Mermaid support)

```mermaid
graph TB
    subgraph Phase1["PHASE 1: PROXY CALCULATION"]
        subgraph VPCalc["CMPI6_VP_Calculation.ipynb"]
            VPInput[CMIP6 NetCDF Files<br/>hurs, tasmax, tasmin]
            VPCalc[Calculate VP using SILO Method<br/>VP = hurs/100 × e_s × 10]
            VPOutput[VP Proxy CSV Files<br/>date, value hPa]
            VPInput --> VPCalc --> VPOutput
        end
        
        subgraph EvapCalc["CMPI6_Evap_Calculation.ipynb"]
            EvapInput[CMIP6 NetCDF Files<br/>tasmax, tasmin, hurs<br/>rsds, sfcWind]
            EvapCalc[Calculate ET₀ using<br/>FAO-56 Penman-Monteith]
            EvapOutput[Evap/ET₀ Proxy CSV Files<br/>date, value mm/day]
            EvapInput --> EvapCalc --> EvapOutput
        end
    end
    
    subgraph Phase2["PHASE 2: CALIBRATION"]
        subgraph Calib["CMPI6_VP_Evap_Calibration.ipynb"]
            CalibInput1[SILO .met Files<br/>1986-2014 baseline]
            CalibInput2[CMIP6 .met Files<br/>obs + future scenarios]
            CalibInput3[VP Proxy CSVs<br/>from Phase 1]
            CalibInput4[Evap Proxy CSVs<br/>from Phase 1]
            
            Step1[STEP 1: Load Files]
            Step2[STEP 2: Extract Baseline Data<br/>1986-2014]
            Step3[STEP 3: Calibration Parametrization<br/>Monthly mean-variance scaling]
            Step4[STEP 4: Generate Calibrated .met]
            Step5[STEP 5: Diagnostics & Reports]
            
            CalibInput1 --> Step1
            CalibInput2 --> Step1
            CalibInput3 --> Step1
            CalibInput4 --> Step1
            Step1 --> Step2 --> Step3 --> Step4 --> Step5
            
            CalibOutput1[Calibrated .met Files]
            CalibOutput2[Diagnostics<br/>Plots & CSV]
            CalibOutput3[Calibration Reports<br/>Markdown]
            
            Step5 --> CalibOutput1
            Step5 --> CalibOutput2
            Step5 --> CalibOutput3
        end
    end
    
    VPOutput --> CalibInput3
    EvapOutput --> CalibInput4
    
    style Phase1 fill:#e1f5ff
    style Phase2 fill:#fff4e1
    style VPCalc fill:#e8f5e9
    style EvapCalc fill:#e8f5e9
    style Calib fill:#fce4ec
```

## Complete Workflow: From CMIP6 Data to Calibrated .met Files

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 1: PROXY CALCULATION                                  │
│                    (CMPI6_VP_Calculation.ipynb & CMPI6_Evap_Calculation.ipynb)      │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 1: CMPI6_VP_Calculation.ipynb                                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  INPUTS:                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ CMIP6 NetCDF Files (from Grid_point_CMIP6_retrieval.ipynb)                   │  │
│  │   • hurs (mean relative humidity, %)                                         │  │
│  │   • tasmax (daily max temperature, °C)                                        │  │
│  │   • tasmin (daily min temperature, °C)                                       │  │
│  │   For: <MODEL>_<SCENARIO>_<LAT>_<LON>                                         │  │
│  │   Scenarios: obs (baseline), ssp245, ssp585, etc.                            │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  CALCULATION:                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ SILO Method for VP Calculation:                                              │  │
│  │                                                                               │  │
│  │ 1. Calculate mean temperature:                                               │  │
│  │    T_mean = (tasmax + tasmin) / 2                                            │  │
│  │                                                                               │  │
│  │ 2. Calculate saturation vapor pressure (kPa):                               │  │
│  │    e_s(T_mean) = 0.611 × exp(17.27 × T_mean / (T_mean + 237.3))              │  │
│  │                                                                               │  │
│  │ 3. Calculate actual vapor pressure (hPa):                                    │  │
│  │    VP(hPa) = (hurs/100) × e_s(T_mean) × 10                                   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  OUTPUTS:                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ VP Proxy CSV Files (PROXY_OUTPUT_DIR):                                       │  │
│  │   • <MODEL>_obs_<LAT>_<LON>_vp_proxy.csv                                     │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>_vp_proxy.csv                              │  │
│  │   Format: date, value (hPa)                                                   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 2: CMPI6_Evap_Calculation.ipynb                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  INPUTS:                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ CMIP6 NetCDF Files:                                                          │  │
│  │   • tasmax, tasmin (temperature, °C)                                          │  │
│  │   • hurs (mean relative humidity, %)                                         │  │
│  │   • rsds (surface downwelling shortwave radiation, W/m²)                     │  │
│  │   • sfcWind (wind speed at 10m, m/s)                                         │  │
│  │   For: <MODEL>_<SCENARIO>_<LAT>_<LON>                                         │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  CALCULATION:                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ FAO-56 Penman-Monteith Method for ET₀:                                      │  │
│  │                                                                               │  │
│  │ 1. Calculate mean temperature: T_mean = (tasmax + tasmin) / 2                │  │
│  │                                                                               │  │
│  │ 2. Calculate vapor pressure from hurs and T_mean                             │  │
│  │                                                                               │  │
│  │ 3. Convert rsds from W/m² to MJ/m²/day                                       │  │
│  │                                                                               │  │
│  │ 4. Adjust sfcWind from 10m to 2m height                                      │  │
│  │                                                                               │  │
│  │ 5. Apply FAO-56 Penman-Monteith formula:                                      │  │
│  │    ET₀ = f(radiation, temperature, humidity, wind)                            │  │
│  │    Output: ET₀ (mm/day) - reference evapotranspiration                      │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  OUTPUTS:                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ Evap/ET₀ Proxy CSV Files (PROXY_OUTPUT_DIR):                                 │  │
│  │   • <MODEL>_obs_<LAT>_<LON>_evap_proxy.csv                                  │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>_evap_proxy.csv                            │  │
│  │   Format: date, value (mm/day)                                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    │
                                    ▼

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2: CALIBRATION                                        │
│                    (CMPI6_VP_Evap_Calibration.ipynb)                                │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  NOTEBOOK 3: CMPI6_VP_Evap_Calibration.ipynb                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  CONFIGURATION:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ • MODEL: e.g., "ACCESS_CM2"                                                  │  │
│  │ • SCENARIO: e.g., "ssp585"                                                   │  │
│  │ • COORDINATES: [(lat, lon), ...]                                             │  │
│  │ • BASELINE_START: "1986-01-01"                                               │  │
│  │ • BASELINE_END: "2014-12-31"                                                 │  │
│  │ • INPUT_MET_DIR: Directory with .met files                                     │  │
│  │ • PROXY_OUTPUT_DIR: Directory with proxy CSVs                                 │  │
│  │ • OUTPUT_DIR: Directory for calibrated outputs                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  STEP 1: Load Required Files                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ INPUTS LOADED:                                                              │  │
│  │                                                                               │  │
│  │ From INPUT_MET_DIR:                                                          │  │
│  │   • SILO_1986-2014_<LAT>_<LON>.met                                          │  │
│  │     └─ Contains: SILO observed VP (hPa) and Evap (mm/day) for baseline       │  │
│  │                                                                               │  │
│  │   • <MODEL>_obs_<LAT>_<LON>.met                                              │  │
│  │     └─ CMIP6 baseline .met file (1985-2014)                                  │  │
│  │                                                                               │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>.met                                       │  │
│  │     └─ CMIP6 future scenario .met file                                       │  │
│  │                                                                               │  │
│  │ From PROXY_OUTPUT_DIR:                                                        │  │
│  │   • <MODEL>_obs_<LAT>_<LON>_vp_proxy.csv                                     │  │
│  │     └─ CMIP6 obs VP proxy (from Notebook 1)                                 │  │
│  │                                                                               │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>_vp_proxy.csv                              │  │
│  │     └─ CMIP6 future VP proxy (from Notebook 1)                               │  │
│  │                                                                               │  │
│  │   • <MODEL>_obs_<LAT>_<LON>_evap_proxy.csv                                   │  │
│  │     └─ CMIP6 obs ET₀ proxy (from Notebook 2)                                 │  │
│  │                                                                               │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>_evap_proxy.csv                            │  │
│  │     └─ CMIP6 future ET₀ proxy (from Notebook 2)                              │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  STEP 2: Extract Baseline Data (1986-2014)                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ • Extract SILO VP and Evap from SILO .met file                               │  │
│  │ • Filter to baseline period: 1986-01-01 to 2014-12-31                        │  │
│  │ • Extract CMIP6 obs VP and Evap proxies from CSV files                       │  │
│  │ • Align all time series by date                                               │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  STEP 3: Calibration Parametrization (Baseline Period)                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ For each variable (VP and Evap) and each calendar month (1-12):                │  │
│  │                                                                               │  │
│  │ 1. Calculate monthly statistics for baseline period:                         │  │
│  │    • SILO (target): μₛ(m), σₛ(m)                                              │  │
│  │    • CMIP6 obs (source): μ꜀(m), σ꜀(m)                                         │  │
│  │                                                                               │  │
│  │ 2. Apply monthly mean-variance bias correction:                             │  │
│  │    If σ꜀(m) ≈ 0:                                                             │  │
│  │      x′ = x + (μₛ(m) − μ꜀(m))  [mean shift only]                            │  │
│  │    Else:                                                                      │  │
│  │      x′ = μₛ(m) + (x − μ꜀(m)) × (σₛ(m) / σ꜀(m))  [mean-variance scaling]    │  │
│  │                                                                               │  │
│  │ 3. Enforce physical bounds:                                                  │  │
│  │    • VP ≥ 0 (hPa)                                                            │  │
│  │    • Evap ≥ 0 (mm/day)                                                       │  │
│  │                                                                               │  │
│  │ 4. Apply correction to:                                                       │  │
│  │    • CMIP6 obs baseline (for QC validation)                                  │  │
│  │    • CMIP6 future scenario (for calibrated output)                            │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  STEP 4: Generate Calibrated .met File                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Read original CMIP6 future .met file                                      │  │
│  │                                                                               │  │
│  │ 2. Replace columns:                                                          │  │
│  │    • vp column → calibrated VP series                                         │  │
│  │    • evap column → calibrated Evap series                                     │  │
│  │                                                                               │  │
│  │ 3. Recalculate metadata:                                                     │  │
│  │    • tav (annual average temperature)                                         │  │
│  │    • amp (temperature amplitude)                                              │  │
│  │                                                                               │  │
│  │ 4. Write calibrated .met file using template format:                      │  │
│  │    • Match exact header structure from template                               │  │
│  │    • Preserve column order and formatting                                     │  │
│  │    • Output: <MODEL>_<SCENARIO>_<LAT>_<LON>_calibrated.met                  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  STEP 5: Generate Diagnostics & Reports                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ A) Baseline Validation (1986-2014):                                           │  │
│  │    • Monthly stats tables (SILO vs raw vs corrected)                          │  │
│  │    • Monthly climatology plots (mean & std)                                   │  │
│  │    • Daily time-series overlay (representative year)                          │  │
│  │    • Distribution histograms                                                   │  │
│  │                                                                               │  │
│  │ B) Future Scenario Checks:                                                    │  │
│  │    • Trend sanity check (raw vs corrected)                                     │  │
│  │    • Variance preservation (rolling std)                                        │  │
│  │    • Scenario separation (if multiple scenarios available)                     │  │
│  │                                                                               │  │
│  │ C) Physical Bounds Validation:                                                │  │
│  │    • No NaNs, no negative values                                              │  │
│  │    • Date continuity and length matching                                      │  │
│  │                                                                               │  │
│  │ D) Calibration Report:                                                        │  │
│  │    • Markdown report with summary statistics                                  │  │
│  │    • Warnings and validation results                                           │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                                 │
│                                    ▼                                                 │
│  OUTPUTS:                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │ Calibrated .met Files (OUTPUT_DIR):                                          │  │
│  │   • <MODEL>_<SCENARIO>_<LAT>_<LON>_calibrated.met                           │  │
│  │                                                                               │  │
│  │ Diagnostics (OUTPUT_DIR/diagnostics/<MODEL>/<LAT>_<LON>/):                   │  │
│  │   • Monthly stats CSV files                                                  │  │
│  │   • Baseline validation plots (PNG)                                           │  │
│  │   • Future scenario validation plots (PNG)                                    │  │
│  │                                                                               │  │
│  │ Reports (OUTPUT_DIR):                                                         │  │
│  │   • calibration_report_<MODEL>_<LAT>_<LON>.md                                │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘

```

## Data Flow Summary

### Input Sources:
1. **CMIP6 NetCDF Files** → Retrieved via `Grid_point_CMIP6_retrieval.ipynb`
2. **SILO .met Files** → Created via `silo_met_file_creation.py` (SILO API Module_Workflow)
3. **CMIP6 .met Files** → Created via `ACCESS met file creation.ipynb` or similar

### Processing Pipeline:
1. **Phase 1 (Proxy Calculation):**
   - `CMPI6_VP_Calculation.ipynb` → VP proxy CSVs
   - `CMPI6_Evap_Calculation.ipynb` → Evap/ET₀ proxy CSVs

2. **Phase 2 (Calibration):**
   - `CMPI6_VP_Evap_Calibration.ipynb` → Calibrated .met files + diagnostics

### Key Calibration Formula:
For each calendar month **m**:
```
x′ = μₛ(m) + (x − μ꜀(m)) × (σₛ(m) / σ꜀(m))
```
Where:
- **x** = original CMIP6 value
- **x′** = calibrated value
- **μₛ(m)** = SILO mean for month m (target)
- **μ꜀(m)** = CMIP6 obs mean for month m (source)
- **σₛ(m)** = SILO std for month m (target)
- **σ꜀(m)** = CMIP6 obs std for month m (source)

### Output Structure:
```
OUTPUT_DIR/
├── <MODEL>_<SCENARIO>_<LAT>_<LON>_calibrated.met
├── calibration_report_<MODEL>_<LAT>_<LON>.md
└── diagnostics/
    └── <MODEL>/
        └── <LAT>_<LON>/
            ├── *_baseline_monthly_stats_*.csv
            ├── *_baseline_monthly_mean_*.png
            ├── *_baseline_monthly_std_*.png
            ├── *_baseline_daily_overlay_*.png
            ├── *_baseline_distribution_*.png
            ├── *_<SCENARIO>_trend_raw_vs_corrected_*.png
            └── *_<SCENARIO>_rolling_std_raw_vs_corrected_*.png
```

## Notes:
- **Baseline Period:** 1986-2014 (historical overlap where both SILO and CMIP6 obs data are available)
- **Calibration Method:** Monthly mean-variance scaling to match SILO climatology
- **Physical Bounds:** VP ≥ 0, Evap ≥ 0 enforced
- **Template Format:** All output .met files match the exact structure of the template file

---

## Simplified Step-by-Step Summary

### Step 1: Calculate VP Proxies
**Notebook:** `CMPI6_VP_Calculation.ipynb`
- **Input:** CMIP6 NetCDF files (hurs, tasmax, tasmin)
- **Process:** Apply SILO method to calculate VP
- **Output:** VP proxy CSV files (one per model/scenario/coordinate)

### Step 2: Calculate Evap/ET₀ Proxies
**Notebook:** `CMPI6_Evap_Calculation.ipynb`
- **Input:** CMIP6 NetCDF files (tasmax, tasmin, hurs, rsds, sfcWind)
- **Process:** Apply FAO-56 Penman-Monteith method to calculate ET₀
- **Output:** Evap/ET₀ proxy CSV files (one per model/scenario/coordinate)

### Step 3: Calibrate VP and Evap
**Notebook:** `CMPI6_VP_Evap_Calibration.ipynb`
- **Inputs:**
  - SILO .met files (baseline 1986-2014)
  - CMIP6 .met files (obs baseline + future scenarios)
  - VP proxy CSVs (from Step 1)
  - Evap proxy CSVs (from Step 2)
- **Process:**
  1. Extract baseline data (1986-2014)
  2. Calculate monthly statistics (mean, std) for SILO and CMIP6 obs
  3. Apply monthly mean-variance bias correction
  4. Generate calibrated .met files
  5. Run diagnostic validation
- **Outputs:**
  - Calibrated .met files
  - Diagnostic plots and CSV files
  - Calibration reports

### Key Relationships:
```
CMIP6 Raw Data
    ↓
[VP Calculation] → VP Proxy CSVs ──┐
                                    ├─→ [Calibration] → Calibrated .met Files
[Evap Calculation] → Evap Proxy CSVs ──┘
                                    ↑
                            SILO Baseline Data
```

### Calibration Formula (per calendar month):
```
Calibrated Value = SILO_mean(month) + (Raw_Value - CMIP6_mean(month)) × (SILO_std(month) / CMIP6_std(month))
```

This ensures the calibrated CMIP6 data matches SILO's monthly mean and variance patterns.


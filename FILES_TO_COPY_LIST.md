# Files to Copy to Final Folder

## Files Created by Calibration Notebook

### 1. Calibrated .met Files (per scenario)
- `ACCESS_CM2_obs_neg31.45_117.55_calibrated.met`
- `ACCESS_CM2_ssp245_neg31.45_117.55_calibrated.met`
- `ACCESS_CM2_ssp585_neg31.45_117.55_calibrated.met`

### 2. Calibrated .csv Files (per scenario, created alongside .met files)
- `ACCESS_CM2_obs_neg31.45_117.55_calibrated.csv`
- `ACCESS_CM2_ssp245_neg31.45_117.55_calibrated.csv`
- `ACCESS_CM2_ssp585_neg31.45_117.55_calibrated.csv`

### 3. Raw (Uncalibrated) .met Files (per scenario)
- `ACCESS_CM2_obs_neg31.45_117.55.met`
- `ACCESS_CM2_ssp245_neg31.45_117.55.met`
- `ACCESS_CM2_ssp585_neg31.45_117.55.met`

### 4. Calibration Report (one per coordinate, not per scenario)
- `calibration_report_ACCESS_CM2_-31.45_117.55.md`

### 5. Diagnostics Folder (contains CSV stats and PNG plots)
- `diagnostics/ACCESS_CM2/-31.45_117.55/`
  - `ACCESS_CM2_-31.45_117.55_baseline_monthly_stats_vp.csv`
  - `ACCESS_CM2_-31.45_117.55_baseline_monthly_stats_evap.csv`
  - `ACCESS_CM2_-31.45_117.55_comprehensive_analysis_report.txt`
  - Various PNG plot files (monthly climatology, daily overlay, distribution, trend checks, variance preservation)

## Summary
- **Total .met files**: 6 (3 calibrated + 3 raw)
- **Total .csv files**: 3 (calibrated versions)
- **Total reports**: 1 (calibration report)
- **Total diagnostics folder**: 1 (with multiple CSV and PNG files inside)

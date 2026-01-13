# File Creation Issues - Summary and Fixes

## Issues Identified

The calibration notebook is not creating files because **required input files are missing or have incorrect naming patterns**. The notebook correctly detects missing files and skips processing.

### Issue 1: SILO File Year Range Mismatch
- **Expected:** `SILO_1986-2014_-31.45_117.55.met`
- **Found:** `SILO_1985-2014_-31.45_117.55.met`
- **Fix:** Update notebook to try both year ranges (1985-2014 and 1986-2014)

### Issue 2: Missing VP Future Files for Coordinates -31.45, 117.55
- **Expected:** 
  - `ACCESS_CM2_ssp245_neg31.45_117.55_vp.csv`
  - `ACCESS_CM2_ssp585_neg31.45_117.55_vp.csv`
- **Found:** Files exist for different coordinates (-31.50, 117.55):
  - `ACCESS_CM2_SSP245_neg31.50_117.55_vp.csv`
  - `ACCESS_CM2_SSP585_neg31.50_117.55_vp.csv`
- **Fix:** Need to either:
  1. Generate VP files for coordinates -31.45, 117.55, OR
  2. Update coordinates in notebook to -31.50, 117.55

### Issue 3: Scenario Name Case Mismatch
- **Notebook uses:** `ssp245`, `ssp585` (lowercase)
- **Files use:** `SSP245`, `SSP585` (uppercase)
- **Fix:** Update notebook to try both lowercase and uppercase scenario names

## Required Files Checklist

For coordinates **-31.45, 117.55**, you need:

### For "obs" scenario:
- ✅ `SILO_1985-2014_-31.45_117.55.met` (or 1986-2014) - **EXISTS but wrong year range**
- ✅ `ACCESS_CM2_obs_neg31.45_117.55.met` - **EXISTS**
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_vp.csv` - **EXISTS**
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_eto.csv` - **EXISTS**

### For "ssp245" scenario:
- ✅ `SILO_1985-2014_-31.45_117.55.met` (or 1986-2014) - **EXISTS but wrong year range**
- ✅ `ACCESS_CM2_obs_neg31.45_117.55.met` - **EXISTS**
- ✅ `ACCESS_CM2_ssp245_neg31.45_117.55.met` - **EXISTS** (as `ACCESS_CM2_ssp245_neg31.45_117.55.met`)
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_vp.csv` - **EXISTS**
- ❌ `ACCESS_CM2_ssp245_neg31.45_117.55_vp.csv` - **MISSING** (only exists for -31.50)
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_eto.csv` - **EXISTS**
- ✅ `ACCESS_CM2_SSP245_neg31.45_117.55_eto.csv` - **EXISTS** (uppercase SSP245)

### For "ssp585" scenario:
- ✅ `SILO_1985-2014_-31.45_117.55.met` (or 1986-2014) - **EXISTS but wrong year range**
- ✅ `ACCESS_CM2_obs_neg31.45_117.55.met` - **EXISTS**
- ✅ `ACCESS_CM2_ssp585_neg31.45_117.55.met` - **EXISTS** (as `ACCESS_CM2_ssp585_neg31.45_117.55.met`)
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_vp.csv` - **EXISTS**
- ❌ `ACCESS_CM2_ssp585_neg31.45_117.55_vp.csv` - **MISSING** (only exists for -31.50)
- ✅ `ACCESS_CM2_obs_neg31.45_117.55_eto.csv` - **EXISTS**
- ✅ `ACCESS_CM2_SSP585_neg31.45_117.55_eto.csv` - **EXISTS** (uppercase SSP585)

## Solutions

### Solution 1: Fix the Notebook (Recommended)
Update the `find_files_for_target` function in cell 5 to:
1. Try both `1985-2014` and `1986-2014` for SILO files
2. Try both lowercase and uppercase scenario names (ssp245, SSP245, ssp585, SSP585)

### Solution 2: Generate Missing VP Files
Run the VP calculation notebook (`CMPI6_VP_Calculation.ipynb`) for:
- Scenario: `ssp245`, Coordinates: `-31.45, 117.55`
- Scenario: `ssp585`, Coordinates: `-31.45, 117.55`

### Solution 3: Use Different Coordinates
If files exist for `-31.50, 117.55`, update the notebook configuration to use those coordinates instead.

## Next Steps

1. **Immediate fix:** Update the notebook to handle year range and case variations (Solution 1)
2. **Generate missing files:** Run VP calculation for ssp245 and ssp585 at -31.45, 117.55 (Solution 2)
3. **Verify:** Re-run the calibration notebook after fixes

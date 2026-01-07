# File Review Summary: Calibration Workflow Files

## Overview
This document categorizes all files in the project based on their relevance to the **CMIP6 VP & Evap Calibration Workflow** as described in `Calibration_Workflow_Diagram.md`.

---

## ✅ FILES NEEDED FOR CALIBRATION WORKFLOW

### Phase 1: Proxy Calculation

1. **`CMPI6_VP_Calculation.ipynb`** ⭐ **ESSENTIAL**
   - **Purpose**: Calculates vapor pressure (VP) proxy from CMIP6 data using SILO method
   - **Inputs**: CMIP6 NetCDF files (hurs, tasmax, tasmin)
   - **Outputs**: VP proxy CSV files
   - **Status**: Required for Phase 1 of calibration workflow

2. **`CMPI6_Evap_Calculation.ipynb`** ⭐ **ESSENTIAL**
   - **Purpose**: Calculates reference evapotranspiration (ET₀) proxy using FAO-56 Penman-Monteith method
   - **Inputs**: CMIP6 NetCDF files (tasmax, tasmin, hurs, rsds, sfcWind)
   - **Outputs**: Evap/ET₀ proxy CSV files
   - **Status**: Required for Phase 1 of calibration workflow

### Phase 2: Calibration

3. **`CMPI6_VP_Evap_Calibration.ipynb`** ⭐ **ESSENTIAL - MAIN WORKFLOW**
   - **Purpose**: Performs monthly mean-variance calibration of VP and Evap, generates calibrated .met files
   - **Inputs**: 
     - SILO .met files (baseline 1986-2014)
     - CMIP6 .met files (obs baseline + future scenarios)
     - VP proxy CSVs (from Phase 1)
     - Evap proxy CSVs (from Phase 1)
   - **Outputs**: Calibrated .met files, diagnostics, reports
   - **Status**: Core calibration notebook - **MOST IMPORTANT FILE**

### Supporting/Preprocessing Files

4. **`Grid_point_CMIP6_retrieval.ipynb`** ⭐ **ESSENTIAL**
   - **Purpose**: Extracts CMIP6 NetCDF data for specific grid points
   - **Inputs**: CMIP6 NetCDF files
   - **Outputs**: CSV files for individual variables (tasmax, tasmin, pr, rsds)
   - **Status**: Required to prepare CMIP6 data before proxy calculations
   - **Note**: Referenced in workflow diagram as data source

5. **`ACCESS met file creation.ipynb`** ⭐ **ESSENTIAL**
   - **Purpose**: Creates CMIP6 .met files by merging base variables with VP and Evap proxies
   - **Inputs**: 
     - Base variables (from Grid_point_CMIP6_retrieval or NetCDF)
     - VP proxy CSVs (from CMPI6_VP_Calculation)
     - Evap proxy CSVs (from CMPI6_Evap_Calculation)
   - **Outputs**: Complete CMIP6 .met files (required input for calibration)
   - **Status**: Required to create .met files that are inputs to calibration

6. **`Complete met file.ipynb`** ⚠️ **LIKELY DUPLICATE**
   - **Purpose**: Appears identical to `ACCESS met file creation.ipynb` (same header/overview)
   - **Status**: Likely a duplicate or alternative version
   - **Recommendation**: **VERIFY** by comparing full contents. If duplicate, delete one. If different, document the difference.

### Documentation Files

7. **`Calibration_Workflow_Diagram.md`** ⭐ **ESSENTIAL**
   - **Purpose**: Complete workflow documentation and diagram
   - **Status**: Reference document for understanding the workflow

8. **`Calibration_Workflow_Diagram.png`** ⭐ **ESSENTIAL**
   - **Purpose**: Visual diagram of the calibration workflow
   - **Status**: Visual reference for the workflow

9. **`Output_Summary.md`** ⭐ **ESSENTIAL**
   - **Purpose**: Documents all outputs produced by the calibration notebook
   - **Status**: Reference for understanding calibration outputs

10. **`Grid_Point_CMIP6_Retrieval_Process_Description.txt`** ⭐ **ESSENTIAL**
    - **Purpose**: Detailed documentation of the grid point retrieval process
    - **Status**: Reference documentation

11. **`README.md`** ⭐ **ESSENTIAL**
    - **Purpose**: Project overview and documentation
    - **Status**: Standard project documentation

12. **`requirements.txt`** ⭐ **ESSENTIAL**
    - **Purpose**: Python package dependencies
    - **Status**: Required for environment setup

---

## ❌ FILES IRRELEVANT OR REDUNDANT

### Executed/Redundant Notebooks

1. **`Anameka South_ACCESS CM2_executed.ipynb`** ❌ **IRRELEVANT**
   - **Reason**: Executed version of a notebook (contains output cells)
   - **Status**: Redundant - execution outputs should not be committed
   - **Recommendation**: Can be deleted or moved to archive

2. **`Anameka South_ACCESS CM2.ipynb`** ❌ **IRRELEVANT**
   - **Reason**: Older/alternative version for extracting tasmax, tasmin, pr only
   - **Status**: Superseded by `Grid_point_CMIP6_retrieval.ipynb` which is more comprehensive
   - **Recommendation**: Can be deleted if functionality is covered by Grid_point_CMIP6_retrieval

3. **`Anameka_South_ACCESS_CM2_SSP585_CMIP6_executed.ipynb`** ❌ **IRRELEVANT**
   - **Reason**: Executed version with output cells
   - **Status**: Redundant
   - **Recommendation**: Can be deleted or moved to archive

4. **`Anameka_South_ACCESS_CM2_SSP585_CMIP6.ipynb`** ❌ **IRRELEVANT**
   - **Reason**: Older/alternative version for specific scenario processing
   - **Status**: Superseded by more general notebooks
   - **Recommendation**: Can be deleted if functionality is covered by other notebooks

5. **`Anameka_South_ACCESS_CM2.ipynb`** ❌ **IRRELEVANT**
   - **Reason**: Minimal notebook, appears incomplete or placeholder
   - **Status**: Not part of calibration workflow
   - **Recommendation**: Can be deleted

### Standalone Scripts (Potentially Redundant)

6. **`convert_to_met_format.py`** ⚠️ **POTENTIALLY REDUNDANT**
   - **Purpose**: Standalone Python script to convert CSV files to MET format
   - **Status**: Functionality appears to be covered by `ACCESS met file creation.ipynb`
   - **Recommendation**: **VERIFY** if this script provides functionality not in the notebook. If redundant, can be deleted.

7. **`Grid point retrieval CMIP6 ACCESS M2.py`** ⚠️ **POTENTIALLY REDUNDANT**
   - **Purpose**: Standalone Python script version of grid point retrieval
   - **Status**: Functionality appears to be covered by `Grid_point_CMIP6_retrieval.ipynb`
   - **Note**: Referenced in `Grid_Point_CMIP6_Retrieval_Process_Description.txt` as alternative to notebook
   - **Recommendation**: Keep if needed for automated/batch processing, otherwise redundant with notebook

8. **`filter_grid_points.py`** ❌ **IRRELEVANT**
   - **Purpose**: Utility script to filter grid points from KML files
   - **Status**: Not part of the calibration workflow (preprocessing utility)
   - **Recommendation**: Keep if needed for project setup, but not part of calibration workflow

---

## 📊 SUMMARY STATISTICS

- **Total Files Reviewed**: 20
- **Essential Files**: 12
- **Irrelevant/Redundant Files**: 8
  - Executed notebooks: 2
  - Older/alternative notebooks: 3
  - Standalone scripts (potentially redundant): 3

---

## ✅ COMPARISON COMPLETED

1. **`Complete met file.ipynb`** vs **`ACCESS met file creation.ipynb`** ✅ **COMPLETED**
   - **Status**: **DUPLICATES** - Functionally identical with minor differences in filename formatting
   - **Result**: See `Notebook_Comparison_ACCESS_vs_Complete.md` for detailed comparison
   - **Recommendation**: Delete `Complete met file.ipynb` (keep `ACCESS met file creation.ipynb` as it's referenced in workflow)
   - **Key Differences**: 
     - Default scenario: "obs" vs "SSP585" (user-configurable anyway)
     - Filename format: 'neg' prefix vs negative sign (minor difference)

2. **`convert_to_met_format.py`** vs **`ACCESS met file creation.ipynb`** ⚠️ **MEDIUM PRIORITY**
   - **Status**: `convert_to_met_format.py` is a standalone script that converts CSV to MET format
   - **Action**: Verify if the Python script provides functionality not available in the notebook
   - **Note**: Script appears to work with pre-extracted CSV files, while notebook extracts from NetCDF
   - **If redundant**: Can be deleted
   - **If unique**: Keep and document use case (e.g., batch processing from CSVs)

---

## 📋 RECOMMENDED WORKFLOW ORDER

Based on the calibration workflow diagram, the recommended execution order is:

1. **Data Retrieval**:
   - `Grid_point_CMIP6_retrieval.ipynb` → Extract CMIP6 NetCDF data

2. **Phase 1: Proxy Calculation**:
   - `CMPI6_VP_Calculation.ipynb` → Generate VP proxy CSVs
   - `CMPI6_Evap_Calculation.ipynb` → Generate Evap proxy CSVs

3. **MET File Creation**:
   - `ACCESS met file creation.ipynb` → Create CMIP6 .met files (for obs and scenarios)
   - **Note**: SILO .met files should be created separately (via SILO API Module_Workflow)

4. **Phase 2: Calibration**:
   - `CMPI6_VP_Evap_Calibration.ipynb` → Perform calibration and generate outputs

---

## ✅ ACTION ITEMS

1. ✅ **COMPLETED**: Compared `Complete met file.ipynb` vs `ACCESS met file creation.ipynb` - See `Notebook_Comparison_ACCESS_vs_Complete.md`
2. ✅ **COMPLETED**: Deleted executed notebooks (`*_executed.ipynb` files)
3. ✅ **COMPLETED**: Deleted older/alternative notebooks (superseded by current versions)
4. ✅ **COMPLETED**: Deleted standalone scripts (redundant with notebook functionality)
5. ⚠️ **PENDING**: Delete `Complete met file.ipynb` (duplicate of `ACCESS met file creation.ipynb`)

---

## 📝 NOTES

- The calibration workflow is well-documented in `Calibration_Workflow_Diagram.md`
- The core workflow consists of 3 main notebooks:
  1. `CMPI6_VP_Calculation.ipynb`
  2. `CMPI6_Evap_Calculation.ipynb`
  3. `CMPI6_VP_Evap_Calibration.ipynb` (main workflow)
- Supporting notebooks prepare data for the calibration workflow
- Several files appear to be older versions or executed copies that can be cleaned up

---

*Generated: 2025-01-27*
*Review based on: Calibration_Workflow_Diagram.md*


# Anameka Grid Coordinates

## Summary

This document lists all Anameka grid coordinates currently defined in the project.

---

## Active Coordinates

### Currently Defined in `CMPI6_VP_Evap_Calibration.ipynb`

**Active Coordinate:**
- **(-31.75, 117.60)** - Primary coordinate used for calibration
  - Latitude: -31.75° (31.75°S)
  - Longitude: 117.60° (117.60°E)
  - Location: Anameka South region

**Commented/Inactive Coordinate:**
- **(-31.50, 117.50)** - Commented out, available for future use
  - Latitude: -31.50° (31.50°S)
  - Longitude: 117.50° (117.50°E)

---

## Coordinate Usage Across Notebooks

### 1. `CMPI6_VP_Evap_Calibration.ipynb`
```python
COORDINATES = [
    (-31.75, 117.60),  # Active - used for calibration
    # (-31.50, 117.50),  # Commented - available for future use
]
```

### 2. Individual Notebooks (Single Coordinate Configuration)

The following notebooks use a single coordinate configuration (not a list):

- **`Grid_point_CMIP6_retrieval.ipynb`**
  - `LATITUDE = -31.75`
  - `LONGITUDE = 117.5999984741211`

- **`CMPI6_VP_Calculation.ipynb`**
  - `LATITUDE = -31.75`
  - `LONGITUDE = 117.5999984741211`

- **`CMPI6_Evap_Calculation.ipynb`**
  - `LATITUDE = -31.75`
  - `LONGITUDE = 117.5999984741211`

- **`ACCESS met file creation.ipynb`**
  - `LATITUDE = -31.75`
  - `LONGITUDE = 117.5999984741211`

---

## Coordinate Details

### Primary Coordinate: (-31.75, 117.60)

**Location**: Anameka South, Western Australia

**Grid Point Used**: (-31.7500, 117.6000)
- The notebooks find the nearest grid point within tolerance (0.01 degrees ≈ 1.1 km)
- Actual grid point used: (-31.7500, 117.6000)

**Coordinate Format Variations**:
- In filenames: `neg31.75_117.60` (using 'neg' prefix)
- In code: `-31.75, 117.60` (standard decimal format)
- In some places: `-31.75, 117.5999984741211` (higher precision)

**Used For**:
- CMIP6 data extraction
- VP proxy calculation
- Evap/ET₀ proxy calculation
- MET file creation
- Calibration process

---

## Adding New Coordinates

To add new coordinates to the calibration workflow:

1. **Update `CMPI6_VP_Evap_Calibration.ipynb`**:
   ```python
   COORDINATES = [
       (-31.75, 117.60),  # Existing coordinate
       (-31.50, 117.50),  # New coordinate
       # Add more as needed
   ]
   ```

2. **For individual notebooks**, update the configuration:
   ```python
   LATITUDE = -31.50
   LONGITUDE = 117.50
   ```

3. **Ensure data files exist** for the new coordinate:
   - CMIP6 NetCDF files
   - SILO baseline .met file: `SILO_1986-2014_{LAT}_{LON}.met`
   - VP and Evap proxy CSV files

---

## Notes

- All coordinates are in **decimal degrees**
- **Latitude**: -90 to 90 (negative for Southern Hemisphere)
- **Longitude**: -180 to 180 (positive for Eastern Hemisphere in Australia)
- Coordinate matching tolerance: **0.01 degrees** (approximately 1.1 km)
- The notebooks automatically find the nearest grid point within tolerance

---

*Last Updated: 2025-01-27*
*Based on current project files*


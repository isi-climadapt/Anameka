# Comparison: `ACCESS met file creation.ipynb` vs `Complete met file.ipynb`

## Summary

Both notebooks are **functionally identical** with the same purpose, structure, and core functionality. They differ only in **minor implementation details** related to coordinate string formatting and file naming conventions.

**Recommendation**: These are duplicates. Keep `ACCESS met file creation.ipynb` (as it's referenced in the workflow documentation) and delete `Complete met file.ipynb`.

---

## Detailed Comparison

### 1. Header and Overview ✅ **IDENTICAL**

Both notebooks have:
- Identical markdown headers
- Same purpose statement
- Same input/output descriptions
- Same configuration instructions

**Verdict**: No differences

---

### 2. Configuration Section ⚠️ **MINOR DIFFERENCES**

#### Default Scenario Setting
- **`ACCESS met file creation.ipynb`**: `SCENARIO = "obs"`
- **`Complete met file.ipynb`**: `SCENARIO = "SSP585"`

**Impact**: This is just a default value that users change anyway. Not a functional difference.

#### Coordinate String Formatting
Both use the same logic:
```python
lat_str = f"{LATITUDE:.2f}".replace('.', '_').replace('-', 'neg')
lon_str = f"{LONGITUDE:.2f}".replace('.', '_').replace('-', 'neg')
```

**Verdict**: Identical

---

### 3. Core Functions ✅ **IDENTICAL**

All core functions are identical:
- `extract_daily_data_from_netcdf()` - Same implementation
- `get_cached_variable_path()` - Same implementation
- `load_cached_variable()` - Same implementation
- `save_cached_variable()` - Same implementation
- `calculate_tav_amp()` - Same implementation
- `create_complete_met_file()` - Same implementation (with one minor difference in filename formatting, see below)

**Verdict**: Functionally identical

---

### 4. VP/Evap Loading Functions ⚠️ **MINOR DIFFERENCES**

#### `load_vp_from_csv()` Function

**`ACCESS met file creation.ipynb`**:
```python
# Try new format first (decimal coordinates with neg prefix: neg31.75_117.60)
if '_' in lat_str and 'neg' in lat_str:
    lat_str_decimal = lat_str.replace('_', '.').replace('neg', 'neg')  # Keeps 'neg' prefix
elif '_' in lat_str:
    lat_str_decimal = lat_str.replace('_', '.').replace('-', 'neg')
else:
    lat_str_decimal = lat_str.replace('-', 'neg')
```

**`Complete met file.ipynb`**:
```python
# Try new format first (decimal coordinates: -31.75_117.60)
lat_str_decimal = lat_str.replace('neg', '-').replace('_', '.')  # Converts 'neg' to '-'
lon_str_decimal = lon_str.replace('_', '.')
```

**Difference**: 
- `ACCESS met file creation.ipynb` preserves the 'neg' prefix in filenames (e.g., `neg31.75`)
- `Complete met file.ipynb` converts 'neg' to '-' (e.g., `-31.75`)

**Impact**: This affects which filename format is searched first, but both functions have fallback logic to try alternative formats. Both should work, but may find files with different naming conventions.

#### `load_evap_from_csv()` Function

Same difference as above:
- **`ACCESS met file creation.ipynb`**: Tries `_eto.csv` first, preserves 'neg' prefix
- **`Complete met file.ipynb`**: Tries `_eto.csv` first, converts 'neg' to '-'

**Verdict**: Minor difference in filename search order, but both have fallback logic

---

### 5. MET File Output Filename ⚠️ **MINOR DIFFERENCE**

#### In `create_complete_met_file()` Function

**`ACCESS met file creation.ipynb`**:
```python
# Create output filename with coordinate-based naming
# Format lat_str to use 'neg' prefix instead of '-' for filenames
lat_str = f"{latitude:.2f}".replace('-', 'neg')
lon_str = f"{longitude:.2f}"
output_filename = f"{model_scenario}_{lat_str}_{lon_str}.met"
```

**`Complete met file.ipynb`**:
```python
# Create output filename with coordinate-based naming
lat_str = f"{latitude:.2f}"  # No replacement, keeps negative sign
lon_str = f"{longitude:.2f}"
output_filename = f"{model_scenario}_{lat_str}_{lon_str}.met"
```

**Difference**:
- **`ACCESS met file creation.ipynb`**: Outputs files like `ACCESS_CM2_SSP585_neg31.75_117.60.met`
- **`Complete met file.ipynb`**: Outputs files like `ACCESS_CM2_SSP585_-31.75_117.60.met`

**Impact**: 
- Files with negative coordinates will have different names
- The 'neg' prefix format is more filesystem-friendly (avoids issues with '-' in filenames)
- The negative sign format is more human-readable

**Verdict**: Different naming convention, but both are valid

---

### 6. Main Processing Logic ✅ **IDENTICAL**

Both notebooks have:
- Same data extraction logic
- Same caching mechanism
- Same VP/Evap loading logic
- Same MET file creation process
- Same error handling

**Verdict**: Identical

---

## Key Differences Summary

| Aspect | ACCESS met file creation.ipynb | Complete met file.ipynb |
|--------|-------------------------------|-------------------------|
| **Default Scenario** | `"obs"` | `"SSP585"` |
| **VP/Evap File Search** | Preserves 'neg' prefix | Converts 'neg' to '-' |
| **Output Filename** | Uses 'neg' prefix (e.g., `neg31.75`) | Uses negative sign (e.g., `-31.75`) |
| **Core Functionality** | ✅ Identical | ✅ Identical |

---

## Recommendation

### Keep: `ACCESS met file creation.ipynb`
**Reasons:**
1. ✅ Referenced in workflow documentation (`Calibration_Workflow_Diagram.md`)
2. ✅ Uses 'neg' prefix format which is more filesystem-friendly
3. ✅ More consistent with other notebooks in the project (which use 'neg' prefix)

### Delete: `Complete met file.ipynb`
**Reasons:**
1. ❌ Duplicate functionality
2. ❌ Not referenced in workflow documentation
3. ❌ Uses negative sign in filenames (less filesystem-friendly)
4. ❌ May cause confusion having two similar notebooks

---

## Migration Notes (if keeping Complete met file.ipynb)

If you decide to keep `Complete met file.ipynb` instead, you would need to:
1. Update `Calibration_Workflow_Diagram.md` to reference `Complete met file.ipynb`
2. Ensure VP/Evap CSV files use negative sign format (or update the search logic)
3. Update any scripts/notebooks that reference the output filenames

**However, this is NOT recommended** as `ACCESS met file creation.ipynb` is already integrated into the workflow.

---

## Conclusion

These notebooks are **duplicates** with only minor differences in:
- Default scenario setting (user-configurable anyway)
- Coordinate string formatting in filenames ('neg' vs '-')

**Action**: Delete `Complete met file.ipynb` and use `ACCESS met file creation.ipynb` as the single source of truth.

---

*Comparison Date: 2025-01-27*
*Files Compared:*
- `ACCESS met file creation.ipynb` (1,453 lines)
- `Complete met file.ipynb` (1,453 lines)


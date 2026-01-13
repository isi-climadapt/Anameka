"""
Script to fix the CMPI6_VP_Evap_Calibration.ipynb notebook
to handle file naming variations (year ranges, case sensitivity)
"""
import json
import re

# Read the notebook
notebook_path = r"c:\Users\ibian\Anameka\CMPI6_VP_Evap_Calibration.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# Find the cell with find_files_for_target function (cell index 4, which is the 5th cell)
target_cell_idx = None
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code' and 'source' in cell:
        source_text = ''.join(cell['source'])
        if 'def find_files_for_target' in source_text:
            target_cell_idx = idx
            break

if target_cell_idx is None:
    print("ERROR: Could not find find_files_for_target function")
    exit(1)

print(f"Found target cell at index {target_cell_idx}")

# Get the cell source
cell = notebook['cells'][target_cell_idx]
source_lines = cell['source']

# Fix 1: Update SILO file finding to try both 1985-2014 and 1986-2014
new_source = []
i = 0
while i < len(source_lines):
    line = source_lines[i]
    
    # Replace SILO file finding section
    if 'silo_pattern = f"SILO_1986-2014' in line:
        # Replace with code that tries both year ranges
        new_source.append('    # Find SILO baseline .met (try both 1985-2014 and 1986-2014)\n')
        new_source.append('    for lat_var in lat_str_variants:\n')
        new_source.append('        for lon_var in lon_str_variants:\n')
        new_source.append('            # Try 1986-2014 first (preferred), then 1985-2014 (fallback)\n')
        new_source.append('            for year_range in [\'1986-2014\', \'1985-2014\']:\n')
        new_source.append('                silo_pattern = f"SILO_{year_range}_{lat_var}_{lon_var}.met"\n')
        new_source.append('                silo_path = os.path.join(input_met_dir, silo_pattern)\n')
        new_source.append('                if os.path.exists(silo_path):\n')
        new_source.append('                    files[\'silo_met\'] = silo_path\n')
        new_source.append('                    break\n')
        new_source.append('            if files[\'silo_met\']:\n')
        new_source.append('                break\n')
        new_source.append('        if files[\'silo_met\']:\n')
        new_source.append('            break\n')
        # Skip the old lines
        while i < len(source_lines) and 'if files[\'silo_met\']:' not in source_lines[i]:
            i += 1
        # Skip the break line
        if i < len(source_lines) and 'break' in source_lines[i]:
            i += 1
        continue
    
    # Fix 2: Update CMIP6 future .met finding to try case variations
    if 'future_pattern = f"{model}_{scenario}_{lat_var}_{lon_var}.met"' in line:
        # Find the start of this section
        start_idx = i - 3  # Go back to the comment line
        # Replace the entire section
        new_source.append('    # Find CMIP6 future .met (skip for obs scenario)\n')
        new_source.append('    if scenario.lower() != "obs":\n')
        new_source.append('        # Try both lowercase and uppercase scenario names\n')
        new_source.append('        scenario_variants = [scenario, scenario.lower(), scenario.upper()]\n')
        new_source.append('        for lat_var in lat_str_variants:\n')
        new_source.append('            for lon_var in lon_str_variants:\n')
        new_source.append('                for scen_var in scenario_variants:\n')
        new_source.append('                    future_pattern = f"{model}_{scen_var}_{lat_var}_{lon_var}.met"\n')
        new_source.append('                    future_path = os.path.join(input_met_dir, future_pattern)\n')
        new_source.append('                    if os.path.exists(future_path):\n')
        new_source.append('                        files[\'cmip6_future_met\'] = future_path\n')
        new_source.append('                        break\n')
        new_source.append('                if files[\'cmip6_future_met\']:\n')
        new_source.append('                    break\n')
        new_source.append('            if files[\'cmip6_future_met\']:\n')
        new_source.append('                break\n')
        # Skip old lines
        while i < len(source_lines) and 'else:' not in source_lines[i]:
            i += 1
        continue
    
    # Fix 3: Update VP future finding to try case variations
    if 'vp_future_patterns = [' in line and 'f"{model}_{scenario}_{lat_var}_{lon_var}_vp.csv"' in ''.join(source_lines[i:i+3]):
        # Replace VP future section
        new_source.append('            # VP future (skip for obs scenario)\n')
        new_source.append('            if scenario.lower() != "obs":\n')
        new_source.append('                # Try both lowercase and uppercase scenario names\n')
        new_source.append('                scenario_variants = [scenario, scenario.lower(), scenario.upper()]\n')
        new_source.append('                for scen_var in scenario_variants:\n')
        new_source.append('                    vp_future_patterns = [\n')
        new_source.append('                        f"{model}_{scen_var}_{lat_var}_{lon_var}_vp.csv",  # With .csv\n')
        new_source.append('                        f"{model}_{scen_var}_{lat_var}_{lon_var}_vp"  # Without .csv\n')
        new_source.append('                    ]\n')
        new_source.append('                    for pattern in vp_future_patterns:\n')
        new_source.append('                        vp_future_path = os.path.join(proxy_output_dir, pattern)\n')
        new_source.append('                        if os.path.exists(vp_future_path):\n')
        new_source.append('                            files[\'vp_future\'] = vp_future_path\n')
        new_source.append('                            break\n')
        new_source.append('                    if files[\'vp_future\']:\n')
        new_source.append('                        break\n')
        # Skip old lines
        while i < len(source_lines) and 'else:' not in source_lines[i]:
            i += 1
        continue
    
    # Fix 4: Update Evap future finding to try case variations
    if 'evap_future_patterns = [' in line and 'f"{model}_{scenario}_{lat_var}_{lon_var}_eto.csv"' in ''.join(source_lines[i:i+3]):
        # Replace Evap future section
        new_source.append('            # Evap future (skip for obs scenario, only eto suffix)\n')
        new_source.append('            if scenario.lower() != "obs":\n')
        new_source.append('                # Try both lowercase and uppercase scenario names\n')
        new_source.append('                scenario_variants = [scenario, scenario.lower(), scenario.upper()]\n')
        new_source.append('                for scen_var in scenario_variants:\n')
        new_source.append('                    evap_future_patterns = [\n')
        new_source.append('                        f"{model}_{scen_var}_{lat_var}_{lon_var}_eto.csv",  # With .csv\n')
        new_source.append('                        f"{model}_{scen_var}_{lat_var}_{lon_var}_eto"  # Without .csv\n')
        new_source.append('                    ]\n')
        new_source.append('                    for pattern in evap_future_patterns:\n')
        new_source.append('                        evap_future_path = os.path.join(proxy_output_dir, pattern)\n')
        new_source.append('                        if os.path.exists(evap_future_path):\n')
        new_source.append('                            files[\'evap_future\'] = evap_future_path\n')
        new_source.append('                            break\n')
        new_source.append('                    if files[\'evap_future\']:\n')
        new_source.append('                        break\n')
        # Skip old lines
        while i < len(source_lines) and 'else:' not in source_lines[i]:
            i += 1
        continue
    
    new_source.append(line)
    i += 1

# Update the cell
notebook['cells'][target_cell_idx]['source'] = new_source

# Write back
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print("Notebook updated successfully!")
print("\nChanges made:")
print("1. SILO file finding now tries both 1985-2014 and 1986-2014 year ranges")
print("2. CMIP6 future .met finding now tries lowercase, original, and uppercase scenario names")
print("3. VP future CSV finding now tries lowercase, original, and uppercase scenario names")
print("4. Evap future CSV finding now tries lowercase, original, and uppercase scenario names")

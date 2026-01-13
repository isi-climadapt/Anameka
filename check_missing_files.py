"""
Script to check which files are missing for CMIP6 calibration
"""
import os
from pathlib import Path

# Configuration from notebook
MODEL = "ACCESS_CM2"
SCENARIOS = ["obs", "ssp245", "ssp585"]
COORDINATES = [(-31.45, 117.55)]  # Current coordinates being used
INPUT_MET_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\-31.45_117.55"
PROXY_OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\-31.45_117.55"

def find_files_for_target(model, scenario, lat, lon, input_met_dir, proxy_output_dir):
    """Find all required files for a target"""
    files = {
        'silo_met': None,
        'cmip6_obs_met': None,
        'cmip6_future_met': None,
        'vp_obs': None,
        'vp_future': None,
        'evap_obs': None,
        'evap_future': None
    }
    
    # Generate coordinate string variants
    lat_str_variants = [
        f"{lat:.2f}".replace("-", "neg"),
        f"{lat:.2f}",
        f"{abs(lat):.2f}".replace(".", "_")
    ]
    lon_str_variants = [
        f"{lon:.2f}",
        f"{lon:.2f}".replace(".", "_")
    ]
    
    # Find SILO baseline .met (try both 1985-2014 and 1986-2014)
    for lat_var in lat_str_variants:
        for lon_var in lon_str_variants:
            for year_range in ['1986-2014', '1985-2014']:
                silo_pattern = f"SILO_{year_range}_{lat_var}_{lon_var}.met"
                silo_path = os.path.join(input_met_dir, silo_pattern)
                if os.path.exists(silo_path):
                    files['silo_met'] = silo_path
                    break
            if files['silo_met']:
                break
        if files['silo_met']:
            break
    
    # Find CMIP6 obs .met
    for lat_var in lat_str_variants:
        for lon_var in lon_str_variants:
            obs_pattern = f"{model}_obs_{lat_var}_{lon_var}.met"
            obs_path = os.path.join(input_met_dir, obs_pattern)
            if os.path.exists(obs_path):
                files['cmip6_obs_met'] = obs_path
                break
        if files['cmip6_obs_met']:
            break
    
    # Find CMIP6 future .met (skip for obs scenario)
    if scenario.lower() != "obs":
        scenario_variants = [scenario, scenario.lower(), scenario.upper()]
        for lat_var in lat_str_variants:
            for lon_var in lon_str_variants:
                for scen_var in scenario_variants:
                    future_pattern = f"{model}_{scen_var}_{lat_var}_{lon_var}.met"
                    future_path = os.path.join(input_met_dir, future_pattern)
                    if os.path.exists(future_path):
                        files['cmip6_future_met'] = future_path
                        break
                if files['cmip6_future_met']:
                    break
            if files['cmip6_future_met']:
                break
    else:
        files['cmip6_future_met'] = files['cmip6_obs_met']
    
    # Find VP proxy CSVs
    for lat_var in lat_str_variants:
        for lon_var in lon_str_variants:
            # VP obs
            vp_obs_patterns = [
                f"{model}_obs_{lat_var}_{lon_var}_vp.csv",
                f"{model}_obs_{lat_var}_{lon_var}_vp"
            ]
            for pattern in vp_obs_patterns:
                vp_obs_path = os.path.join(proxy_output_dir, pattern)
                if os.path.exists(vp_obs_path):
                    files['vp_obs'] = vp_obs_path
                    break
            
            # VP future
            if scenario.lower() != "obs":
                scenario_variants = [scenario, scenario.lower(), scenario.upper()]
                for scen_var in scenario_variants:
                    vp_future_patterns = [
                        f"{model}_{scen_var}_{lat_var}_{lon_var}_vp.csv",
                        f"{model}_{scen_var}_{lat_var}_{lon_var}_vp"
                    ]
                    for pattern in vp_future_patterns:
                        vp_future_path = os.path.join(proxy_output_dir, pattern)
                        if os.path.exists(vp_future_path):
                            files['vp_future'] = vp_future_path
                            break
                    if files['vp_future']:
                        break
            else:
                files['vp_future'] = files['vp_obs']
            
            # Evap obs
            evap_obs_patterns = [
                f"{model}_obs_{lat_var}_{lon_var}_eto.csv",
                f"{model}_obs_{lat_var}_{lon_var}_eto"
            ]
            for pattern in evap_obs_patterns:
                evap_obs_path = os.path.join(proxy_output_dir, pattern)
                if os.path.exists(evap_obs_path):
                    files['evap_obs'] = evap_obs_path
                    break
            
            # Evap future
            if scenario.lower() != "obs":
                scenario_variants = [scenario, scenario.lower(), scenario.upper()]
                for scen_var in scenario_variants:
                    evap_future_patterns = [
                        f"{model}_{scen_var}_{lat_var}_{lon_var}_eto.csv",
                        f"{model}_{scen_var}_{lat_var}_{lon_var}_eto"
                    ]
                    for pattern in evap_future_patterns:
                        evap_future_path = os.path.join(proxy_output_dir, pattern)
                        if os.path.exists(evap_future_path):
                            files['evap_future'] = evap_future_path
                            break
                    if files['evap_future']:
                        break
            else:
                files['evap_future'] = files['evap_obs']
            
            if files['vp_obs'] and files['vp_future'] and files['evap_obs'] and files['evap_future']:
                break
        if files['vp_obs'] and files['vp_future'] and files['evap_obs'] and files['evap_future']:
            break
    
    return files

# Check files for each scenario
print("="*70)
print("MISSING FILES CHECK FOR CMIP6 CALIBRATION")
print("="*70)
print(f"Model: {MODEL}")
print(f"Coordinates: {COORDINATES}")
print(f"Input Directory: {INPUT_MET_DIR}")
print(f"Proxy Directory: {PROXY_OUTPUT_DIR}")
print("="*70)

for lat, lon in COORDINATES:
    print(f"\nCoordinates: ({lat}, {lon})")
    print("-"*70)
    
    for scenario in SCENARIOS:
        print(f"\nScenario: {scenario}")
        files = find_files_for_target(MODEL, scenario, lat, lon, INPUT_MET_DIR, PROXY_OUTPUT_DIR)
        
        # Determine required files
        if scenario.lower() == 'obs':
            required = ['silo_met', 'cmip6_obs_met', 'vp_obs', 'evap_obs']
        else:
            required = ['silo_met', 'cmip6_obs_met', 'cmip6_future_met', 
                       'vp_obs', 'vp_future', 'evap_obs', 'evap_future']
        
        missing = []
        found = []
        
        for key in required:
            if files.get(key) is None:
                missing.append(key)
            else:
                found.append((key, os.path.basename(files[key])))
        
        if missing:
            print(f"  [MISSING] ({len(missing)} files):")
            for key in missing:
                print(f"     - {key}")
        else:
            print(f"  [OK] All required files found!")
        
        if found:
            print(f"  [FOUND] ({len(found)} files):")
            for key, filename in found:
                print(f"     - {key}: {filename}")

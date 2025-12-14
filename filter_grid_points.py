"""
Script to filter grid points that fall inside farm polygon(s) from KML file.
Exports results to CSV, KML, JSON, and Excel formats.
"""

import os
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import json
import simplekml
import xml.etree.ElementTree as ET
import re

# File paths
KML_INPUT = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\kml\PROJ0025_GIS_Anameka_Farms_250716.kml"
GRID_FILE = r"C:\Users\ibian\Desktop\ClimAdapt\CMIP6\CMIP6 Grid points.xlsx"
OUTPUT_DIR = r"C:\Users\ibian\Desktop\ClimAdapt\Anameka\Grid"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_kml_polygons(kml_file_path):
    """
    Parse KML file and extract all polygons.
    Returns a Shapely MultiPolygon or Polygon.
    """
    with open(kml_file_path, 'r', encoding='utf-8') as f:
        kml_content = f.read()
    
    # Parse XML
    root = ET.fromstring(kml_content)
    
    # Define namespace (KML 2.2) - try both with and without namespace
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    polygons = []
    
    # Find all coordinate elements - try with namespace first
    coord_elements = root.findall('.//kml:coordinates', namespaces)
    
    # If no elements found with namespace, try without namespace
    if not coord_elements:
        coord_elements = root.findall('.//coordinates')
    
    for coord_elem in coord_elements:
        if coord_elem.text:
            # Parse coordinates: "lon,lat,alt lon,lat,alt ..."
            coord_text = coord_elem.text.strip()
            # Split by whitespace and newlines
            coord_pairs = re.split(r'[\s\n]+', coord_text)
            
            coords = []
            for pair in coord_pairs:
                pair = pair.strip()
                if pair:
                    parts = pair.split(',')
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            coords.append((lon, lat))
                        except ValueError:
                            continue
            
            # Create polygon if we have at least 3 points
            if len(coords) >= 3:
                # Ensure polygon is closed (first point == last point)
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                try:
                    polygon = Polygon(coords)
                    if polygon.is_valid:
                        polygons.append(polygon)
                except Exception as e:
                    print(f"  Warning: Could not create polygon from coordinates: {e}")
                    continue
    
    if not polygons:
        raise ValueError("No valid polygons found in KML file")
    
    # Combine all polygons into a single geometry
    if len(polygons) == 1:
        return polygons[0]
    else:
        return unary_union(polygons)


def load_grid_points(excel_file_path):
    """
    Load grid points from Excel file.
    Returns a DataFrame with 'lat' and 'lon' columns.
    """
    df = pd.read_excel(excel_file_path)
    
    # Ensure columns are named correctly (case-insensitive)
    df.columns = df.columns.str.lower()
    
    if 'lat' not in df.columns or 'lon' not in df.columns:
        raise ValueError(f"Expected 'lat' and 'lon' columns. Found: {df.columns.tolist()}")
    
    return df


def filter_points_in_polygon(df, polygon):
    """
    Filter points that fall inside the polygon.
    Returns filtered DataFrame with original lat/lon values preserved.
    """
    # Create a copy to avoid modifying original
    df_filtered = df.copy()
    
    # Create Point geometries for each row
    points = [Point(row['lon'], row['lat']) for _, row in df.iterrows()]
    
    # Check which points are inside the polygon
    inside_mask = [polygon.contains(point) for point in points]
    
    # Filter DataFrame
    df_selected = df_filtered[inside_mask].copy()
    
    return df_selected


def export_to_csv(df, output_path):
    """Export DataFrame to CSV."""
    df.to_csv(output_path, index=False)
    print(f"  [OK] CSV exported: {output_path}")


def export_to_excel(df, output_path):
    """Export DataFrame to Excel."""
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"  [OK] Excel exported: {output_path}")


def export_to_json(df, output_path):
    """Export DataFrame to JSON."""
    # Convert to records format (list of dictionaries)
    records = df.to_dict('records')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    print(f"  [OK] JSON exported: {output_path}")


def export_to_kml(df, output_path):
    """Export selected points to KML for Google Earth Pro."""
    kml_output = simplekml.Kml()
    
    for idx, row in df.iterrows():
        # Create a point placemark
        pnt = kml_output.newpoint(
            name=f"Grid Point {idx}",
            coords=[(row['lon'], row['lat'])]
        )
        pnt.description = f"Latitude: {row['lat']}, Longitude: {row['lon']}"
    
    kml_output.save(output_path)
    print(f"  [OK] KML exported: {output_path}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Grid Point Filtering Script")
    print("=" * 60)
    
    # Step 1: Load and parse KML polygon
    print("\n[1/5] Loading farm polygon from KML...")
    try:
        farm_polygon = parse_kml_polygons(KML_INPUT)
        print(f"  [OK] KML loaded successfully")
        if isinstance(farm_polygon, MultiPolygon):
            print(f"  [OK] Found {len(farm_polygon.geoms)} polygon(s)")
        else:
            print(f"  [OK] Found 1 polygon")
    except Exception as e:
        print(f"  [ERROR] Error loading KML: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Load grid points
    print("\n[2/5] Loading grid points from Excel...")
    try:
        grid_df = load_grid_points(GRID_FILE)
        total_points = len(grid_df)
        print(f"  [OK] Loaded {total_points:,} grid points")
    except Exception as e:
        print(f"  [ERROR] Error loading grid points: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Filter points inside polygon
    print("\n[3/5] Filtering points inside farm polygon...")
    try:
        selected_df = filter_points_in_polygon(grid_df, farm_polygon)
        selected_count = len(selected_df)
        print(f"  [OK] Filtering complete")
    except Exception as e:
        print(f"  [ERROR] Error filtering points: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Print counts
    print("\n[4/5] Results Summary:")
    print(f"  - Total grid points: {total_points:,}")
    print(f"  - Selected points (inside polygon): {selected_count:,}")
    print(f"  - Percentage: {(selected_count/total_points*100):.2f}%")
    
    # Step 5: Export results
    print("\n[5/5] Exporting results...")
    
    # Base filename for outputs
    base_name = "filtered_grid_points"
    
    # Export to CSV
    csv_path = os.path.join(OUTPUT_DIR, f"{base_name}.csv")
    export_to_csv(selected_df, csv_path)
    
    # Export to Excel
    excel_path = os.path.join(OUTPUT_DIR, f"{base_name}.xlsx")
    export_to_excel(selected_df, excel_path)
    
    # Export to JSON
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    export_to_json(selected_df, json_path)
    
    # Export to KML
    kml_path = os.path.join(OUTPUT_DIR, f"{base_name}.kml")
    export_to_kml(selected_df, kml_path)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print(f"All outputs saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()


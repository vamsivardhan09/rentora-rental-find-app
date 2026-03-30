import pandas as pd
import os
import json

# Set the source directory for CSV files
# We check two locations based on system structure
base_paths = [
    r'c:\Users\kiran\OneDrive\Desktop\SQL',
    os.path.join(os.getcwd(), 'data')
]

localities = [
    'Whitefield', 'Electronic_City', 'Yelahanka', 'Bellandur', 
    'Kaggadasapura', 'Brookefield', 'Varthur', 'K.R Puram'
]

display_names = {
    'Whitefield': 'Whitefield',
    'Electronic_City': 'Electronic City',
    'Yelahanka': 'Yelahanka',
    'Bellandur': 'Bellandur',
    'Kaggadasapura': 'Kaggadasapura',
    'Brookefield': 'Brookefield',
    'Varthur': 'Varthur',
    'K.R Puram': 'K.R Puram'
}

data = {
    'locs': [],
    'listings': [],
    'avgRent': [],
    'rentPSF': [],
    'avgSize': [],
    'deposit': [],
    'gym': [],
    'pool': [],
    'lift': [],
    'bhk1': [],
    'bhk2': [],
    'bhk3': [],
    'bhk4p': [],
    'rk1': [],
    'furnFF': [],
    'furnSF': [],
    'furnNF': [],
    'leaseAny': [],
    'leaseFamily': [],
    'leaseBach': [],
    'bhkRents': {'RK1': {}, 'BHK1': {}, 'BHK2': {}, 'BHK3': {}, 'BHK4': {}}
}

def clean_bool(s):
    """Matches logic in import_csv.py for robust boolean detection"""
    val = str(s).strip().lower()
    return 1 if val in ['true', '1', 'yes', 'y', '1.0'] else 0

for loc in localities:
    # Try finding the file with underscore or space
    found_path = None
    possible_names = [f"{loc}.csv", f"{loc.replace('_', ' ')}.csv"]
    
    for bp in base_paths:
        for pn in possible_names:
            p = os.path.join(bp, pn)
            if os.path.exists(p):
                found_path = p
                break
        if found_path: break
        
    if not found_path:
        print(f"ERROR: Could not find CSV for {loc} in any base paths.")
        continue
    
    try:
        df = pd.read_csv(found_path)
    except Exception as e:
        print(f"ERROR: Could not read {found_path} - {e}")
        continue
    
    # Ensure critical columns are numeric
    df['rent'] = pd.to_numeric(df['rent'], errors='coerce')
    df['deposit'] = pd.to_numeric(df['deposit'], errors='coerce')
    df['property_size'] = pd.to_numeric(df['property_size'], errors='coerce')
    
    # Cleaning: Mandatory stats for benchmarking
    df = df.dropna(subset=['rent', 'property_size'])
    df = df[df['property_size'] > 0]
    
    if df.empty:
        print(f"WARNING: No valid entries for {loc}")
        continue

    dn = display_names[loc]
    data['locs'].append(dn)
    data['listings'].append(int(len(df)))
    
    # Aggregated Averages
    rent_avg = df['rent'].mean()
    size_avg = df['property_size'].mean()
    dep_avg = df['deposit'].mean() if 'deposit' in df.columns else 0
    psf_avg = (df['rent'] / df['property_size']).mean()

    data['avgRent'].append(int(rent_avg) if not pd.isna(rent_avg) else 0)
    data['avgSize'].append(int(size_avg) if not pd.isna(size_avg) else 0)
    data['deposit'].append(int(dep_avg) if not pd.isna(dep_avg) else 0)
    data['rentPSF'].append(round(psf_avg if not pd.isna(psf_avg) else 0, 2))
    
    # Enhanced Amenity Detection (Handles strings like 'Yes', 'True', etc.)
    for col, key in [('gym', 'gym'), ('swimming_pool', 'pool'), ('lift', 'lift')]:
        if col in df.columns:
            # Apply same boolean conversion as the importer
            bool_series = df[col].apply(clean_bool)
            mean_val = bool_series.mean()
            data[key].append(round(float(mean_val), 3))
        else:
            data[key].append(0.0)
    
    # Property Types & Counts
    data['rk1'].append(int((df['type'] == 'RK1').sum()))
    data['bhk1'].append(int((df['type'] == 'BHK1').sum()))
    data['bhk2'].append(int((df['type'] == 'BHK2').sum()))
    data['bhk3'].append(int((df['type'] == 'BHK3').sum()))
    data['bhk4p'].append(int((df['type'].isin(['BHK4', 'BHK4PLUS'])).sum()))
    
    # Furnishing
    data['furnFF'].append(int((df['furnishing'] == 'FULLY_FURNISHED').sum()))
    data['furnSF'].append(int((df['furnishing'] == 'SEMI_FURNISHED').sum()))
    data['furnNF'].append(int((df['furnishing'] == 'NOT_FURNISHED').sum()))
    
    # Lease Types
    data['leaseAny'].append(int((df['lease_type'] == 'ANYONE').sum()))
    data['leaseFamily'].append(int((df['lease_type'] == 'FAMILY').sum()))
    data['leaseBach'].append(int((df['lease_type'] == 'BACHELOR').sum()))

    # BHK Rents for Problem Solver
    for bhk in ['RK1', 'BHK1', 'BHK2', 'BHK3', 'BHK4']:
        # Categorize BHK4 and BHK4PLUS for the solver's 4BHK option
        bhk_filter = ['BHK4', 'BHK4PLUS'] if bhk == 'BHK4' else [bhk]
        avg = df[df['type'].isin(bhk_filter)]['rent'].mean()
        data['bhkRents'][bhk][dn] = int(avg) if not pd.isna(avg) else 0

print(json.dumps(data, indent=2))

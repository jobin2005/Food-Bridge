# utils/pincode.py
import os
from geopy.distance import geodesic
import pandas as pd

# Load pincode data
pincode_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'pincode_lat_long.csv'))
pincode_df.dropna(subset=['latitude', 'longitude'], inplace=True)
pincode_df['pincode'] = pincode_df['key'].astype(str).str.extract(r'(\d{6})')

def get_nearby_pincodes(base_pincode, radius_km=50):
    base_pincode = str(base_pincode)

    if base_pincode not in pincode_df['pincode'].values:
        print(f"Pincode {base_pincode} not found.")
        return []

    base = pincode_df[pincode_df['pincode'] == base_pincode].iloc[0]
    base_coord = (float(base['latitude']), float(base['longitude']))

    nearby_pins = []

    for _, row in pincode_df.iterrows():
        pin = row['pincode']
        coord = (float(row['latitude']), float(row['longitude']))
        distance = geodesic(base_coord, coord).km
        if distance <= radius_km:
            nearby_pins.append(pin)

    return nearby_pins

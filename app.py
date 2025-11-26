# app.py - WalletSafe (Public Google Sheet Edition)
# No auth needed - fetches CSV directly from published sheet
# Run: streamlit run app.py | Deploy: Streamlit Cloud

import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math

@st.cache_data(ttl=3600)  # Cache for 1 hour (hourly updates)
def load_data():
    try:
        # Your public sheet CSV export URL (gid=0 for first sheet)
        SHEET_KEY = '115DX0WMEfNNWzhAC26MTV1KdH0c86RVZysCBIZaaqho'
        url = f'https://docs.google.com/spreadsheets/d/{SHEET_KEY}/export?format=csv&gid=0'
        response = requests.get(url)
        response.raise_for_status()
        
        # Read CSV with flexible parsing for varying fields
        df = pd.read_csv(StringIO(response.text), on_bad_lines='skip')
        
        # Standardize columns (based on your Excel headers)
        df.columns = df.columns.str.strip()  # Clean headers
        expected_cols = ['Название заправки', 'Адрес', 'Город', 'Провинция', 'Бензин 95', 'Дизель', 'Рабочее время', 'Lat (Широта)', 'Long (Долгота)', 'Oбновлено в']
        df = df.reindex(columns=expected_cols, fill_value='')
        
        # Rename for simplicity
        df = df.rename(columns={
            'Название заправки': 'name',
            'Адрес': 'address',
            'Город': 'city',
            'Провинция': 'province',
            'Бензин 95': 'gas95_raw',
            'Дизель': 'diesel_raw',
            'Рабочее время': 'hours',
            'Lat (Широта)': 'lat_raw',
            'Long (Долгота)': 'lng_raw',
            'Oбновлено в': 'updated_raw'
        })
        
        # Clean prices (remove ' €' and convert to float)
        df['gas95'] = pd.to_numeric(df['gas95_raw'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel_raw'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        
        # Clean lat/lng
        df['lat'] = pd.to_numeric(df['lat_raw'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng_raw'], errors='coerce')
        
        # Filter valid stations (prices > 0, valid coords)
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0) & df['lat'].notna() & df['lng'].notna()]
        
        # Convert updated (Excel serial to date)
        def serial_to_date(serial):
            if pd.isna(serial):
                return 'N/A'
            try:
                base = datetime(1899, 12, 30)
                delta = timedelta(days=serial)
                return (base + delta).strftime('%Y-%m-%d %H:%M')
            except:
                return 'N/A'
        df['updated_date'] = df['updated_raw'].apply(serial_to_date)
        
        stations = df[['name', 'city', 'gas95', 'diesel', 'hours', 'lat', 'lng', 'updated_date']].to_dict('records')
        last_update = df['updated_date'].dropna().iloc[0] if not df['updated_date'].dropna().empty else 'N/A'
        
        return stations, last_update
    except Exception as e:
        st.error(f"Error loading sheet: {e}. Ensure sheet is published as CSV.")
        return [], 'N/A'

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon']) if r else None
    except:
        return None

# App Layout
st.set_page_config(page_title="WalletSafe", layout="wide")

# Custom CSS (clean white minimalist)
st.markdown("""
    <style>
    .stApp { background-color: white; }
    .logo { font-size: 32px; font-weight: 600; text-align: center; margin-bottom: 20px; padding: 20px; }
    .logo svg { width: 48px; height: 48px; vertical-align: middle; margin-right: 12px; fill: black; }
    .station { background: white; padding: 20px; border: 1px solid #eee; border-radius: 16px; margin-bottom: 16px; cursor: pointer; transition: box-shadow 0.2s; }
    .station:hover { box-shadow: 0 6px 30px rgba(0,0,0,0.08); }
    .name { font-size: 20px; font-weight: 600; }
    .price { font-size: 28px; font-weight: bold; color: black; margin: 10px 0; }
    .info { font-size: 15px; color: #555; }
    .controls { background: #fafafa; padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 20px; }
    .stButton > button { background: black; color: white; border-radius: 12px; border: none; padding: 12px 24px; font-weight: 500; }
    .stSlider > div > div > div > div { background: #ddd; }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="logo">
        <svg viewBox="0 0 64 64"><rect x="12" y="20" width="40" height="28" rx="6" fill="black"/><path d="M22 28 L32 34 L42 28" stroke="white" stroke-width="4" fill="none"/><circle cx="44" cy="34" r="8" fill="black"/></svg>
        WalletSafe
    </div>
""", unsafe_allow_html=True)

# Load data
stations, last_update = load_data()

# Controls
col1, col2 = st.columns([3, 1])
with col1:
    fuel = st.selectbox("Fuel Type", ["gas95", "diesel"], format_func=lambda x: "Gasoline 95" if x == "gas95" else "Diesel")
with col2:
    zip_input = st.text_input("ZIP Code", placeholder="e.g., 02001")

radius = st.slider("Search Radius (km)", 5, 100, 30)

if st.button("Use My Location"):
    # Note: Geolocation in Streamlit needs browser support; default to demo for now
    st.info("Enable location in browser. Using demo coords for now.")
    lat, lng = 38.99, -1.85  # Albacete demo
    search_results(lat, lng, fuel, radius, stations)
elif st.button("Find Cheapest", type="primary"):
    if zip_input:
        coords = geocode_zip(zip_input)
        if coords:
            lat, lng = coords
            search_results(lat, lng, fuel, radius, stations)
        else:
            st.error("Invalid ZIP.")
    else:
        st.error("Enter ZIP or use location.")

# Function to display results
def search_results(lat, lng, fuel, radius, stations):
    results = []
    for s in stations:
        price = s[fuel]
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= radius:
            results.append({**s, 'price': price, 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))  # Price first, then distance

    if not results:
        st.warning("No stations in radius.")
        return

    # Top 5 Cards
    for s in results[:5]:
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.markdown(f"""
                <div class="station" onclick="this.style.transform='scale(1.02)'">
                    <div class="name">{s['name']} • {s['city']}</div>
                    <div class="price">{s['price']:.3f} €</div>
                    <div class="info">{s['dist']:.1f} km • {s['hours']}</div>
                </div>
            """, unsafe_allow_html=True)
        with col_b:
            if st.button("Drive", key=f"drive_{id(s)}"):
                st.markdown(f"[Open Google Maps](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']}&travelmode=driving)")

    # Map
    m = folium.Map(location=[lat, lng], zoom_start=11)
    folium.CircleMarker([lat, lng], radius=8, popup="You", color="blue").add_to(m)
    for s in results[:5]:
        folium.Marker([s['lat'], s['lng']], popup=f"{s['name']} - {s['price']:.3f}€", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
        folium.PolyLine([[lat, lng], [s['lat'], s['lng']]], color="blue", weight=3).add_to(m)
    st_folium(m, width=700, height=500)

# Footer: Last Update
st.caption(f"**Last Updated:** {last_update} (refreshes hourly from your sheet)")
if not stations:
    st.info("No data loaded. Check sheet publish settings.")

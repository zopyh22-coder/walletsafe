# app.py - WalletSafe Streamlit Edition
# Deploy: Streamlit Cloud | Run local: streamlit run app.py

import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math

# Google Sheets setup (make sheet public or use service account)
gc = gspread.service_account()  # Assumes credentials.json uploaded to repo; for public sheet, use below
# SHEET_URL = 'https://docs.google.com/spreadsheets/d/115DX0WMEfNNWzhAC26MTV1KdH0c86RVZysCBIZaaqho/edit?usp=sharing'
# For public read: sheet = gc.open_by_url(SHEET_URL).sheet1

@st.cache_data(ttl=3600)  # Cache 1 hour for hourly updates
def load_data():
    try:
        # For public sheet - replace with your key if needed
        SHEET_KEY = '115DX0WMEfNNWzhAC26MTV1KdH0c86RVZysCBIZaaqho'
        SHEET_ID = '1'
        url = f'https://docs.google.com/spreadsheets/d/{SHEET_KEY}/export?format=csv&gid={SHEET_ID}'
        df = pd.read_csv(url)
        
        # Clean columns (match your sheet)
        df.columns = ['name', 'address', 'city', 'province', 'gas95', 'diesel', 'hours', 'lat', 'lng', 'updated']
        
        # Clean prices
        df['gas95'] = pd.to_numeric(df['gas95'].str.replace(' €', ''), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel'].str.replace(' €', ''), errors='coerce')
        
        # Filter valid stations (both prices > 0)
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0)]
        
        # Convert updated serial date
        base = datetime(1899, 12, 30)
        df['updated_date'] = df['updated'].apply(lambda x: (base + timedelta(x)).strftime('%Y-%m-%d %H:%M') if pd.notna(x) else 'N/A')
        
        return df[['name', 'city', 'gas95', 'diesel', 'hours', 'lat', 'lng', 'updated_date']].to_dict('records'), df['updated_date'].iloc[0] if not df.empty else 'N/A'
    except Exception as e:
        st.error(f"Error loading data: {e}. Check sheet access.")
        return [], 'N/A'

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode_zip(zip_code):
    # Simple Nominatim (free)
    import requests
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon']) if r else None
    except:
        return None

# Streamlit App
st.set_page_config(page_title="WalletSafe", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for clean white minimalist look
st.markdown("""
    <style>
    body { background-color: white; color: black; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: white; }
    .logo { font-size: 32px; font-weight: 600; text-align: center; margin-bottom: 20px; }
    .logo svg { width: 48px; height: 48px; vertical-align: middle; margin-right: 12px; }
    .station { background: white; padding: 20px; border: 1px solid #eee; border-radius: 16px; margin-bottom: 16px; cursor: pointer; transition: box-shadow 0.2s; }
    .station:hover { box-shadow: 0 6px 30px rgba(0,0,0,0.08); }
    .name { font-size: 20px; font-weight: 600; }
    .price { font-size: 28px; font-weight: bold; color: #000; margin: 10px 0; }
    .info { font-size: 15px; color: #555; }
    .controls { background: #fafafa; padding: 20px; border-radius: 16px; text-align: center; }
    button { background: black; color: white; border: none; border-radius: 12px; padding: 14px 20px; font-size: 16px; cursor: pointer; }
    button:hover { background: #333; }
    #map { border-radius: 20px; box-shadow: 0 6px 40px rgba(0,0,0,0.1); }
    .slider { width: 80%; max-width: 500px; }
    </style>
""", unsafe_allow_html=True)

# Header with Logo
st.markdown("""
    <div class="logo">
        <svg viewBox="0 0 64 64"><rect x="12" y="20" width="40" height="28" rx="6" fill="black"/><path d="M22 28 L32 34 L42 28" stroke="white" stroke-width="4" fill="none"/><circle cx="44" cy="34" r="8" fill="black"/></svg>
        WalletSafe
    </div>
""", unsafe_allow_html=True)

# Load data
stations, last_update = load_data()

col1, col2 = st.columns([3, 1])
with col1:
    fuel = st.selectbox("Fuel Type", ["gas95", "diesel"], format_func=lambda x: "Gasoline 95" if x == "gas95" else "Diesel")
with col2:
    zip_input = st.text_input("ZIP Code (Spain)", placeholder="e.g., 02001")

radius = st.slider("Search Radius (km)", 5, 100, 30, key="radius")
use_geo = st.button("Use My Location")

if st.button("Find Cheapest Stations", type="primary"):
    if zip_input:
        coords = geocode_zip(zip_input)
        if not coords:
            st.error("Invalid ZIP. Try another.")
        else:
            lat, lng = coords
    elif use_geo:
        # Streamlit geolocation (requires config.toml or browser support)
        st.warning("Geolocation: Enable in browser settings.")
        lat, lng = 38.99, -1.85  # Default to Albacete for demo
    else:
        st.error("Enter ZIP or use location.")
        st.stop()

    # Filter & Sort: Price first, then distance
    results = []
    for s in stations:
        price = s[fuel]
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= radius:
            results.append({**s, 'price': price, 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))  # Cheapest then closest

    # Display Top 5
    for s in results[:5]:
        with st.container():
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"""
                    <div class="station">
                        <div class="name">{s['name']} • {s['city']}</div>
                        <div class="price">{s['price']:.3f} €</div>
                        <div class="info">{s['dist']:.1f} km • {s['hours']}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("Drive", key=f"drive_{s['name']}"):
                    st.components.v1.html(f'<a href="https://www.google.com/maps/dir/?api=1&destination={s["lat"]},{s["lng"]}&travelmode=driving" target="_blank">Open Maps</a>', height=0)

    # Map
    if results:
        m = folium.Map(location=[lat, lng], zoom_start=11, tiles="OpenStreetMap")
        folium.CircleMarker([lat, lng], radius=8, popup="You", color="blue", fill=True).add_to(m)
        for s in results[:5]:
            folium.Marker([s['lat'], s['lng']], popup=f"{s['name']} - {s['price']:.3f}€", icon=folium.Icon(color="red", icon="fuel-pump")).add_to(m)
            # Route line
            folium.PolyLine([[lat, lng], [s['lat'], s['lng']]], color="blue", weight=3, opacity=0.6).add_to(m)
        st_folium(m, width=700, height=500)

# Last Update
if last_update != 'N/A':
    st.caption(f"Last Updated: {last_update} (refreshes hourly)")

if not stations:
    st.info("No valid stations found. Check sheet data.")

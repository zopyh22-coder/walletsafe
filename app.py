# app.py – WalletSafe Final Version
# Works on Streamlit Cloud without any secrets

import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math

# ——— REAL WALLET LOGO (SVG) ———
wallet_svg = """
<svg width="48" height="48" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="18" width="44" height="32" rx="8" fill="#000"/>
  <rect x="18" y="25" width="28" height="18" rx="4" fill="#fff"/>
  <circle cx="46" cy="33" r="10" fill="#000"/>
  <path d="M41 30 L46 33 L41 36" stroke="#fff" stroke-width="4" fill="none"/>
</svg>
"""

# ——— LOAD DATA FROM YOUR PUBLIC SHEET ———
@st.cache_data(ttl=3600)  # refresh every hour
def load_data():
    try:
        # This is the working public CSV link (you already have it)
        csv_url = "https://docs.google.com/spreadsheets/d/115DX0WMEfNNWzhAC26MTV1KdH0c86RVZysCBIZaaqho/export?format=csv&gid=0"
        r = requests.get(csv_url)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        
        # Auto-detect columns (works even if order changes)
        df = df.rename(columns=lambda x: x.strip())
        col_map = {
            'Название заправки': 'name', 'Город': 'city', 'Бензин 95': 'gas95_raw',
            'Дизель': 'diesel_raw', 'Рабочее время': 'hours',
            'Lat (Широта)': 'lat', 'Long (Долгота)': 'lng', 'Oбновлено в': 'updated_raw'
        }
        df = df.rename(columns={v: k for k, v in col_map.items() if v in df.columns})
        
        # Clean prices
        df['gas95'] = pd.to_numeric(df['gas95_raw'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel_raw'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        
        # Clean coordinates
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        
        # Filter valid stations
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0) & df['lat'].notna() & df['lng'].notna()]
        
        # Convert update time
        def serial_to_date(x):
            if pd.isna(x): return "Unknown"
            try:
                return (datetime(1899,12,30) + timedelta(days=float(x))).strftime("%d.%m.%Y %H:%M")
            except:
                return "Unknown"
        df['updated'] = df['updated_raw'].apply(serial_to_date)
        
        stations = df[['name','city','gas95','diesel','hours','lat','lng','updated']].to_dict('records')
        last_update = df['updated'].iloc[0] if not df.empty else "Unknown"
        return stations, last_update
    except Exception as e:
        st.error("Could not load data. Make sure the sheet is published as CSV.")
        return [], "Error"

# ——— DISTANCE CALCULATION ———
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# ——— GEOCODE ZIP ———
def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        if r:
            return float(r[0]['lat']), float(r[0]['lon'])
    except:
        pass
    return None

# ——— STREAMLIT APP ———
st.set_page_config(page_title="WalletSafe", layout="centered")

st.markdown(f"""
<div style="text-align:center; padding:30px 0;">
    {wallet_svg}
    <h1 style="display:inline; margin-left:12px; font-weight:600;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

stations, last_update = load_data()

col1, col2 = st.columns([2,1])
with col1:
    fuel = st.selectbox("Fuel", ["gas95","diesel"], format_func=lambda x: "Gasoline 95" if x=="gas95" else "Diesel")
with col2:
    zip_code = st.text_input("ZIP Code", placeholder="e.g. 02001")

radius = st.slider("Radius (km)", 5, 100, 30)

if st.button("Use My Location"):
    st.warning("Geolocation not supported in preview. Using demo location.")
    lat, lng = 38.985, -1.855  # Albacete centre

if st.button("Find Cheapest Stations", type="primary"):
    if zip_code:
        coords = geocode_zip(zip_code)
        if not coords:
            st.error("Invalid ZIP code")
            st.stop()
        lat, lng = coords
    elif 'lat' not in locals():
        st.error("Enter a ZIP code or use location")
        st.stop()

    results = []
    for s in stations:
        price = s[fuel]
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= radius:
            results.append({**s, 'price': price, 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))

    if not results:
        st.info("No stations found in this radius.")
    else:
        st.success(f"Found {len(results)} stations – showing top 5 cheapest")
        for s in results[:5]:
            col1, col2 = st.columns([4,1])
            with col1:
                st.markdown(f"""
                <div style="padding:18px; border:1px solid #eee; border-radius:16px; margin:10px 0; cursor:pointer;">
                    <b style="font-size:20px">{s['name']}</b> • {s['city']}<br>
                    <span style="font-size:28px; font-weight:bold">{s['price']:.3f} €</span><br>
                    <span style="color:#555">{s['dist']:.1f} km • {s['hours']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"[Drive](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']}&travelmode=driving)")

        # Map
        m = folium.Map(location=[lat, lng], zoom_start=11)
        folium.CircleMarker([lat, lng], radius=8, color="blue", fill=True, popup="You are here").add_to(m)
        for s in results[:5]:
            folium.Marker([s['lat'], s['lng']], 
                         popup=f"<b>{s['name']}</b><br>{s['price']:.3f}€", 
                         icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
            folium.PolyLine([[lat,lng],[s['lat'],s['lng']]], color="#0066ff", weight=4, opacity=0.6).add_to(m)
        st_folium(m, width=700, height=500)

st.caption(f"Last updated: **{last_update}** • Data refreshes hourly")

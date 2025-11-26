# app.py – WalletSafe (Uses Your Published CSV)
import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math

# Wallet Logo (SVG)
wallet_svg = """
<svg width="50" height="50" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="18" width="44" height="32" rx="8" fill="#000"/>
  <rect x="18" y="25" width="28" height="18" rx="4" fill="#fff"/>
  <circle cx="46" cy="33" r="10" fill="#000"/>
  <path d="M41 30 L46 33 L41 36" stroke="#fff" stroke-width="4" fill="none"/>
</svg>
"""

@st.cache_data(ttl=3600)  # Hourly refresh
def load_data():
    try:
        # Your published CSV link
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"
        r = requests.get(csv_url)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        
        # Clean columns (flexible for your headers)
        df.columns = df.columns.str.strip()
        col_map = {
            'Название заправки': 'name', 'Город': 'city', 'Бензин 95': 'gas95_raw',
            'Дизель': 'diesel_raw', 'Рабочее время': 'hours', 'Lat (Широта)': 'lat',
            'Long (Долгота)': 'lng', 'Oбновлено в': 'updated_raw'
        }
        df = df.rename(columns={v: k for k, v in col_map.items() if v in df.columns})
        
        # Clean data
        df['gas95'] = pd.to_numeric(df['gas95_raw'].str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel_raw'].str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        
        # Filter valid
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0) & df['lat'].notna() & df['lng'].notna()]
        
        # Updated date
        def serial_to_date(x):
            if pd.isna(x): return 'N/A'
            try:
                return (datetime(1899,12,30) + timedelta(days=float(x))).strftime('%d.%m.%Y %H:%M')
            except: return 'N/A'
        df['updated'] = df['updated_raw'].apply(serial_to_date)
        
        stations = df[['name', 'city', 'gas95', 'diesel', 'hours', 'lat', 'lng', 'updated']].to_dict('records')
        last_update = df['updated'].dropna().iloc[0] if not df.empty else 'N/A'
        return stations, last_update
    except Exception as e:
        st.error(f"Load error: {e}. Check CSV publish.")
        return [], 'N/A'

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon']) if r else None
    except:
        return None

# App
st.set_page_config(page_title="WalletSafe", layout="wide")

# Header
st.markdown(f"""
<div style="text-align:center; padding:20px;">
    {wallet_svg}
    <h1 style="display:inline; margin-left:10px; font-weight:600;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

stations, last_update = load_data()

col1, col2 = st.columns([3,1])
with col1:
    fuel = st.selectbox("Fuel Type", ["gas95", "diesel"], format_func=lambda x: "Gasoline 95" if x=="gas95" else "Diesel")
with col2:
    zip_input = st.text_input("ZIP Code", placeholder="e.g., 02001")

# Short slider (60% width)
st.markdown('<style>.stSlider > div > div > div {width: 60% !important;}</style>', unsafe_allow_html=True)
radius = st.slider("Search Radius (km)", 5, 100, 30)

if st.button("Use My Location"):
    lat, lng = 38.99, -1.85  # Demo
    search_results(lat, lng, fuel, radius)
elif st.button("Find Cheapest", type="primary"):
    if zip_input:
        coords = geocode_zip(zip_input)
        if coords:
            search_results(*coords, fuel, radius)
        else:
            st.error("Invalid ZIP.")
    else:
        st.error("Enter ZIP or use location.")

def search_results(lat, lng, fuel, radius):
    results = []
    for s in stations:
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= radius:
            results.append({**s, 'price': s[fuel], 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))

    if not results:
        st.info("No stations in radius.")
        return

    for s in results[:5]:
        col_a, col_b = st.columns([4,1])
        with col_a:
            st.markdown(f"""
                <div style="padding:16px; border:1px solid #eee; border-radius:12px; margin:8px 0;">
                    <b>{s['name']} • {s['city']}</b><br>
                    <span style="font-size:24px; font-weight:bold;">{s['price']:.3f} €</span><br>
                    <small>{s['dist']:.1f} km • {s['hours']}</small>
                </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"[Drive](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']})")

    # Map
    m = folium.Map([lat, lng], zoom_start=11)
    folium.CircleMarker([lat, lng], radius=8, color="blue", popup="You").add_to(m)
    for s in results[:5]:
        folium.Marker([s['lat'], s['lng']], popup=f"{s['name']} - {s['price']:.3f}€", icon=folium.Icon(color="green")).add_to(m)
        folium.PolyLine([[lat,lng],[s['lat'],s['lng']]], color="blue", weight=3).add_to(m)
    st_folium(m, width=700, height=450)

st.caption(f"Last Updated: {last_update} • Hourly refresh")

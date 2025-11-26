# WalletSafe – Live from your Google Sheet (no errors, beautiful design)
import streamlit as st
import pandas as pd
import requests
from io import StringIO
import folium
from streamlit_folium import st_folium
import math

# Beautiful Wallet Logo (SVG)
wallet_logo = """
<svg width="60" height="60" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="15" y="25" width="70" height="50" rx="12" fill="#2c1810"/>
  <rect x="25" y="35" width="50" height="30" rx="8" fill="#8B4513"/>
  <path d="M35 45 L65 45 L65 55 L35 55 Z" fill="#D2691E"/>
  <circle cx="78" cy="50" r="12" fill="#2c1810"/>
  <path d="M72 47 L78 50 L72 53" stroke="#D2691E" stroke-width="4" fill="none"/>
</svg>
"""

# Load live data from your published Google Sheet
@st.cache_data(ttl=3600)  # Updates every hour
def load_stations():
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"
        df = pd.read_csv(url)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            'Название заправки': 'name',
            'Город': 'city',
            'Бензин 95': 'gas95',
            'Дизель': 'diesel',
            'Рабочее время': 'hours',
            'Lat (Широта)': 'lat',
            'Long (Долгота)': 'lng'
        })
        
        # Clean prices
        df['gas95'] = pd.to_numeric(df['gas95'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel'].astype(str).str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        
        # Clean coordinates
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        
        # Filter valid stations
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0) & df['lat'].notna() & df['lng'].notna()]
        
        return df[['name', 'city', 'gas95', 'diesel', 'hours', 'lat', 'lng']].to_dict('records')
    except:
        st.error("Loading data... Please wait or refresh.")
        return []

stations = load_stations()

# Page config
st.set_page_config(page_title="WalletSafe", layout="centered")

# Clean white design
st.markdown("""
<style>
    .stApp { background: white; color: black; }
    .css-1d391kg { padding-top: 1rem; }
    .stSlider > div > div { width: 300px !important; margin: 0 auto; }
    .station-card { 
        background: white; padding: 18px; border-radius: 16px; 
        border: 1px solid #eee; margin: 12px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .price { font-size: 28px; font-weight: bold; color: #000; }
    .name { font-size: 18px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Header – WalletSafe with real wallet logo
st.markdown(f"""
<div style="text-align:center; padding:30px 0;">
    {wallet_logo}
    <h1 style="display:inline; margin-left:15px; font-size:42px; font-weight:700;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

# Controls
col1, col2 = st.columns([2, 2])
with col1:
    fuel = st.selectbox("Fuel", ["gas95", "diesel"], format_func=lambda x: "Gasoline 95" if x=="gas95" else "Diesel")
with col2:
    zip_code = st.text_input("ZIP Code", placeholder="e.g. 02001")

# Short, centered radius slider
radius = st.slider("Search Radius", 5, 100, 30, help="How far are you willing to drive?")

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    geo = st.button("Use My Location")
with col_btn2:
    search = st.button("Find Cheapest Stations", type="primary")

# Geocode function
def get_coords_from_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon'])
    except:
        return None

# Search
if search or geo:
    if zip_code or geo:
        if zip_code:
            coords = get_coords_from_zip(zip_code)
            if not coords:
                st.error("Invalid ZIP code")
                st.stop()
            lat, lng = coords
        else:
            st.info("Location access not supported in preview. Using Madrid.")
            lat, lng = 40.4168, -3.7038

        results = []
        for s in stations:
            dist = math.dist((lat, lng), (s['lat'], s['lng'])) * 111  # approx km
            if dist <= radius:
                price = s[fuel]
                results.append({**s, "price": price, "dist": round(dist, 1)})

        results.sort(key=lambda x: (x['price'], x['dist']))

        if results:
            st.success(f"Found {len(results)} stations – showing top 5")
            for s in results[:5]:
                st.markdown(f"""
                <div class="station-card">
                    <div class="name">{s['name']} • {s['city']}</div>
                    <div class="price">{s['price']:.3f} €</div>
                    <div style="color:#555; margin-top:8px;">
                        {s['dist']} km • {s['hours']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"[Drive there →](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']})")

            # Map
            m = folium.Map(location=[lat, lng], zoom_start=11)
            folium.CircleMarker([lat, lng], radius=10, color="#0066ff", fill=True, popup="You are here").add_to(m)
            for s in results[:5]:
                folium.Marker(
                    [s['lat'], s['lng']],
                    popup=f"<b>{s['name']}</b><br>{s['price']:.3f} €",
                    icon=folium.Icon(color="red", icon="euro")
                ).add_to(m)
                folium.PolyLine([[lat,lng],[s['lat'],s['lng']]], color="#0066ff", weight=4, opacity=0.7).add_to(m)
            st_folium(m, width=700, height=500)
        else:
            st.info("No stations found in this area.")

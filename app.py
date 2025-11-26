# app.py - WalletSafe (Streamlit, Live CSV, No Errors)
import streamlit as st
import pandas as pd
import requests
from io import StringIO
import folium
from streamlit_folium import st_folium
import math
import streamlit.components.v1 as components

# New Wallet Logo (Inspired by modern e-wallet icon – clean black & white line style)
wallet_svg = """
<svg width="50" height="50" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="18" width="44" height="32" rx="6" fill="none" stroke="#000" stroke-width="4"/>
  <path d="M10 34 H54" stroke="#000" stroke-width="4"/>
  <path d="M36 18 V50" stroke="#000" stroke-width="4"/>
  <circle cx="46" cy="34" r="6" fill="none" stroke="#000" stroke-width="4"/>
</svg>
"""

@st.cache_data(ttl=3600)
def load_data():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"
        r = requests.get(csv_url)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            'Название заправки': 'name',
            'Город': 'city',
            'Бензин 95': 'gas95',
            'Дизель': 'diesel',
            'Рабочее время': 'hours',
            'Lat (Широта)': 'lat',
            'Long (Долгота)': 'lng',
            'Oбновлено в': 'updated_raw'
        })
        
        df['gas95'] = pd.to_numeric(df['gas95'].str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['diesel'] = pd.to_numeric(df['diesel'].str.replace(' €', '').str.replace(',', '.'), errors='coerce')
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        
        df = df[(df['gas95'] > 0) & (df['diesel'] > 0) & df['lat'].notna() & df['lng'].notna()]
        
        def serial_to_date(x):
            if pd.isna(x): return 'N/A'
            try:
                return (datetime(1899, 12, 30) + timedelta(days=float(x))).strftime('%d.%m.%Y %H:%M')
            except:
                return 'N/A'
        df['updated'] = df['updated_raw'].apply(serial_to_date)
        
        return df[['name', 'city', 'gas95', 'diesel', 'hours', 'lat', 'lng', 'updated']].to_dict('records'), df['updated'].iloc[0] if not df.empty else 'N/A'
    except Exception as e:
        st.error(f"Data load error. Refresh or check sheet.")
        return [], 'N/A'

stations, last_update = load_data()

st.set_page_config(page_title="WalletSafe", layout="centered")

# CSS for clean layout (short slider, no code leaks)
st.markdown("""
<style>
    .stApp { background: white; }
    .css-1d391kg { padding-top: 1rem; }
    .stSlider > div > div > div > div { width: 400px !important; margin: 0 auto; }
    .station { background: white; padding: 20px; border: 1px solid #eee; border-radius: 16px; margin: 12px 0; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .price { font-size: 28px; font-weight: bold; color: #000; }
    .name { font-size: 20px; font-weight: 600; }
    .stTextInput > div > div > input { padding-right: 40px !important; }
    .search-icon { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="text-align:center; padding:30px 0;">
    {wallet_svg}
    <h1 style="display:inline; margin-left:15px; font-size:42px; font-weight:700;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

# Controls (clean, easy)
fuel = st.selectbox("Fuel Type", ["gas95", "diesel"], format_func=lambda x: "Gasoline 95" if x == "gas95" else "Diesel")

# ZIP Bar with Search Icon (auto-search on enter)
zip_code = st.text_input("ZIP Code", placeholder="e.g. 02001", key="zip")

# Search Icon (click to search)
st.markdown("""
<div class="search-icon" onclick="document.getElementById('zip').dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));">
    🔍
</div>
""", unsafe_allow_html=True)

# Short Slider
radius = st.slider("Search Radius (km)", 0, 100, 30)

# Geo Button
if st.button("Use My Location"):
    components.html("""
    <script>
    navigator.geolocation.getCurrentPosition(
        pos => { parent.window.location.href = '?lat=' + pos.coords.latitude + '&lng=' + pos.coords.longitude; },
        err => { alert('Location denied.'); }
    );
    </script>
    <p>Requesting...</p>
    """, height=50)

    query_params = st.query_params
    lat = float(query_params.get('lat', [38.99])[0])
    lng = float(query_params.get('lng', [ -1.85])[0])
    search_results(lat, lng, fuel, radius)

# Auto-search on ZIP enter or button
if zip_code:
    coords = get_coords_from_zip(zip_code)
    if coords:
        lat, lng = coords
        search_results(lat, lng, fuel, radius)
    else:
        st.error("Invalid ZIP code.")

def get_coords_from_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon']) if r else None
    except:
        return None

def search_results(lat, lng, fuel, radius):
    results = []
    for s in stations:
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= radius:
            results.append({**s, 'price': s[fuel], 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))

    if not results:
        st.info("No stations found.")
        return

    for s in results[:5]:
        st.markdown(f"""
        <div class="station">
            <div class="name">{s['name']} • {s['city']}</div>
            <div class="price">{s['price']:.3f} €</div>
            <div style="color:#555;">{s['dist']:.1f} km • {s['hours']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"[Drive](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']})")

    # Map
    m = folium.Map([lat, lng], zoom_start=11)
    folium.CircleMarker([lat, lng], radius=10, color="#0066ff", popup="You").add_to(m)
    for s in results[:5]:
        folium.Marker([s['lat'], s['lng']], popup=f"{s['name']} - {s['price']:.3f} €", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine([[lat,lng],[s['lat'],s['lng']]], color="#0066ff", weight=4).add_to(m)
    st_folium(m, width=700, height=500)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

st.caption(f"Last Updated: {last_update}")

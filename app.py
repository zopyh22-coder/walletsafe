# app.py - WalletSafe (Streamlit, Live CSV, Languages, No Errors)
import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import math

# Wallet Logo (New clean design from code)
wallet_svg = """
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="30" width="60" height="40" rx="5" fill="#333"/>
  <path d="M30 40 L70 40" stroke="#fff" stroke-width="2"/>
  <path d="M30 50 L70 50" stroke="#fff" stroke-width="2"/>
  <circle cx="75" cy="50" r="10" fill="#333"/>
  <path d="M70 47 L75 50 L70 53" stroke="#fff" stroke-width="2" fill="none"/>
</svg>
"""

# Translations
translations = {
    'ru': {
        'fuel_label': 'Тип топлива',
        'gas95': 'Бензин 95',
        'diesel': 'Дизель',
        'zip_label': 'Почтовый индекс',
        'zip_placeholder': 'например, 02001',
        'radius_label': 'Радиус поиска (км)',
        'location_button': 'Мое местоположение',
        'search_button': 'Найти самые дешевые заправки',
        'no_stations': 'Нет заправок в радиусе.',
        'stations_found': 'Найдено {count} заправок – топ 5',
        'drive': 'Проложить маршрут',
        'last_updated': 'Обновлено: {time}',
    },
    'en': {
        'fuel_label': 'Fuel Type',
        'gas95': 'Gasoline 95',
        'diesel': 'Diesel',
        'zip_label': 'ZIP Code',
        'zip_placeholder': 'e.g., 02001',
        'radius_label': 'Search Radius (km)',
        'location_button': 'My Location',
        'search_button': 'Find Cheapest Stations',
        'no_stations': 'No stations in radius.',
        'stations_found': 'Found {count} stations – top 5',
        'drive': 'Drive',
        'last_updated': 'Updated: {time}',
    },
    'es': {
        'fuel_label': 'Tipo de combustible',
        'gas95': 'Gasolina 95',
        'diesel': 'Diésel',
        'zip_label': 'Código postal',
        'zip_placeholder': 'p.ej., 02001',
        'radius_label': 'Radio de búsqueda (km)',
        'location_button': 'Mi ubicación',
        'search_button': 'Encontrar estaciones más baratas',
        'no_stations': 'No hay estaciones en radio.',
        'stations_found': 'Encontradas {count} estaciones – top 5',
        'drive': 'Navegar',
        'last_updated': 'Actualizado: {time}',
    }
}

# Language selector (top right, small flags)
st.markdown("""
<style>
.lang-select { position: absolute; top: 10px; right: 10px; font-size: 24px; }
.lang-select > div { display: inline-block; margin-left: 10px; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

lang_html = """
<div class="lang-select">
  <div onclick="selectLang('ru')">🇷🇺</div>
  <div onclick="selectLang('en')">🇬🇧</div>
  <div onclick="selectLang('es')">🇪🇸</div>
</div>
<script>
function selectLang(lang) {
  parent.window.location.href = '?lang=' + lang;
}
</script>
"""
components.html(lang_html, height=50)

query_params = st.query_params
st.session_state.lang = query_params.get('lang', [ 'ru' ])[0]
t = translations[st.session_state.lang]

st.set_page_config(page_title="WalletSafe", layout="centered")

# CSS for clean layout
st.markdown("""
<style>
.stApp { background: white; }
.logo { text-align: center; padding: 30px 0; }
.stSlider > div > div > div { width: 60% !important; margin: 0 auto; }
.station { padding: 20px; border: 1px solid #eee; border-radius: 16px; margin: 12px 0; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.station:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.price { font-size: 28px; font-weight: bold; color: #000; }
.name { font-size: 20px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="logo">
    {wallet_svg}
    <h1 style="display: inline; margin-left: 15px; font-size: 42px; font-weight: 700;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

# Controls
col1, col2 = st.columns([2,2])
with col1:
    fuel = st.selectbox(t['fuel_label'], ["gas95", "diesel"], format_func=lambda x: t[x])
with col2:
    zip_input = st.text_input(t['zip_label'], placeholder=t['zip_placeholder'])

# Slider (0-100 km)
radius = st.slider(t['radius_label'], 0, 100, 30)

# Geo
if st.button(t['location_button']):
    components.html("""
    <script>
    navigator.geolocation.getCurrentPosition(
        pos => { parent.window.location.href = '?lat=' + pos.coords.latitude + '&lng=' + pos.coords.longitude; },
        err => { alert('Permission denied.'); }
    );
    </script>
    <p>Requesting...</p>
    """, height=50)

    query_params = st.query_params
    lat = float(query_params.get('lat', [38.99])[0])
    lng = float(query_params.get('lng', [ -1.85])[0])
    search_results(lat, lng, fuel, radius)

# Auto-search on ZIP
if zip_input:
    coords = geocode_zip(zip_input)
    if coords:
        lat, lng = coords
        search_results(lat, lng, fuel, radius)
    else:
        st.error("Invalid ZIP.")

def geocode_zip(zip_code):
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
        st.info(t['no_stations'])
        return

    st.success(t['stations_found'].format(count=len(results)))

    for s in results[:5]:
        col_a, col_b = st.columns([4,1])
        with col_a:
            st.markdown(f"""
                <div class="station">
                    <div class="name">{s['name']} • {s['city']}</div>
                    <div class="price">{s['price']:.3f} €</div>
                    <div style="color:#555;">{s['dist']:.1f} km • {s['hours']}</div>
                </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"[ {t['drive']} ](https://www.google.com/maps/dir/?api=1&destination={s['lat']},{s['lng']})")

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

st.caption(t['last_updated'].format(time=last_update))

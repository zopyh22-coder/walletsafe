# app.py - WalletSafe (Streamlit, Sample Data, Languages, Tabs for Radius)
import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import streamlit.components.v1 as components
import requests

# Wallet Logo (Clean, modern style)
wallet_svg = """
<svg width="50" height="50" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="18" width="44" height="32" rx="6" fill="none" stroke="#000" stroke-width="4"/>
  <path d="M10 34 H54" stroke="#000" stroke-width="4"/>
  <path d="M36 18 V50" stroke="#000" stroke-width="4"/>
  <circle cx="46" cy="34" r="6" fill="none" stroke="#000" stroke-width="4"/>
</svg>
"""

# Sample Stations (from your sheet – replace with full list)
stations = [
    {"name": "Nº 10.935", "city": "Abengibre", "gas95": 1.399, "diesel": 1.419, "hours": "07:00–22:00", "lat": 39.211417, "lng": -1.539167},
    {"name": "REPSOL", "city": "Alatoz", "gas95": 1.609, "diesel": 1.559, "hours": "7:00-23:00", "lat": 39.100389, "lng": -1.346083},
    {"name": "BP ROMICA", "city": "Albacete", "gas95": 1.519, "diesel": 1.509, "hours": "06:00–22:00", "lat": 39.054694, "lng": -1.832000},
    {"name": "CARREFOUR", "city": "Albacete", "gas95": 1.509, "diesel": 1.459, "hours": "08:00–22:00", "lat": 38.985667, "lng": -1.868500},
    {"name": "PLENERGY", "city": "Albacete", "gas95": 1.379, "diesel": 1.337, "hours": "24/7", "lat": 39.000861, "lng": -1.849833},
    {"name": "REPSOL", "city": "Albacete", "gas95": 1.539, "diesel": 1.509, "hours": "06:00–22:00", "lat": 38.999722, "lng": -1.854556},
    {"name": "PLENERGY", "city": "Albacete", "gas95": 1.379, "diesel": 1.337, "hours": "24/7", "lat": 39.005528, "lng": -1.884444},
    {"name": "TAMOS", "city": "Albacete", "gas95": 1.499, "diesel": 1.509, "hours": "05:00–01:00", "lat": 39.003333, "lng": -1.864917},
    {"name": "MOEVE", "city": "Albacete", "gas95": 1.499, "diesel": 1.545, "hours": "06:00–22:00", "lat": 39.005083, "lng": -1.859917},
    {"name": "A&A", "city": "Albacete", "gas95": 1.347, "diesel": 1.297, "hours": "09:00–21:30", "lat": 39.006889, "lng": -1.885361},
    # Add full list here – replace with all parsed rows from your sheet
]

# Last Update (from sheet)
last_update = "26.11.2025 20:30"

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
        'apply_radius': 'Применить радиус',
        'no_stations': 'Нет заправок в радиусе.',
        'stations_found': 'Найдено {count} заправок – топ 5',
        'drive': 'Проложить маршрут',
        'last_updated': 'Обновлено: {time}',
        'search_tab': 'Поиск',
        'results_tab': 'Результаты',
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
        'apply_radius': 'Apply Radius',
        'no_stations': 'No stations in radius.',
        'stations_found': 'Found {count} stations – top 5',
        'drive': 'Drive',
        'last_updated': 'Updated: {time}',
        'search_tab': 'Search',
        'results_tab': 'Results',
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
        'apply_radius': 'Aplicar radio',
        'no_stations': 'No hay estaciones en radio.',
        'stations_found': 'Encontradas {count} estaciones – top 5',
        'drive': 'Navegar',
        'last_updated': 'Actualizado: {time}',
        'search_tab': 'Buscar',
        'results_tab': 'Resultados',
    }
}

# Language selector (top right, small flags)
st.markdown("""
<style>
.lang-select { position: absolute; top: 10px; right: 10px; font-size: 18px; }
.lang-select > div { display: inline-block; margin-left: 5px; cursor: pointer; }
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
components.html(lang_html, height=40)

query_params = st.query_params
st.session_state.lang = query_params.get('lang', ['ru'])[0]
t = translations[st.session_state.lang]

st.set_page_config(page_title="WalletSafe", layout="centered")

# CSS for clean, easy layout (short slider)
st.markdown("""
<style>
.stApp { background: white; }
.logo { text-align: center; padding: 30px 0; }
.stSlider > div > div > div { width: 60% !important; margin: 0 auto; }
.station { padding: 20px; border: 1px solid #eee; border-radius: 16px; margin: 12px 0; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.station:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.price { font-size: 28px; font-weight: bold; color: #000; }
.name { font-size: 20px; font-weight: 600; }
.stTextInput > div > div { position: relative; }
.search-icon { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 20px; color: #333; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="logo">
    {wallet_svg}
    <h1 style="display: inline; margin-left: 15px; font-size: 42px; font-weight: 700;">WalletSafe</h1>
</div>
""", unsafe_allow_html=True)

# Tabs for Search and Results
tab1, tab2 = st.tabs([t['search_tab'], t['results_tab']])

with tab1:
    fuel = st.selectbox(t['fuel_label'], ["gas95", "diesel"], format_func=lambda x: t[x])
    zip_input = st.text_input(t['zip_label'], placeholder=t['zip_placeholder'])
    st.markdown('<div class="search-icon" onclick="parent.document.querySelector(\'[data-testid="stButton"][label="Search"]\').click();">🔍</div>', unsafe_allow_html=True)

    if st.button(t['search_button']):
        if zip_input:
            coords = geocode_zip(zip_input)
            if coords:
                st.session_state['lat'], st.session_state['lng'] = coords
                st.session_state['fuel'] = fuel
                st.session_state['radius'] = 30  # Default
                st.session_state['searched'] = True
                st.experimental_rerun()
            else:
                st.error("Invalid ZIP.")
        else:
            st.error("Enter ZIP.")

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
        st.session_state['lat'], st.session_state['lng'] = lat, lng
        st.session_state['fuel'] = fuel
        st.session_state['radius'] = 30  # Default
        st.session_state['searched'] = True
        st.experimental_rerun()

with tab2:
    if 'searched' in st.session_state and st.session_state['searched']:
        # Radius slider appears here after search
        st.markdown("<p style='text-align:center; font-weight:600;'>Adjust radius to update results</p>", unsafe_allow_html=True)
        radius = st.slider("", 0, 100, st.session_state['radius'], label_visibility="collapsed")
        
        if radius != st.session_state['radius']:
            st.session_state['radius'] = radius
            st.experimental_rerun()

        lat = st.session_state['lat']
        lng = st.session_state['lng']
        fuel = st.session_state['fuel']
        radius = st.session_state['radius']
        
        results = []
        for s in stations:
            dist = haversine(lat, lng, s['lat'], s['lng'])
            if dist <= radius:
                results.append({**s, 'price': s[fuel], 'dist': dist})

        results.sort(key=lambda x: (x['price'], x['dist']))

        if not results:
            st.info(t['no_stations'])
        else:
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
    else:
        st.info("Perform a search to see results.")

def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}).json()
        return float(r[0]['lat']), float(r[0]['lon']) if r else None
    except:
        return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

st.caption(t['last_updated'].format(time=last_update))

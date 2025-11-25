import streamlit as st
import pandas as pd
import numpy as np
import pgeocode
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

# --- 1. НАСТРОЙКИ ---
APP_TITLE = "WalletSafe"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. ПЕРЕВОДЫ ---
TRANSLATIONS = {
    "RU": {
        "sidebar_title": "Настройки поиска",
        "lang_label": "Язык / Language",
        "mode_geo": "📍 Моя геолокация",
        "mode_zip": "📮 Почтовый индекс",
        "zip_label": "Введите индекс (5 цифр):",
        "zip_btn": "🔍 Найти",
        "zip_ok": "📍 Район найден:",
        "zip_err": "❌ Индекс не найден. Проверьте формат (например, 28001).",
        "geo_btn": "Определить координаты",
        "geo_ok": "✅ Локация найдена!",
        "geo_wait": "Разрешите доступ к GPS...",
        "filter_title": "Фильтры",
        "fuel_label": "Топливо",
        "radius_label": "Радиус (км)",
        "results": "Результаты",
        "found": "Найдено:",
        "price": "Цена:",
        "empty": "😔 В этом радиусе пусто.",
        "addr": "Адрес:",
        "btn": "📍 Маршрут"
    },
    "EN": {
        "sidebar_title": "Search Settings",
        "lang_label": "Language",
        "mode_geo": "📍 My Location",
        "mode_zip": "📮 Postal Code",
        "zip_label": "Enter Zip (5 digits):",
        "zip_btn": "🔍 Search",
        "zip_ok": "📍 Area found:",
        "zip_err": "❌ Zip not found. Check format (e.g. 28001).",
        "geo_btn": "Get Coordinates",
        "geo_ok": "✅ Location detected!",
        "geo_wait": "Allow GPS access...",
        "filter_title": "Filters",
        "fuel_label": "Fuel",
        "radius_label": "Radius (km)",
        "results": "Results",
        "found": "Found:",
        "price": "Price:",
        "empty": "😔 No stations here.",
        "addr": "Address:",
        "btn": "📍 Route"
    },
    "ES": {
        "sidebar_title": "Configuración",
        "lang_label": "Idioma",
        "mode_geo": "📍 Mi ubicación",
        "mode_zip": "📮 Código Postal",
        "zip_label": "Introduce CP (5 dígitos):",
        "zip_btn": "🔍 Buscar",
        "zip_ok": "📍 Zona encontrada:",
        "zip_err": "❌ CP no encontrado (ej. 28001).",
        "geo_btn": "Obtener coordenadas",
        "geo_ok": "✅ Ubicación detectada!",
        "geo_wait": "Permite acceso al GPS...",
        "filter_title": "Filtros",
        "fuel_label": "Combustible",
        "radius_label": "Radio (km)",
        "results": "Resultados",
        "found": "Encontradas:",
        "price": "Precio:",
        "empty": "😔 No hay gasolineras.",
        "addr": "Dirección:",
        "btn": "📍 Ruta"
    }
}

# --- 3. ФУНКЦИИ ---
@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, dtype=str)
        if df.empty: return None
        
        # Переименование
        rename_map = {
            'Lat (Широта)': 'latitude', 'Long (Долгота)': 'longitude',
            'Название заправки': 'Name', 'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel', 'Адрес': 'Address', 'Рабочее время': 'Hours'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        # Очистка чисел
        for col in ['Gasolina 95', 'Diesel']:
            if col in df.columns:
                df[col] = df[col].str.replace('€', '', regex=False)\
                                 .str.replace(' ', '', regex=False)\
                                 .str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude'])
    except:
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2-lon1)/2)**2
    return R * (2 * np.arcsin(np.sqrt(a)))

def get_coords_from_zip(zip_code):
    # ОЧЕНЬ НАДЕЖНЫЙ ПОИСК
    zip_clean = str(zip_code).strip()
    
    # 1. База данных (pgeocode)
    try:
        nomi = pgeocode.Nominatim('es')
        res = nomi.query_postal_code(zip_clean)
        if not np.isnan(res.latitude) and not np.isnan(res.longitude):
            return res.latitude, res.longitude
    except Exception as e:
        print(f"DB Error: {e}") # Лог для отладки

    # 2. Онлайн поиск (Nominatim) с большим таймаутом
    try:
        geolocator = Nominatim(user_agent="walletsafe_app_v_final_fix", timeout=10)
        loc = geolocator.geocode(f"{zip_clean}, Spain")
        if loc: return loc.latitude, loc.longitude
        
        # Попытка 3: Просто цифры
        loc = geolocator.geocode(zip_clean, country_codes="es")
        if loc: return loc.latitude, loc.longitude
    except Exception as e:
        print(f"Online Error: {e}")
        
    return None

# --- 4. ИНТЕРФЕЙС ---
st.set_page_config(page_title="WalletSafe", page_icon="⛽", layout="wide")

# СТИЛЬ (Dark Minimal)
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e0e0e0; }
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: #1e1e1e; border: 1px solid #333; padding: 20px; border-radius: 12px;
    }
    h1, h2, h3, p, span, label { color: #fff !important; }
    button { background-color: #333 !important; color: white !important; border: 1px solid #555 !important; }
    input { color: black !important; }
    </style>
""", unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = "RU"
if 'u_lat' not in st.session_state: st.session_state.u_lat = None
if 'u_lon' not in st.session_state: st.session_state.u_lon = None

with st.sidebar:
    lang = st.selectbox("🌐 Language", ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"], 
                        index=0 if st.session_state.lang=="RU" else (1 if st.session_state.lang=="ES" else 2))
    
    if "Русский" in lang: st.session_state.lang = "RU"
    elif "Español" in lang: st.session_state.lang = "ES"
    else: st.session_state.lang = "EN"
    
    L = TRANSLATIONS[st.session_state.lang]
    
    st.header(L["sidebar_title"])
    mode = st.radio("Mode", [L["mode_geo"], L["mode_zip"]], label_visibility="collapsed")
    
    if mode == L["mode_geo"]:
        loc = get_geolocation()
        if loc:
            st.session_state.u_lat = loc['coords']['latitude']
            st.session_state.u_lon = loc['coords']['longitude']
            st.success(L["geo_ok"])
        else:
            st.info(L["geo_wait"])
            if st.button(L["geo_btn"]): st.rerun()
            
    else:
        with st.form("zip"):
            code = st.text_input(L["zip_label"])
            if st.form_submit_button(L["zip_btn"]):
                coords = get_coords_from_zip(code)
                if coords:
                    st.session_state.u_lat, st.session_state.u_lon = coords
                    st.success(f"{L['zip_ok']} {code}")
                else:
                    st.error(L["zip_err"])

    st.divider()
    st.subheader(L["filter_title"])
    fuel = st.radio(L["fuel_label"], ["Gasolina 95", "Diesel"])
    rad = st.number_input(L["radius_label"], 0.1, 100.0, 10.0, 0.5)

st.title("⛽ WalletSafe")
df = load_data()

if df is not None and st.session_state.u_lat:
    # РАСЧЕТЫ
    df['dist'] = calculate_distance(st.session_state.u_lat, st.session_state.u_lon, 
                                  df['latitude'].values, df['longitude'].values)
    
    res = df[(df['dist'] <= rad) & (df[fuel] > 0)].copy().sort_values(by=fuel)
    
    st.subheader(L["results"])
    st.caption(f"{L['found']} {len(res)}")
    
    if len(res) == 0:
        st.warning(L["empty"])
    else:
        # КАРТА СНИЗУ, СПИСОК СВЕРХУ
        for _, row in res.head(10).iterrows():
            link = f"https://www.google.com/maps/dir/?api=1&destination={row['latitude']},{row['longitude']}"
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"**{row['Name']}**")
                    st.caption(f"{row['Address']}")
                with c2:
                    st.metric(L["price"], f"{row[fuel]:.3f} €")
                with c3:
                    st.markdown(f"📏 {row['dist']:.1f} km")
                    st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none"><div style="background:#ff4b4b;color:white;padding:5px;border-radius:5px;text-align:center">{L["btn"]}</div></a>', unsafe_allow_html=True)
        
        st.map(res[['latitude', 'longitude']])

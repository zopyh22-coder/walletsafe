import streamlit as st
import pandas as pd
import numpy as np
import pgeocode
from geopy.geocoders import ArcGIS
from streamlit_js_eval import get_geolocation

# --- 1. КОНФИГУРАЦИЯ ---
APP_TITLE = "WalletSafe"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. ЛОКАЛИЗАЦИЯ ---
TRANSLATIONS = {
    "RU": {
        "sidebar_title": "Настройки поиска",
        "lang_label": "Язык / Language",
        "mode_geo": "📍 Моя геолокация",
        "mode_zip": "📮 Почтовый индекс",
        "zip_label": "Введите индекс (например, 08001):",
        "zip_btn": "🔍 Найти",
        "zip_ok": "📍 Район найден: ",
        "zip_err": "❌ Индекс не найден. Попробуйте другой.",
        "geo_btn": "Получить координаты",
        "geo_ok": "✅ Локация найдена!",
        "geo_wait": "Разрешите доступ к GPS...",
        "filter_title": "Фильтры",
        "fuel_label": "Вид топлива",
        "radius_label": "Радиус (км)",
        "radius_help": "Введите 0.5 для 500 метров",
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
        "zip_label": "Enter Zip (e.g. 08001):",
        "zip_btn": "🔍 Search",
        "zip_ok": "📍 Area found:",
        "zip_err": "❌ Zip not found.",
        "geo_btn": "Get Coordinates",
        "geo_ok": "✅ Location detected!",
        "geo_wait": "Allow GPS access...",
        "filter_title": "Filters",
        "fuel_label": "Fuel",
        "radius_label": "Radius (km)",
        "radius_help": "Enter 0.5 for 500 meters",
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
        "zip_label": "Introduce CP (ej. 08001):",
        "zip_btn": "🔍 Buscar",
        "zip_ok": "📍 Zona encontrada:",
        "zip_err": "❌ CP no encontrado.",
        "geo_btn": "Obtener coordenadas",
        "geo_ok": "✅ Ubicación detectada!",
        "geo_wait": "Permite acceso al GPS...",
        "filter_title": "Filtros",
        "fuel_label": "Combustible",
        "radius_label": "Radio (km)",
        "radius_help": "Introduce 0.5 para 500 metros",
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
        
        rename_map = {
            'Lat (Широта)': 'latitude', 'Long (Долгота)': 'longitude',
            'Название заправки': 'Name', 'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel', 'Адрес': 'Address', 'Рабочее время': 'Hours'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
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
    # 1. НОРМАЛИЗАЦИЯ: Убираем пробелы, делаем строку
    z = str(zip_code).strip()
    
    # 2. ФОРМАТИРОВАНИЕ: В Испании индексы всегда 5 знаков. 
    # Если ввели "8001", делаем "08001". Это КРИТИЧЕСКИ важно для pgeocode.
    z = z.zfill(5) 
    
    # 3. ПОИСК В БАЗЕ (pgeocode - оффлайн)
    try:
        nomi = pgeocode.Nominatim('es')
        res = nomi.query_postal_code(z)
        
        # Если база вернула координаты (не NaN)
        if not np.isnan(res.latitude) and not np.isnan(res.longitude):
            return res.latitude, res.longitude
    except:
        pass

    # 4. РЕЗЕРВ (ArcGIS - онлайн, он надежнее Nominatim)
    try:
        geolocator = ArcGIS()
        # Пробуем формат "08001, Spain"
        loc = geolocator.geocode(f"{z}, Spain")
        if loc: return loc.latitude, loc.longitude
    except:
        pass
        
    return None

# --- 4. ИНТЕРФЕЙС ---
st.set_page_config(page_title="WalletSafe", page_icon="⛽", layout="wide")

# СТИЛЬ (Чистый темный фон)
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
    
    # Выбор режима (Без городов, только Гео и Индекс)
    mode = st.radio("Mode", [L["mode_geo"], L["mode_zip"]], label_visibility="collapsed")
    
    if mode == L["mode_geo"]:
        st.write(L["geo_wait"])
        loc = get_geolocation()
        if loc:
            st.session_state.u_lat = loc['coords']['latitude']
            st.session_state.u_lon = loc['coords']['longitude']
            st.success(L["geo_ok"])
        else:
            if st.button(L["geo_btn"]): st.rerun()
            
    else:
        # Поиск по индексу
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
    # Радиус от 0.1 км до 100 км
    rad = st.number_input(L["radius_label"], 0.1, 100.0, 10.0, 0.5, help=L["radius_help"])

st.title("⛽ WalletSafe")
df = load_data()

if df is not None and st.session_state.u_lat:
    # Расчеты
    df['dist'] = calculate_distance(st.session_state.u_lat, st.session_state.u_lon, 
                                  df['latitude'].values, df['longitude'].values)
    
    res = df[(df['dist'] <= rad) & (df[fuel] > 0)].copy().sort_values(by=fuel)
    
    st.subheader(L["results"])
    st.caption(f"{L['found']} {len(res)}")
    
    if len(res) == 0:
        st.warning(L["empty"])
    else:
        # СПИСОК (Сверху)
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
                    st.markdown(f'<a href="{link}" target="_blank" style="text-decoration:none"><div style="background:#ff4b4b;color:white;padding:8px;border-radius:5px;text-align:center;font-weight:bold">{L["btn"]} ➜</div></a>', unsafe_allow_html=True)
        
        # КАРТА (Снизу)
        st.map(res[['latitude', 'longitude']])
else:
    if not st.session_state.u_lat:
        st.info(L["start_info"])

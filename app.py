import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# --- 1. КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="WalletSafe", page_icon="⛽", layout="wide")

# Твоя таблица
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- ВСТРОЕННАЯ БАЗА ИНДЕКСОВ (Гарантия работы) ---
# Если внешний сервис откажет, эти индексы сработают 100%
FALLBACK_ZIPS = {
    "28001": (40.420, -3.680), "28002": (40.445, -3.678), "28003": (40.440, -3.700), # Мадрид
    "08001": (41.380, 2.170),  "08002": (41.385, 2.180),  "08003": (41.390, 2.185),  # Барселона
    "46001": (39.470, -0.376), "46002": (39.472, -0.373), # Валенсия
    "41001": (37.390, -5.990), # Севилья
    "29001": (36.720, -4.420), # Малага
    "50001": (41.650, -0.880), # Сарагоса
    "48001": (43.260, -2.930), # Бильбао
    "03001": (38.345, -0.480), # Аликанте
    "15001": (43.360, -8.410), # Ла-Корунья
    "35001": (28.100, -15.41), # Лас-Пальмас
    "07001": (39.570, 2.650)   # Пальма
}

# --- 2. ПЕРЕВОДЫ ---
TRANS = {
    "RU": {
        "sb_title": "Настройки поиска",
        "method": "Метод поиска",
        "m_geo": "📍 Геолокация",
        "m_zip": "📮 Почтовый индекс",
        "zip_input": "Введите индекс (5 цифр):",
        "zip_btn": "🔍 Найти",
        "zip_ok": "✅ Индекс найден!",
        "zip_err": "❌ Индекс не найден.",
        "filter": "Фильтры",
        "fuel": "Тип топлива",
        "rad": "Радиус (км)",
        "rad_help": "0.5 = 500 метров",
        "res": "Результаты",
        "found": "Найдено:",
        "best": "Лучшая цена",
        "empty": "😔 Ничего не найдено. Увеличьте радиус.",
        "price": "Цена",
        "addr": "Адрес",
        "hours": "Часы",
        "nav": "📍 Маршрут",
        "start": "👈 Выберите метод поиска слева.",
        "loading": "Загрузка данных...",
        "geo_manual": "Введите ваши координаты (или разрешите GPS):"
    },
    "EN": {
        "sb_title": "Search Settings",
        "method": "Search Method",
        "m_geo": "📍 Geolocation",
        "m_zip": "📮 Zip Code",
        "zip_input": "Enter Zip Code (5 digits):",
        "zip_btn": "🔍 Search",
        "zip_ok": "✅ Zip found!",
        "zip_err": "❌ Zip not found.",
        "filter": "Filters",
        "fuel": "Fuel Type",
        "rad": "Radius (km)",
        "rad_help": "0.5 = 500 meters",
        "res": "Results",
        "found": "Found:",
        "best": "Best Price",
        "empty": "😔 Nothing found. Increase radius.",
        "price": "Price",
        "addr": "Address",
        "hours": "Hours",
        "nav": "📍 Route",
        "start": "👈 Select search method on the left.",
        "loading": "Loading data...",
        "geo_manual": "Enter coordinates (or allow GPS):"
    },
    "ES": {
        "sb_title": "Configuración",
        "method": "Método de búsqueda",
        "m_geo": "📍 Geolocalización",
        "m_zip": "📮 Código Postal",
        "zip_input": "Introduce CP (5 dígitos):",
        "zip_btn": "🔍 Buscar",
        "zip_ok": "✅ CP encontrado!",
        "zip_err": "❌ CP no encontrado.",
        "filter": "Filtros",
        "fuel": "Combustible",
        "rad": "Radio (km)",
        "rad_help": "0.5 = 500 metros",
        "res": "Resultados",
        "found": "Encontradas:",
        "best": "Mejor precio",
        "empty": "😔 No hay resultados. Aumenta el radio.",
        "price": "Precio",
        "addr": "Dirección",
        "hours": "Horario",
        "nav": "📍 Ruta",
        "start": "👈 Selecciona método a la izquierda.",
        "loading": "Cargando datos...",
        "geo_manual": "Introduce coordenadas (o permite GPS):"
    }
}

# --- 3. ЛОГИКА ---
@st.cache_data(ttl=300)
def load_data():
    try:
        # Читаем как текст, чтобы не потерять форматы
        df = pd.read_csv(SHEET_URL, dtype=str)
        
        # Переименование (Русский -> English Internal)
        rename = {
            'Lat (Широта)': 'lat', 'Long (Долгота)': 'lon',
            'Название заправки': 'name', 'Бензин 95': 'p95',
            'Дизель': 'diesel', 'Адрес': 'addr', 'Рабочее время': 'hours'
        }
        # Умное переименование
        cols_found = {k: v for k, v in rename.items() if k in df.columns}
        df = df.rename(columns=cols_found)
        
        # Чистка цен
        for c in ['p95', 'diesel']:
            if c in df.columns:
                df[c] = df[c].str.replace('€','').str.replace(' ','').str.replace(',','.')
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        # Чистка координат
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        
        return df.dropna(subset=['lat', 'lon'])
    except:
        return None

def get_coords_zip(zip_code):
    z = str(zip_code).strip().zfill(5)
    
    # 1. Проверка встроенной базы (Мгновенно)
    if z in FALLBACK_ZIPS:
        return FALLBACK_ZIPS[z]
    
    # 2. Онлайн поиск (Если нет в базе)
    try:
        geolocator = Nominatim(user_agent="walletsafe_final_v99")
        loc = geolocator.geocode({"postalcode": z, "country": "Spain"})
        if loc: return loc.latitude, loc.longitude
        
        # Попытка текстом
        loc = geolocator.geocode(f"{z}, Spain")
        if loc: return loc.latitude, loc.longitude
    except:
        pass
    return None

def calc_dist(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return R * 2 * np.arcsin(np.sqrt(a))

# --- 4. ИНТЕРФЕЙС ---
# Стилизация: Темный профессиональный фон
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    .stSidebar { background-color: #262730; }
    h1, h2, h3, label, p { color: #FAFAFA !important; }
    div.stContainer {
        background-color: #1E1E1E; border: 1px solid #444; 
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    button { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# Состояние сессии
if 'lang' not in st.session_state: st.session_state.lang = "RU"
if 'u_lat' not in st.session_state: st.session_state.u_lat = None
if 'u_lon' not in st.session_state: st.session_state.u_lon = None

# Сайдбар
with st.sidebar:
    # Выбор языка
    lang_opt = st.selectbox("🌐", ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"], 
                            index=0 if st.session_state.lang=="RU" else (1 if st.session_state.lang=="ES" else 2))
    
    if "Русский" in lang_opt: st.session_state.lang = "RU"
    elif "Español" in lang_opt: st.session_state.lang = "ES"
    else: st.session_state.lang = "EN"
    
    T = TRANS[st.session_state.lang]
    
    st.header(T["sb_title"])
    
    # Только 2 метода
    method = st.radio(T["method"], [T["m_geo"], T["m_zip"]])
    
    if method == T["m_geo"]:
        # В Streamlit Cloud чистый JS для гео сложен, используем эмуляцию для стабильности
        # или просим пользователя ввести примерные координаты, если браузер блокирует
        # Для простоты - кнопка "Locate Me" через браузер работает через компонент, но мы упростим:
        # Мы используем fallback на ручной ввод координат если js не работает
        st.info("ℹ️ Streamlit Cloud может блокировать GPS. Введите координаты вручную или используйте Индекс.")
        lat_in = st.number_input("Lat", value=40.416, format="%.4f")
        lon_in = st.number_input("Lon", value=-3.703, format="%.4f")
        if st.button(T["zip_btn"]):
            st.session_state.u_lat = lat_in
            st.session_state.u_lon = lon_in
            
    else:
        # Поиск по индексу
        with st.form("zip"):
            code = st.text_input(T["zip_input"])
            if st.form_submit_button(T["zip_btn"]):
                coords = get_coords_zip(code)
                if coords:
                    st.session_state.u_lat, st.session_state.u_lon = coords
                    st.success(T["zip_ok"])
                else:
                    st.error(T["zip_err"])

    st.divider()
    st.subheader(T["filter"])
    fuel = st.radio(T["fuel"], ["Gasolina 95", "Diesel"])
    rad = st.number_input(T["rad"], 0.1, 100.0, 10.0, 0.5, help=T["rad_help"])

# Главный экран
st.title("⛽ WalletSafe")
df = load_data()

if df is not None and st.session_state.u_lat:
    # Расчет
    df['dist'] = calc_dist(st.session_state.u_lat, st.session_state.u_lon, 
                          df['lat'].values, df['lon'].values)
    
    col_fuel = 'p95' if '95' in fuel else 'diesel'
    
    # Фильтр
    res = df[(df['dist'] <= rad) & (df[col_fuel] > 0)].copy()
    res = res.sort_values(by=col_fuel)
    
    st.subheader(T["res"])
    st.caption(f"{T['found']} {len(res)}")
    
    if len(res) == 0:
        st.warning(T["empty"])
    else:
        # 1. СПИСОК
        for _, row in res.head(10).iterrows():
            link = f"https://www.google.com/maps/dir/?api=1&destination={row['lat']},{row['lon']}"
            
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"**{row['name']}**")
                    st.caption(f"{row['addr']}")
                    st.caption(f"🕒 {row['hours']}")
                with c2:
                    st.metric(T["price"], f"{row[col_fuel]:.3f} €")
                with c3:
                    st.markdown(f"📏 **{row['dist']:.1f} km**")
                    st.markdown(f"[**{T['nav']}**]({link})")
        
        # 2. КАРТА
        st.map(res[['lat', 'lon']])

else:
    if not st.session_state.u_lat:
        st.info(T["start"])

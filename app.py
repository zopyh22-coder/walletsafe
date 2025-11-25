import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

# --- 1. НАСТРОЙКИ И ЯЗЫКИ ---
APP_TITLE = "WalletSafe"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# Словарь переводов
TRANSLATIONS = {
    "RU": {
        "title_sub": "Самое дешевое топливо рядом с тобой.",
        "sidebar_title": "Настройки",
        "lang_select": "Язык / Idioma / Language",
        "search_mode": "Способ поиска",
        "mode_geo": "📍 Моя геолокация",
        "mode_city": "🏙 Выбрать город",
        "mode_zip": "📮 Почтовый индекс",
        "city_select": "Выберите город:",
        "zip_input": "Введите индекс (например, 28001):",
        "zip_error": "❌ Индекс не найден. Проверьте формат.",
        "zip_found": "📍 Район найден: ",
        "geo_wait": "Разрешите доступ к геопозиции...",
        "geo_success": "✅ Геолокация получена!",
        "geo_error": "⚠️ Не удалось получить координаты. Проверьте настройки браузера.",
        "filters": "Фильтры",
        "fuel_type": "Топливо",
        "radius": "Радиус поиска (км)",
        "results_found": "Найдено заправок:",
        "best_price": "Лучшая цена",
        "empty_area": "😔 В этом радиусе пусто. Увеличьте радиус поиска!",
        "top_list": "Топ заправок:",
        "address": "Адрес:",
        "hours": "Время работы:",
        "btn_route": "📍 Маршрут",
        "start_prompt": "👈 Выберите способ поиска слева.",
        "loading_err": "Ошибка загрузки данных."
    },
    "ES": {
        "title_sub": "El combustible más barato cerca de ti.",
        "sidebar_title": "Configuración",
        "lang_select": "Idioma",
        "search_mode": "Modo de búsqueda",
        "mode_geo": "📍 Mi ubicación",
        "mode_city": "🏙 Elegir ciudad",
        "mode_zip": "📮 Código Postal",
        "city_select": "Elige ciudad:",
        "zip_input": "Introduce CP (ej. 28001):",
        "zip_error": "❌ Código postal no encontrado.",
        "zip_found": "📍 Zona encontrada: ",
        "geo_wait": "Permita el acceso a la ubicación...",
        "geo_success": "✅ Ubicación detectada!",
        "geo_error": "⚠️ No se pudo obtener la ubicación.",
        "filters": "Filtros",
        "fuel_type": "Combustible",
        "radius": "Radio de búsqueda (km)",
        "results_found": "Gasolineras encontradas:",
        "best_price": "Mejor precio",
        "empty_area": "😔 No hay gasolineras aquí. ¡Aumenta el radio!",
        "top_list": "Mejores opciones:",
        "address": "Dirección:",
        "hours": "Horario:",
        "btn_route": "📍 Ir",
        "start_prompt": "👈 Elige un modo de búsqueda a la izquierda.",
        "loading_err": "Error al cargar datos."
    },
    "EN": {
        "title_sub": "Cheapest fuel near you.",
        "sidebar_title": "Settings",
        "lang_select": "Language",
        "search_mode": "Search Mode",
        "mode_geo": "📍 My Location",
        "mode_city": "🏙 Select City",
        "mode_zip": "📮 Zip Code",
        "city_select": "Select city:",
        "zip_input": "Enter Zip Code (e.g. 28001):",
        "zip_error": "❌ Zip code not found.",
        "zip_found": "📍 Area found: ",
        "geo_wait": "Allow location access...",
        "geo_success": "✅ Location detected!",
        "geo_error": "⚠️ Could not get location.",
        "filters": "Filters",
        "fuel_type": "Fuel Type",
        "radius": "Search Radius (km)",
        "results_found": "Stations found:",
        "best_price": "Best Price",
        "empty_area": "😔 No stations here. Increase the radius!",
        "top_list": "Top Stations:",
        "address": "Address:",
        "hours": "Hours:",
        "btn_route": "📍 Route",
        "start_prompt": "👈 Select search mode on the left.",
        "loading_err": "Error loading data."
    }
}

CITIES = {
    "Madrid": {"lat": 40.4168, "lon": -3.7038},
    "Barcelona": {"lat": 41.3851, "lon": 2.1734},
    "Valencia": {"lat": 39.4699, "lon": -0.3763},
    "Sevilla": {"lat": 37.3891, "lon": -5.9845},
    "Zaragoza": {"lat": 41.6488, "lon": -0.8891},
    "Málaga": {"lat": 36.7213, "lon": -4.4214},
    "Murcia": {"lat": 37.9922, "lon": -1.1307},
    "Palma": {"lat": 39.5696, "lon": 2.6502},
    "Bilbao": {"lat": 43.2630, "lon": -2.9350},
    "Alicante": {"lat": 38.3452, "lon": -0.4810}
}

# --- 2. ФУНКЦИИ ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        if df.empty: return None

        # Переименование (Внутренние имена остаются английскими для логики)
        df = df.rename(columns={
            'Lat (Широта)': 'latitude', 
            'Long (Долгота)': 'longitude',
            'Название заправки': 'Name',
            'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel',
            'Адрес': 'Address',
            'Рабочее время': 'Hours'
        })
        
        # Очистка
        for col in ['Gasolina 95', 'Diesel']:
            df[col] = df[col].astype(str).str.replace('€', '').str.replace(' ', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except:
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
        * np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def get_location_from_zip(zip_code):
    try:
        # Улучшенный поиск: указываем страну явно
        geolocator = Nominatim(user_agent="walletsafe_spain_explorer")
        # Сначала пробуем строгий поиск по Испании
        location = geolocator.geocode({"postalcode": zip_code, "country": "Spain"})
        # Если не нашли, пробуем просто текст
        if not location:
            location = geolocator.geocode(f"{zip_code}, Spain")
            
        if location:
            return location.latitude, location.longitude
        return None
    except:
        return None

# --- 3. ИНТЕРФЕЙС ---
st.set_page_config(page_title=APP_TITLE, page_icon="⛽", layout="wide")

# Выбор языка (В сайдбаре сверху)
with st.sidebar:
    # Используем session_state чтобы помнить выбор
    if 'lang' not in st.session_state:
        st.session_state.lang = "RU"
        
    lang_choice = st.selectbox(
        "🌐 Language / Язык / Idioma",
        ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"],
        index=0 if st.session_state.lang == "RU" else (1 if st.session_state.lang == "ES" else 2)
    )
    
    if "Русский" in lang_choice: st.session_state.lang = "RU"
    elif "Español" in lang_choice: st.session_state.lang = "ES"
    else: st.session_state.lang = "EN"

    L = TRANSLATIONS[st.session_state.lang] # Текущий словарь

st.title(f"⛽ {APP_TITLE}")
st.write(L["title_sub"])

df = load_data()

if df is not None:
    # --- БОКОВАЯ ПАНЕЛЬ ---
    with st.sidebar:
        st.header(L["sidebar_title"])
        
        # Режимы поиска
        search_options = [L["mode_geo"], L["mode_city"], L["mode_zip"]]
        search_mode = st.radio(L["search_mode"], search_options)
        
        my_lat, my_lon = None, None
        
        # ЛОГИКА 1: Геолокация
        if search_mode == L["mode_geo"]:
            # Автоматически запрашиваем локацию
            loc = get_geolocation()
            
            if loc:
                my_lat = loc['coords']['latitude']
                my_lon = loc['coords']['longitude']
                st.success(L["geo_success"])
            else:
                st.info(L["geo_wait"])

        # ЛОГИКА 2: Город
        elif search_mode == L["mode_city"]:
            selected_city = st.selectbox(L["city_select"], list(CITIES.keys()))
            my_lat = CITIES[selected_city]["lat"]
            my_lon = CITIES[selected_city]["lon"]
            
        # ЛОГИКА 3: Zip (Индекс)
        else:
            zip_code = st.text_input(L["zip_input"])
            if zip_code:
                coords = get_location_from_zip(zip_code)
                if coords:
                    my_lat, my_lon = coords
                    st.success(f"{L['zip_found']} {zip_code}")
                else:
                    st.error(L["zip_error"])
        
        st.divider()
        st.subheader(L["filters"])
        fuel_type = st.radio(L["fuel_type"], ["Gasolina 95", "Diesel"])
        radius = st.slider(L["radius"], 1, 50, 10)

    # --- РЕЗУЛЬТАТЫ ---
    if my_lat and my_lon:
        df['Distance_km'] = calculate_distance(my_lat, my_lon, df['latitude'], df['longitude'])
        
        filtered_df = df[
            (df['Distance_km'] <= radius) & 
            (df[fuel_type] > 0)
        ].copy()
        
        filtered_df = filtered_df.sort_values(by=fuel_type, ascending=True)
        
        # 1. СПИСОК (СВЕРХУ)
        st.subheader(f"🏆 {L['top_list']}")
        st.caption(f"{L['results_found']} {len(filtered_df)}")
        
        if len(filtered_df) == 0:
            st.warning(L["empty_area"])
        else:
            for i, row in filtered_df.head(5).iterrows():
                price = row[fuel_type]
                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={row['latitude']},{row['longitude']}"
                
                with st.container():
                    c1, c2, c3 = st.columns([3, 2, 2])
                    
                    with c1:
                        st.markdown(f"### {row['Name']}")
                        st.markdown(f"**{L['address']}** {row['Address']}")
                        st.caption(f"⏰ {L['hours']} {row['Hours']}")
                    
                    with c2:
                        st.metric(L["best_price"], f"{price:.3f} €")
                    
                    with c3:
                        st.markdown(f"📏 **{row['Distance_km']:.1f} km**")
                        # Кнопка
                        st.markdown(f"""
                            <a href="{maps_link}" target="_blank">
                                <button style="
                                    background-color: #FF4B4B; 
                                    color: white; 
                                    padding: 8px 16px; 
                                    border: none; 
                                    border-radius: 4px; 
                                    cursor: pointer;
                                    width: 100%;
                                    font-weight: bold;">
                                    {L['btn_route']}
                                </button>
                            </a>
                        """, unsafe_allow_html=True)
                    st.divider()

            # 2. КАРТА (СНИЗУ)
            st.map(filtered_df[['latitude', 'longitude']])
            
    else:
        # Если не выбрана локация
        if search_mode != L["mode_geo"]: 
            st.info(L["start_prompt"])
else:
    st.error("Error loading data / Ошибка загрузки данных")

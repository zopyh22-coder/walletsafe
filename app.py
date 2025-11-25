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
        "zip_search_btn": "🔍 Найти индекс",
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
        "zip_search_btn": "🔍 Buscar CP",
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
        "zip_search_btn": "🔍 Search Zip",
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
@st.cache_data(ttl=60, show_spinner=True)
def load_data():
    try:
        # 1. Читаем все как строки (dtype=str), чтобы избежать ошибок типов при чтении
        df = pd.read_csv(SHEET_URL, dtype=str)
        
        if df.empty:
            return None

        # 2. Переименование колонок
        # Используем словарь для перевода заголовков из Гугл Таблицы (Русский) в код (Английский)
        rename_map = {
            'Lat (Широта)': 'latitude', 
            'Long (Долгота)': 'longitude',
            'Название заправки': 'Name',
            'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel',
            'Адрес': 'Address',
            'Рабочее время': 'Hours'
        }
        # Проверяем, есть ли нужные колонки, прежде чем переименовывать
        available_cols = set(df.columns)
        # Переименовываем только те, что нашли
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in available_cols})
        
        # Проверка критических колонок
        if 'latitude' not in df.columns or 'Gasolina 95' not in df.columns:
            # Если переименование не сработало (заголовки в таблице другие), возвращаем ошибку с списком колонок
            raise ValueError(f"Неверные заголовки в таблице. Найдены: {list(available_cols)}")

        # 3. Очистка и конвертация данных
        for col in ['Gasolina 95', 'Diesel']:
            if col in df.columns:
                # Убираем значок евро и пробелы, меняем запятую на точку (на всякий случай)
                df[col] = df[col].str.replace('€', '', regex=False).str.replace(' ', '', regex=False).str.replace(',', '.', regex=False)
                # Превращаем в числа
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Координаты
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # Удаляем строки без координат
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except Exception as e:
        # Показываем ошибку прямо на экране
        st.error(f"🔥 Ошибка в load_data: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    # Конвертация в радианы
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def get_location_from_zip(zip_code):
    try:
        # Обновленный User Agent для надежности и таймаут
        geolocator = Nominatim(user_agent="walletsafe_v3_secure_locator", timeout=10)
        zip_code = zip_code.strip()
        
        # Попытка 1: Формат "28001 Spain" (Самый надежный для Nominatim)
        location = geolocator.geocode(f"{zip_code} Spain")
        
        # Попытка 2: Строгий поиск по словарю
        if not location:
            location = geolocator.geocode({"postalcode": zip_code, "country": "Spain"})
            
        # Попытка 3: Поиск просто по номеру (иногда работает лучше)
        if not location:
            location = geolocator.geocode(zip_code)
        
        if location:
            return location.latitude, location.longitude
        return None
    except:
        return None

# --- 3. ИНТЕРФЕЙС ---
st.set_page_config(page_title=APP_TITLE, page_icon="⛽", layout="wide")

# Инициализация языка
if 'lang' not in st.session_state:
    st.session_state.lang = "RU"

with st.sidebar:
    lang_choice = st.selectbox(
        "🌐 Language / Язык / Idioma",
        ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"],
        index=0 if st.session_state.lang == "RU" else (1 if st.session_state.lang == "ES" else 2)
    )
    if "Русский" in lang_choice: st.session_state.lang = "RU"
    elif "Español" in lang_choice: st.session_state.lang = "ES"
    else: st.session_state.lang = "EN"

L = TRANSLATIONS[st.session_state.lang]

st.title(f"⛽ {APP_TITLE}")
st.write(L["title_sub"])

df = load_data()

if df is not None:
    with st.sidebar:
        st.header(L["sidebar_title"])
        
        search_options = [L["mode_geo"], L["mode_city"], L["mode_zip"]]
        search_mode = st.radio(L["search_mode"], search_options)
        
        # Инициализируем переменные для координат, чтобы они сохранялись между перезагрузками
        if 'user_lat' not in st.session_state: st.session_state.user_lat = None
        if 'user_lon' not in st.session_state: st.session_state.user_lon = None

        # ЛОГИКА ПОИСКА
        if search_mode == L["mode_geo"]:
            loc = get_geolocation()
            if loc:
                st.session_state.user_lat = loc['coords']['latitude']
                st.session_state.user_lon = loc['coords']['longitude']
                st.success(L["geo_success"])
            else:
                st.info(L["geo_wait"])

        elif search_mode == L["mode_city"]:
            selected_city = st.selectbox(L["city_select"], list(CITIES.keys()))
            st.session_state.user_lat = CITIES[selected_city]["lat"]
            st.session_state.user_lon = CITIES[selected_city]["lon"]
            
        else:
            # Используем форму для почтового индекса, чтобы избежать спам-запросов при вводе
            with st.form(key='zip_form'):
                zip_code_input = st.text_input(L["zip_input"])
                submit_button = st.form_submit_button(label=L["zip_search_btn"])
            
            if submit_button and zip_code_input:
                coords = get_location_from_zip(zip_code_input)
                if coords:
                    st.session_state.user_lat, st.session_state.user_lon = coords
                    st.success(f"{L['zip_found']} {zip_code_input}")
                else:
                    st.error(L["zip_error"])
        
        st.divider()
        st.subheader(L["filters"])
        fuel_type = st.radio(L["fuel_type"], ["Gasolina 95", "Diesel"])
        radius = st.slider(L["radius"], 1, 50, 10)

    # Используем координаты из session_state для отображения
    if st.session_state.user_lat and st.session_state.user_lon:
        # Расчет дистанции
        df['Distance_km'] = calculate_distance(st.session_state.user_lat, st.session_state.user_lon, df['latitude'].values, df['longitude'].values)
        
        # Фильтрация
        mask = (df['Distance_km'] <= radius) & (df[fuel_type] > 0)
        filtered_df = df[mask].copy()
        
        filtered_df = filtered_df.sort_values(by=fuel_type, ascending=True)
        
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
                        st.markdown(f"""<a href="{maps_link}" target="_blank"><button style="background-color: #FF4B4B; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-weight: bold;">{L['btn_route']}</button></a>""", unsafe_allow_html=True)
                    st.divider()

            st.map(filtered_df[['latitude', 'longitude']])
            
    else:
        if search_mode != L["mode_geo"]: 
            st.info(L["start_prompt"])
else:
    # Если df is None, ошибка уже показана в load_data
    pass

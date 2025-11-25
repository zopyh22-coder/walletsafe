import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# --- 1. НАСТРОЙКИ ---
APP_TITLE = "WalletSafe 🇪🇸"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. КООРДИНАТЫ ГОРОДОВ (Резерв) ---
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

# --- 3. ФУНКЦИИ ---
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        if df.empty: return None

        # Переименование
        df = df.rename(columns={
            'Lat (Широта)': 'latitude', 
            'Long (Долгота)': 'longitude',
            'Название заправки': 'Name',
            'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel',
            'Адрес': 'Address',
            'Рабочее время': 'Hours'
        })
        
        # Очистка цен
        for col in ['Gasolina 95', 'Diesel']:
            df[col] = df[col].astype(str).str.replace('€', '').str.replace(' ', '')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Очистка координат
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
        geolocator = Nominatim(user_agent="walletsafe_app_v1")
        location = geolocator.geocode(f"{zip_code}, Spain")
        if location:
            return location.latitude, location.longitude
        return None
    except:
        return None

# --- 4. ИНТЕРФЕЙС ---
st.set_page_config(page_title=APP_TITLE, page_icon="⛽", layout="wide")

st.title(f"⛽ {APP_TITLE}")
st.write("Находи лучшие цены и строй маршрут в один клик.")

df = load_data()

if df is not None:
    # --- БОКОВАЯ ПАНЕЛЬ (ПОИСК) ---
    with st.sidebar:
        st.header("📍 Где искать?")
        
        # Выбор режима: Город или Индекс
        search_mode = st.radio("Способ поиска:", ["Выбрать город", "Почтовый индекс"])
        
        my_lat, my_lon = None, None
        
        if search_mode == "Выбрать город":
            selected_city = st.selectbox("Город:", list(CITIES.keys()))
            my_lat = CITIES[selected_city]["lat"]
            my_lon = CITIES[selected_city]["lon"]
            
        else:
            zip_code = st.text_input("Введите индекс (например, 28001):")
            if zip_code:
                coords = get_location_from_zip(zip_code)
                if coords:
                    my_lat, my_lon = coords
                    st.success(f"Найдено: {zip_code}")
                else:
                    st.error("Индекс не найден. Попробуй другой.")
        
        st.divider()
        fuel_type = st.radio("Топливо:", ["Gasolina 95", "Diesel"])
        radius = st.slider("Радиус (км):", 1, 50, 10)

    # --- ГЛАВНАЯ ЧАСТЬ ---
    if my_lat and my_lon:
        # Расчеты
        df['Distance_km'] = calculate_distance(my_lat, my_lon, df['latitude'], df['longitude'])
        
        # Фильтр и Сортировка
        filtered_df = df[
            (df['Distance_km'] <= radius) & 
            (df[fuel_type] > 0)
        ].copy()
        
        filtered_df = filtered_df.sort_values(by=fuel_type, ascending=True)
        
        # 1. СПИСОК (СВЕРХУ)
        st.subheader(f"🏆 Лучшие цены ({len(filtered_df)} найдено)")
        
        if len(filtered_df) == 0:
            st.warning("В этом радиусе пусто. Увеличь радиус поиска!")
        else:
            # Показываем топ-5 карточек КРУПНО
            for i, row in filtered_df.head(5).iterrows():
                price = row[fuel_type]
                # Ссылка на Google Maps
                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={row['latitude']},{row['longitude']}"
                
                with st.container():
                    # Красивая карточка
                    c1, c2, c3 = st.columns([3, 2, 2])
                    
                    with c1:
                        st.markdown(f"**{row['Name']}**")
                        st.caption(f"{row['Address']}")
                    
                    with c2:
                        st.metric("Цена", f"{price:.3f} €")
                    
                    with c3:
                        st.markdown(f"📏 **{row['Distance_km']:.1f} км**")
                        # Кнопка навигации
                        st.markdown(f"[📍 Маршрут]({maps_link})", unsafe_allow_html=True)
                    
                    st.divider()

            # 2. КАРТА (СНИЗУ)
            st.subheader("🗺 Посмотреть на карте")
            st.map(filtered_df[['latitude', 'longitude']])
            
    else:
        st.info("👈 Выбери город или введи индекс слева, чтобы начать.")
else:
    st.error("Ошибка загрузки данных.")

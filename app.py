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
        st.header("⚙️ Панель управления")
        
        st.info("👇 **Шаг 1:** Выберите место поиска")
        # Выбор режима
        search_mode = st.radio("Как искать?", ["По городу", "По почтовому индексу (Zip)"])
        
        my_lat, my_lon = None, None
        
        if search_mode == "По городу":
            selected_city = st.selectbox("Выберите город:", list(CITIES.keys()))
            my_lat = CITIES[selected_city]["lat"]
            my_lon = CITIES[selected_city]["lon"]
            
        else:
            zip_code = st.text_input("Введите индекс (например, 28001):")
            if zip_code:
                coords = get_location_from_zip(zip_code)
                if coords:
                    my_lat, my_lon = coords
                    st.success(f"📍 Найдено: {zip_code}")
                else:
                    st.error("❌ Индекс не найден. Попробуй другой.")
        
        st.divider()
        st.info("👇 **Шаг 2:** Настройте фильтры")
        
        fuel_type = st.radio("Что ищем?", ["Gasolina 95", "Diesel"])
        radius = st.slider("Максимальное расстояние (км):", 1, 50, 10)

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
        st.subheader(f"🏆 Топ заправок: {fuel_type}")
        st.caption(f"Найдено {len(filtered_df)} заправок в радиусе {radius} км.")
        
        if len(filtered_df) == 0:
            st.warning("😔 В этом радиусе пусто. Попробуйте увеличить расстояние в меню слева!")
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
                        st.markdown(f"### ⛽ {row['Name']}")
                        st.markdown(f"**Адрес:** {row['Address']}")
                        st.caption(f"⏰ Время работы: {row['Hours']}")
                    
                    with c2:
                        st.metric("Цена за литр", f"{price:.3f} €")
                    
                    with c3:
                        st.markdown(f"📏 **{row['Distance_km']:.1f} км** от вас")
                        # Кнопка навигации (выглядит как кнопка)
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
                                    📍 Маршрут
                                </button>
                            </a>
                        """, unsafe_allow_html=True)
                    
                    st.divider()

            # 2. КАРТА (СНИЗУ)
            st.subheader("🗺 Карта расположения")
            st.write("Нажмите на точки, чтобы увидеть детали.")
            st.map(filtered_df[['latitude', 'longitude']])
            
    else:
        st.info("👈 Пожалуйста, выберите город или введите индекс в меню слева, чтобы начать поиск.")
else:
    st.error("Ошибка загрузки данных. Проверьте подключение к Google Таблице.")

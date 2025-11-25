import streamlit as st
import pandas as pd
import numpy as np

# --- 1. НАСТРОЙКИ ---
APP_TITLE = "WalletSafe 🇪🇸"
# ТВОЯ ССЫЛКА НА ГУГЛ ТАБЛИЦУ:
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. КООРДИНАТЫ ГОРОДОВ ---
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
@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # Переименовываем колонки
        df = df.rename(columns={
            'Lat': 'latitude', 
            'Long': 'longitude',
            'Station Name': 'Name',
            'Price 95': 'Gasolina 95',
            'Price Diesel': 'Diesel'
        })
        
        # Превращаем координаты в числа
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except Exception as e:
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    # Формула расстояния
    R = 6371 
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
        * np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# --- 4. ИНТЕРФЕЙС ---
# ИСПРАВЛЕНО: layout="wide" вместо mobile
st.set_page_config(page_title=APP_TITLE, page_icon="⛽", layout="wide")

st.title(f"⛽ {APP_TITLE}")
st.write("Самое дешевое топливо рядом с тобой.")

df = load_data()

if df is not None:
    # --- БОКОВАЯ ПАНЕЛЬ ---
    with st.sidebar:
        st.header("Настройки поиска")
        selected_city = st.selectbox("Где ты сейчас?", list(CITIES.keys()))
        my_lat = CITIES[selected_city]["lat"]
        my_lon = CITIES[selected_city]["lon"]
        
        st.divider()
        fuel_type = st.radio("Топливо:", ["Gasolina 95", "Diesel"])
        radius = st.slider("Радиус (км):", 1, 50, 10)

    # --- РАСЧЕТЫ ---
    df['Distance_km'] = calculate_distance(my_lat, my_lon, df['latitude'], df['longitude'])
    
    # Фильтр
    filtered_df = df[
        (df['Distance_km'] <= radius) & 
        (df[fuel_type] > 0)
    ].copy()
    
    filtered_df = filtered_df.sort_values(by=fuel_type, ascending=True)

    # --- ВЫВОД ---
    col1, col2 = st.columns(2)
    col1.metric("Найдено заправок", len(filtered_df))
    
    if len(filtered_df) > 0:
        best_price = filtered_df.iloc[0][fuel_type]
        col2.metric("Лучшая цена", f"{best_price:.3f} €")
        
        # Карта
        st.map(filtered_df[['latitude', 'longitude']])
        
        # Список
        st.subheader("Топ заправок:")
        for i, row in filtered_df.head(10).iterrows():
            st.markdown(f"""
            **{row['Name']}** 📍 {row['Address']} ({row['Distance_km']:.1f} км)  
            🕒 {row['Hours']}  
            ### {row[fuel_type]:.3f} €
            ---
            """)
    else:
        st.warning("Нет заправок поблизости. Увеличь радиус поиска!")
else:
    st.error("Ошибка загрузки данных. Проверь ссылку в коде.")

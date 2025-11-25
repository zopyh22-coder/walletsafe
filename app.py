import streamlit as st
import pandas as pd
import numpy as np

# --- 1. НАСТРОЙКИ ---
APP_TITLE = "WalletSafe 🇪🇸"
# ТВОЯ ССЫЛКА УЖЕ ВСТАВЛЕНА СЮДА:
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. КООРДИНАТЫ ГОРОДОВ (Чтобы не вводить вручную) ---
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

# --- 3. ФУНКЦИИ (МОЗГИ ПРИЛОЖЕНИЯ) ---
@st.cache_data(ttl=3600) # Обновлять данные раз в час
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        
        # Переименовываем для удобства
        df = df.rename(columns={
            'Lat': 'latitude', 
            'Long': 'longitude',
            'Station Name': 'Name',
            'Price 95': 'Gasolina 95',
            'Price Diesel': 'Diesel'
        })
        
        # Чистим ошибки в координатах
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except Exception as e:
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    # Математика для расчета расстояния
    R = 6371 # Радиус Земли
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2) * np.sin(dlat/2) + np.cos(np.radians(lat1)) \
        * np.cos(np.radians(lat2)) * np.sin(dlon/2) * np.sin(dlon/2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# --- 4. ИНТЕРФЕЙС (ТО, ЧТО ВИДИТ ЧЕЛОВЕК) ---
st.set_page_config(page_title=APP_TITLE, page_icon="⛽", layout="mobile")

# Заголовок
st.title(f"⛽ {APP_TITLE}")
st.write("Самое дешевое топливо рядом с тобой.")

# Загружаем данные
df = load_data()

if df is None:
    st.error("Ошибка! Проверь ссылку CSV в коде (Шаг 1).")
    st.stop()

# --- БОКОВАЯ ПАНЕЛЬ (Настройки) ---
st.sidebar.header("Настройки поиска")

# Выбор города (чтобы не искать координаты)
selected_city = st.sidebar.selectbox("Где ты сейчас?", list(CITIES.keys()))
my_lat = CITIES[selected_city]["lat"]
my_lon = CITIES[selected_city]["lon"]

# Выбор топлива
fuel_type = st.sidebar.radio("Какое топливо?", ["Gasolina 95", "Diesel"])

# ДЖОЙСТИК (Слайдер дистанции)
radius = st.sidebar.slider("Радиус поиска (км)", 1, 50, 10)

# --- РАСЧЕТЫ ---
# Считаем расстояние до каждой заправки
df['Distance_km'] = calculate_distance(my_lat, my_lon, df['latitude'], df['longitude'])

# Фильтруем (берем только те, что в радиусе и с ценой > 0)
filtered_df = df[
    (df['Distance_km'] <= radius) & 
    (df[fuel_type] > 0)
].copy()

# Сортируем: дешевые сверху
filtered_df = filtered_df.sort_values(by=fuel_type, ascending=True)

# --- РЕЗУЛЬТАТЫ ---
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Найдено заправок", value=len(filtered_df))
with col2:
    if len(filtered_df) > 0:
        cheapest_price = filtered_df.iloc[0][fuel_type]
        st.metric(label="Лучшая цена", value=f"{cheapest_price:.3f} €")

# Карта
st.map(filtered_df[['latitude', 'longitude']])

# Список
if len(filtered_df) == 0:
    st.warning("В этом радиусе нет заправок. Увеличь радиус джойстиком!")
else:
    st.subheader(f"Список (Топ-10)")
    for i, row in filtered_df.head(10).iterrows():
        price = row[fuel_type]
        # Карточка заправки
        with st.container():
            st.markdown(f"""
            **{row['Name']}** 📍 {row['Address']}  
            📏 {row['Distance_km']:.1f} км • 🕒 {row['Hours']}  
            ### {price:.3f} €
            """)
            st.divider()

import streamlit as st
import pandas as pd
import numpy as np
import pgeocode
from streamlit_js_eval import get_geolocation

# --- 1. НАСТРОЙКИ ПРИЛОЖЕНИЯ ---
APP_TITLE = "WalletSafe"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv"

# --- 2. СЛОВАРЬ ПЕРЕВОДОВ ---
TRANSLATIONS = {
    "RU": {
        "page_title": "WalletSafe",
        "sub_title": "Найди выгодное топливо рядом.",
        "sidebar_header": "Настройки поиска",
        "lang_label": "Язык / Language",
        "search_mode_label": "Способ поиска",
        "opt_geo": "📍 Моя геолокация",
        "opt_zip": "📮 Почтовый индекс",
        "zip_input_label": "Введите индекс (5 цифр):",
        "zip_btn": "🔍 Найти",
        "zip_success": "📍 Район найден:",
        "zip_fail": "❌ Индекс не найден в базе Испании.",
        "geo_btn_label": "Получить координаты",
        "geo_success": "✅ Локация определена!",
        "geo_fail": "⚠️ Не удалось получить доступ к GPS.",
        "geo_prompt": "Нажмите кнопку или разрешите доступ в браузере.",
        "filter_header": "Фильтры",
        "fuel_label": "Вид топлива",
        "radius_label": "Радиус поиска (км):",
        "radius_help": "Введите 0.5 для 500 метров",
        "results_header": "Результаты",
        "found_count": "Найдено заправок:",
        "best_price_label": "Лучшая цена:",
        "empty_warning": "😔 В этом радиусе нет заправок. Попробуйте увеличить радиус!",
        "start_info": "👈 Выберите способ поиска в меню слева.",
        "loading_error": "Ошибка загрузки данных.",
        "card_address": "Адрес:",
        "card_hours": "Режим работы:",
        "card_btn": "📍 Маршрут",
        "km_away": "км от вас"
    },
    "EN": {
        "page_title": "WalletSafe",
        "sub_title": "Find the best fuel prices nearby.",
        "sidebar_header": "Search Settings",
        "lang_label": "Language",
        "search_mode_label": "Search Mode",
        "opt_geo": "📍 My Location",
        "opt_zip": "📮 Postal Code",
        "zip_input_label": "Enter Zip Code (5 digits):",
        "zip_btn": "🔍 Search",
        "zip_success": "📍 Area found:",
        "zip_fail": "❌ Zip code not found in Spain database.",
        "geo_btn_label": "Get Coordinates",
        "geo_success": "✅ Location detected!",
        "geo_fail": "⚠️ Could not access GPS.",
        "geo_prompt": "Click button or allow access in browser.",
        "filter_header": "Filters",
        "fuel_label": "Fuel Type",
        "radius_label": "Search Radius (km):",
        "radius_help": "Enter 0.5 for 500 meters",
        "results_header": "Results",
        "found_count": "Stations found:",
        "best_price_label": "Best Price:",
        "empty_warning": "😔 No stations in this radius. Try increasing it!",
        "start_info": "👈 Select a search mode on the left.",
        "loading_error": "Error loading data.",
        "card_address": "Address:",
        "card_hours": "Hours:",
        "card_btn": "📍 Route",
        "km_away": "km away"
    },
    "ES": {
        "page_title": "WalletSafe",
        "sub_title": "Encuentra el mejor precio cerca de ti.",
        "sidebar_header": "Configuración",
        "lang_label": "Idioma",
        "search_mode_label": "Modo de búsqueda",
        "opt_geo": "📍 Mi ubicación",
        "opt_zip": "📮 Código Postal",
        "zip_input_label": "Introduce CP (5 dígitos):",
        "zip_btn": "🔍 Buscar",
        "zip_success": "📍 Zona encontrada:",
        "zip_fail": "❌ Código postal no encontrado en España.",
        "geo_btn_label": "Obtener coordenadas",
        "geo_success": "✅ Ubicación detectada!",
        "geo_fail": "⚠️ No se pudo acceder al GPS.",
        "geo_prompt": "Pulsa el botón o permite el acceso.",
        "filter_header": "Filtros",
        "fuel_label": "Tipo de combustible",
        "radius_label": "Radio de búsqueda (km):",
        "radius_help": "Introduce 0.5 para 500 metros",
        "results_header": "Resultados",
        "found_count": "Gasolineras encontradas:",
        "best_price_label": "Mejor precio:",
        "empty_warning": "😔 No hay gasolineras en este radio. ¡Auméntalo!",
        "start_info": "👈 Selecciona un modo de búsqueda a la izquierda.",
        "loading_error": "Error al cargar datos.",
        "card_address": "Dirección:",
        "card_hours": "Horario:",
        "card_btn": "📍 Ruta",
        "km_away": "km de ti"
    }
}

# --- 3. ФУНКЦИИ ---
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, dtype=str)
        if df.empty: return None

        rename_map = {
            'Lat (Широта)': 'latitude', 
            'Long (Долгота)': 'longitude',
            'Название заправки': 'Name',
            'Бензин 95': 'Gasolina 95',
            'Дизель': 'Diesel',
            'Адрес': 'Address',
            'Рабочее время': 'Hours'
        }
        
        cols_to_rename = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=cols_to_rename)
        
        for col in ['Gasolina 95', 'Diesel']:
            if col in df.columns:
                df[col] = df[col].str.replace('€', '', regex=False)\
                                 .str.replace(' ', '', regex=False)\
                                 .str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        df = df.dropna(subset=['latitude', 'longitude'])
        
        return df
    except:
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def get_coords_from_zip(zip_code):
    try:
        nomi = pgeocode.Nominatim('es') 
        location = nomi.query_postal_code(str(zip_code).strip())
        
        if not np.isnan(location.latitude) and not np.isnan(location.longitude):
            return location.latitude, location.longitude
        return None
    except:
        return None

# --- 4. ИНТЕРФЕЙС ---
st.set_page_config(page_title="WalletSafe", page_icon="⛽", layout="wide")

# СТИЛЬНЫЙ ФОН (Градиент + Современный вид)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    h1, h2, h3, p, label, span, div {
        color: #f0f2f6 !important;
    }
    /* Карточки заправок */
    div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    /* Кнопки */
    button {
        border-radius: 8px !important;
    }
    /* Поля ввода */
    input {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'lang' not in st.session_state: st.session_state.lang = "RU"
if 'user_lat' not in st.session_state: st.session_state.user_lat = None
if 'user_lon' not in st.session_state: st.session_state.user_lon = None

with st.sidebar:
    lang_choice = st.selectbox(
        "🌐 Language",
        ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"],
        index=0 if st.session_state.lang == "RU" else (1 if st.session_state.lang == "ES" else 2)
    )
    
    if "Русский" in lang_choice: st.session_state.lang = "RU"
    elif "Español" in lang_choice: st.session_state.lang = "ES"
    else: st.session_state.lang = "EN"
    
    L = TRANSLATIONS[st.session_state.lang]

    st.header(L["sidebar_header"])
    
    # Только два режима: Гео и Индекс
    mode = st.radio(L["search_mode_label"], [L["opt_geo"], L["opt_zip"]])
    
    if mode == L["opt_geo"]:
        st.write(L["geo_prompt"])
        loc = get_geolocation()
        
        if loc:
            st.session_state.user_lat = loc['coords']['latitude']
            st.session_state.user_lon = loc['coords']['longitude']
            st.success(L["geo_success"])
        else:
            if st.button(L["geo_btn_label"]):
                st.info("Check browser permissions.")

    else: # Поиск по Индексу
        with st.form("zip_form"):
            zip_code = st.text_input(L["zip_input_label"])
            submitted = st.form_submit_button(L["zip_btn"])
            
            if submitted and zip_code:
                coords = get_coords_from_zip(zip_code)
                if coords:
                    st.session_state.user_lat, st.session_state.user_lon = coords
                    st.success(f"{L['zip_success']} {zip_code}")
                else:
                    st.error(L["zip_fail"])

    st.divider()
    st.subheader(L["filter_header"])
    fuel_type = st.radio(L["fuel_label"], ["Gasolina 95", "Diesel"])
    
    # Поле ввода для радиуса
    radius = st.number_input(
        L["radius_label"], 
        min_value=0.1, 
        max_value=100.0, 
        value=10.0, 
        step=0.5,
        help=L["radius_help"]
    )

st.title(f"⛽ {L['page_title']}")
st.write(L["sub_title"])

df = load_data()

if df is not None:
    if st.session_state.user_lat and st.session_state.user_lon:
        # Расчет дистанции
        df['Distance_km'] = calculate_distance(
            st.session_state.user_lat, 
            st.session_state.user_lon, 
            df['latitude'].values, 
            df['longitude'].values
        )
        
        mask = (df['Distance_km'] <= radius) & (df[fuel_type] > 0)
        results = df[mask].copy()
        
        results = results.sort_values(by=fuel_type, ascending=True)
        
        st.subheader(L["results_header"])
        st.caption(f"{L['found_count']} {len(results)}")
        
        if len(results) == 0:
            st.warning(L["empty_warning"])
        else:
            # Топ-10
            for _, row in results.head(10).iterrows():
                price = row[fuel_type]
                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={row['latitude']},{row['longitude']}"
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"#### {row['Name']}")
                        st.markdown(f"**{L['card_address']}** {row['Address']}")
                        st.caption(f"{L['card_hours']} {row['Hours']}")
                        
                    with col2:
                        st.metric(L["best_price_label"], f"{price:.3f} €")
                        
                    with col3:
                        dist = f"{row['Distance_km']:.1f} {L['km_away']}"
                        st.info(f"📏 {dist}")
                        st.markdown(f"""
                            <a href="{maps_link}" target="_blank" style="text-decoration: none;">
                                <div style="
                                    background-color: #ff4b4b;
                                    color: white;
                                    padding: 8px;
                                    border-radius: 5px;
                                    text-align: center;
                                    font-weight: bold;
                                    margin-top: 5px;">
                                    {L['card_btn']} ➜
                                </div>
                            </a>
                        """, unsafe_allow_html=True)
                    
            st.map(results[['latitude', 'longitude']])
            
    else:
        st.info(L["start_info"])
else:
    st.error(L["loading_error"])

import streamlit as st
import pandas as pd
import numpy as np
import pgeocode
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation
import pydeck as pdk

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
        "zip_input_label": "Введите индекс (например, 28001):",
        "zip_btn": "🔍 Найти",
        "zip_success": "📍 Район найден:",
        "zip_fail": "❌ Индекс не найден. Проверь формат (5 цифр) или попробуйте другой.",
        "geo_btn_label": "Получить координаты",
        "geo_success": "✅ Локация определена!",
        "geo_fail": "⚠️ Не удалось получить доступ к GPS.",
        "geo_prompt": "Нажмите кнопку ниже и разрешите доступ к геолокации в браузере.",
        "filter_header": "Фильтры",
        "fuel_label": "Вид топлива",
        "radius_label": "Радиус поиска (км):",
        "radius_help": "Можно ввести 0.5 для 500 метров",
        "results_header": "Результаты рядом с вами",
        "found_count": "Найдено заправок:",
        "best_price_label": "Лучшая цена:",
        "empty_warning": "😔 В этом радиусе нет заправок. Увеличьте радиус или проверьте индекс.",
        "start_info": "👈 Слева выберите способ поиска (по геолокации или индексу) и радиус.",
        "loading_error": "Ошибка загрузки данных.",
        "card_address": "Адрес:",
        "card_hours": "Режим работы:",
        "card_btn": "📍 Маршрут",
        "km_away": "км от вас",
        "sort_header": "Сортировка и качество",
        "sort_price_first": "Сначала по цене (дешевле выше)",
        "quality_label": "Минимальное качество (если есть рейтинг в базе)",
        "any_quality": "Любое",
        "availability_label": "Доступность",
        "availability_any": "Любая",
        "availability_24_7": "Только 24/7",
    },
    "EN": {
        "page_title": "WalletSafe",
        "sub_title": "Find the best fuel prices nearby.",
        "sidebar_header": "Search Settings",
        "lang_label": "Language",
        "search_mode_label": "Search Mode",
        "opt_geo": "📍 My Location",
        "opt_zip": "📮 Postal Code",
        "zip_input_label": "Enter Zip Code (e.g. 28001):",
        "zip_btn": "🔍 Search",
        "zip_success": "📍 Area found:",
        "zip_fail": "❌ Zip code not found. Check format (5 digits) or try another.",
        "geo_btn_label": "Get Coordinates",
        "geo_success": "✅ Location detected!",
        "geo_fail": "⚠️ Could not access GPS.",
        "geo_prompt": "Click the button below and allow location access in your browser.",
        "filter_header": "Filters",
        "fuel_label": "Fuel Type",
        "radius_label": "Search Radius (km):",
        "radius_help": "You can type 0.5 for 500 meters",
        "results_header": "Results near you",
        "found_count": "Stations found:",
        "best_price_label": "Best Price:",
        "empty_warning": "😔 No stations in this radius. Try increasing it or check the postcode.",
        "start_info": "👈 Select a search mode (GPS or postal code) and a radius on the left.",
        "loading_error": "Error loading data.",
        "card_address": "Address:",
        "card_hours": "Hours:",
        "card_btn": "📍 Route",
        "km_away": "km away",
        "sort_header": "Sorting & quality",
        "sort_price_first": "Price first (cheapest on top)",
        "quality_label": "Minimum quality (if rating exists)",
        "any_quality": "Any",
        "availability_label": "Availability",
        "availability_any": "Any",
        "availability_24_7": "Only 24/7",
    },
    "ES": {
        "page_title": "WalletSafe",
        "sub_title": "Encuentra el mejor precio cerca de ti.",
        "sidebar_header": "Configuración",
        "lang_label": "Idioma",
        "search_mode_label": "Modo de búsqueda",
        "opt_geo": "📍 Mi ubicación",
        "opt_zip": "📮 Código Postal",
        "zip_input_label": "Introduce CP (ej. 28001):",
        "zip_btn": "🔍 Buscar",
        "zip_success": "📍 Zona encontrada:",
        "zip_fail": "❌ Código postal no encontrado. Revisa el formato (5 dígitos) o prueba otro.",
        "geo_btn_label": "Obtener coordenadas",
        "geo_success": "✅ ¡Ubicación detectada!",
        "geo_fail": "⚠️ No se pudo acceder al GPS.",
        "geo_prompt": "Pulsa el botón abajo y permite el acceso a la ubicación en el navegador.",
        "filter_header": "Filtros",
        "fuel_label": "Tipo de combustible",
        "radius_label": "Radio de búsqueda (km):",
        "radius_help": "Puedes poner 0.5 para 500 metros",
        "results_header": "Resultados cerca de ti",
        "found_count": "Gasolineras encontradas:",
        "best_price_label": "Mejor precio:",
        "empty_warning": "😔 No hay gasolineras en este radio. Aumenta el radio o revisa el código postal.",
        "start_info": "👈 Elige a la izquierda el modo de búsqueda (GPS o código postal) y el radio.",
        "loading_error": "Error al cargar datos.",
        "card_address": "Dirección:",
        "card_hours": "Horario:",
        "card_btn": "📍 Ruta",
        "km_away": "km de ti",
        "sort_header": "Orden y calidad",
        "sort_price_first": "Primero por precio (más barato arriba)",
        "quality_label": "Calidad mínima (si hay rating)",
        "any_quality": "Cualquiera",
        "availability_label": "Disponibilidad",
        "availability_any": "Cualquiera",
        "availability_24_7": "Solo 24/7",
    }
}

# --- 3. ФУНКЦИИ ---
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, dtype=str)
        if df.empty:
            return None

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

        # Цены – в float
        for col in ['Gasolina 95', 'Diesel']:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .str.replace('€', '', regex=False)
                    .str.replace(' ', '', regex=False)
                    .str.replace(',', '.', regex=False)
                )
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        df = df.dropna(subset=['latitude', 'longitude'])

        # Если есть колонка качества – приводим к числу
        if 'Quality' in df.columns:
            df['Quality'] = pd.to_numeric(df['Quality'], errors='coerce')

        return df
    except Exception:
        return None


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # радиус Земли в км
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def get_coords_from_zip(zip_code: str):
    """
    Возвращает (lat, lon) для любого корректного индекса Испании или None.
    1) чистим всё, кроме цифр
    2) проверяем, что длина = 5
    3) сначала pgeocode (офлайн), затем Nominatim (онлайн)
    """
    zip_clean = ''.join(ch for ch in str(zip_code) if ch.isdigit())

    # Испанский индекс – 5 цифр
    if len(zip_clean) != 5:
        return None

    # 1. pgeocode – оффлайн
    try:
        nomi = pgeocode.Nominatim('es')
        location = nomi.query_postal_code(zip_clean)
        # location – Series
        if hasattr(location, "latitude") and pd.notna(location.latitude) and pd.notna(location.longitude):
            return float(location.latitude), float(location.longitude)
    except Exception:
        pass

    # 2. Fallback: Nominatim (онлайн)
    try:
        geolocator = Nominatim(user_agent="walletsafe_app_v1")
        location = geolocator.geocode(f"{zip_clean}, Spain")
        if location:
            return float(location.latitude), float(location.longitude)
    except Exception:
        pass

    return None


# --- 4. ИНТЕРФЕЙС ---
st.set_page_config(page_title="WalletSafe", page_icon="⛽", layout="wide")

# --- 4.1. Кастомный красивый фон и чуть чище UI ---
st.markdown(
    """
    <style>
    /* Основной фон: тёмный градиент */
    .stApp {
        background: radial-gradient(circle at top left, #1f2933 0, #020617 45%, #000000 100%);
        color: #e5e7eb;
    }

    /* Прячем системное меню Streamlit для более "app"-вида */
    #MainMenu, footer {visibility: hidden;}

    /* Заголовок приложения */
    .walletsafe-header {
        padding: 1.5rem 1rem 0.5rem 1rem;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(59,130,246,0.20), rgba(56,189,248,0.10));
        border: 1px solid rgba(148,163,184,0.4);
        box-shadow: 0 18px 45px rgba(15,23,42,0.9);
        margin-bottom: 1.5rem;
    }

    .walletsafe-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .walletsafe-subtitle {
        font-size: 0.98rem;
        opacity: 0.85;
    }

    /* Сайдбар */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #020617 45%, #030712 100%);
        border-right: 1px solid #1f2937;
    }

    /* Заголовки, текст */
    h1, h2, h3, h4, h5, h6, label, p, span {
        color: #f9fafb !important;
    }

    /* Карточки заправок */
    .station-card {
        background: rgba(15,23,42,0.96);
        border-radius: 16px;
        padding: 1.0rem 1.2rem;
        margin-bottom: 0.8rem;
        border: 1px solid rgba(55,65,81,0.9);
        box-shadow: 0 12px 30px rgba(15,23,42,0.85);
    }
    .station-name {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.15rem;
    }

    /* Кнопка маршрута (внутри markdown-ссылки) */
    .route-button {
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: white;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
        margin-top: 0.4rem;
        border: 1px solid rgba(248,250,252,0.25);
        text-decoration: none;
        display: inline-block;
    }
    .route-button:hover {
        filter: brightness(1.1);
    }

    /* Инпуты и кнопки */
    .stTextInput input, .stNumberInput input {
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 8px !important;
        border: 1px solid #374151 !important;
    }

    .stButton>button, .stRadio>div>label {
        border-radius: 999px !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #2563eb, #22c55e) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover {
        filter: brightness(1.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Состояние
if "lang" not in st.session_state:
    st.session_state.lang = "RU"
if "user_lat" not in st.session_state:
    st.session_state.user_lat = None
if "user_lon" not in st.session_state:
    st.session_state.user_lon = None

# --- 4.2. Сайдбар ---
with st.sidebar:
    lang_choice = st.selectbox(
        "🌐 Language",
        ["🇷🇺 Русский", "🇪🇸 Español", "🇬🇧 English"],
        index=0 if st.session_state.lang == "RU" else (1 if st.session_state.lang == "ES" else 2),
    )

    if "Русский" in lang_choice:
        st.session_state.lang = "RU"
    elif "Español" in lang_choice:
        st.session_state.lang = "ES"
    else:
        st.session_state.lang = "EN"

    L = TRANSLATIONS[st.session_state.lang]

    st.header(L["sidebar_header"])

    # ДВА РЕЖИМА: ГЕО и ИНДЕКС
    mode = st.radio(L["search_mode_label"], [L["opt_geo"], L["opt_zip"]])

    if mode == L["opt_geo"]:
        st.write(L["geo_prompt"])
        if st.button(L["geo_btn_label"], use_container_width=True):
            loc = get_geolocation()
            if loc and "coords" in loc:
                st.session_state.user_lat = loc["coords"]["latitude"]
                st.session_state.user_lon = loc["coords"]["longitude"]
                st.success(L["geo_success"])
            else:
                st.warning(L["geo_fail"])
    else:
        # Поиск по индексу
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

    radius = st.number_input(
        L["radius_label"],
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=0.5,
        help=L["radius_help"],
    )

    st.subheader(L["sort_header"])
    st.caption(L["sort_price_first"])

    # Фильтр качества (работает, только если колонка Quality есть)
    quality_min = None
    if st.checkbox(L["quality_label"]):
        quality_min = st.slider("⭐", min_value=1.0, max_value=5.0, value=3.0, step=0.5)

    # Фильтр доступности (на будущее – если добавите колонку Accessibility или 24/7 в Hours)
    availability_choice = st.selectbox(
        L["availability_label"],
        [L["availability_any"], L["availability_24_7"]],
    )

# --- 4.3. Header в основной части ---
L = TRANSLATIONS[st.session_state.lang]

st.markdown(
    f"""
    <div class="walletsafe-header">
        <div class="walletsafe-title">⛽ {L['page_title']}</div>
        <div class="walletsafe-subtitle">{L['sub_title']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

df = load_data()

if df is None:
    st.error(L["loading_error"])
else:
    if st.session_state.user_lat is not None and st.session_state.user_lon is not None:
        # --- 4.4. Расчёт расстояний ---
        df = df.copy()
        df["Distance_km"] = calculate_distance(
            st.session_state.user_lat,
            st.session_state.user_lon,
            df["latitude"].values,
            df["longitude"].values,
        )

        # Базовый фильтр: по радиусу и по тому, чтобы цена была > 0
        mask = (df["Distance_km"] <= radius) & (df[fuel_type].notna())
        results = df[mask].copy()

        # Фильтр качества
        if quality_min is not None and "Quality" in results.columns:
            results = results[results["Quality"] >= quality_min]

        # Фильтр доступности – пример: 24/7 ищем либо по колонке Accessibility, либо по Hours
        if availability_choice != L["availability_any"]:
            if "Accessibility" in results.columns:
                results = results[results["Accessibility"].str.contains("24", case=False, na=False)]
            else:
                if "Hours" in results.columns:
                    results = results[results["Hours"].str.contains("24", case=False, na=False)]

        # Сортировка: сначала по цене, потом по расстоянию, потом по качеству (если есть)
        sort_cols = [fuel_type, "Distance_km"]
        ascending = [True, True]
        if "Quality" in results.columns:
            sort_cols.append("Quality")
            ascending.append(False)  # выше качество – лучше

        results = results.sort_values(by=sort_cols, ascending=ascending)

        # --- 4.5. Вывод результатов ---
        st.subheader(L["results_header"])
        st.caption(f"{L['found_count']} {len(results)}")

        if results.empty:
            st.warning(L["empty_warning"])
        else:
            # Ограничиваем 5–7 опций: возьмём максимум 7
            max_rows = 7
            top_results = results.head(max_rows)

            # Карточки
            for _, row in top_results.iterrows():
                price = row[fuel_type]
                if pd.isna(price):
                    continue

                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={row['latitude']},{row['longitude']}"

                st.markdown('<div class="station-card">', unsafe_allow_html=True)

                col1, col2, col3 = st.columns([3, 1.7, 1.7])

                with col1:
                    st.markdown(
                        f"""
                        <div class="station-name">{row.get('Name', '—')}</div>
                        <div><b>{L['card_address']}</b> {row.get('Address', '—')}</div>
                        <div style="font-size: 0.8rem; opacity: 0.85;">
                            {L['card_hours']} {row.get('Hours', '—')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.metric(L["best_price_label"], f"{price:.3f} €")

                with col3:
                    dist_text = f"{row['Distance_km']:.1f} {L['km_away']}"
                    st.info(f"📏 {dist_text}")

                    st.markdown(
                        f"""
                        <a href="{maps_link}" target="_blank" class="route-button">
                            {L['card_btn']} ➜
                        </a>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

            # --- 4.6. Красивая карта без блока "Найти города" ---
            map_data = top_results[["latitude", "longitude", "Name", "Address", fuel_type]].copy()
            map_data = map_data.rename(
                columns={
                    "latitude": "lat",
                    "longitude": "lon",
                    fuel_type: "price",
                }
            )

            initial_view = pdk.ViewState(
                latitude=float(map_data["lat"].mean()),
                longitude=float(map_data["lon"].mean()),
                zoom=11,
                pitch=0,
            )

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[lon, lat]",
                get_radius=200,
                get_fill_color="[239, 68, 68, 200]",
                pickable=True,
            )

            tooltip = {
                "html": "<b>{Name}</b><br/>{Address}<br/>" + fuel_type + ": {price} €",
                "style": {"backgroundColor": "#0f172a", "color": "white"},
            }

            deck = pdk.Deck(
                initial_view_state=initial_view,
                layers=[layer],
                tooltip=tooltip,
            )

            st.pydeck_chart(deck)

    else:
        st.info(L["start_info"])

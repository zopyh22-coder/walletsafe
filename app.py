# app.py — WalletSafe (полностью рабочий, чистый, белый дизайн)
# Запуск: python3 app.py

from flask import Flask, render_template_string, request, jsonify
import math
import requests

app = Flask(__name__)

# ------------------- ДАННЫЕ ЗАПРАВОК (все цены > 0) -------------------
stations = [
    {"name": "PLENERGY", "city": "Albacete", "gas95": 1.379, "diesel": 1.337, "hours": "24/7", "lat": 39.000861, "lng": -1.849833},
    {"name": "A&A", "city": "Albacete", "gas95": 1.347, "diesel": 1.297, "hours": "09:00–21:30", "lat": 39.006889, "lng": -1.885361},
    {"name": "GMOIL", "city": "Albacete", "gas95": 1.335, "diesel": 1.295, "hours": "24/7", "lat": 39.022139, "lng": -1.882056},
    {"name": "ALCAMPO", "city": "Albacete", "gas95": 1.339, "diesel": 1.330, "hours": "24/7", "lat": 39.009639, "lng": -1.878111},
    {"name": "FAMILY ENERGY", "city": "Albacete", "gas95": 1.359, "diesel": 1.319, "hours": "07:00–23:00", "lat": 38.988972, "lng": -1.847361},
    {"name": "BALLENOIL", "city": "Almansa", "gas95": 1.379, "diesel": 1.349, "hours": "24/7", "lat": 38.871556, "lng": -1.108000},
    {"name": "LA REMEDIADORA", "city": "La Roda", "gas95": 1.329, "diesel": 1.319, "hours": "24/7", "lat": 39.201139, "lng": -2.147750},
    # ← сюда можно добавить ещё тысячи заправок
]

# ------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ -------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},+Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe/1.0'}, timeout=5)
        data = r.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except:
        pass
    return None

# ------------------- HTML + CSS + JS (всё в одном файле) -------------------
HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WalletSafe</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        body,html{margin:0;padding:0;background:#fff;font-family:system-ui,sans-serif;color:#000}
        header{background:#fff;padding:20px 0;text-align:center;border-bottom:1px solid #eee}
        .logo{font-size:28px;font-weight:600}
        .logo svg{width:44px;height:44px;vertical-align:middle;margin-right:10px}
        .container{max-width:1000px;margin:0 auto;padding:20px}
        .controls{background:#fafafa;padding:20px;border-radius:16px;margin-bottom:30px;text-align:center}
        select, input[type=text], button{margin:8px;padding:14px 18px;border-radius:12px;border:1px solid #ddd;font-size:16px}
        button{background:#000;color:#fff;border:none;cursor:pointer}
        button:hover{background:#333}
        .slider{width:80%;max-width:500px;height:8px;border-radius:5px;background:#ddd;outline:none}
        .results .station{background:#fff;padding:20px;border:1px solid #eee;border-radius:16px;margin-bottom:16px;cursor:pointer;transition:0.2s}
        .station:hover{box-shadow:0 6px 30px rgba(0,0,0,0.08)}
        .name{font-size:20px;font-weight:600}
        .price{font-size:28px;font-weight:bold;margin:10px 0}
        .info{font-size:15px;color:#555}
        #map{height:520px;border-radius:20px;margin-top:40px;box-shadow:0 6px 40px rgba(0,0,0,0.1)}
    </style>
</head>
<body>

<header>
    <div class="logo">
        <svg viewBox="0 0 64 64"><rect x="12" y="20" width="40" height="28" rx="6" fill="#000"/><path d="M22 28 L32 34 L42 28" stroke="#fff" stroke-width="4" fill="none"/><circle cx="44" cy="34" r="8" fill="#000"/></svg>
        WalletSafe
    </div>
</header>

<div class="container">
    <div class="controls">
        <select id="fuel">
            <option value="gas95">Бензин 95</option>
            <option value="diesel">Дизель</option>
        </select>
        <input type="text" id="zip" placeholder="Почтовый индекс (например 02001)">
        <button onclick="useGeo()">Моя геолокация</button><br><br>
        <input type="range" class="slider" id="radius" min="5" max="100" value="30" oninput="val.textContent=this.value">
        <span style="font-size:18px"><span id="val">30</span> км</span><br><br>
        <button onclick="search()" style="padding:16px 40px;font-size:18px">Найти самые дешёвые</button>
    </div>

    <div id="results"></div>
    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
let map, userMarker, routeLayer;
let userPos = null;

async function search() {
    const fuel = document.getElementById('fuel').value;
    const zip = document.getElementById('zip').value.trim();
    const radius = parseInt(document.getElementById('radius').value);
    let lat, lng;

    if (zip) {
        const r = await fetch(`/zip/${zip}`);
        const d = await r.json();
        if (d.error) return alert("Неверный индекс");
        lat = d.lat; lng = d.lng;
    } else {
        const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej));
        lat = pos.coords.latitude; lng = pos.coords.longitude;
    }

    userPos = {lat, lng};
    const resp = await fetch(`/search?fuel=${fuel}&lat=${lat}&lng=${lng}&dist=${radius}`);
    const list = await resp.json();

    const results = document.getElementById('results');
    results.innerHTML = list.length === 0 ? "<p style='text-align:center;color:#777;padding:40px'>Ничего не найдено</p>" : "";

    initMap(lat, lng);
    if (userMarker) userMarker.setLatLng([lat, lng]);
    else userMarker = L.circleMarker([lat, lng], {radius:9, color:'#0066ff', fillOpacity:1}).addTo(map).bindPopup("Вы здесь").openPopup();

    list.slice(0,5).forEach(s => {
        const div = document.createElement('div');
        div.className = 'station';
        div.innerHTML = `
            <div class="name">${s.name} • ${s.city}</div>
            <div class="price">${s.price.toFixed(3)} €</div>
            <div class="info">${s.dist.toFixed(1)} км • ${s.hours}</div>
            <button onclick="goGoogle(${s.lat},${s.lng})" style="margin-top:12px">Проложить маршрут в Google Maps</button>
        `;
        div.onclick = () => focusStation(s.lat, s.lng, s.name, s.price);
        results.appendChild(div);
    });
}

function initMap(lat, lng) {
    if (map) map.remove();
    map = L.map('map').setView([lat, lng], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    document.getElementById('map').style.display = 'block';
    routeLayer = L.layerGroup().addTo(map);
}

function focusStation(lat, lng, name, price) {
    map.setView([lat, lng], 15);
    routeLayer.clearLayers();
    L.marker([lat, lng], {icon: L.divIcon({className:'dot', html:'●', iconSize:[24,24]})})
        .addTo(map).bindPopup(`<b>${name}</b><br>${price.toFixed(3)} €`).openPopup();
    if (userPos) L.polyline([[userPos.lat,userPos.lng],[lat,lng]], {color:'#0066ff', weight:5, opacity:0.7}).addTo(routeLayer);
}

function goGoogle(lat, lng) {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=driving`, '_blank');
}

function useGeo() {
    document.getElementById('zip').value = '';
    search();
}
</script>
</body>
</html>
'''

# ------------------- МАРШРУТЫ -------------------
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/zip/<zip_code>')
def zip_route(zip_code):
    coords = geocode_zip(zip_code)
    if coords:
        return jsonify(lat=coords[0], lng=coords[1])
    return jsonify(error=True), 400

@app.route('/search')
def search():
    fuel = request.args.get('fuel')
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    max_dist = float(request.args.get('dist', 50))

    results = []
    for s in stations:
        if s.get(fuel, 0) <= 0: continue
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= max_dist:
            results.append({**s, 'price': s[fuel], 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))   # ← сначала самая низкая цена, потом ближайшие
    return jsonify(results)

# ------------------- ЗАПУСК -------------------
if __name__ == '__main__':
    print("\nWalletSafe запущен! Открой → http://127.0.0.1:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

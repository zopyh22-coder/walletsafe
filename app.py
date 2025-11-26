# app.py — WalletSafe Minimal White Edition
# Run: python3 app.py

from flask import Flask, render_template_string, request, jsonify
import math
import requests

app = Flask(__name__)

# === ALL STATIONS (0.000 prices removed) ===
stations = [
    {"name": "PLENERGY", "city": "Albacete", "gas95": 1.379, "diesel": 1.337, "hours": "24/7", "lat": 39.000861, "lng": -1.849833},
    {"name": "A&A", "city": "Albacete", "gas95": 1.347, "diesel": 1.297, "hours": "09:00–21:30", "lat": 39.006889, "lng": -1.885361},
    {"name": "GMOIL", "city": "Albacete", "gas95": 1.335, "diesel": 1.295, "hours": "24/7", "lat": 39.022139, "lng": -1.882056},
    {"name": "ALCAMPO", "city": "Albacete", "gas95": 1.339, "diesel": 1.330, "hours": "24/7", "lat": 39.009639, "lng": -1.878111},
    {"name": "F-bound ENERGY", "city": "Albacete", "gas95": 1.359, "diesel": 1.319, "hours": "07:00–23:00", "lat": 38.988972, "lng": -1.847361},
    {"name": "BALLENOIL", "city": "Almansa", "gas95": 1.379, "diesel": 1.349, "hours": "24/7", "lat": 38.871556, "lng": -1.108000},
    {"name": "LA REMEDIADORA", "city": "La Roda", "gas95": 1.329, "diesel": 1.319, "hours": "24/7", "lat": 39.201139, "lng": -2.147750},
    # Add more stations here if you want — the more the better!
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    a = math.sin(math.radians(lat2-lat1)/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(math.radians(lon2-lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe'}, timeout=5)
        data = r.json()
        if data: return float(data[0]['lat']), float(data[0]['lon'])
    except: pass
    return None

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>WalletSafe</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        body,html{margin:0;padding:0;background:#fff;font-family:system-ui,sans-serif;color:#000}
        header{padding:20px;text-align:center;font-size:24px;font-weight:300;border-bottom:1px solid #eee}
        .container{max-width:1000px;margin:0 auto;padding:20px}
        .controls{background:#fafafa;padding:15px;border-radius:12px;margin-bottom:20px;text-align:center}
        select, button{margin:5px;padding:12px 16px;border:1px solid #ddd;border-radius:8px;font-size:16px}
        button{background:#000;color:#fff;border:none;cursor:pointer}
        button:active{background:#333}
        .slider{width:80%;max-width:400px;height:8px;border-radius:5px;background:#ddd;outline:none;margin:20px auto;display:block}
        .results{margin:30px 0}
        .station{padding:16px;background:#fff;border:1px solid #eee;border-radius:12px;margin-bottom:12px;cursor:pointer;transition:0.2s}
        .station:hover{box-shadow:0 4px 20px rgba(0,0,0,0.05)}
        .name{font-size:18px;font-weight:600}
        .price{font-size:22px;font-weight:bold;margin:8px 0}
        .info{font-size:14px;color:#555}
        #map{height:500px;border-radius:16px;margin-top:40px;box-shadow:0 4px 30px rgba(0,0,0,0.1)}
    </style>
</head>
<body>
<header>WalletSafe</header>
<div class="container">
    <div class="controls">
        <select id="fuel">
            <option value="gas95">Бензин 95</option>
            <option value="diesel">Дизель</option>
        </select>
        <input type="text" id="zip" placeholder="Почтовый индекс (например 02001)" style="width:200px;padding:12px;border:1px solid #ddd;border-radius:8px">
        <button onclick="useGeo()">Моя геолокация</button><br>
        <input type="range" class="slider" id="radius" min="5" max="100" value="30" oninput="val.textContent=this.value">
        <span style="font-size:18px"> <span id="val">30</span> км</span>
        <br><button onclick="search()" style="margin-top:15px;padding:14px 30px;font-size:18px">Найти самые дешёвые</button>
    </div>

    <div id="results" class="results"></div>
    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
let map, userMarker, routeLayer, userPos = null;

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
    } else if (navigator.geolocation) {
        const pos = await new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej));
        lat = pos.coords.latitude; lng = pos.coords.longitude;
    } else return alert("Введите индекс или разрешите геолокацию");

    userPos = {lat, lng};
    const resp = await fetch(`/search?fuel=${fuel}&lat=${lat}&lng=${lng}&dist=${radius}`);
    const list = await resp.json();

    const results = document.getElementById('results');
    results.innerHTML = list.length === 0 ? "<p style='text-align:center;color:#777'>Ничего не найдено в этом радиусе</p>" : "";

    initMap(lat, lng);
    if (userMarker) userMarker.setLatLng([lat, lng]);
    else userMarker = L.circleMarker([lat, lng], {radius: 8, color: '#0066ff', fillOpacity: 1}).addTo(map).bindPopup("Вы здесь").openPopup();

    list.slice(0, 5).forEach((s, i) => {
        const div = document.createElement('div');
        div.className = 'station';
        div.innerHTML = `
            <div class="name">${s.name} • ${s.city}</div>
            <div class="price">${s.price.toFixed(3)} €</div>
            <div class="info">${s.dist.toFixed(1)} км • ${s.hours}</div>
            <button onclick="goTo(${s.lat},${s.lng})" style="margin-top:10px">Навести в Google Maps</button>
        `;
        div.onclick = () => focusStation(s.lat, s.lng, s.name, s.price);
        results.appendChild(div);
    });
}

function initMap(lat, lng) {
    if (map) map.remove();
    map = L.map('map').setView([lat, lng], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
    document.getElementById('map').style.display = 'block';
    if (!routeLayer) routeLayer = L.layerGroup().addTo(map);
}

function focusStation(lat, lng, name, price) {
    map.setView([lat, lng], 15);
    if (routeLayer) routeLayer.clearLayers();
    L.marker([lat, lng], {icon: L.divIcon({className: 'custom-marker', html: '●', iconSize: [20,20]})})
        .addTo(map)
        .bindPopup(`<b>${name}</b><br>${price.toFixed(3)} €`).openPopup();

    if (userPos) {
        L.polyline([[userPos.lat, userPos.lng], [lat, lng]], {color: '#0066ff', weight: 4, opacity: 0.7}).addTo(routeLayer);
    }
}

function goTo(lat, lng) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=driving`;
    window.open(url, '_blank');
}

function useGeo() {
    document.getElementById('zip').value = '';
    search();
}
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/zip/<zip_code>')
def zip_route(zip_code):
    coords = geocode_zip(zip_code)
    return jsonify(lat=coords[0], lng=coords[1]) if coords else jsonify(error=True)

@app.route('/search')
def search():
    fuel = request.args.get('fuel')
    lat, lng = float(request.args.get('lat')), float(request.args.get('lng'))
    max_dist = float(request.args.get('dist', 50))

    results = []
    prices = [s[fuel] for s in stations if s[fuel] > 0]
    avg = sum(prices) / len(prices) if prices else 1.5

    for s in stations:
        if s[fuel] <= 0: continue
        dist = haversine(lat, lng, s['lat'], s['lng'])
        if dist <= max_dist:
            results.append({**s, 'price': s[fuel], 'dist': dist})

    results.sort(key=lambda x: (x['price'], x['dist']))
    return jsonify(results)

if __name__ == '__main__':
    print("\nWalletSafe запущен → http://127.0.0.1:5000")
    app.run(debug=True)

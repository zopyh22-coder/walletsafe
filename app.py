# app.py – WalletSafe (Python + Flask version)
# Double-click or run: python3 app.py

from flask import Flask, render_template_string, request, jsonify
import math
import requests

app = Flask(__name__)

# ——— ALL STATIONS (filtered, 0.000 removed) ———
stations = [
    {"name": "Nº 10.935", "city": "Abengibre", "gas95": 1.399, "diesel": 1.419, "hours": "07:00–22:00", "lat": 39.211417, "lng": -1.539167},
    {"name": "PLENERGY", "city": "Albacete", "gas95": 1.379, "diesel": 1.337, "hours": "24/7", "lat": 39.000861, "lng": -1.849833},
    {"name": "A&A", "city": "Albacete", "gas95": 1.347, "diesel": 1.297, "hours": "09:00–21:30", "lat": 39.006889, "lng": -1.885361},
    {"name": "FAMILY ENERGY", "city": "Albacete", "gas95": 1.359, "diesel": 1.319, "hours": "07:00–23:00", "lat": 38.988972, "lng": -1.847361},
    {"name": "ALCAMPO", "city": "Albacete", "gas95": 1.339, "diesel": 1.330, "hours": "24/7", "lat": 39.009639, "lng": -1.878111},
    {"name": "GMOIL", "city": "Albacete", "gas95": 1.335, "diesel": 1.295, "hours": "24/7", "lat": 39.022139, "lng": -1.882056},
    {"name": "BALLENOIL", "city": "Almansa", "gas95": 1.379, "diesel": 1.349, "hours": "24/7", "lat": 38.871556, "lng": -1.108000},
    {"name": "PLENERGY", "city": "Almansa", "gas95": 1.379, "diesel": 1.349, "hours": "24/7", "lat": 38.878667, "lng": -1.100028},
    {"name": "VIRGEN DE LAS NIEVES", "city": "Cenizate", "gas95": 1.372, "diesel": 1.379, "hours": "24/7", "lat": 39.301000, "lng": -1.664167},
    {"name": "LA REMEDIADORA", "city": "La Roda", "gas95": 1.329, "diesel": 1.319, "hours": "24/7", "lat": 39.201139, "lng": -2.147750},
    # ... (more stations — you can keep adding the rest here)
]

# Simple haversine distance
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Geocode ZIP (free)
def geocode_zip(zip_code):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={zip_code},Spain&format=json&limit=1"
        r = requests.get(url, headers={'User-Agent': 'WalletSafe/1.0'}, timeout=5)
        data = r.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except:
        pass
    return None

HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WalletSafe – Дешёвый бензин рядом</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <style>
        body{font-family:Arial;margin:0;background:#f0f8ff;color:#333}
        header{background:#1976D2;color:white;padding:1rem;text-align:center}
        .logo{font-size:1.8rem;font-weight:bold}
        .container{max-width:1100px;margin:auto;padding:1rem}
        .form{background:white;padding:1rem;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);margin-bottom:1rem;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
        select,input,button{padding:10px;border-radius:4px;border:1px solid #ccc}
        button{background:#1976D2;color:white;border:none;cursor:pointer}
        button:hover{background:#1565c0}
        .results{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
        .card{background:white;padding:1rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
        .price{font-size:1.4rem;font-weight:bold;color:#2E7D32}
        .save{color:#4CAF50;font-weight:bold}
        #map{height:400px;margin:2rem 0;border-radius:8px;display:none}
    </style>
</head>
<body>
<header><div class="logo">WalletSafe</div></header>
<div class="container">
    <div class="form">
        <select id="fuel"><option value="gas95">Бензин 95</option><option value="diesel">Дизель</option></select>
        <input type="text" id="zip" placeholder="Почтовый индекс (например 02001)">
        <button onclick="geo()">Моя геолокация</button>
        <input type="range" id="dist" min="0" max="100" value="50" oninput="d.value=value"><output id="d">50</output> км
        <button onclick="search()">Поиск</button>
    </div>
    <div id="results"></div>
    <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
let map, marker;
async function search(){
    const fuel=document.getElementById('fuel').value;
    const zip=document.getElementById('zip').value.trim();
    const maxDist=parseInt(document.getElementById('dist').value);
    let lat, lng;
    if(zip){const resp=await fetch(`/zip/${zip}`);const data=await resp.json();if(!data.error){lat=data.lat;lng=data.lng;}}
    else if(navigator.geolocation){
        const pos=await new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(res,rej));
        lat=pos.coords.latitude; lng=pos.coords.longitude;
    }else{alert("Введите ZIP или разрешите геолокацию");return;}
    const resp=await fetch(`/search?fuel=${fuel}&lat=${lat}&lng=${lng}&dist=${maxDist}`);
    const stations=await resp.json();
    const r=document.getElementById('results');
    r.innerHTML='';
    if(stations.length===0){r.innerHTML='<p>Ничего не найдено в этом радиусе</p>';return;}
    stations.forEach(s=>{
        const div=document.createElement('div');div.className='card';
        div.innerHTML=`<h3>${s.name} (${s.city})</h3>
            <p class="price">${s.price} €/л</p>
            <p>${s.dist.toFixed(1)} км • Экономия ${(s.avg-s.price).toFixed(3)} €/л</p>
            <p>${s.hours}</p>
            <button onclick="showMap(${s.lat},${s.lng},'${s.name}')">Показать на карте</button>`;
        r.appendChild(div);
    });
}
function showMap(lat,lng,name){
    const m=document.getElementById('map');
    m.style.display='block';
    if(map)map.remove();
    map=L.map('map').setView([lat,lng],13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    L.marker([lat,lng]).addTo(map).bindPopup(name).openPopup();
}
function geo(){
    document.getElementById('zip').value='';
    search();
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/zip/<zip_code>')
def zip_route(zip_code):
    coords = geocode_zip(zip_code)
    if coords:
        return jsonify(lat=coords[0], lng=coords[1])
    return jsonify(error="Invalid ZIP"), 400

@app.route('/search')
def search():
    fuel = request.args.get('fuel')
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    max_dist = float(request.args.get('dist', 50))
    results = []
    avg = sum(s[fuel] for s in stations if s[fuel]>0) / len([s for s in stations if s[fuel]>0]) if any(s[fuel] > 0 for s in stations) else 1.45
    for s in stations:
        if s[fuel] == 0: continue
        dist = distance(lat, lng, s['lat'], s['lng'])
        if dist <= max_dist:
            results.append({**s, 'dist': dist, 'price': s[fuel], 'avg': round(avg,3)})
    results.sort(key=lambda x: (x['price'], x['dist']))
    return jsonify(results[:20])

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

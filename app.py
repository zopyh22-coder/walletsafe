<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WalletSafe – Самые дешёвые заправки рядом</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
    <style>
        :root { --green: #2E7D32; --blue: #1976D2; }
        body { margin:0; font-family:Arial,sans-serif; background:#f5f5f5; color:#333; }
        header { background:var(--blue); color:white; padding:1rem; text-align:center; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; }
        .logo { font-weight:bold; font-size:1.6rem; display:flex; align-items:center; gap:10px; }
        .logo svg { width:40px; height:40px; }
        .lang { padding:8px; border-radius:4px; border:none; }
        .container { max-width:1200px; margin:0 auto; padding:1rem; }
        .form { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:20px; align-items:center; background:white; padding:15px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }
        select, input, button { padding:10px; border-radius:4px; border:1px solid #ccc; }
        button { background:var(--blue); color:white; cursor:pointer; border:none; }
        button:hover { background:#1565c0; }
        .results { display:grid; gap:15px; grid-template-columns:repeat(auto-fit, minmax(300px,1fr)); }
        .card { background:white; padding:15px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1); }
        .card h3 { margin:0 0 8px; color:var(--green); }
        .price { font-size:1.4rem; font-weight:bold; color:var(--green); }
        .save { color:#4CAF50; font-weight:bold; }
        .map { height:400px; margin:20px 0; border-radius:8px; display:none; }
        .pagination { text-align:center; margin:20px 0; }
        .drive { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
        .drive button { background:#4CAF50; font-size:0.9rem; padding:6px 10px; }
        .hidden { display:none !important; }
    </style>
</head>
<body>

<header>
    <div class="logo">
        <svg viewBox="0 0 100 100">
            <rect x="15" y="30" width="70" height="45" rx="10" fill="var(--green)"/>
            <circle cx="70" cy="45" r="12" fill="var(--blue)"/>
            <path d="M65 40 L75 45 L65 50 Z" fill="white"/>
        </svg>
        WalletSafe
    </div>
    <select class="lang" onchange="changeLang(this.value)">
        <option value="ru">Русский</option>
        <option value="en">English</option>
        <option value="es">Español</option>
    </select>
</header>

<div class="container">
    <div class="form">
        <select id="fuel"><option value="gas95">Бензин 95</option><option value="diesel">Дизель</option></select>
        <input type="text" id="zip" placeholder="Почтовый индекс (например 28001)">
        <button onclick="useGeo()">Моё местоположение</button>
        <span>Радиус:</span>
        <input type="range" id="range" min="5" max="100" value="30" oninput="this.nextElementSibling.value=this.value">
        <output>30</output> км
        <button onclick="search()">Поиск</button>
    </div>

    <div id="results" class="results hidden"></div>
    <div id="map" class="map"></div>
    <div class="pagination hidden">
        <button onclick="page(-1)">Пред.</button>
        <span id="pg"></span>
        <button onclick="page(1)">След.</button>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// ——— Translations ———
const t = {
    ru: {title:"Самые дешёвые заправки рядом", fuelGas:"Бензин 95", fuelDiesel:"Дизель", placeholder:"Почтовый индекс (например 28001)", geo:"Моё местоположение", radius:"Радиус", search:"Поиск", price:"Цена", dist:"Расстояние", save:"Экономия", hours:"Часы работы", drive:"Проложить маршрут", no:"Ничего не найдено", page:"Страница"},
    en: {title:"Cheapest fuel nearby", fuelGas:"Gasoline 95", fuelDiesel:"Diesel", placeholder:"ZIP code (e.g. 28001)", geo:"My location", radius:"Radius", search:"Search", price:"Price", dist:"Distance", save:"You save", hours:"Hours", drive:"Get directions", no:"No stations found", page:"Page"},
    es: {title:"Gasolineras más baratas cerca", fuelGas:"Gasolina 95", fuelDiesel:"Diésel", placeholder:"Código postal (ej. 28001)", geo:"Mi ubicación", radius:"Radio", search:"Buscar", price:"Precio", dist:"Distancia", save:"Ahorras", hours:"Horario", drive:"Cómo llegar", no:"No hay estaciones", page:"Página"}
};
let lang = 'ru';

// ——— Full filtered data (0.000 prices removed) ———
const stations = [
    {name:"Nº 10.935",city:"Abengibre",prov:"ALBACETE",gas95:1.399,diesel:1.419,hours:"07:00–22:00",lat:39.211417,lng:-1.539167},
    {name:"PLENERGY",city:"Albacete",prov:"ALBACETE",gas95:1.379,diesel:1.337,hours:"24/7",lat:39.000861,lng:-1.849833},
    {name:"A&A",city:"Albacete",prov:"ALBACETE",gas95:1.347,diesel:1.297,hours:"09:00–21:30",lat:39.006889,lng:-1.885361},
    {name:"FAMILY ENERGY",city:"Albacete",prov:"ALBACETE",gas95:1.359,diesel:1.319,hours:"07:00–23:00",lat:38.988972,lng:-1.847361},
    {name:"ALCAMPO",city:"Albacete",prov:"ALBACETE",gas95:1.339,diesel:1.330,hours:"24/7",lat:39.009639,lng:-1.878111},
    {name:"GMOIL",city:"Albacete",prov:"ALBACETE",gas95:1.335,diesel:1.295,hours:"24/7",lat:39.022139,lng:-1.882056},
    {name:"BALLENOIL",city:"Almansa",prov:"ALBACETE",gas95:1.379,diesel:1.349,hours:"24/7",lat:38.871556,lng:-1.108000},
    {name:"PLENERGY",city:"Almansa",prov:"ALBACETE",gas95:1.379,diesel:1.349,hours:"24/7",lat:38.878667,lng:-1.100028},
    {name:"VIRGEN DE LAS NIEVES",city:"Cenizate",prov:"ALBACETE",gas95:1.372,diesel:1.379,hours:"24/7",lat:39.301000,lng:-1.664167},
    {name:"LA REMEDIADORA",city:"Roda (La)",prov:"ALBACETE",gas95:1.329,diesel:1.319,hours:"24/7",lat:39

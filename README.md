# 🛰️ NASA JPL Asteroid Prospector & Machine Learning API

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Deploy to Render](https://img.shields.io/badge/Deploy%20to-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com)

Plataforma inteligente de Machine Learning y Prospección Espacial diseñada para predecir la composición mineralógica de asteroides y su viabilidad económica para la **Utilización de Recursos In Situ (ISRU)** y minería espacial, entrenada con datos del **NASA Jet Propulsion Laboratory (JPL) Small-Body Database**.

---

## 🌟 Características Principales

- **Modelos Predictivos Random Forest**:
  - **Clasificador Multiclase**: Discrimina entre 4 familias taxonómicas de asteroides: *Carbonáceo (C)*, *Silicatos / Rocoso (S)*, *Metálico (M/X)* y *Basáltico (V)*.
  - **Detector Binario de Cuerpos Metálicos**: Especializado en la identificación de anomalías ricas en Platino, Oro, Hierro y Níquel con calibración de umbral de decisión.
- **Evaluación Minera & Astrofísica (ISRU)**:
  - Estimación de potencial de metales preciosos, recursos hídricos para combustible criogénico ($H_2 / O_2$) y materiales estructurales.
  - Identificación de la zona orbital (*NEO*, *Cinturón Principal*, *Troyanos de Júpiter*, etc.).
  - Síntesis explicativa astrofísica basada en reflectividad de albedo y tamaño físico.
- **Frontend Interactivo Glassmorphic**:
  - Telemetría en tiempo real, barras de probabilidad relativas y tarjetas de potencial minero.
  - Perfiles preconfigurados de asteroides emblemáticos: **16-Psyche** (Metálico), **101955-Bennu** (Carbonáceo), **4-Vesta** (Basáltico) y **433-Eros** (Silicatos).
- **Backend de Alto Desempeño**:
  - Desarrollado en **FastAPI** con validación de esquemas en tiempo de compilación con **Pydantic v2**.
  - Documentación interactiva automática con Swagger / OpenAPI (`/docs`).
  - Listo para despliegue sin costo en **Render**, **Railway**, **Fly.io** o contenedores Docker.

---

## 🏗️ Arquitectura del Sistema

```
data/
├── app.py                             # API REST FastAPI y servidor de interfaz web
├── rf_asteroides_jpl_multiclase.joblib # Modelo Random Forest Multiclase (NASA JPL)
├── rf_asteroides_jpl_binario.joblib    # Detector Random Forest Binario de Metales
├── metadata_asteroides_jpl.json       # Métricas de entrenamiento y descripciones mineralógicas
├── dataset_asteroides_nasa_jpl.csv    # Dataset procesado del JPL Small-Body Database
├── extract_jpl_dataset.py             # Script de extracción y limpieza de datos JPL
├── train_asteroid_model.py            # Script de entrenamiento y evaluación de modelos
├── static/                            # Frontend Web interactivo
│   ├── index.html                     # Dashboard visual
│   ├── app.js                         # Lógica cliente y consumo de API REST
│   └── style.css                      # Estilos espaciales y layout adaptativo
├── tests/                             # Suite de pruebas automatizadas
│   ├── test_api_integration.py       # Pruebas de integración del backend
│   └── test_e2e_playwright.js         # Pruebas End-to-End de interfaz de usuario
├── requirements.txt                   # Dependencias de producción para despliegue
├── requirements-dev.txt               # Dependencias adicionales para pruebas locales
├── Procfile                           # Script de arranque para plataformas PaaS
├── render.yaml                        # Blueprint para despliegue automático en Render
├── runtime.txt / .python-version      # Fijación de versión de Python (3.11.9)
├── .gitignore                         # Archivos excluidos del control de versiones
├── DEPLOYMENT.md                      # Guía detallada de despliegue en Render y GitHub
└── README.md                          # Documentación del proyecto
```

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/nasa-asteroid-prospector.git
cd nasa-asteroid-prospector
```

### 2. Crear y activar un entorno virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Iniciar el servidor de desarrollo
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Abre tu navegador en:
- **Dashboard Web**: [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 📡 Endpoints del API

### `GET /api/v1/health`
Verifica la disponibilidad de la API y el estado en memoria de los modelos entrenados.

### `GET /api/v1/metadata`
Retorna las métricas del clasificador, importancias relativas de las variables y taxonomía de asteroides.

### `POST /api/v1/predict`
Predice la composición del asteroide y genera la auditoría de potencial minero.

#### Ejemplo de Cuerpo de Solicitud (JSON):
```json
{
  "magnitud_absoluta_H": 5.90,
  "albedo_geometrico": 0.12,
  "diametro_km": 226.0,
  "semieje_mayor_au": 2.924,
  "excentricidad": 0.134,
  "inclinacion_grados": 3.09,
  "distancia_perihelio_au": 2.532,
  "periodo_rotacion_horas": 4.196
}
```

---

## ☁️ Despliegue Gratuito en la Nube

Para desplegar esta aplicación en **Render** sin costo y conectarla a tu repositorio de GitHub, consulta la [Guía Completa de Despliegue Paso a Paso (DEPLOYMENT.md)](DEPLOYMENT.md).

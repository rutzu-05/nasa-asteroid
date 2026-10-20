# 🚀 Guía de Despliegue en Render (Nivel Gratuito) y GitHub

Esta guía detalla el paso a paso para publicar el proyecto **NASA JPL Asteroid Prospector & Machine Learning API** en **GitHub** y desplegarlo sin costo en **Render**.

---

## 📋 Resumen de Archivos de Despliegue Incluidos

| Archivo | Propósito |
| :--- | :--- |
| `render.yaml` | Especificación de infraestructura como código (Blueprint) para despliegue automático con 1 clic en Render. |
| `Procfile` | Comando estándar de arranque para servidores PaaS (`uvicorn app:app --host 0.0.0.0 --port $PORT`). |
| `requirements.txt` | Dependencias de producción optimizadas para bajo consumo de memoria RAM (< 512MB). |
| `requirements-dev.txt` | Dependencias para ejecución de suites de pruebas (`pytest`, `requests`). |
| `runtime.txt` / `.python-version` | Fija la versión recomendada de Python (`3.11.9`) para descargar wheels precompilados de `scikit-learn` y `pandas`. |
| `.gitignore` | Evita subir archivos temporales, carpetas de agentes, capturas de pantalla y cachés. |

---

## 🛰️ Paso 1: Inicialización y Subida a GitHub

### 1.1 Crear el repositorio en GitHub
1. Abre tu navegador e inicia sesión en [GitHub](https://github.com/).
2. Haz clic en el botón verde **"New"** (o ve a [github.com/new](https://github.com/new)).
3. Configura el repositorio:
   - **Repository name**: `nasa-asteroid`
   - **Description**: *API REST de Machine Learning y Dashboard para clasificación y prospección minera de asteroides (NASA JPL).*
   - **Visibility**: **Public** (necesario para el plan gratuito ilimitado de Render).
   - **Initialize this repository with**: No selecciones README, .gitignore ni licencia (ya los tenemos generados localmente).
4. Haz clic en **"Create repository"**.
5. Copia la URL del repositorio (`https://github.com/rutzu-05/nasa-asteroid.git`).

### 1.2 Inicializar Git y realizar el primer Commit local
Abre PowerShell o tu terminal en la carpeta del proyecto y ejecuta:

```powershell
# 1. Inicializar el repositorio Git
git init

# 2. Configurar la rama principal como 'main'
git branch -M main

# 3. Agregar los archivos al área de preparación (stage)
git add .

# 4. Verificar qué archivos se incluirán
git status

# 5. Crear el primer commit
git commit -m "feat: initial commit with FastAPI backend, ML models, UI, and Render deployment config"
```

### 1.3 Conectar y Subir a GitHub
Reemplaza `<TU_USUARIO>` y `<TU_REPOSITORIO>` por tus datos reales:

```powershell
# 1. Vincular el repositorio remoto de GitHub
git remote add origin https://github.com/<TU_USUARIO>/<TU_REPOSITORIO>.git

# 2. Subir los archivos a la rama main
git push -u origin main
```

*(Si Git te solicita autenticación en Windows, se abrirá la ventana de GitHub Credential Manager para autorizar con tu navegador).*

---

## ☁️ Paso 2: Despliegue en Render (Plan Gratuito)

Render ofrece alojamiento web gratuito para servicios web en Python con soporte de HTTPS automático, CI/CD integrado y subdominios `*.onrender.com`.

### Opción A: Despliegue Automático mediante Blueprint (`render.yaml`) ⭐ *Recomendada*
1. Inicia sesión en [Render](https://dashboard.render.com/).
2. En el panel principal, haz clic en **"New +"** en la esquina superior derecha.
3. Selecciona **"Blueprint"**.
4. Conecta tu cuenta de GitHub (si aún no lo has hecho) y selecciona el repositorio `nasa-asteroid`.
5. Render detectará automáticamente el archivo `render.yaml` y configurará:
   - **Service Name**: `nasa-asteroid`
   - **Environment**: `Python`
   - **Plan**: `Free`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
6. Haz clic en **"Apply"**. Render comenzará la construcción y despliegue automáticamente.

---

### Opción B: Despliegue Manual paso a paso (Dashboard de Render)
Si prefieres configurarlo manualmente en el panel de Render:

1. Ve a [dashboard.render.com](https://dashboard.render.com/).
2. Haz clic en **"New +"** > **"Web Service"**.
3. Selecciona **"Build and deploy from a Git repository"** y presiona **Next**.
4. Busca y selecciona tu repositorio `nasa-asteroid`.
5. Rellena los siguientes campos exactamente como se indica:

| Parámetro | Valor a Configurar |
| :--- | :--- |
| **Name** | `nasa-asteroid` |
| **Region** | `Oregon (US West)` u `Ohio (US East)` |
| **Branch** | `main` |
| **Root Directory** | *(Dejar vacío para usar la raíz)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt` |
| **Start Command** | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` (0.1 CPU, 512 MB RAM) |

6. Despliega la sección **"Advanced"**:
   - **Health Check Path**: `/api/v1/health`
   - **Add Environment Variable**:
     - `PYTHON_VERSION` = `3.11.9`
7. Haz clic en **"Create Web Service"**.

---

## 🔍 Paso 3: Verificación del Despliegue

Una vez que los registros indiquen `==> Your service is live 🎉`, copia la URL generada por Render (ej. `https://nasa-asteroid.onrender.com`):

1. **Dashboard Web Interactivo**:
   Abre `https://tu-app.onrender.com/` en tu navegador para interactuar con la interfaz espacial y probar las predicciones en tiempo real.
2. **Documentación Swagger / OpenAPI**:
   Abre `https://tu-app.onrender.com/docs` para ver e interactuar con la documentación interactiva de endpoints.
3. **Endpoint de Salud**:
   Visita `https://tu-app.onrender.com/api/v1/health` para comprobar que ambos modelos (`rf_multi` y `rf_bin`) estén cargados en memoria.
4. **Prueba de Inferencia con `curl`**:
   ```bash
   curl -X POST "https://tu-app.onrender.com/api/v1/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "magnitud_absoluta_H": 5.90,
       "albedo_geometrico": 0.12,
       "diametro_km": 226.0,
       "semieje_mayor_au": 2.924,
       "excentricidad": 0.134,
       "inclinacion_grados": 3.09,
       "distancia_perihelio_au": 2.532,
       "periodo_rotacion_horas": 4.196
     }'
   ```

---

## ⚡ Consideraciones del Nivel Gratuito de Render (Spin-down)

> [!NOTE]
> En el plan gratuito de Render, el servicio se suspende (entra en reposo) si no recibe tráfico durante 15 minutos. La primera petición tras un período de inactividad puede tardar aproximadamente **40 a 50 segundos** mientras la instancia levanta el contenedor e inicializa los modelos en memoria. Las peticiones subsecuentes responderán en menos de 100 milisegundos.

### Cómo mantener el servicio activo (Keep-Alive gratuito)
Si deseas evitar el retardo del arranque en frío (cold start), puedes configurar un monitor de estado gratuito que envíe un ping HTTP a tu ruta de salud cada 10 minutos:
1. Regístrate en [UptimeRobot](https://uptimerobot.com/) o [Cron-Job.org](https://cron-job.org/) (gratuitos).
2. Crea un nuevo monitor tipo **HTTP(s)**.
3. URL: `https://tu-app.onrender.com/api/v1/health`
4. Intervalo de monitorización: **10 o 14 minutos**.
5. ¡Listo! Tu servicio se mantendrá activo durante el día sin entrar en reposo.

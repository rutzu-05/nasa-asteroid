"""
API REST con FastAPI para la Clasificación y Prospección de Asteroides (NASA JPL)
Misión: Utilización de Recursos In Situ (ISRU) y Minería Espacial.
"""

import json
import os
from typing import Dict, Any, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from batch_processor import (
    read_uploaded_file,
    process_batch_dataframe,
    generate_enriched_csv
)

# =============================================================================
# INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# =============================================================================
app = FastAPI(
    title="NASA JPL Asteroid Prospector API",
    description="API de Machine Learning para predecir la composición geoquímica y potencial minero de asteroides a partir de datos del NASA JPL Small-Body Database.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# CARGA DE MODELOS DE MACHINE LEARNING Y METADATOS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_MULTI_PATH = os.path.join(BASE_DIR, "rf_asteroides_jpl_multiclase.joblib")
MODEL_BIN_PATH = os.path.join(BASE_DIR, "rf_asteroides_jpl_binario.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "metadata_asteroides_jpl.json")

rf_multi = None
rf_bin = None
metadata = {}

try:
    if os.path.exists(MODEL_MULTI_PATH):
        rf_multi = joblib.load(MODEL_MULTI_PATH)
        print(f"[OK] Modelo Multiclase de Asteroides cargado: {MODEL_MULTI_PATH}")
    if os.path.exists(MODEL_BIN_PATH):
        rf_bin = joblib.load(MODEL_BIN_PATH)
        print(f"[OK] Detector Binario de Metales cargado: {MODEL_BIN_PATH}")
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"[OK] Metadatos de Asteroides cargados: {METADATA_PATH}")
except Exception as e:
    print(f"[ERROR] Error al cargar modelos de asteroides: {e}")

# =============================================================================
# MODELOS DE VALIDACIÓN PYDANTIC
# =============================================================================
class AsteroidInput(BaseModel):
    magnitud_absoluta_H: float = Field(
        ...,
        ge=-5.0,
        le=35.0,
        description="Magnitud absoluta H (Luminosidad intrínseca, ej. 5.90)",
        examples=[5.90]
    )
    albedo_geometrico: float = Field(
        ...,
        ge=0.001,
        le=1.0,
        description="Albedo geométrico visual (Reflectividad de la superficie entre 0.001 y 1.0)",
        examples=[0.12]
    )
    diametro_km: float = Field(
        ...,
        gt=0.0,
        le=2000.0,
        description="Diámetro medio en kilómetros (ej. 226.0)",
        examples=[226.0]
    )
    semieje_mayor_au: float = Field(
        ...,
        gt=0.0,
        le=100.0,
        description="Semieje mayor de la órbita en Unidades Astronómicas (AU)",
        examples=[2.924]
    )
    excentricidad: float = Field(
        ...,
        ge=0.0,
        le=1.5,
        description="Excentricidad orbital (0.0 para circular)",
        examples=[0.134]
    )
    inclinacion_grados: float = Field(
        ...,
        ge=0.0,
        le=180.0,
        description="Inclinación orbital en grados respecto a la eclíptica (0.0 - 180.0)",
        examples=[3.09]
    )
    distancia_perihelio_au: float = Field(
        ...,
        gt=0.0,
        le=100.0,
        description="Distancia de perihelio en AU (punto más cercano al Sol)",
        examples=[2.532]
    )
    periodo_rotacion_horas: Optional[float] = Field(
        default=6.8,
        gt=0.0,
        le=5000.0,
        description="Período de rotación sobre su eje en horas (Opcional, por defecto 6.8h)",
        examples=[4.196]
    )

class MiningPotential(BaseModel):
    metales_preciosos: str
    recursos_hidricos_combustible: str
    materiales_estructurales: str
    calificacion_general: str

class PredictionResponse(BaseModel):
    status: str
    prediccion: str
    confianza: float
    probabilidades: Dict[str, float]
    es_metalico: bool
    probabilidad_metalica_detector: float
    icono: str
    minerales_clave: str
    albedo_tipico: str
    objetivo_mision: str
    zona_orbital: str
    interpretacion_astrofisica: str
    potencial_minero: MiningPotential
    parametros_normalizados: Dict[str, float]

# =============================================================================
# ENDPOINTS DEL API
# =============================================================================
@app.get("/api/v1/health", tags=["Salud"])
def health_check():
    """Verifica que el servicio y los modelos de asteroides estén listos en memoria."""
    return {
        "status": "healthy",
        "service": "NASA JPL Asteroid Prospector",
        "models_loaded": {
            "asteroid_multiclass_rf": rf_multi is not None,
            "metallic_detector_rf": rf_bin is not None,
            "metadata": bool(metadata)
        },
        "version": "2.0.0"
    }

@app.get("/api/v1/metadata", tags=["Información"])
def get_metadata():
    """Retorna métricas de precisión, importancias de variables y taxonomía de la NASA."""
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metadatos no disponibles."
        )
    return metadata

@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Inferencia"])
def predict_asteroid_composition(data: AsteroidInput):
    """
    Predice la composición mineralógica y potencial minero del asteroide usando Random Forest.
    """
    if rf_multi is None or rf_bin is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los modelos de Machine Learning no están cargados."
        )

    features = metadata.get("features", [
        'magnitud_absoluta_H', 'albedo_geometrico', 'diametro_km',
        'semieje_mayor_au', 'excentricidad', 'inclinacion_grados',
        'distancia_perihelio_au', 'periodo_rotacion_horas'
    ])

    rot = data.periodo_rotacion_horas if data.periodo_rotacion_horas is not None else 6.8

    input_df = pd.DataFrame([{
        'magnitud_absoluta_H': data.magnitud_absoluta_H,
        'albedo_geometrico': data.albedo_geometrico,
        'diametro_km': data.diametro_km,
        'semieje_mayor_au': data.semieje_mayor_au,
        'excentricidad': data.excentricidad,
        'inclinacion_grados': data.inclinacion_grados,
        'distancia_perihelio_au': data.distancia_perihelio_au,
        'periodo_rotacion_horas': rot
    }])[features]

    # Inferencia Multiclase
    pred_class = str(rf_multi.predict(input_df)[0])
    probas = rf_multi.predict_proba(input_df)[0]
    classes = list(rf_multi.classes_)

    prob_dict = {
        cls: round(float(p) * 100, 2)
        for cls, p in zip(classes, probas)
    }
    confianza = round(float(np.max(probas)) * 100, 2)

    # Inferencia con Detector Binario Metálico
    bin_proba = float(rf_bin.predict_proba(input_df)[0][1])
    es_metalico = bool(bin_proba >= 0.40 or pred_class == "Metálico (Fe-Ni, Oro, Platino)")

    # Clasificación de Zona Orbital
    a = data.semieje_mayor_au
    q = data.distancia_perihelio_au
    if q < 1.3:
        zona_orbital = "NEO (Asteroide Cercano a la Tierra) - Alta Accesibilidad Operativa"
    elif 2.0 <= a <= 3.3:
        zona_orbital = "Cinturón Principal de Asteroides (Entre Marte y Júpiter)"
    elif 5.0 <= a <= 5.5:
        zona_orbital = "Asteroide Troyano (Puntos de Lagrange de Júpiter)"
    elif a > 5.5:
        zona_orbital = "Centauro / Objeto Transneptuniano Exterior"
    else:
        zona_orbital = "Órbita Intermedia del Sistema Solar"

    # Enriquecimiento Geoquímico
    family_info = metadata.get("descripcion_familias_mineras", {}).get(pred_class, {
        "minerales_clave": "Silicatos y óxidos metálicos.",
        "albedo_tipico": "0.10 - 0.25",
        "objetivo_mision": "Exploración y muestreo de superficie.",
        "icono": "🪐"
    })

    # Potencial de Minería Espacial
    if pred_class == "Metálico (Fe-Ni, Oro, Platino)":
        potencial = MiningPotential(
            metales_preciosos="Muy Alto (Alta ley de Au, Pt, Ni, Fe)",
            recursos_hidricos_combustible="Bajo / Nulo (Cuerpo desvolatilizado)",
            materiales_estructurales="Excepcional (Aleaciones ultradensas)",
            calificacion_general="Objetivo de Máxima Prioridad Económica (Trillones USD)"
        )
    elif pred_class == "Carbonáceo (Agua, Compuestos Orgánicos)":
        potencial = MiningPotential(
            metales_preciosos="Bajo / Trazas de metales nativos",
            recursos_hidricos_combustible="Excepcional (Agua ligada H2O para producir H2/O2)",
            materiales_estructurales="Moderado (Arcillas y carbono)",
            calificacion_general="Objetivo Estratégico de Repostaje e Hidratación Espacial"
        )
    elif pred_class == "Silicatos / Rocoso (Mg-Fe, Piroxeno)":
        potencial = MiningPotential(
            metales_preciosos="Moderado (Inclusiones metálicas kamacita)",
            recursos_hidricos_combustible="Bajo (Pocos volátiles)",
            materiales_estructurales="Muy Alto (Silicio para celdas solares y piroxeno)",
            calificacion_general="Objetivo Estructural y Manufactura en Órbita"
        )
    else: # Basáltico
        potencial = MiningPotential(
            metales_preciosos="Bajo (Corteza diferenciada)",
            recursos_hidricos_combustible="Nulo (Lavas ígneas desgasificadas)",
            materiales_estructurales="Alto (Roca basáltica para blindaje contra radiación)",
            calificacion_general="Objetivo de Alto Valor Geológico y Científico"
        )

    # Justificación Astrofísica
    explicacion = []
    if data.albedo_geometrico < 0.08:
        explicacion.append(f"El bajo albedo ({data.albedo_geometrico:.3f}) indica una superficie oscura rica en carbono elemental y minerales hidratados que absorben fuertemente la radiación solar.")
    elif data.albedo_geometrico > 0.30:
        explicacion.append(f"El alto albedo ({data.albedo_geometrico:.3f}) revela una superficie sumamente brillante con corteza ígnea cristalina y plagioclasa basáltica.")
    elif 0.09 <= data.albedo_geometrico <= 0.25:
        explicacion.append(f"El albedo intermedio-metálico ({data.albedo_geometrico:.3f}) concuerda con silicatos de piroxeno o reflectividad de aleaciones de hierro-níquel en superficie.")

    if data.diametro_km > 100:
        explicacion.append(f"Con un diámetro masivo de {data.diametro_km:,.1f} km, el cuerpo experimentó calentamiento radiogénico y diferenciación interna de capas.")
    elif data.diametro_km < 5:
        explicacion.append(f"Su tamaño reducido ({data.diametro_km:.2f} km) es típico de un fragmento de colisión secundaria con baja gravedad superficial.")

    explicacion.append(f"Su ubicación orbital ({a:.2f} AU) y cercanía perihélica ({q:.2f} AU) determinan la accesibilidad cinemática (Delta-V) para sondas de prospección.")

    return PredictionResponse(
        status="success",
        prediccion=pred_class,
        confianza=confianza,
        probabilidades=prob_dict,
        es_metalico=es_metalico,
        probabilidad_metalica_detector=round(bin_proba * 100, 2),
        icono=family_info.get("icono", "🪐"),
        minerales_clave=family_info.get("minerales_clave", "N/A"),
        albedo_tipico=family_info.get("albedo_tipico", "N/A"),
        objetivo_mision=family_info.get("objetivo_mision", "N/A"),
        zona_orbital=zona_orbital,
        interpretacion_astrofisica=" ".join(explicacion),
        potencial_minero=potencial,
        parametros_normalizados={
            "H": data.magnitud_absoluta_H,
            "albedo": data.albedo_geometrico,
            "diametro_km": data.diametro_km,
            "semieje_au": a
        }
    )

# =============================================================================
# ENDPOINTS DE PROCESAMIENTO MASIVO (CSV / EXCEL)
# =============================================================================
@app.get("/api/v1/template/csv", tags=["Procesamiento Masivo"])
def download_csv_template():
    """Descarga un archivo CSV de prueba preconfigurado con asteroides del catálogo de la NASA."""
    template_path = os.path.join(BASE_DIR, "prueba_asteroides_entrada.csv")
    if not os.path.exists(template_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plantilla CSV no encontrada en el servidor."
        )
    return FileResponse(
        template_path,
        media_type="text/csv",
        filename="plantilla_asteroides_prueba.csv"
    )

@app.post("/api/v1/predict/batch", tags=["Procesamiento Masivo"])
async def predict_batch_asteroids(file: UploadFile = File(...)):
    """
    Recibe un archivo CSV o Excel (.xlsx/.xls) con telemetría de asteroides,
    ejecuta inferencia masiva y devuelve un reporte estadístico e informe analítico ISRU.
    """
    if rf_multi is None or rf_bin is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los modelos de Machine Learning no están cargados en el servidor."
        )

    try:
        contents = await file.read()
        raw_df = read_uploaded_file(contents, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al leer el archivo: {str(e)}"
        )

    try:
        result = process_batch_dataframe(raw_df, rf_multi, rf_bin, metadata)
        # Quitar el DataFrame interno antes de retornar JSON
        result.pop("_valid_df", None)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante el procesamiento masivo: {str(e)}"
        )

@app.post("/api/v1/predict/batch/export", tags=["Procesamiento Masivo"])
async def export_batch_predictions_csv(file: UploadFile = File(...)):
    """
    Recibe un archivo CSV o Excel y devuelve directamente un archivo CSV enriquecido
    con las predicciones del modelo, probabilidades, potencial minero y zona orbital.
    """
    if rf_multi is None or rf_bin is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los modelos de Machine Learning no están cargados en el servidor."
        )

    try:
        contents = await file.read()
        raw_df = read_uploaded_file(contents, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al leer el archivo: {str(e)}"
        )

    try:
        result = process_batch_dataframe(raw_df, rf_multi, rf_bin, metadata)
        valid_df = result.get("_valid_df")
        csv_text = generate_enriched_csv(valid_df)
        
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="reporte_asteroides_predicciones.csv"'
            }
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar exportación CSV: {str(e)}"
        )

# =============================================================================
# SERVIR FRONTEND ESTÁTICO
# =============================================================================
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

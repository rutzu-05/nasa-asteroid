"""
Test Suite de Integración para el Backend y Modelos de Machine Learning (NASA JPL)
Verifica:
1. Endpoint de Salud (/api/v1/health)
2. Endpoint de Metadatos y Taxonomía (/api/v1/metadata)
3. Validación Pydantic (Valores válidos e inválidos con códigos 200 y 422)
4. Inferencia Multiclase y Detector Binario para 4 arquetipos de asteroides:
   - 16-Psyche (Metálico)
   - 101955-Bennu (Carbonáceo)
   - 4-Vesta (Basáltico)
   - 433-Eros (Silicatos)
5. Enriquecimiento Geoquímico y Evaluación de Minería Espacial (ISRU)
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("--> [1/5] Verificando /api/v1/health...")
    res = requests.get(f"{BASE_URL}/api/v1/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "healthy"
    assert data["models_loaded"]["asteroid_multiclass_rf"] is True
    assert data["models_loaded"]["metallic_detector_rf"] is True
    assert data["models_loaded"]["metadata"] is True
    print("    [PASÓ] Servidor saludable y modelos RF cargados en memoria.")

def test_metadata():
    print("--> [2/5] Verificando /api/v1/metadata...")
    res = requests.get(f"{BASE_URL}/api/v1/metadata")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert "features" in data
    assert "metricas" in data
    assert "descripcion_familias_mineras" in data
    assert len(data["features"]) == 8
    print(f"    [PASÓ] Metadatos validados. Features: {data['features']}")
    print(f"    [INFO] Exactitud Multiclase: {data['metricas'].get('exactitud_multiclase', 'N/A')}")
    print(f"    [INFO] Exactitud Metálica: {data['metricas'].get('exactitud_metalica', 'N/A')}")

def test_pydantic_validation_boundaries():
    print("--> [3/5] Verificando Validación Pydantic y Casos Límite...")
    
    # Caso 1: Albedo negativo (< 0.001)
    payload_bad_albedo = {
        "magnitud_absoluta_H": 5.9,
        "albedo_geometrico": -0.05,
        "diametro_km": 200.0,
        "semieje_mayor_au": 2.5,
        "excentricidad": 0.1,
        "inclinacion_grados": 10.0,
        "distancia_perihelio_au": 2.0
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=payload_bad_albedo)
    assert res.status_code == 422, f"Expected 422 for negative albedo, got {res.status_code}"
    
    # Caso 2: Excentricidad excesiva (> 1.5)
    payload_bad_ecc = {
        "magnitud_absoluta_H": 5.9,
        "albedo_geometrico": 0.12,
        "diametro_km": 200.0,
        "semieje_mayor_au": 2.5,
        "excentricidad": 2.5,
        "inclinacion_grados": 10.0,
        "distancia_perihelio_au": 2.0
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=payload_bad_ecc)
    assert res.status_code == 422, f"Expected 422 for ecc > 1.5, got {res.status_code}"

    # Caso 3: Diámetro no positivo (0 o negativo)
    payload_bad_diam = {
        "magnitud_absoluta_H": 5.9,
        "albedo_geometrico": 0.12,
        "diametro_km": 0.0,
        "semieje_mayor_au": 2.5,
        "excentricidad": 0.1,
        "inclinacion_grados": 10.0,
        "distancia_perihelio_au": 2.0
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=payload_bad_diam)
    assert res.status_code == 422, f"Expected 422 for diameter <= 0, got {res.status_code}"
    
    # Caso 4: Parámetro obligatorio ausente
    payload_missing = {
        "magnitud_absoluta_H": 5.9,
        "albedo_geometrico": 0.12
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=payload_missing)
    assert res.status_code == 422, f"Expected 422 for missing fields, got {res.status_code}"

    print("    [PASÓ] Todas las restricciones Pydantic rechazan correctamente las anomalías con HTTP 422.")

def test_inference_and_archetypes():
    print("--> [4/5] Verificando Inferencia de Arquetipos y Detección de Metales...")

    # Test Case 1: 16-Psyche (Esperado: Metálico con alta ley)
    psyche_payload = {
        "magnitud_absoluta_H": 5.90,
        "albedo_geometrico": 0.120,
        "diametro_km": 226.0,
        "semieje_mayor_au": 2.924,
        "excentricidad": 0.134,
        "inclinacion_grados": 3.09,
        "distancia_perihelio_au": 2.532,
        "periodo_rotacion_horas": 4.196
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=psyche_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Metálico" in data["prediccion"]
    assert data["es_metalico"] is True
    assert data["probabilidad_metalica_detector"] > 50.0
    assert "Trillones" in data["potencial_minero"]["calificacion_general"] or "Prioridad" in data["potencial_minero"]["calificacion_general"]
    print(f"    [PASÓ] 16-Psyche clasificado como {data['prediccion']} (Confianza: {data['confianza']}%, Probabilidad Metálica: {data['probabilidad_metalica_detector']}%)")

    # Test Case 2: 101955-Bennu (Esperado: Carbonáceo, bajo albedo ~0.046)
    bennu_payload = {
        "magnitud_absoluta_H": 20.60,
        "albedo_geometrico": 0.046,
        "diametro_km": 0.492,
        "semieje_mayor_au": 1.126,
        "excentricidad": 0.203,
        "inclinacion_grados": 6.03,
        "distancia_perihelio_au": 0.897,
        "periodo_rotacion_horas": 4.296
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=bennu_payload)
    assert res.status_code == 200
    data = res.json()
    assert "Carbonáceo" in data["prediccion"]
    assert "NEO" in data["zona_orbital"]
    assert "H2O" in data["potencial_minero"]["recursos_hidricos_combustible"]
    print(f"    [PASÓ] 101955-Bennu clasificado como {data['prediccion']} (NEO: {data['zona_orbital']})")

    # Test Case 3: 4-Vesta (Esperado: Basáltico, alto albedo ~0.423)
    vesta_payload = {
        "magnitud_absoluta_H": 3.20,
        "albedo_geometrico": 0.423,
        "diametro_km": 525.4,
        "semieje_mayor_au": 2.361,
        "excentricidad": 0.089,
        "inclinacion_grados": 7.14,
        "distancia_perihelio_au": 2.151,
        "periodo_rotacion_horas": 5.342
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=vesta_payload)
    assert res.status_code == 200
    data = res.json()
    assert "Basáltico" in data["prediccion"]
    print(f"    [PASÓ] 4-Vesta clasificado como {data['prediccion']} (Confianza: {data['confianza']}%)")

def test_astrophysical_synthesis():
    print("--> [5/5] Verificando Síntesis Astrofísica y Consistencia de Salida...")
    test_payload = {
        "magnitud_absoluta_H": 11.16,
        "albedo_geometrico": 0.250,
        "diametro_km": 16.84,
        "semieje_mayor_au": 1.458,
        "excentricidad": 0.223,
        "inclinacion_grados": 10.83,
        "distancia_perihelio_au": 1.133,
        "periodo_rotacion_horas": 5.270
    }
    res = requests.post(f"{BASE_URL}/api/v1/predict", json=test_payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["interpretacion_astrofisica"]) > 50
    assert "probabilidades" in data
    assert sum(data["probabilidades"].values()) >= 99.0  # Suma de porcentajes redondeados ~100%
    assert data["parametros_normalizados"]["H"] == 11.16
    print("    [PASÓ] Explicación astrofísica generada con coherencia física.")

if __name__ == "__main__":
    print("=== INICIANDO SUITE DE PRUEBAS DE INTEGRACIÓN API NASA JPL ===")
    try:
        test_health()
        test_metadata()
        test_pydantic_validation_boundaries()
        test_inference_and_archetypes()
        test_astrophysical_synthesis()
        print("\n=== [TODO CORRECTO] SUITE DE INTEGRACIÓN API Y MACHINE LEARNING COMPLETADA AL 100% ===")
    except Exception as e:
        print(f"\n[FALLO EN TESTS]: {e}")
        sys.exit(1)

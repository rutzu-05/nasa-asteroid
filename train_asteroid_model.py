"""
Entrenamiento y Evaluación del Modelo Random Forest para la Clasificación
y Prospección Minera de Asteroides (NASA JPL Small-Body Database)
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split, cross_val_score

def train_asteroid_ml(csv_path="dataset_asteroides_nasa_jpl.csv"):
    print("=" * 80)
    print("ENTRENAMIENTO DEL MODELO MACHINE LEARNING (NASA JPL ASTEROIDS)")
    print("=" * 80)
    
    # 1. Carga de datos
    df = pd.read_csv(csv_path)
    print(f"--> Dataset cargado: {len(df):,} asteroides.")
    
    # Variables predictoras (Fotometría, Dimensión y Órbita)
    features = [
        'magnitud_absoluta_H',    # Luminosidad intrínseca
        'albedo_geometrico',      # Reflectividad de la superficie
        'diametro_km',            # Tamaño / Volumen
        'semieje_mayor_au',       # Distancia al Sol (AU)
        'excentricidad',          # Elongación de la órbita
        'inclinacion_grados',     # Inclinación orbital
        'distancia_perihelio_au', # Distancia mínima al Sol
        'periodo_rotacion_horas'  # Tiempo de rotación
    ]
    
    target_multi = 'composicion_mineral_dominante'
    
    # Target Binario Especial: Metálico de Alta Ley (Oro, Platino, Fe, Ni) vs Otros
    df['es_metalico'] = (df[target_multi] == 'Metálico (Fe-Ni, Oro, Platino)').astype(int)
    
    X = df[features]
    y_multi = df[target_multi]
    y_bin = df['es_metalico']
    
    print("\n[1/3] Distribución de Clases:")
    for cls_name, cnt in y_multi.value_counts().items():
        print(f"      - {cls_name}: {cnt} asteroides ({cnt/len(df)*100:.1f}%)")
        
    # Partición estratificada (75% entrenamiento / 25% prueba)
    X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(
        X, y_multi, test_size=0.25, random_state=42, stratify=y_multi
    )
    
    # =========================================================================
    # MODELO MULTICLASE: RANDOM FOREST CLASSIFIER
    # =========================================================================
    print("\n[2/3] Entrenando Random Forest Multiclase (n_estimators=300, max_depth=12)...")
    rf_multi = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=4,
        class_weight='balanced', # Ponderación para equilibrar la clase minoritaria basáltica
        oob_score=True,
        random_state=42,
        n_jobs=-1
    )
    rf_multi.fit(X_train_m, y_train_m)
    
    pred_m = rf_multi.predict(X_test_m)
    acc_m = accuracy_score(y_test_m, pred_m)
    oob_m = rf_multi.oob_score_
    
    print(f"      * Exactitud en Conjunto de Prueba (Accuracy): {acc_m*100:.2f}%")
    print(f"      * Validación Out-Of-Bag (OOB Score):          {oob_m*100:.2f}%")
    print("\n      Reporte de Clasificación Multiclase:")
    print(classification_report(y_test_m, pred_m))
    
    # Importancia de variables
    importances = dict(zip(features, [round(float(v), 4) for v in rf_multi.feature_importances_]))
    print("      Importancia de Parámetros Astronómicos (%):")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"        - {feat}: {imp*100:.2f}%")
        
    # =========================================================================
    # MODELO BINARIO: DETECTOR DE ALTA LEY METÁLICA (ORO, PLATINO, HIERRO, NÍQUEL)
    # =========================================================================
    print("\n[3/3] Entrenando Detector Especializado de Asteroides Metálicos...")
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X, y_bin, test_size=0.25, random_state=42, stratify=y_bin
    )
    
    rf_bin = RandomForestClassifier(
        n_estimators=250,
        max_depth=10,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf_bin.fit(X_train_b, y_train_b)
    
    pred_b = rf_bin.predict(X_test_b)
    proba_b = rf_bin.predict_proba(X_test_b)[:, 1]
    acc_b = accuracy_score(y_test_b, pred_b)
    auc_b = roc_auc_score(y_test_b, proba_b)
    
    print(f"      * Exactitud Detección Metálica: {acc_b*100:.2f}%")
    print(f"      * Área Bajo la Curva ROC (AUC): {auc_b*100:.2f}%")
    
    # =========================================================================
    # EXPORTACIÓN DE LOS MODELOS Y METADATOS
    # =========================================================================
    model_multi_file = "rf_asteroides_jpl_multiclase.joblib"
    model_bin_file = "rf_asteroides_jpl_binario.joblib"
    metadata_file = "metadata_asteroides_jpl.json"
    
    joblib.dump(rf_multi, model_multi_file, compress=3)
    joblib.dump(rf_bin, model_bin_file, compress=3)
    
    meta = {
        "dataset": "NASA JPL Small-Body Database (SBDB)",
        "fuente_oficial": "https://ssd.jpl.nasa.gov/tools/sbdb_query.html",
        "algoritmo": "Random Forest Classifier",
        "features": features,
        "clases": list(rf_multi.classes_),
        "metricas": {
            "exactitud_multiclase": round(float(acc_m), 4),
            "oob_score": round(float(oob_m), 4),
            "exactitud_metalica": round(float(acc_b), 4),
            "roc_auc_metalica": round(float(auc_b), 4)
        },
        "importancia_variables": importances,
        "descripcion_familias_mineras": {
            "Metálico (Fe-Ni, Oro, Platino)": {
                "minerales_clave": "Hierro (Fe), Níquel (Ni), Cobalto (Co), Oro (Au), Platino (Pt), Iridio (Ir)",
                "albedo_tipico": "0.10 - 0.25 (Reflectividad metálica en radar)",
                "objetivo_mision": "Minería espacial de metales preciosos e industriales para manufactura orbital (ej. Misión NASA Psyche).",
                "icono": "💎"
            },
            "Carbonáceo (Agua, Compuestos Orgánicos)": {
                "minerales_clave": "Carbono elemental, aminoácidos, arcillas hidratadas, agua ligada (H2O)",
                "albedo_tipico": "0.03 - 0.08 (Muy oscuros, absorben luz)",
                "objetivo_mision": "Extracción de agua para soporte vital y producción de combustible espacial (H2/O2) (ej. Misión OSIRIS-REx a Bennu).",
                "icono": "🌱"
            },
            "Silicatos / Rocoso (Mg-Fe, Piroxeno)": {
                "minerales_clave": "Olivino, Piroxeno, Silicatos de magnesio y hierro",
                "albedo_tipico": "0.15 - 0.25 (Brillo intermedio)",
                "objetivo_mision": "Materiales pétreos y silicio para paneles solares y blindaje contra radiación.",
                "icono": "🪨"
            },
            "Basáltico (Magmático, Rocas Ígneas)": {
                "minerales_clave": "Basalto, plagioclasa cálcica, piroxenos ricos en hierro",
                "albedo_tipico": "0.30 - 0.45 (Muy brillantes)",
                "objetivo_mision": "Corteza de asteroides diferenciados con historia volcánica (tipo asteroide 4-Vesta).",
                "icono": "🌋"
            }
        }
    }
    
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        
    print("\n[OK] Modelos y metadatos exportados exitosamente:")
    print(f"     - {model_multi_file} ({os.path.getsize(model_multi_file)/1024:.1f} KB)")
    print(f"     - {model_bin_file} ({os.path.getsize(model_bin_file)/1024:.1f} KB)")
    print(f"     - {metadata_file}")
    print("=" * 80)
    
    # Prueba de inferencia de 3 asteroides célebres reales de la NASA
    print("\n--> INFERENCIA CON ASTEROIDES REALES CÉLEBRES DE LA NASA:")
    
    test_asteroids = [
        {
            "nombre": "16 Psyche (El asteroide de oro y metales valuado en trillones)",
            "data": {
                'magnitud_absoluta_H': 5.90,
                'albedo_geometrico': 0.120,
                'diametro_km': 226.0,
                'semieje_mayor_au': 2.924,
                'excentricidad': 0.134,
                'inclinacion_grados': 3.09,
                'distancia_perihelio_au': 2.532,
                'periodo_rotacion_horas': 4.196
            }
        },
        {
            "nombre": "101955 Bennu (Destino carbonáceo de la misión OSIRIS-REx)",
            "data": {
                'magnitud_absoluta_H': 20.60,
                'albedo_geometrico': 0.046,
                'diametro_km': 0.492,
                'semieje_mayor_au': 1.126,
                'excentricidad': 0.203,
                'inclinacion_grados': 6.03,
                'distancia_perihelio_au': 0.897,
                'periodo_rotacion_horas': 4.296
            }
        },
        {
            "nombre": "4 Vesta (Cuerpo basáltico con corteza volcánica magmática)",
            "data": {
                'magnitud_absoluta_H': 3.20,
                'albedo_geometrico': 0.423,
                'diametro_km': 525.4,
                'semieje_mayor_au': 2.361,
                'excentricidad': 0.089,
                'inclinacion_grados': 7.14,
                'distancia_perihelio_au': 2.151,
                'periodo_rotacion_horas': 5.342
            }
        }
    ]
    
    for item in test_asteroids:
        row = pd.DataFrame([item["data"]])[features]
        pred = rf_multi.predict(row)[0]
        probas = rf_multi.predict_proba(row)[0]
        prob_dict = {cls: round(float(p) * 100, 1) for cls, p in zip(rf_multi.classes_, probas)}
        print(f"\n  Asteroide: {item['nombre']}")
        print(f"  Entradas: Albedo={item['data']['albedo_geometrico']}, H={item['data']['magnitud_absoluta_H']}, Diametro={item['data']['diametro_km']} km, a={item['data']['semieje_mayor_au']} AU")
        print(f"  Resultado Predicho: {pred} (Confianza: {max(probas)*100:.1f}%)")
        print(f"  Probabilidades: {prob_dict}")
        
    return rf_multi, rf_bin, meta

if __name__ == "__main__":
    train_asteroid_ml()

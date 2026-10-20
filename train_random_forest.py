"""
Script de Limpieza de Datos y Entrenamiento del Modelo Random Forest
para la Predicción de Composición de Cuerpos Celestes (NASA)
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

def clean_data(input_csv="meteorite_landings.csv"):
    print(f"--> Cargando dataset original: {input_csv}...")
    df_raw = pd.read_csv(input_csv)
    print(f"    Dimensiones originales: {df_raw.shape[0]:,} filas, {df_raw.shape[1]} columnas")

    # 1. Limpieza de nulos en variables clave
    df_clean = df_raw.dropna(subset=['mass (g)', 'year', 'reclat', 'reclong']).copy()
    
    # 2. Descartar coordenadas inválidas (0,0 - Null Island)
    df_clean = df_clean[(df_clean['reclat'] != 0) | (df_clean['reclong'] != 0)]
    
    # 3. Filtrar años históricos coherentes
    df_clean = df_clean[(df_clean['year'] >= 800) & (df_clean['year'] <= 2026)]
    
    # 4. Mapeo taxonómico a 4 Familias Geoquímicas Dominantes
    def map_composition(recclass):
        r = str(recclass).strip()
        if 'Iron' in r or 'Pallasite' in r or 'Mesosiderite' in r:
            return 'Metálico (Fe-Ni, Oro, Platino)'
        elif r.startswith(('C', 'CM', 'CO', 'CV', 'CI', 'CR', 'CK', 'CH', 'CB')) and not r.startswith('Chondrite-fusion'):
            return 'Carbonáceo (Carbono, Volátiles)'
        elif r.startswith(('H', 'L', 'LL', 'EH', 'EL', 'R')):
            return 'Silicatos / Rocoso (Mg-Fe)'
        elif any(ach in r for ach in ['Eucrite', 'Diogenite', 'Howardite', 'Ureilite', 'Aubrite', 'Martian', 'Lunar', 'Achondrite']):
            return 'Basáltico / Acondrita (Magmático)'
        return np.nan

    df_clean['Composicion_Dominante'] = df_clean['recclass'].apply(map_composition)
    df_clean = df_clean.dropna(subset=['Composicion_Dominante']).copy()
    
    # 5. Ingeniería de Características (Feature Engineering)
    df_clean['log_mass'] = np.log10(df_clean['mass (g)'] + 1)
    df_clean['fall_num'] = (df_clean['fall'] == 'Fell').astype(int)
    df_clean['abs_lat'] = np.abs(df_clean['reclat'])
    df_clean['is_polar'] = (df_clean['abs_lat'] > 60).astype(int)
    df_clean['Es_Metalico'] = (df_clean['Composicion_Dominante'] == 'Metálico (Fe-Ni, Oro, Platino)').astype(int)

    print(f"--> Datos limpios y validados: {len(df_clean):,} registros.")
    print("    Distribución por familia geoquímica:")
    for comp, count in df_clean['Composicion_Dominante'].value_counts().items():
        print(f"      - {comp}: {count:,} ({count/len(df_clean)*100:.1f}%)")

    # Guardar dataset procesado
    output_clean = "cuerpos_nasa_procesado_ml.csv"
    df_clean.to_csv(output_clean, index=False)
    print(f"--> Dataset limpio guardado en: {output_clean}")
    
    return df_clean

def train_models(df_clean):
    feature_cols = ['log_mass', 'fall_num', 'year', 'reclat', 'reclong', 'abs_lat', 'is_polar']
    
    # =========================================================================
    # MODELO 1: RANDOM FOREST MULTICLASE (4 Clases)
    # =========================================================================
    print("\n--> Entrenando Modelo Multiclase (Random Forest)...")
    
    # Balanceo estratificado equitativo para evitar sesgo hacia Silicatos
    min_samples = df_clean['Composicion_Dominante'].value_counts().min() # ~743
    df_multi_bal = df_clean.groupby('Composicion_Dominante').sample(n=min_samples, random_state=42).copy()
    
    X_multi = df_multi_bal[feature_cols]
    y_multi = df_multi_bal['Composicion_Dominante']
    
    X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(
        X_multi, y_multi, test_size=0.30, random_state=42, stratify=y_multi
    )
    
    rf_multi = RandomForestClassifier(
        n_estimators=250,
        max_depth=12,
        min_samples_split=4,
        oob_score=True,
        random_state=42,
        n_jobs=-1
    )
    rf_multi.fit(X_train_m, y_train_m)
    
    pred_m = rf_multi.predict(X_test_m)
    acc_m = accuracy_score(y_test_m, pred_m)
    oob_m = rf_multi.oob_score_
    
    print(f"    * Exactitud Multiclase (Test): {acc_m:.4f} ({acc_m*100:.2f}%)")
    print(f"    * OOB Score (Validación Interna): {oob_m:.4f} ({oob_m*100:.2f}%)")
    print("\n    Reporte de Clasificación Multiclase:")
    print(classification_report(y_test_m, pred_m))
    
    # Importancia de características
    importances_m = dict(zip(feature_cols, [round(float(v), 4) for v in rf_multi.feature_importances_]))
    print("    Importancia de Variables (Multiclase):")
    for feat, imp in sorted(importances_m.items(), key=lambda x: x[1], reverse=True):
        print(f"      - {feat}: {imp*100:.2f}%")
        
    # =========================================================================
    # MODELO 2: RANDOM FOREST BINARIO (Detección de Metales de Alta Ley / Oro / Fe)
    # =========================================================================
    print("\n--> Entrenando Modelo Especializado Binario (Detección Metálica)...")
    pos_met = df_clean[df_clean['Es_Metalico'] == 1]
    neg_met = df_clean[df_clean['Es_Metalico'] == 0].sample(n=len(pos_met), random_state=42)
    df_bin = pd.concat([pos_met, neg_met]).sample(frac=1, random_state=42)
    
    X_bin = df_bin[feature_cols]
    y_bin = df_bin['Es_Metalico']
    
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X_bin, y_bin, test_size=0.30, random_state=42, stratify=y_bin
    )
    
    rf_bin = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf_bin.fit(X_train_b, y_train_b)
    
    pred_b = rf_bin.predict(X_test_b)
    proba_b = rf_bin.predict_proba(X_test_b)[:, 1]
    acc_b = accuracy_score(y_test_b, pred_b)
    auc_b = roc_auc_score(y_test_b, proba_b)
    
    print(f"    * Exactitud Binaria Metálica: {acc_b:.4f} ({acc_b*100:.2f}%)")
    print(f"    * Área Bajo la Curva ROC (AUC): {auc_b:.4f} ({auc_b*100:.2f}%)")
    
    # =========================================================================
    # SERIALIZACIÓN Y EXPORTACIÓN DE ARTEFACTOS
    # =========================================================================
    model_file_multi = "rf_cuerpos_nasa_multiclase.joblib"
    model_file_bin = "rf_cuerpos_nasa_binario.joblib"
    
    joblib.dump(rf_multi, model_file_multi, compress=3)
    joblib.dump(rf_bin, model_file_bin, compress=3)
    print(f"\n--> Modelos exportados:")
    print(f"    - {model_file_multi} ({os.path.getsize(model_file_multi)/1024:.1f} KB)")
    print(f"    - {model_file_bin} ({os.path.getsize(model_file_bin)/1024:.1f} KB)")
    
    # Metadata para el API
    metadata = {
        "model_name": "NASA Meteorite Composition Random Forest",
        "algorithm": "RandomForestClassifier",
        "feature_columns": feature_cols,
        "classes": list(rf_multi.classes_),
        "metrics": {
            "multiclass_accuracy": round(float(acc_m), 4),
            "multiclass_oob_score": round(float(oob_m), 4),
            "binary_metallic_accuracy": round(float(acc_b), 4),
            "binary_metallic_auc": round(float(auc_b), 4)
        },
        "feature_importances": importances_m,
        "family_descriptions": {
            "Metálico (Fe-Ni, Oro, Platino)": {
                "descripcion": "Cuerpo de alta densidad formado principalmente por aleaciones de Hierro y Níquel (kamacita y taenita), con concentraciones de metales del grupo del platino (Pt, Ir, Os) y oro (Au).",
                "densidad_aprox": "7.0 - 8.0 g/cm3",
                "origen": "Núcleos diferenciados de protoplanetas destruidos en el cinturón de asteroides.",
                "icono": "💎"
            },
            "Carbonáceo (Carbono, Volátiles)": {
                "descripcion": "Meteoritos primitivos ricos en compuestos orgánicos, aminoácidos, agua ligada y minerales hidratados de carbono.",
                "densidad_aprox": "2.2 - 2.9 g/cm3",
                "origen": "Cometas y asteroides exteriores inalterados desde el origen del Sistema Solar.",
                "icono": "🌱"
            },
            "Silicatos / Rocoso (Mg-Fe)": {
                "descripcion": "La familia más abundante (condritas ordinarias). Compuestos de silicatos de magnesio y hierro (olivino y piroxeno) con pequeñas inclusiones metálicas.",
                "densidad_aprox": "3.0 - 3.8 g/cm3",
                "origen": "Corteza y manto de asteroides no fundidos.",
                "icono": "🪨"
            },
            "Basáltico / Acondrita (Magmático)": {
                "descripcion": "Rocas ígneas espaciales originadas por vulcanismo y procesos magmáticos similares a la lava terrestre o corteza lunar y marciana.",
                "densidad_aprox": "2.9 - 3.4 g/cm3",
                "origen": "Corteza de cuerpos masivos como el asteroide 4-Vesta, la Luna y Marte.",
                "icono": "🌋"
            }
        }
    }
    
    metadata_file = "model_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"--> Metadatos guardados en: {metadata_file}")
    
    return rf_multi, rf_bin, metadata

def test_inference(rf_multi, feature_cols):
    print("\n--> Ejecutando prueba de inferencia simulada...")
    
    test_cases = [
        {
            "nombre": "Meteorito Metálico Masivo en Desierto (ej. Hoba / Campo del Cielo)",
            "mass": 650000.0, # 650 kg
            "fall": "Found",
            "year": 1920,
            "reclat": -27.46,
            "reclong": -60.43
        },
        {
            "nombre": "Fragmento Pequeño en Glaciar Antártico (ej. Acondrita / Basáltico)",
            "mass": 18.5, # 18.5 gramos
            "fall": "Found",
            "year": 1988,
            "reclat": -84.00,
            "reclong": 160.00
        },
        {
            "nombre": "Caída Observada Reciente (Condrita de Silicatos)",
            "mass": 1200.0, # 1.2 kg
            "fall": "Fell",
            "year": 2013,
            "reclat": 55.15,
            "reclong": 61.41
        }
    ]
    
    for case in test_cases:
        log_m = np.log10(case["mass"] + 1)
        fall_n = 1 if case["fall"] == "Fell" else 0
        abs_l = abs(case["reclat"])
        is_pol = 1 if abs_l > 60 else 0
        
        row = pd.DataFrame([{
            'log_mass': log_m,
            'fall_num': fall_n,
            'year': case['year'],
            'reclat': case['reclat'],
            'reclong': case['reclong'],
            'abs_lat': abs_l,
            'is_polar': is_pol
        }])[feature_cols]
        
        pred = rf_multi.predict(row)[0]
        probas = rf_multi.predict_proba(row)[0]
        prob_dict = {cls: round(float(p) * 100, 1) for cls, p in zip(rf_multi.classes_, probas)}
        
        print(f"\n  Caso: {case['nombre']}")
        print(f"  Inputs: Masa={case['mass']}g, Tipo={case['fall']}, Año={case['year']}, Lat={case['reclat']}, Long={case['reclong']}")
        print(f"  -> Prediccion: {pred} (Confianza: {max(probas)*100:.1f}%)")
        print(f"     Desglose: {prob_dict}")

if __name__ == "__main__":
    df_clean = clean_data("meteorite_landings.csv")
    rf_multi, rf_bin, metadata = train_models(df_clean)
    test_inference(rf_multi, metadata["feature_columns"])
    print("\n[OK] Preparacion del Modelo de Machine Learning completada exitosamente.")

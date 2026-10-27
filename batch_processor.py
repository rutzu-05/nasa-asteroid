"""
Procesador de Datos Masivos (Excel / CSV) para Asteroides NASA JPL
Permite la ingestión de datasets tabulares, normalización heurística de columnas,
inferencia vectorial con Random Forest y generación de reportes analíticos para ISRU.
"""

import io
import re
import unicodedata
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# Mapeo de alias para columnas esperadas (soporta español, inglés y abreviaturas técnicas JPL)
COLUMN_ALIASES = {
    'magnitud_absoluta_H': [
        'magnitud_absoluta_h', 'magnitud_absoluta', 'magnitud_h', 'magnitud', 'h',
        'absolute_magnitude', 'abs_mag', 'mag_h', 'h_mag'
    ],
    'albedo_geometrico': [
        'albedo_geometrico', 'albedo', 'geometric_albedo', 'pv', 'p_v', 'visual_albedo', 'albedo_v'
    ],
    'diametro_km': [
        'diametro_km', 'diametro', 'diameter', 'diameter_km', 'diam', 'diam_km'
    ],
    'semieje_mayor_au': [
        'semieje_mayor_au', 'semieje_mayor', 'semieje', 'a',
        'semi_major_axis', 'semi_major_axis_au', 'sma', 'semi_major'
    ],
    'excentricidad': [
        'excentricidad', 'e', 'eccentricity', 'ecc', 'excentricite'
    ],
    'inclinacion_grados': [
        'inclinacion_grados', 'inclinacion', 'i', 'inclination',
        'inclination_deg', 'inc', 'incl'
    ],
    'distancia_perihelio_au': [
        'distancia_perihelio_au', 'distancia_perihelio', 'perihelio', 'q',
        'perihelion_distance', 'perihelion_dist', 'perihelion', 'perihelio_au'
    ],
    'periodo_rotacion_horas': [
        'periodo_rotacion_horas', 'periodo_rotacion', 'rot_per', 'rot_period',
        'rotation_period', 'periodo', 'rot', 'rotacion', 'rot_hours'
    ],
    'nombre_asteroide': [
        'nombre_asteroide', 'nombre', 'name', 'full_name', 'asteroid_name',
        'designation', 'des', 'id', 'asteroide', 'object', 'identificador'
    ]
}

REQUIRED_FEATURES = [
    'magnitud_absoluta_H',
    'albedo_geometrico',
    'diametro_km',
    'semieje_mayor_au',
    'excentricidad',
    'inclinacion_grados',
    'distancia_perihelio_au'
]

ALL_FEATURES = REQUIRED_FEATURES + ['periodo_rotacion_horas']

def _normalize_header(header: str) -> str:
    """Normaliza un texto para matching: minúsculas, sin acentos ni caracteres especiales."""
    text = str(header).strip().lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text

def resolve_column_mapping(df_columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """
    Identifica qué columnas del dataframe corresponden a cada feature estándar.
    Retorna (mapeo {estandar: col_original}, faltantes).
    """
    mapping = {}
    normalized_cols = {col: _normalize_header(col) for col in df_columns}
    
    for std_name, aliases in COLUMN_ALIASES.items():
        found = None
        # Búsqueda exacta primero
        for orig_col, norm_col in normalized_cols.items():
            for alias in aliases:
                norm_alias = _normalize_header(alias)
                if norm_col == norm_alias:
                    found = orig_col
                    break
            if found:
                break
        
        # Si no hubo coincidencia exacta, probar contención para nombres largos
        if not found and std_name not in ['excentricidad', 'inclinacion_grados']:
            for orig_col, norm_col in normalized_cols.items():
                if norm_col in [_normalize_header(a) for a in aliases]:
                    found = orig_col
                    break

        if found:
            mapping[std_name] = found

    missing_required = [f for f in REQUIRED_FEATURES if f not in mapping]
    return mapping, missing_required

def read_uploaded_file(contents: bytes, filename: str) -> pd.DataFrame:
    """
    Carga un archivo en memoria (.csv, .xlsx, .xls) tolerando distintos delimitadores y codificaciones.
    """
    fname = filename.lower()
    
    if fname.endswith(('.xlsx', '.xls')):
        try:
            return pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise ValueError(f"Error al leer archivo Excel ({filename}): {str(e)}")
            
    # Asumir CSV o texto plano delimitado
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    df = None
    last_err = None

    for enc in encodings:
        try:
            # Intento de detección automática de separador (coma, punto y coma, tab)
            df = pd.read_csv(io.BytesIO(contents), sep=None, engine='python', encoding=enc)
            if df is not None and len(df.columns) > 1:
                break
        except Exception as e:
            last_err = e
            continue

    if df is None or len(df.columns) <= 1:
        # Fallback a comas explícitas
        try:
            df = pd.read_csv(io.BytesIO(contents), sep=',', encoding='utf-8')
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(contents), sep=';', encoding='latin1')
            except Exception as e:
                raise ValueError(f"No se pudo parsear el archivo CSV: {str(last_err or e)}")

    return df

def get_orbital_zone(a: float, q: float) -> str:
    """Determina la zona orbital y accesibilidad cinemática."""
    if q < 1.3:
        return "NEO (Cercano a la Tierra) - Máxima Accesibilidad"
    elif 2.0 <= a <= 3.3:
        return "Cinturón Principal de Asteroides"
    elif 5.0 <= a <= 5.5:
        return "Asteroide Troyano (Júpiter)"
    elif a > 5.5:
        return "Centauro / Objeto Transneptuniano"
    else:
        return "Órbita Intermedia"

def get_mining_profile(pred_class: str) -> Dict[str, str]:
    """Genera perfil minero simplificado para reporte."""
    if pred_class == "Metálico (Fe-Ni, Oro, Platino)":
        return {
            "potencial_resumen": "Máxima Prioridad Económica (Au, Pt, Ni, Fe)",
            "valor_estrategico": "Metales Preciosos & Siderúrgicos",
            "clase_corta": "Metálico",
            "badge_color": "metal"
        }
    elif pred_class == "Carbonáceo (Agua, Compuestos Orgánicos)":
        return {
            "potencial_resumen": "Estratégico para Repostaje & H2O",
            "valor_estrategico": "Agua, Hidrógeno Líquido & Volátiles",
            "clase_corta": "Carbonáceo",
            "badge_color": "carbon"
        }
    elif pred_class == "Silicatos / Rocoso (Mg-Fe, Piroxeno)":
        return {
            "potencial_resumen": "Manufactura Orbital (Silicio, Piroxeno)",
            "valor_estrategico": "Materiales Estructurales & Silicio",
            "clase_corta": "Silicatos",
            "badge_color": "silicate"
        }
    else: # Basáltico
        return {
            "potencial_resumen": "Valor Geológico & Blindaje",
            "valor_estrategico": "Corteza Ígnea Diferenciada",
            "clase_corta": "Basáltico",
            "badge_color": "basalt"
        }

def process_batch_dataframe(
    raw_df: pd.DataFrame,
    rf_multi: Any,
    rf_bin: Any,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Procesa masivamente el DataFrame: normaliza columnas, ejecuta inferencia con Random Forest,
    y computa indicadores ejecutivos de prospección.
    """
    if raw_df.empty:
        raise ValueError("El archivo subido no contiene registros.")

    mapping, missing = resolve_column_mapping(raw_df.columns.tolist())
    if missing:
        raise ValueError(
            f"Faltan las siguientes columnas obligatorias: {', '.join(missing)}. "
            f"Columnas detectadas: {', '.join(raw_df.columns.tolist())}"
        )

    # Construir DataFrame estandarizado
    standard_df = pd.DataFrame()
    for std_name, orig_col in mapping.items():
        standard_df[std_name] = raw_df[orig_col]

    # Nombre opcional
    if 'nombre_asteroide' not in standard_df.columns:
        standard_df['nombre_asteroide'] = [f"Asteroide #{i+1}" for i in range(len(standard_df))]
    else:
        standard_df['nombre_asteroide'] = standard_df['nombre_asteroide'].fillna(
            pd.Series([f"Asteroide #{i+1}" for i in range(len(standard_df))])
        ).astype(str)

    # Período de rotación opcional (default 6.8h)
    if 'periodo_rotacion_horas' not in standard_df.columns:
        standard_df['periodo_rotacion_horas'] = 6.8
    else:
        standard_df['periodo_rotacion_horas'] = pd.to_numeric(
            standard_df['periodo_rotacion_horas'], errors='coerce'
        ).fillna(6.8)

    # Conversión numérica de variables obligatorias
    for feat in REQUIRED_FEATURES:
        standard_df[feat] = pd.to_numeric(standard_df[feat], errors='coerce')

    # Identificar filas válidas vs inválidas
    # Criterios: H entre -5 y 35, albedo > 0, diametro > 0, a > 0, e >= 0, i >= 0, q > 0
    valid_mask = (
        standard_df['magnitud_absoluta_H'].between(-5.0, 35.0) &
        standard_df['albedo_geometrico'].between(0.0001, 1.0) &
        (standard_df['diametro_km'] > 0.0) &
        (standard_df['semieje_mayor_au'] > 0.0) &
        (standard_df['excentricidad'] >= 0.0) &
        (standard_df['inclinacion_grados'] >= 0.0) &
        (standard_df['distancia_perihelio_au'] > 0.0)
    )

    total_rows = len(standard_df)
    valid_df = standard_df[valid_mask].copy()
    invalid_count = total_rows - len(valid_df)

    if valid_df.empty:
        raise ValueError("Ninguna de las filas cumple con los rangos físicos válidos de asteroides.")

    # Inferencia vectorial
    feature_cols = metadata.get("features", ALL_FEATURES)
    X = valid_df[feature_cols]

    preds_multi = rf_multi.predict(X)
    probas_multi = rf_multi.predict_proba(X)
    classes_multi = list(rf_multi.classes_)

    bin_probas = rf_bin.predict_proba(X)[:, 1] if rf_bin is not None else np.zeros(len(valid_df))

    # Incorporar resultados a valid_df
    confianzas = np.max(probas_multi, axis=1) * 100.0
    es_metalico_detector = (bin_probas >= 0.40) | (preds_multi == "Metálico (Fe-Ni, Oro, Platino)")

    valid_df['prediccion'] = preds_multi
    valid_df['confianza'] = np.round(confianzas, 2)
    valid_df['es_metalico'] = es_metalico_detector
    valid_df['probabilidad_metalica'] = np.round(bin_probas * 100.0, 2)

    # Zonas orbitales y perfiles
    zonas = [get_orbital_zone(a, q) for a, q in zip(valid_df['semieje_mayor_au'], valid_df['distancia_perihelio_au'])]
    valid_df['zona_orbital'] = zonas

    perfiles = [get_mining_profile(p) for p in preds_multi]
    valid_df['potencial_minero'] = [p['potencial_resumen'] for p in perfiles]
    valid_df['valor_estrategico'] = [p['valor_estrategico'] for p in perfiles]
    valid_df['clase_corta'] = [p['clase_corta'] for p in perfiles]
    valid_df['badge_color'] = [p['badge_color'] for p in perfiles]

    # Probabilidades detalladas
    prob_cols = {}
    for i, cls in enumerate(classes_multi):
        prob_cols[f"prob_{cls}"] = np.round(probas_multi[:, i] * 100.0, 2)

    # Métricas agregadas de reporte
    composition_counts = valid_df['prediccion'].value_counts().to_dict()
    composition_percentages = {
        cls: round((cnt / len(valid_df)) * 100.0, 1)
        for cls, cnt in composition_counts.items()
    }

    metallic_count = int(valid_df['es_metalico'].sum())
    water_count = int((valid_df['prediccion'] == "Carbonáceo (Agua, Compuestos Orgánicos)").sum())
    neo_count = int(valid_df['zona_orbital'].str.startswith("NEO").sum())

    # Ranking de objetivos prioritarios para minería:
    # Criterio: Cuerpos metálicos o carbonáceos de alto valor, ordenados por probabilidad metálica y accesibilidad
    def priority_score(row):
        score = 0.0
        if row['es_metalico']:
            score += 100.0 + row['probabilidad_metalica']
        elif row['prediccion'] == "Carbonáceo (Agua, Compuestos Orgánicos)":
            score += 60.0 + row['confianza'] * 0.4
        elif row['prediccion'] == "Silicatos / Rocoso (Mg-Fe, Piroxeno)":
            score += 30.0
        # Bono de accesibilidad NEO (menor delta-V)
        if "NEO" in row['zona_orbital']:
            score += 25.0
        return score

    valid_df['priority_score'] = valid_df.apply(priority_score, axis=1)
    top_targets_df = valid_df.sort_values(by=['priority_score', 'diametro_km'], ascending=[False, False]).head(5)

    top_targets = []
    for _, row in top_targets_df.iterrows():
        top_targets.append({
            "nombre": str(row['nombre_asteroide']),
            "prediccion": str(row['prediccion']),
            "clase_corta": str(row['clase_corta']),
            "confianza": float(row['confianza']),
            "es_metalico": bool(row['es_metalico']),
            "probabilidad_metalica": float(row['probabilidad_metalica']),
            "diametro_km": float(row['diametro_km']),
            "zona_orbital": str(row['zona_orbital']),
            "potencial_resumen": str(row['potencial_minero']),
            "valor_estrategico": str(row['valor_estrategico']),
            "badge_color": str(row['badge_color'])
        })

    # Lista de todos los registros procesados para tabla
    records = []
    for _, row in valid_df.iterrows():
        record = {
            "nombre_asteroide": str(row['nombre_asteroide']),
            "magnitud_absoluta_H": float(row['magnitud_absoluta_H']),
            "albedo_geometrico": float(row['albedo_geometrico']),
            "diametro_km": float(row['diametro_km']),
            "semieje_mayor_au": float(row['semieje_mayor_au']),
            "excentricidad": float(row['excentricidad']),
            "inclinacion_grados": float(row['inclinacion_grados']),
            "distancia_perihelio_au": float(row['distancia_perihelio_au']),
            "periodo_rotacion_horas": float(row['periodo_rotacion_horas']),
            "prediccion": str(row['prediccion']),
            "clase_corta": str(row['clase_corta']),
            "confianza": float(row['confianza']),
            "es_metalico": bool(row['es_metalico']),
            "probabilidad_metalica": float(row['probabilidad_metalica']),
            "zona_orbital": str(row['zona_orbital']),
            "potencial_minero": str(row['potencial_minero']),
            "badge_color": str(row['badge_color'])
        }
        records.append(record)

    summary = {
        "total_registros": total_rows,
        "registros_validos": len(valid_df),
        "registros_invalidos": invalid_count,
        "conteo_metalicos": metallic_count,
        "porcentaje_metalicos": round((metallic_count / len(valid_df)) * 100.0, 1),
        "conteo_recursos_hidricos": water_count,
        "porcentaje_recursos_hidricos": round((water_count / len(valid_df)) * 100.0, 1),
        "conteo_neos": neo_count,
        "porcentaje_neos": round((neo_count / len(valid_df)) * 100.0, 1),
        "distribucion_composicion": composition_counts,
        "porcentajes_composicion": composition_percentages,
        "diametro_promedio_km": round(float(valid_df['diametro_km'].mean()), 2),
        "diametro_maximo_km": round(float(valid_df['diametro_km'].max()), 2),
        "albedo_promedio": round(float(valid_df['albedo_geometrico'].mean()), 3)
    }

    return {
        "status": "success",
        "summary": summary,
        "top_targets": top_targets,
        "records": records,
        "_valid_df": valid_df # DataFrame para exportar fácilmente a CSV
    }

def generate_enriched_csv(valid_df: pd.DataFrame) -> str:
    """
    Genera el contenido CSV del reporte enriquecido con todas las predicciones de ML.
    """
    export_cols = [
        'nombre_asteroide',
        'prediccion',
        'confianza',
        'es_metalico',
        'probabilidad_metalica',
        'potencial_minero',
        'zona_orbital',
        'albedo_geometrico',
        'diametro_km',
        'magnitud_absoluta_H',
        'semieje_mayor_au',
        'excentricidad',
        'inclinacion_grados',
        'distancia_perihelio_au',
        'periodo_rotacion_horas'
    ]
    # Filtrar solo columnas existentes
    cols = [c for c in export_cols if c in valid_df.columns]
    out_df = valid_df[cols].copy()
    
    # Renombrar columnas para reporte legible
    out_df.rename(columns={
        'nombre_asteroide': 'Asteroide',
        'prediccion': 'Composicion_Predicha',
        'confianza': 'Confianza_Pct',
        'es_metalico': 'Es_Metalico',
        'probabilidad_metalica': 'Probabilidad_Metalica_Pct',
        'potencial_minero': 'Potencial_Minero_ISRU',
        'zona_orbital': 'Zona_Orbital',
        'albedo_geometrico': 'Albedo_Visual_pv',
        'diametro_km': 'Diametro_km',
        'magnitud_absoluta_H': 'Magnitud_H',
        'semieje_mayor_au': 'Semieje_Mayor_AU',
        'excentricidad': 'Excentricidad',
        'inclinacion_grados': 'Inclinacion_deg',
        'distancia_perihelio_au': 'Perihelio_AU',
        'periodo_rotacion_horas': 'Rotacion_horas'
    }, inplace=True)

    buffer = io.StringIO()
    out_df.to_csv(buffer, index=False, encoding='utf-8')
    return buffer.getvalue()

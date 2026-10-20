"""
Extracción y Limpieza Oficial del Dataset de Asteroides de la NASA (JPL SBDB)
Herramienta: NASA JPL Small-Body Database Query API (https://ssd-api.jpl.nasa.gov/sbdb_query.api)
Objetivo: Clasificación Espectral y Mineralógica para Minería y Exploración Espacial.
"""

import os
import requests
import numpy as np
import pandas as pd

def extract_jpl_asteroids():
    print("=" * 80)
    print("EXTRACCIÓN DE DATOS DESDE NASA JPL SMALL-BODY DATABASE (SBDB)")
    print("=" * 80)
    
    url = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
    params = {
        'fields': 'full_name,H,diameter,albedo,rot_per,a,e,i,q,spec_B,spec_T,class',
        'sb-kind': 'a',
        'sb-ns': 'n',       # Asteroides numerados con observaciones fotométricas y espectrales
        'limit': '150000'
    }
    
    print("\n[1/4] Consultando API de la NASA (JPL Solar System Dynamics)...")
    response = requests.get(url, params=params, timeout=90)
    
    if response.status_code != 200:
        raise Exception(f"Error al conectar con la API de la NASA: {response.status_code}")
        
    json_data = response.json()
    fields = json_data.get('fields', [])
    records = json_data.get('data', [])
    print(f"      Total de cuerpos recuperados: {len(records):,} asteroides.")
    
    df_raw = pd.DataFrame(records, columns=fields)
    
    print("\n[2/4] Filtrando asteroides con espectroscopía y parámetros físicos...")
    # Filtrar solo aquellos que tienen clasificación espectral documentada (Bus-DeMeo o Tholen)
    has_spec = df_raw[df_raw['spec_B'].notna() | df_raw['spec_T'].notna()].copy()
    print(f"      Asteroides con taxonomía espectral validada: {len(has_spec):,}")
    
    # Mapeo a Familias Mineralógicas para Minería Espacial y Misiones Exploratorias
    def map_asteroid_family(row):
        spec = str(row['spec_B']).strip() if pd.notna(row['spec_B']) else str(row['spec_T']).strip()
        albedo = float(row['albedo']) if pd.notna(row['albedo']) else np.nan
        
        # 1. Metálico (Complejo X/M - Hierro, Níquel, Cobalto, Oro, Platino)
        if spec in ['M', 'Xe', 'Xk', 'Xc', 'X'] or 'M' in spec:
            if pd.notna(albedo) and albedo < 0.075 and spec in ['P', 'D']:
                return 'Carbonáceo (Agua, Compuestos Orgánicos)'
            return 'Metálico (Fe-Ni, Oro, Platino)'
        
        # 2. Basáltico / Magmático (Clase V - Vulcanismo y corteza magmática como 4-Vesta)
        elif spec.startswith('V'):
            return 'Basáltico (Magmático, Rocas Ígneas)'
            
        # 3. Silicatos / Rocoso (Complejo S, Q, K, A, L - Olivino y Piroxeno)
        elif spec.startswith(('S', 'Q', 'K', 'A', 'L')):
            return 'Silicatos / Rocoso (Mg-Fe, Piroxeno)'
            
        # 4. Carbonáceo / Primitivo / Volátiles (Complejo C, B, D, P, F, G, T - Agua y C)
        elif spec.startswith(('C', 'B', 'D', 'P', 'F', 'G', 'T')):
            return 'Carbonáceo (Agua, Compuestos Orgánicos)'
            
        return 'Indeterminado'

    has_spec['Familia_Minera'] = has_spec.apply(map_asteroid_family, axis=1)
    df_clean = has_spec[has_spec['Familia_Minera'] != 'Indeterminado'].copy()
    
    # Conversión y limpieza de tipos numéricos
    num_cols = ['H', 'diameter', 'albedo', 'rot_per', 'a', 'e', 'i', 'q']
    for col in num_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
    print("\n[3/4] Limpieza de valores nulos e imputación física:")
    # Filtrar asteroides que tengan al menos Albedo y Magnitud H
    df_clean = df_clean.dropna(subset=['H', 'a', 'e', 'i', 'q', 'albedo']).copy()
    
    # Si falta el diámetro, se calcula usando la ley fotométrica estándar de asteroides:
    # D = (1329 / sqrt(albedo)) * 10^(-0.2 * H)
    missing_diam = df_clean['diameter'].isna()
    if missing_diam.sum() > 0:
        calculated_diam = (1329.0 / np.sqrt(df_clean.loc[missing_diam, 'albedo'])) * (10.0 ** (-0.2 * df_clean.loc[missing_diam, 'H']))
        df_clean.loc[missing_diam, 'diameter'] = calculated_diam
        print(f"      Calculados {missing_diam.sum()} diámetros faltantes mediante ley fotométrica estándar.")
        
    # Imputar rotación con la mediana astronómica (aprox. 6.8 horas)
    rot_median = df_clean['rot_per'].median()
    df_clean['rot_per'] = df_clean['rot_per'].fillna(rot_median)
    
    # Renombrar columnas para mayor claridad científica
    df_clean = df_clean.rename(columns={
        'full_name': 'nombre_asteroide',
        'H': 'magnitud_absoluta_H',
        'diameter': 'diametro_km',
        'albedo': 'albedo_geometrico',
        'rot_per': 'periodo_rotacion_horas',
        'a': 'semieje_mayor_au',
        'e': 'excentricidad',
        'i': 'inclinacion_grados',
        'q': 'distancia_perihelio_au',
        'class': 'clase_orbital',
        'spec_B': 'espectro_Bus_DeMeo',
        'spec_T': 'espectro_Tholen',
        'Familia_Minera': 'composicion_mineral_dominante'
    })
    
    print("\n[4/4] Distribución del Dataset Final Extraído de NASA JPL:")
    for fam, cnt in df_clean['composicion_mineral_dominante'].value_counts().items():
        print(f"      * {fam}: {cnt:,} asteroides ({cnt/len(df_clean)*100:.1f}%)")
        
    out_file = "dataset_asteroides_nasa_jpl.csv"
    df_clean.to_csv(out_file, index=False, encoding='utf-8')
    print(f"\n[OK] Dataset guardado exitosamente en: {out_file}")
    print(f"     Total de asteroides catalogados: {len(df_clean):,}")
    print("=" * 80)
    return df_clean

if __name__ == "__main__":
    extract_jpl_asteroids()

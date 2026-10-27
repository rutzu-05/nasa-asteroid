import os
import sys
import io

# Asegurar que el directorio raíz del proyecto esté en el sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_template_download():
    response = client.get("/api/v1/template/csv")
    assert response.status_code == 200
    assert "nombre_asteroide" in response.text
    assert "16 Psyche" in response.text

def test_batch_predict_csv():
    with open("prueba_asteroides_entrada.csv", "rb") as f:
        response = client.post(
            "/api/v1/predict/batch",
            files={"file": ("prueba_asteroides_entrada.csv", f, "text/csv")}
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert summary["total_registros"] == 16
    assert summary["registros_validos"] == 16
    assert summary["conteo_metalicos"] > 0
    assert len(data["records"]) == 16
    assert len(data["top_targets"]) <= 5
    print("\n[SUCCESS] Batch Predict OK:", summary)

def test_batch_export_csv():
    with open("prueba_asteroides_entrada.csv", "rb") as f:
        response = client.post(
            "/api/v1/predict/batch/export",
            files={"file": ("prueba_asteroides_entrada.csv", f, "text/csv")}
        )
    assert response.status_code == 200, response.text
    assert "text/csv" in response.headers.get("content-type", "")
    lines = response.text.splitlines()
    assert len(lines) == 17  # 1 header + 16 rows
    assert "Composicion_Predicha" in lines[0]
    print("\n[SUCCESS] Batch Export CSV OK:", lines[0])

if __name__ == "__main__":
    test_template_download()
    test_batch_predict_csv()
    test_batch_export_csv()
    print("\nTODOS LOS TESTS DE PROCESAMIENTO MASIVO PASARON EXITOSAMENTE!")

"""
API e frontend simples para previsão de HH em produção.
Carrega o modelo 5 features conforme config (versionamento MLOps).
Uso: python app.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml
import joblib
from flask import Flask, request, jsonify, send_from_directory

BASE = Path(__file__).resolve().parent
APP_DIR = BASE / "app"
VARIANT = "5features"
FEATURES = ["acft", "sum_daily_hours", "Cycles", "sum_uti_mensal", "age_fleet"]

app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")

_model = None
_scaler_x = None
_scaler_y = None
_loaded_version = None


def _resolve_models_dir():
    """Define pasta do modelo: por versão (registry) ou flat (retrocompat)."""
    config_path = BASE / "config.yaml"
    if not config_path.exists():
        return BASE / "models"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    mlops = config.get("mlops", {})
    prod_ver = mlops.get("production_version", "latest")
    registry_path = BASE / mlops.get("registry_file", "models/registry.json")

    if prod_ver != "latest" and prod_ver:
        version_dir = BASE / "models" / prod_ver
        if version_dir.exists():
            return version_dir

    if registry_path.exists():
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            versions = registry.get("versions", [])
            if versions:
                last = versions[-1]
                path_rel = last.get("path", "")
                version_dir = (BASE / path_rel).resolve()
                if version_dir.exists():
                    return version_dir
        except (json.JSONDecodeError, KeyError):
            pass

    # Retrocompat: modelo na pasta models/ (sem subpasta de versão)
    return BASE / "models"


def load_artifacts():
    global _model, _scaler_x, _scaler_y, _loaded_version
    if _model is not None:
        return
    models_dir = _resolve_models_dir()
    model_path = models_dir / f"model_hh_semanal_{VARIANT}.keras"
    scaler_x_path = models_dir / f"scaler_X_{VARIANT}.joblib"
    scaler_y_path = models_dir / f"scaler_y_{VARIANT}.joblib"
    if not model_path.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {model_path}. Rode: python train.py [--version 1.0.0]"
        )
    _model = tf.keras.models.load_model(model_path)
    _scaler_x = joblib.load(scaler_x_path)
    _scaler_y = joblib.load(scaler_y_path)
    try:
        _loaded_version = str(models_dir.relative_to(BASE)) if BASE in models_dir.parents else str(models_dir)
    except ValueError:
        _loaded_version = str(models_dir)


@app.route("/")
def index():
    """Serve a página do formulário."""
    return send_from_directory(APP_DIR, "index.html")


@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Recebe JSON com as 5 features, retorna HH previsto.
    Exemplo: {"acft": 260, "sum_daily_hours": 2200, "Cycles": 1500, "sum_uti_mensal": 9000, "age_fleet": 1e7}
    """
    try:
        load_artifacts()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500

    data = request.get_json(force=True, silent=True) or {}
    missing = [f for f in FEATURES if f not in data]
    if missing:
        return jsonify({"error": f"Features faltando: {missing}"}), 400

    try:
        X = pd.DataFrame([[float(data[f]) for f in FEATURES]], columns=FEATURES)
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Valores inválidos: {e}"}), 400

    X_scaled = _scaler_x.transform(X)
    y_scaled = _model.predict(X_scaled, verbose=0)
    HH = float(_scaler_y.inverse_transform(y_scaled)[0, 0])

    return jsonify({"HH": round(HH, 4), "features_used": FEATURES})


@app.route("/api/info")
def info():
    """Informações do modelo (features, variante, versão carregada)."""
    return jsonify({
        "variant": VARIANT,
        "features": FEATURES,
        "model_version": _loaded_version,
        "description": "Previsão de HH (Homem-Hora) semanal - itens não programados B737NG",
    })


if __name__ == "__main__":
    try:
        load_artifacts()
        print(f"Modelo carregado (versão: {_loaded_version or 'models'}).")
    except FileNotFoundError as e:
        print("Aviso:", e)
        print("Rode: python train.py [--version 1.0.0]")
    print("Acesse: http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)

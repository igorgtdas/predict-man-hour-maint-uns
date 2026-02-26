"""
Script de treino do modelo de previsão de HH.
Carrega dataset, treina duas variantes (4 e 5 features), salva modelo, scalers e metadados.
Uso: python train.py [--config config.yaml] [--dataset data/processed/dataset_uti_vs_hh_semanal.csv]
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config não encontrado: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_model(input_dim: int, units: list[int] = (100, 100)):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Dense(units[0], activation="relu"),
        tf.keras.layers.Dense(units[1], activation="relu"),
        tf.keras.layers.Dense(1, activation="linear"),
    ])
    model.compile(optimizer="Adam", loss="mean_squared_error")
    return model


def main():
    parser = argparse.ArgumentParser(description="Treino do modelo HH - TCC")
    parser.add_argument("--config", default="config.yaml", help="Caminho para config.yaml")
    parser.add_argument("--dataset", default=None, help="Caminho para dataset_uti_vs_hh_semanal.csv")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
    parser.add_argument("--version", default=None, help="Versão do modelo (ex: 1.0.0). Se omitido, usa data YYYYMMDD.")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    config = load_config(base / args.config)
    paths_cfg = config["paths"]
    train_cfg = config.get("training", {})
    proj = Path(paths_cfg.get("project_root", "."))
    if not proj.is_absolute():
        proj = base / proj
    proj = proj.resolve()

    dataset_path = args.dataset or (proj / paths_cfg["dataset_semanal"])
    dataset_path = Path(dataset_path)
    if not dataset_path.is_absolute():
        dataset_path = proj / dataset_path
    if not dataset_path.exists():
        print(f"Dataset não encontrado: {dataset_path}")
        sys.exit(1)

    models_base = proj / paths_cfg["models_dir"]
    models_base.mkdir(parents=True, exist_ok=True)

    # Versionamento: pasta por versão (ex: models/1.0.0/ ou models/20240226/)
    version = args.version or datetime.now().strftime("%Y%m%d")
    models_dir = models_base / version
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"Versão: {version} -> {models_dir}")

    features_4 = train_cfg.get("features_4", ["acft", "sum_daily_hours", "Cycles", "sum_uti_mensal"])
    features_5 = train_cfg.get("features_5", ["acft", "sum_daily_hours", "Cycles", "sum_uti_mensal", "age_fleet"])
    target = train_cfg.get("target", "HH")
    test_size = train_cfg.get("test_size", 0.25)
    val_split = train_cfg.get("validation_split", 0.2)
    epochs = train_cfg.get("epochs", 10)
    batch_size = train_cfg.get("batch_size", 50)
    units = train_cfg.get("units", [100, 100])
    random_state = args.seed

    np.random.seed(random_state)
    tf.random.set_seed(random_state)

    data = pd.read_csv(dataset_path, encoding="ISO-8859-1")
    data["date"] = pd.to_datetime(data["date"])

    metadata = {
        "dataset": str(dataset_path),
        "trained_at": datetime.now().isoformat(),
        "random_state": random_state,
        "test_size": test_size,
        "validation_split": val_split,
        "epochs": epochs,
        "batch_size": batch_size,
        "models": {},
    }

    for variant_name, features in [("4features", features_4), ("5features", features_5)]:
        for f in features:
            if f not in data.columns:
                print(f"Coluna ausente no dataset: {f}")
                sys.exit(1)
        X = data[features]
        y = data[target].values.reshape(-1, 1)

        scaler_X = MinMaxScaler()
        scaler_y = MinMaxScaler()
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_scaled, test_size=test_size, random_state=random_state
        )

        model = build_model(input_dim=len(features), units=units)
        hist = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=val_split,
            verbose=1,
        )

        y_pred_scaled = model.predict(X_test)
        y_pred = scaler_y.inverse_transform(y_pred_scaled)
        y_test_orig = scaler_y.inverse_transform(y_test)

        mae = mean_absolute_error(y_test_orig, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred))
        r2 = r2_score(y_test_orig, y_pred)
        n, k = len(X_test), len(features)
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - k - 1) if n > k + 1 else r2

        model_path = models_dir / f"model_hh_semanal_{variant_name}.keras"
        scaler_x_path = models_dir / f"scaler_X_{variant_name}.joblib"
        scaler_y_path = models_dir / f"scaler_y_{variant_name}.joblib"

        model.save(model_path)
        joblib.dump(scaler_X, scaler_x_path)
        joblib.dump(scaler_y, scaler_y_path)

        metadata["models"][variant_name] = {
            "features": features,
            "model_path": str(model_path),
            "scaler_X_path": str(scaler_x_path),
            "scaler_y_path": str(scaler_y_path),
            "MAE": float(mae),
            "RMSE": float(rmse),
            "R2": float(r2),
            "Adj_R2": float(adj_r2),
        }
        print(f"\n{variant_name}: MAE={mae:.3f}, RMSE={rmse:.3f}, R2={r2:.4f} -> {model_path}")

    meta_path = models_dir / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadados salvos: {meta_path}")

    # Registry MLOps: registrar esta versão para rastreio e "latest"
    mlops_cfg = config.get("mlops", {})
    registry_path = proj / mlops_cfg.get("registry_file", "models/registry.json")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = {"versions": []}
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    try:
        path_rel = str(models_dir.relative_to(proj))
    except ValueError:
        path_rel = str(models_dir)
    entry = {
        "version": version,
        "trained_at": metadata["trained_at"],
        "path": path_rel,
        "dataset": str(dataset_path.name),
        "metrics_5features": metadata["models"].get("5features", {}),
        "metrics_4features": metadata["models"].get("4features", {}),
    }
    registry["versions"] = registry.get("versions", []) + [entry]
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    print(f"Registry atualizado: {registry_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

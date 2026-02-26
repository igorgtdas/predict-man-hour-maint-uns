"""
Script principal da pipeline de dados.
Lê config.yaml, executa ingestão → processamento HH → utilização → join → validação → salva dataset.
Uso: python run_data_pipeline.py [--config caminho/config.yaml]
"""
import argparse
import sys
from pathlib import Path

import yaml

# Permite rodar a partir da pasta TCC
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.ingest_unscheduled import run as ingest_unscheduled
from pipeline.process_unscheduled_hh import run as process_unscheduled_hh
from pipeline.process_utilization import run as process_utilization
from pipeline.build_dataset import run as build_dataset
from pipeline.validate_dataset import run as validate_dataset


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config não encontrado: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(root: Path, value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = root / p
    return p.resolve()


def main():
    parser = argparse.ArgumentParser(description="Pipeline de dados - TCC Previsão HH")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Caminho para config.yaml",
    )
    parser.add_argument(
        "--skip-utilization",
        action="store_true",
        help="Pular utilização (usar só se já tiver bd_utilização e bd_tah em data/processed)",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    config = load_config(base / args.config)
    paths = config["paths"]
    proj = resolve_path(base, paths.get("project_root", "."))
    encoding = config.get("data_pipeline", {}).get("encoding", "ISO-8859-1")
    required_cols = config.get("data_pipeline", {}).get("required_columns")
    min_date = config.get("data_pipeline", {}).get("min_date", "2014-12-31")
    ac_type = config.get("data_pipeline", {}).get("ac_type_filter", "B737NG")

    dir_all = resolve_path(proj, paths["unscheduled_all"])
    dir_2021 = resolve_path(proj, paths["unscheduled_2021"])
    data_processed = resolve_path(proj, paths["data_processed"])
    data_processed.mkdir(parents=True, exist_ok=True)
    out_semanal = resolve_path(proj, paths["dataset_semanal"])

    # Opção: usar CSV já consolidado (quando os Excel estão fora do projeto, ex. OneDrive)
    unscheduled_csv = paths.get("unscheduled_csv")
    csv_path = resolve_path(proj, unscheduled_csv) if unscheduled_csv else None

    if csv_path and csv_path.exists():
        print("Etapa 1: Carregando Unscheduled do CSV (unscheduled_csv no config)...")
        import pandas as pd
        df_uns = pd.read_csv(csv_path, encoding=encoding)
        df_uns.to_csv(data_processed / "bd_unscheduled_itens.csv", index=False)
        print(f"  -> {len(df_uns)} registros")
    else:
        print("Etapa 1: Ingestão Unscheduled Items (Excel)...")
        df_uns = ingest_unscheduled(
            dir_all=str(dir_all),
            dir_2021=str(dir_2021),
            encoding=encoding,
        )
        df_uns.to_csv(data_processed / "bd_unscheduled_itens.csv", index=False)
        print(f"  -> {len(df_uns)} registros")

    print("Etapa 2: Processamento HH (limpeza e agregação)...")
    df_hh = process_unscheduled_hh(df_uns, ac_type_filter=ac_type)
    df_hh.to_csv(data_processed / "bd_hh_agrupado.csv", index=False)
    print(f"  -> {len(df_hh)} linhas (CLOSING_DATE, AC, HH)")

    if args.skip_utilization:
        # Carregar bd_utilização e bd_tah se existirem
        util_path = data_processed / "bd_utilização_agrupado.csv"
        tah_path = data_processed / "bd_utl_tah.csv"
        if not util_path.exists() or not tah_path.exists():
            print("Erro: --skip-utilization exige bd_utilização_agrupado.csv e bd_utl_tah.csv em data/processed.")
            sys.exit(1)
        import pandas as pd
        df_utilizacao = pd.read_csv(util_path)
        if "Unnamed: 0" in df_utilizacao.columns:
            df_utilizacao = df_utilizacao.drop(columns=["Unnamed: 0"])
        df_utilizacao["Dep._Date"] = pd.to_datetime(df_utilizacao["Dep._Date"])
        df_utl_tah = pd.read_csv(tah_path)
        df_utl_tah["Dep._Date"] = pd.to_datetime(df_utl_tah["Dep._Date"])
    else:
        print("Etapa 3: Processamento Utilização...")
        util_dir = resolve_path(proj, paths["utilization_dir"])
        df_utilizacao, df_utl_tah = process_utilization(str(util_dir))
        df_utilizacao.to_csv(data_processed / "bd_utilização_agrupado.csv", index=False)
        df_utl_tah.to_csv(data_processed / "bd_utl_tah.csv", index=False)
        print(f"  -> utilização: {len(df_utilizacao)} linhas")

    print("Etapa 4: Build dataset semanal (join + agregação)...")
    df_final = build_dataset(
        df_hh=df_hh,
        df_utilizacao=df_utilizacao,
        df_utl_tah=df_utl_tah,
        min_date=min_date,
    )
    print(f"  -> {len(df_final)} semanas")

    print("Etapa 5: Validação...")
    errs = validate_dataset(df_final, required_columns=required_cols)
    if errs:
        for e in errs:
            print(f"  ERRO: {e}")
        sys.exit(1)
    print("  -> OK")

    df_final.to_csv(out_semanal, index=False)
    print(f"Dataset salvo: {out_semanal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

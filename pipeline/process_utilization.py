"""
Ingestão e processamento da base de utilização de aeronaves (CSV).
"""
import warnings
from pathlib import Path

import pandas as pd


USECOLS = ["Dep. Date", "A/C", "AC-Type", "# per Day", "Hours", "Cycles", "TAH", "TAC"]


def _read_utilization_dir(diretorio: str) -> pd.DataFrame:
    path = Path(diretorio)
    if not path.exists():
        return pd.DataFrame()
    lista = []
    for f in path.iterdir():
        if f.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(f, usecols=USECOLS, encoding="utf-8", on_bad_lines="skip")
                lista.append(df)
            except Exception as e:
                raise RuntimeError(f"Erro ao ler {f}: {e}") from e
    if not lista:
        return pd.DataFrame()
    return pd.concat(lista, ignore_index=True).drop_duplicates()


def run(diretorio: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Lê todos os CSV do diretório de utilização, limpa e agrega.
    Retorna:
      - df_utilizacao: agrupado por Dep._Date e A/C com Hours_dec (sum), Cycles (sum)
      - df_utl_tah: agrupado por Dep._Date e A/C com Hours_dec (sum), TAH_dec (max) para idade da frota
    """
    df = _read_utilization_dir(diretorio)
    if df.empty:
        raise FileNotFoundError(
            f"Nenhum CSV encontrado em {diretorio}. Verifique config (utilization_dir)."
        )

    df.columns = df.columns.str.replace(" ", "_")
    df["Dep._Date"] = df["Dep._Date"].astype(str).str.replace(".", "-")
    if "Cycles" in df.columns and df["Cycles"].dtype == object:
        df["Cycles"] = df["Cycles"].str.replace("'", "", regex=False)
    df = df.loc[df["Dep._Date"] != "0 "]
    df["Dep._Date"] = pd.to_datetime(df["Dep._Date"])
    df = df.dropna(subset=["Hours"])

    # Hours e TAH no formato HH:MM -> decimal
    h = df["Hours"].astype(str).str.split(":", expand=True)
    df["Hours_h"] = pd.to_numeric(h[0], errors="coerce").fillna(0)
    df["Hours_m"] = pd.to_numeric(h[1], errors="coerce").fillna(0)
    df["Hours_dec"] = df["Hours_h"] + (df["Hours_m"] * 100 / 60) / 100

    tah = df["TAH"].astype(str).str.split(":", expand=True)
    df["TAH_h"] = pd.to_numeric(tah[0], errors="coerce").fillna(0)
    df["TAH_m"] = pd.to_numeric(tah[1], errors="coerce").fillna(0)
    df["TAH_dec"] = df["TAH_h"] + (df["TAH_m"] * 100 / 60) / 100

    df = df.drop(columns=["Hours", "Hours_h", "Hours_m", "TAH_h", "TAH_m", "TAC"], errors="ignore")
    df["Cycles"] = pd.to_numeric(df["Cycles"], errors="coerce").fillna(1)

    # Agregação por dia e prefixo
    df_hd = df.groupby(["Dep._Date", "A/C"]).agg(
        {"Hours_dec": "sum", "Cycles": "sum"}
    ).reset_index()
    df_tah = df.groupby(["Dep._Date", "A/C"]).agg(
        {"Hours_dec": "sum", "TAH_dec": "max"}
    ).reset_index()

    return df_hd, df_tah

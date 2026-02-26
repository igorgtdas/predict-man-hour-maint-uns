"""
Ingestão e consolidação dos dados de Unscheduled Items (Excel).
Suporta dois formatos: pasta 'all' (colunas antigas) e pasta '2021' (colunas novas).
"""
import os
import warnings
from pathlib import Path

import pandas as pd


# Colunas antigas (all) -> mapeamento para nome canônico
COLS_OLD = [
    "SIGN", "AC", "AC Type", "ISSUE STATION", "CLOSING DATE",
    "ATA", "ATA DESC", "HH Planejado WO", "HH Executado WO"
]
# Colunas 2021
COLS_2021 = [
    "SIGN", "AC", "AC_Type", "ISSUE_STATION", "CLOSING_DATE",
    "ATA", "DESCRIPTION", "hh_plan", "hh_exec"
]
# Nomes canônicos após unificação
CANONICAL = [
    "SIGN", "AC", "AC_Type", "ISSUE_Station", "CLOSING_DATE",
    "ATA", "ATA_DESC", "HH_Planejado_WO", "HH_Executado_WO"
]


def _read_dir_excel(diretorio: str, usecols: list, encoding: str = "utf-8") -> pd.DataFrame:
    """Lê todos os .xlsx/.xls de um diretório e concatena."""
    path = Path(diretorio)
    if not path.exists():
        return pd.DataFrame()
    lista = []
    warnings.simplefilter("ignore", category=UserWarning)
    for f in path.iterdir():
        if f.suffix.lower() in (".xlsx", ".xls"):
            try:
                df = pd.read_excel(f, usecols=usecols)
                lista.append(df)
            except Exception as e:
                raise RuntimeError(f"Erro ao ler {f}: {e}") from e
    if not lista:
        return pd.DataFrame()
    return pd.concat(lista, ignore_index=True)


def _normalize_2021(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do formato 2021 para o canônico (igual ao formato 'all')."""
    rename = {
        "ISSUE_STATION": "ISSUE_Station",
        "DESCRIPTION": "ATA_DESC",
        "hh_plan": "HH_Planejado_WO",
        "hh_exec": "HH_Executado_WO",
    }
    # Garantir HH_Executado_WO e HH_Planejado_WO como string para concat com 'all'
    if "hh_exec" in df.columns:
        df = df.rename(columns=rename)
    if "HH_Executado_WO" in df.columns and df["HH_Executado_WO"].dtype != object:
        df["HH_Executado_WO"] = df["HH_Executado_WO"].astype(str).str.replace(",", ".")
    if "HH_Planejado_WO" in df.columns and df["HH_Planejado_WO"].dtype != object:
        df["HH_Planejado_WO"] = df["HH_Planejado_WO"].astype(str).str.replace(",", ".")
    return df


def _normalize_old(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do formato antigo para o canônico."""
    rename = {
        "AC Type": "AC_Type",
        "ISSUE STATION": "ISSUE_Station",
        "CLOSING DATE": "CLOSING_DATE",
        "ATA DESC": "ATA_DESC",
        "HH Planejado WO": "HH_Planejado_WO",
        "HH Executado WO": "HH_Executado_WO",
    }
    return df.rename(columns=rename)


def run(
    dir_all: str,
    dir_2021: str,
    encoding: str = "ISO-8859-1",
) -> pd.DataFrame:
    """
    Lê as duas pastas (all e 2021), unifica esquema e retorna um único DataFrame.
    Filtra linhas SIGN in ['PILOT','CABIN'] e remove coluna SIGN.
    """
    dfs = []

    df_all = _read_dir_excel(dir_all, usecols=COLS_OLD, encoding=encoding)
    if not df_all.empty:
        df_all = _normalize_old(df_all)
        dfs.append(df_all)

    df_2021 = _read_dir_excel(dir_2021, usecols=COLS_2021, encoding=encoding)
    if not df_2021.empty:
        df_2021 = _normalize_2021(df_2021)
        dfs.append(df_2021)

    if not dfs:
        raise FileNotFoundError(
            f"Nenhum arquivo Excel encontrado em {dir_all} ou {dir_2021}. "
            "Verifique config.yaml (unscheduled_all, unscheduled_2021)."
        )

    consolidado = pd.concat(dfs, ignore_index=True)
    consolidado = consolidado.drop_duplicates()

    # Filtrar PILOT e CABIN
    if "SIGN" in consolidado.columns:
        consolidado = consolidado.loc[~consolidado["SIGN"].isin(["PILOT", "CABIN"])]
        consolidado = consolidado.drop(columns=["SIGN"])

    return consolidado

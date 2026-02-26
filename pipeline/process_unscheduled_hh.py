"""
Limpeza e agregação dos Unscheduled Items: tratamento de HH, filtros (B737NG, ATA),
agregação por data e prefixo (AC).
"""
import pandas as pd


def _hh_to_decimal(series: pd.Series) -> pd.Series:
    """Converte coluna no formato 'HH:MM' ou similar para decimal (horas)."""
    parts = series.astype(str).str.split(":", expand=True)
    if parts.shape[1] < 2:
        return pd.to_numeric(series, errors="coerce")
    h = pd.to_numeric(parts[0], errors="coerce").fillna(0)
    m = pd.to_numeric(parts[1], errors="coerce").fillna(0)
    return h + (m * 100 / 60) / 100


def run(df_uns: pd.DataFrame, ac_type_filter: str = "B737NG") -> pd.DataFrame:
    """
    Recebe o DataFrame consolidado de Unscheduled (já com colunas canônicas).
    - Normaliza nomes de colunas (espaços -> _)
    - Converte CLOSING_DATE para datetime
    - Filtra HH_* com len <= 8 (evita valores tipo '1900-01-01...')
    - Converte HH planejado/executado para decimal; onde HH executado == 0 usa planejado; depois substitui 0 pela média
    - Filtra AC_Type == ac_type_filter
    - Exclui ATA_DESC == 'ADMINISTRATIVE - GENERAL'
    - Mantém conjuntos maiores (motor, APU, trem de pouso)
    - Agrupa por CLOSING_DATE e AC, soma HH.
    Retorna DataFrame com colunas: CLOSING_DATE, AC, HH.
    """
    df = df_uns.copy()
    df.columns = df.columns.str.replace(" ", "_")

    if "CLOSING_DATE" not in df.columns:
        raise ValueError("DataFrame deve conter coluna CLOSING_DATE")
    df["CLOSING_DATE"] = pd.to_datetime(df["CLOSING_DATE"])

    # Colunas de HH podem ter nomes ligeiramente diferentes
    col_exec = None
    col_plan = None
    for c in df.columns:
        if "Executado" in c or "exec" in c.lower():
            col_exec = c
        if "Planejado" in c or "plan" in c.lower():
            col_plan = c
    if col_exec is None or col_plan is None:
        raise ValueError("Colunas de HH Executado e Planejado não encontradas.")

    # Filtrar linhas com HH em formato inválido (> 24h gera string longa)
    df[col_exec] = df[col_exec].astype(str)
    df[col_plan] = df[col_plan].astype(str)
    df = df[df[col_exec].str.len() <= 8]
    df = df[df[col_plan].str.len() <= 8]

    df["HH_Planejado_dec"] = _hh_to_decimal(df[col_plan])
    df["HH_Executado_dec"] = _hh_to_decimal(df[col_exec])
    df["HH"] = df["HH_Executado_dec"]
    df.loc[df["HH_Executado_dec"] == 0, "HH"] = df["HH_Planejado_dec"]
    avg = df["HH"].replace(0, pd.NA).mean()
    if pd.isna(avg):
        avg = df["HH"].mean()
    df["HH"] = df["HH"].replace(0, avg)

    # Filtro por tipo de aeronave
    ac_col = "AC_Type" if "AC_Type" in df.columns else "AC Type"
    if ac_col not in df.columns:
        raise ValueError("Coluna de tipo de aeronave não encontrada.")
    df = df.loc[df[ac_col] == ac_type_filter]

    # Excluir ADMINISTRATIVE - GENERAL
    ata_desc_col = "ATA_DESC" if "ATA_DESC" in df.columns else "ATA DESC"
    if ata_desc_col in df.columns:
        df = df.loc[~df[ata_desc_col].isin(["ADMINISTRATIVE - GENERAL"])]

    # Manter apenas colunas necessárias para agregação (conjuntos maiores = não excluir motor/APU/trem)
    df = df[["CLOSING_DATE", "AC", "HH"]].copy()
    df_ng_agrupado = df.groupby(["CLOSING_DATE", "AC"], as_index=False).agg({"HH": "sum"})

    return df_ng_agrupado

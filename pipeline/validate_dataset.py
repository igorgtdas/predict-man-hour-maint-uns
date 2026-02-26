"""
Validação básica do dataset final (schema, nulos, faixas).
"""
import pandas as pd

REQUIRED_COLUMNS = [
    "date", "acft", "sum_daily_hours", "age_fleet", "Cycles", "sum_uti_mensal", "HH"
]


def run(df: pd.DataFrame, required_columns: list[str] | None = None) -> list[str]:
    """
    Valida o DataFrame do dataset semanal.
    Retorna lista de mensagens de erro (vazia se tudo ok).
    """
    errors = []
    required = required_columns or REQUIRED_COLUMNS

    for col in required:
        if col not in df.columns:
            errors.append(f"Coluna obrigatória ausente: {col}")

    if errors:
        return errors

    if df["date"].isna().any():
        errors.append("Coluna 'date' contém nulos.")
    if df["HH"].isna().any():
        errors.append("Coluna 'HH' contém nulos.")
    if (df["HH"] < 0).any():
        errors.append("Coluna 'HH' contém valores negativos.")
    if (df["acft"] < 0).any():
        errors.append("Coluna 'acft' contém valores negativos.")

    if len(df) == 0:
        errors.append("Dataset está vazio após filtros.")

    return errors

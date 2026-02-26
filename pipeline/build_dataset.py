"""
Junção dos dados de HH (agrupado) com utilização e construção do dataset final semanal.
"""
import pandas as pd


def run(
    df_hh: pd.DataFrame,
    df_utilizacao: pd.DataFrame,
    df_utl_tah: pd.DataFrame,
    min_date: str = "2014-12-31",
) -> pd.DataFrame:
    """
    df_hh: colunas CLOSING_DATE, AC, HH
    df_utilizacao: Dep._Date, A/C, Hours_dec, Cycles
    df_utl_tah: Dep._Date, A/C, Hours_dec, TAH_dec
    Faz merge por key_id = date + AC, depois agregação semanal e merge com sum_uti_mensal.
    """
    df_utilizacao = df_utilizacao.copy()
    df_utilizacao["Dep._Date"] = pd.to_datetime(df_utilizacao["Dep._Date"])
    df_utilizacao["key_id"] = df_utilizacao["Dep._Date"].astype(str) + df_utilizacao["A/C"]
    df_utilizacao = df_utilizacao[["key_id", "Dep._Date", "A/C", "Hours_dec", "Cycles"]]

    df_hh = df_hh.copy()
    df_hh["CLOSING_DATE"] = pd.to_datetime(df_hh["CLOSING_DATE"])
    df_hh["key_id"] = df_hh["CLOSING_DATE"].astype(str) + df_hh["AC"]

    df_utl_tah = df_utl_tah.copy()
    df_utl_tah["Dep._Date"] = pd.to_datetime(df_utl_tah["Dep._Date"])
    df_utl_tah["key_id"] = df_utl_tah["Dep._Date"].astype(str) + df_utl_tah["A/C"]
    df_utl_tah = df_utl_tah[["key_id", "TAH_dec"]]

    df_interme = pd.merge(
        df_utilizacao, df_hh, how="inner", on="key_id"
    )
    df_final = pd.merge(df_interme, df_utl_tah, how="left", on="key_id")
    df_final = df_final[
        ["Dep._Date", "A/C", "Hours_dec", "TAH_dec", "Cycles", "HH"]
    ].copy()
    df_final.columns = ["date", "acft", "sum_daily_hours", "age_fleet", "Cycles", "HH"]
    df_final["HH"] = df_final["HH"].fillna(0)

    # Média de utilização mensal (soma no mês) para join depois
    df_avg_um = df_final.groupby(pd.Grouper(key="date", freq="M")).agg(
        {"sum_daily_hours": "sum"}
    ).reset_index()
    df_avg_um = df_avg_um.rename(columns={"sum_daily_hours": "sum_uti_mensal"})
    df_avg_um["key_2"] = df_avg_um["date"].dt.strftime("%Y%m")

    # Agregação semanal
    df_final_group = df_final.groupby(pd.Grouper(key="date", freq="7D")).agg(
        {
            "acft": "count",
            "sum_daily_hours": "sum",
            "age_fleet": "sum",
            "Cycles": "sum",
            "HH": "sum",
        }
    ).reset_index()
    df_final_group["key_2"] = df_final_group["date"].dt.strftime("%Y%m")
    df_final_group = pd.merge(df_final_group, df_avg_um[["key_2", "sum_uti_mensal"]], how="left", on="key_2")
    df_final_group = df_final_group.drop(columns=["key_2"])

    # Reordenar colunas: date, acft, sum_daily_hours, age_fleet, Cycles, sum_uti_mensal, HH
    cols = ["date", "acft", "sum_daily_hours", "age_fleet", "Cycles", "sum_uti_mensal", "HH"]
    df_final_group = df_final_group[[c for c in cols if c in df_final_group.columns]]

    # Filtro de data (corrige bug do notebook que usava df_final em vez de df_final_group)
    df_final_group = df_final_group.loc[df_final_group["date"] > min_date]

    return df_final_group

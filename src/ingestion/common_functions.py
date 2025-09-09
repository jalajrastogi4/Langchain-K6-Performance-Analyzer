import pandas as pd
from src.ingestion.schema import url_mappings, rename_map


def to_pivot_df(df):
    """
    Pivot dataframe to normalized schema.
    """
    if df.empty:
        return pd.DataFrame()

    df_pivot = df.pivot_table(
        index=["timestamp", "name", "method", "url", "status"],
        columns="metric_name",
        values="metric_value",
        aggfunc="first",
    ).reset_index()

    df_pivot["url"] = df_pivot["url"].map(url_mappings)
    df_pivot = df_pivot.rename(columns=rename_map)

    if "http_req_failed" in df_pivot.columns:
        df_pivot["success"] = df_pivot["http_req_failed"].apply(lambda x: x == 0)
        df_pivot = df_pivot.drop(columns=["http_req_failed"])

    if "http_reqs" in df_pivot.columns:
        df_pivot = df_pivot.drop(columns=["http_reqs"])

    if df_pivot['timestamp'].dtype != 'datetime64[ns]':
        df_pivot['timestamp'] = pd.to_datetime(df_pivot['timestamp'])

    return df_pivot
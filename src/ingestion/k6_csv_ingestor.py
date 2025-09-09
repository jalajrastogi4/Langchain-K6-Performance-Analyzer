import pandas as pd
from src.ingestion.schema import metrics_of_interest
from src.ingestion.common_functions import to_pivot_df


def normalizer_k6_csv(chunk: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSV chunk from K6 results.
    """
    filtered = chunk[chunk["metric_name"].isin(metrics_of_interest)]
    pivoted = to_pivot_df(filtered)
    return pivoted


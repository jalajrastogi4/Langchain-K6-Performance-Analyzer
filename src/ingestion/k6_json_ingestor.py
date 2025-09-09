import pandas as pd
import json
from src.ingestion.schema import metrics_of_interest
from src.ingestion.common_functions import to_pivot_df


def process_chunk(lines) -> pd.DataFrame:
    """
    Process raw JSON lines into intermediate dataframe.
    """
    records = []
    for line in lines:
        try:
            obj = json.loads(line.strip())
        except json.JSONDecodeError:
            continue

        if obj.get("type") != "Point":
            continue

        metric = obj.get("metric")
        data = obj.get("data", {})
        tags = data.get("tags", {})

        if metric not in metrics_of_interest:
            continue

        records.append({
            "timestamp": pd.to_datetime(data.get("time")),
            "metric_name": metric,
            "metric_value": data.get("value"),
            "name": tags.get("name"),
            "method": tags.get("method"),
            "url": tags.get("url"),
            "status": tags.get("status"),
        })
    return pd.DataFrame(records)


def normalizer_k6_json(json_file: str, chunk_size: int = 50000) -> pd.DataFrame:
    """
    Generate normalized dataframe chunks from JSON file.
    """
    with open(json_file, "r", encoding="utf-8") as f:
        buffer = []
        for i, line in enumerate(f, 1):
            buffer.append(line)
            if i % chunk_size == 0:
                df = process_chunk(buffer)
                df_chunk = to_pivot_df(df) if not df.empty else pd.DataFrame()
                if not df_chunk.empty:
                    yield df_chunk
                buffer = []
        if buffer:  # leftover
            df = process_chunk(buffer)
            df_chunk = to_pivot_df(df)
            if not df_chunk.empty:
                yield df_chunk


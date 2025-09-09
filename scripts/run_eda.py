import pandas as pd
import os
from datetime import datetime

# from fix_imports import fix_imports
from src.eda.metrics import GlobalMetricsAggregator, EndpointMetricsAggregator
from src.ingestion.k6_csv_ingestor import normalizer_k6_csv
from src.ingestion.k6_json_ingestor import normalizer_k6_json

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CSV_FILE = "results.csv"
JSON_FILE = "results.json"


RESULT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "metrics_data")
METRICS_GLOBAL_FILE = "global_metrics.csv"
METRICS_ENDPOINT_FILE = "endpoint_metrics.csv"


class DataEDA:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.csvfile = os.path.join(self.data_dir, CSV_FILE)
        self.jsonfile = os.path.join(self.data_dir, JSON_FILE)

        self.result_dir = RESULT_DIR
        os.makedirs(self.result_dir, exist_ok=True)  # ensure folder exists
        self.global_result_file = os.path.join(self.result_dir, METRICS_GLOBAL_FILE)
        self.endpoint_result_file = os.path.join(self.result_dir, METRICS_ENDPOINT_FILE)

        self.global_metrics_aggregator = GlobalMetricsAggregator()
        self.endpoint_metrics_aggregator = EndpointMetricsAggregator()

    def run_eda(self, file_type: str, chunk_size: int = 10000):
        if file_type == "csv":
            if os.path.exists(self.csvfile):
                chunks = pd.read_csv(self.csvfile, chunksize=chunk_size)
                for chunk in chunks:
                    df = normalizer_k6_csv(chunk)
                    self.global_metrics_aggregator.update(df)
                    self.endpoint_metrics_aggregator.update(df)
            else:
                raise FileNotFoundError(f"CSV file {self.csvfile} not found")
        elif file_type == "json":
            if os.path.exists(self.jsonfile):
                for chunk_df in normalizer_k6_json(self.jsonfile, chunk_size=chunk_size):
                    self.global_metrics_aggregator.update(chunk_df)
                    self.endpoint_metrics_aggregator.update(chunk_df)
            else:
                raise FileNotFoundError(f"JSON file {self.jsonfile} not found")

    def get_global_metrics(self):
        return self.global_metrics_aggregator.get_metrics()

    def get_endpoint_metrics(self):
        return self.endpoint_metrics_aggregator.get_metrics()


if __name__ == "__main__":
    eda = DataEDA()
    start_time = datetime.now()
    print("Start time: ", start_time)
    eda.run_eda(file_type="json", chunk_size=10000)
    end_time = datetime.now()
    print("End time: ", end_time)
    print("Time taken: ", end_time - start_time)

    global_metrics = eda.get_global_metrics()
    endpoint_metrics = eda.get_endpoint_metrics()

    print(f"Global metrics: {global_metrics}")
    print(f"Endpoint metrics: {endpoint_metrics}")

    # Save to CSV
    pd.DataFrame([global_metrics]).to_csv(eda.global_result_file, index=False)
    pd.DataFrame(endpoint_metrics).to_csv(eda.endpoint_result_file, index=False)

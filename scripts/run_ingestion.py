import os
import pandas as pd

from src.ingestion.k6_csv_ingestor import normalizer_k6_csv
from src.ingestion.k6_json_ingestor import normalizer_k6_json

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CSV_FILE = "results.csv"
JSON_FILE = "results.json"


class DataIngestion:
    def __init__(self, data_dir: str = DATA_DIR):

        self.data_dir = data_dir
        self.csvfile = os.path.join(self.data_dir, CSV_FILE)
        self.jsonfile = os.path.join(self.data_dir, JSON_FILE)

    def ingest_data(self, file_type: str, chunk_size: int = 10000) -> pd.DataFrame:
        if file_type == "csv":
            if os.path.exists(self.csvfile):
                chunks = pd.read_csv(self.csvfile, chunksize=chunk_size)
                for chunk in chunks:
                    df = normalizer_k6_csv(chunk)
                    yield df
            else:
                raise FileNotFoundError(f"CSV file {self.csvfile} not found")
        elif file_type == "json":
            if os.path.exists(self.jsonfile):
                for chunk_df in normalizer_k6_json(self.jsonfile, chunk_size=chunk_size):
                    yield chunk_df
            else:
                raise FileNotFoundError(f"JSON file {self.jsonfile} not found")



if __name__ == "__main__":
    ingestion = DataIngestion()
    for chunk_df in ingestion.ingest_data(file_type="json", chunk_size=10000):
        print(chunk_df.head())
        break
    for chunk_df in ingestion.ingest_data(file_type="csv", chunk_size=10000):
        print(chunk_df.head())
        break

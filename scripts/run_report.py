import os
import pandas as pd

from src.eda.report_generator import ReportGenerator
from src.eda.plots import (
    plot_status_distribution,
    plot_endpoint_latencies,
    plot_endpoint_rps
)

RESULT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "metrics_data")
METRICS_GLOBAL_FILE = "global_metrics.csv"
METRICS_ENDPOINT_FILE = "endpoint_metrics.csv"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "reports")



if __name__ == "__main__":
    global_metrics = pd.read_csv(os.path.join(RESULT_DIR, METRICS_GLOBAL_FILE))
    endpoint_metrics = pd.read_csv(os.path.join(RESULT_DIR, METRICS_ENDPOINT_FILE))

    global_metrics = global_metrics.to_dict(orient="records")[0]

    plots = {
        "status_dist": plot_status_distribution(global_metrics),
        "latencies": plot_endpoint_latencies(endpoint_metrics),
        "rps": plot_endpoint_rps(endpoint_metrics)
    }

    report_generator = ReportGenerator()
    report_generator.generate_report(global_metrics, endpoint_metrics, plots, os.path.join(OUTPUT_DIR, "report.html"))

    print("Report generated successfully")
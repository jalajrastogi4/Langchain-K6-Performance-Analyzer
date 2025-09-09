import matplotlib.pyplot as plt
import pandas as pd

def plot_status_distribution(global_metrics: dict):
    """
    Plot the status distribution.
    """
    labels = ["2xx", "3xx", "4xx", "5xx"]
    values = [
        global_metrics.get("status_2xx", 0),
        global_metrics.get("status_3xx", 0),
        global_metrics.get("status_4xx", 0),
        global_metrics.get("status_5xx", 0),
    ]

    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Global Status Code Distribution")
    return fig

def plot_endpoint_latencies(endpoint_metrics: list | pd.DataFrame):
    """
    Plot the endpoint latencies.
    """
    df = pd.DataFrame(endpoint_metrics) if isinstance(endpoint_metrics, list) else endpoint_metrics
    df = df.sort_values("p90_response_time", ascending=False)

    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(df["url"], df["median_response_time"], label="p50")
    ax.bar(df["url"], df["p90_response_time"], label="p90")
    ax.bar(df["url"], df["p95_response_time"], label="p95")
    ax.bar(df["url"], df["p99_response_time"], label="p99")
    ax.set_xticklabels(df["url"], rotation=45, ha="right")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Endpoint Latency Percentiles")
    ax.legend()
    fig.tight_layout()
    return fig

def plot_endpoint_rps(endpoint_metrics: list | pd.DataFrame):
    """
    Plot the endpoint rps.
    """
    df = pd.DataFrame(endpoint_metrics) if isinstance(endpoint_metrics, list) else endpoint_metrics
    df = df.sort_values("rps", ascending=False)

    fig, ax = plt.subplots(figsize=(12,6))
    ax.bar(df["url"], df["rps"])
    ax.set_xticklabels(df["url"], rotation=45, ha="right")
    ax.set_ylabel("Requests per Second")
    ax.set_title("Endpoint Throughput (RPS)")
    fig.tight_layout()
    return fig

def generate_all_plots(global_metrics: dict, endpoint_metrics: list | pd.DataFrame):
    """
    Generate all plots.
    """
    return {
        "status_dist": plot_status_distribution(global_metrics),
        "latencies": plot_endpoint_latencies(endpoint_metrics),
        "rps": plot_endpoint_rps(endpoint_metrics),
    }




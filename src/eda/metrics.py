import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from src.eda.utility import StreamingStats, ReservoirSampler

class GlobalMetricsAggregator:
    def __init__(self, sampler_size:int = 50000):
        """
        Initialize the global metrics aggregator.
        """
        self.total_requests = 0
        self.success_count = 0
        # self.response_times = []
        self.request_status_error = 0
        self.min_timestamp = None
        self.max_timestamp = None
        self.status_code_counts = Counter()

        self.sampler_size = sampler_size
        self.response_stats = StreamingStats()
        self.response_sampler = ReservoirSampler(self.sampler_size)
        

    def update(self, df_chunk):
        """
        Update the global metrics.
        """
        if df_chunk.empty:
            return

        n = len(df_chunk)
        self.total_requests += n
        self.success_count += df_chunk["success"].sum()
        # self.response_times.extend(df_chunk["response_time_ms"].tolist())
        self.request_status_error += (df_chunk["status"].astype(int) >= 400).sum()

        # Duration and RPS calculation
        if self.min_timestamp is None or df_chunk["timestamp"].min() < self.min_timestamp:
            self.min_timestamp = df_chunk["timestamp"].min()
        if self.max_timestamp is None or df_chunk["timestamp"].max() > self.max_timestamp:
            self.max_timestamp = df_chunk["timestamp"].max()
        self.status_code_counts.update(df_chunk["status"].astype(int))

        # Handle streaming for reeponse time
        for rt in df_chunk["response_time_ms"]:
            self.response_stats.update(rt)
            self.response_sampler.update(rt)

    def get_metrics(self):
        """
        Get the global metrics.
        """
        if self.total_requests == 0:
            return {}

        duration_sec = (self.max_timestamp - self.min_timestamp).total_seconds() if self.min_timestamp and self.max_timestamp else 0
        return {
            "total_requests": self.total_requests,
            "success_rate": self.success_count / self.total_requests,
            "failure_rate": 1 - self.success_count / self.total_requests,
            "median_response_time": self.response_sampler.percentile(50),
            "avg_response_time": self.response_stats.avg,
            "p90_response_time": self.response_sampler.percentile(90),
            "p95_response_time": self.response_sampler.percentile(95),
            "p99_response_time": self.response_sampler.percentile(99),
            "max_response_time": self.response_stats.max,
            "min_response_time": self.response_stats.min,
            "request_status_error": self.request_status_error / self.total_requests,
            "rps": self.total_requests / duration_sec if duration_sec > 0 else None,
            "status_2xx": sum([v for k,v in self.status_code_counts.items() if k >= 200 and k < 300]) / self.total_requests,
            "status_3xx": sum([v for k,v in self.status_code_counts.items() if k >= 300 and k < 400]) / self.total_requests,
            "status_4xx": sum([v for k,v in self.status_code_counts.items() if k >= 400 and k < 500]) / self.total_requests,
            "status_5xx": sum([v for k,v in self.status_code_counts.items() if k >= 500 and k < 600]) / self.total_requests,
        }


class EndpointMetricsAggregator:
    def __init__(self, sampler_size: int = 50000):
        """
        Initialize the endpoint metrics aggregator.
        """
        self.sampler_size = sampler_size
        self.data = defaultdict(lambda: {
            "total_requests": 0,
            "success_count": 0,
            "request_status_error": 0,
            "min_timestamp": None,
            "max_timestamp": None,
            "200_status_count": 0,
            "300_status_count": 0,
            "400_status_count": 0,
            "500_status_count": 0,
            "response_stats": StreamingStats(),
            "response_sampler": ReservoirSampler(self.sampler_size),
            "blocked_ms_stats": StreamingStats(),
            "blocked_ms_sampler": ReservoirSampler(self.sampler_size),
            "connecting_ms_stats": StreamingStats(),
            "connecting_ms_sampler": ReservoirSampler(self.sampler_size),
            "receiving_ms_stats": StreamingStats(),
            "receiving_ms_sampler": ReservoirSampler(self.sampler_size),
            "sending_ms_stats": StreamingStats(),
            "sending_ms_sampler": ReservoirSampler(self.sampler_size),
            "tls_handshake_ms_stats": StreamingStats(),
            "tls_handshake_ms_sampler": ReservoirSampler(self.sampler_size),
            "waiting_ms_stats": StreamingStats(),
            "waiting_ms_sampler": ReservoirSampler(self.sampler_size),
        })

    def update(self, df_chunk):
        """
        Update the endpoint metrics.
        """
        if df_chunk.empty:
            return

        df_chunk["status"] = df_chunk["status"].astype(int)

        # Group by URL
        grouped = df_chunk.groupby("url")

        for url, group in grouped:
            stats = self.data[url]
            n = len(group)

            stats["total_requests"] += n
            stats["success_count"] += group["success"].sum()
            stats["request_status_error"] += (group["status"] >= 400).sum()

            # Duration and RPS calculation
            min_ts, max_ts = group["timestamp"].min(), group["timestamp"].max()
            if stats["min_timestamp"] is None or min_ts < stats["min_timestamp"]:
                stats["min_timestamp"] = min_ts
            if stats["max_timestamp"] is None or max_ts > stats["max_timestamp"]:
                stats["max_timestamp"] = max_ts

            # Status code
            stats["200_status_count"] += ((group["status"] >= 200) & (group["status"] < 300)).sum()
            stats["300_status_count"] += ((group["status"] >= 300) & (group["status"] < 400)).sum()
            stats["400_status_count"] += ((group["status"] >= 400) & (group["status"] < 500)).sum()
            stats["500_status_count"] += ((group["status"] >= 500) & (group["status"] < 600)).sum()

            # Update streaming stats and samplers
            for col, stat_key, sampler_key in [
                ("response_time_ms", "response_stats", "response_sampler"),
                ("blocked_ms", "blocked_ms_stats", "blocked_ms_sampler"),
                ("connecting_ms", "connecting_ms_stats", "connecting_ms_sampler"),
                ("receiving_ms", "receiving_ms_stats", "receiving_ms_sampler"),
                ("sending_ms", "sending_ms_stats", "sending_ms_sampler"),
                ("tls_handshake_ms", "tls_handshake_ms_stats", "tls_handshake_ms_sampler"),
                ("waiting_ms", "waiting_ms_stats", "waiting_ms_sampler"),
            ]:
                values = group[col].dropna().values
                for v in values:
                    stats[stat_key].update(v)
                    stats[sampler_key].update(v)

    def get_metrics(self):
        """
        Get the endpoint metrics.
        """
        results = []
        for url, stats in self.data.items():
            if stats["total_requests"] == 0:
                continue

            duration = (
                (stats["max_timestamp"] - stats["min_timestamp"]).total_seconds()
                if stats["min_timestamp"] and stats["max_timestamp"]
                else 0
            )
            p90 = stats["response_sampler"].percentile(90)
            p50 = stats["response_sampler"].percentile(50)

            results.append({
                "url": url,
                "total_requests": stats["total_requests"],
                "success_rate": stats["success_count"] / stats["total_requests"],
                "failure_rate": 1 - stats["success_count"] / stats["total_requests"],
                "median_response_time": p50,
                "avg_response_time": stats["response_stats"].avg,
                "p90_response_time": p90,
                "p95_response_time": stats["response_sampler"].percentile(95),
                "p99_response_time": stats["response_sampler"].percentile(99),
                "min_response_time": stats["response_stats"].min,
                "max_response_time": stats["response_stats"].max,
                "tail_latency_gap": (p90 - p50) if (p90 is not None and p50 is not None) else None,
                "request_status_error": stats["request_status_error"] / stats["total_requests"],
                "blocked_ms": stats["blocked_ms_stats"].avg,
                "connecting_ms": stats["connecting_ms_stats"].avg,
                "receiving_ms": stats["receiving_ms_stats"].avg,
                "sending_ms": stats["sending_ms_stats"].avg,
                "tls_handshake_ms": stats["tls_handshake_ms_stats"].avg,
                "waiting_ms": stats["waiting_ms_stats"].avg,
                "rps": stats["total_requests"] / duration if duration > 0 else None,
                "status_2xx": stats["200_status_count"] / stats["total_requests"],
                "status_3xx": stats["300_status_count"] / stats["total_requests"],
                "status_4xx": stats["400_status_count"] / stats["total_requests"],
                "status_5xx": stats["500_status_count"] / stats["total_requests"],
            })
        return results


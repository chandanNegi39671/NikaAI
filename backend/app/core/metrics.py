"""
backend/app/core/metrics.py
───────────────────────────
Prometheus telemetry metrics configuration for Nika AI.
"""

import psutil
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

# ── Metrics Definitions ───────────────────────────────────────────────────────

# API Telemetry
REQUEST_COUNT = Counter(
    "nika_api_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "nika_api_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# YOLO Telemetry
YOLO_INFERENCE_TIME = Histogram(
    "nika_yolo_inference_time_seconds", "YOLOv8 inference execution time in seconds"
)

YOLO_FPS = Gauge("nika_yolo_fps", "Current throughput frame rate (FPS) of YOLO model")

# Cache Telemetry
CACHE_HITS = Counter(
    "nika_cache_hits_total", "Total count of cache hits", ["cache_type"]
)

CACHE_MISSES = Counter(
    "nika_cache_misses_total", "Total count of cache misses", ["cache_type"]
)

# System Load Telemetry
CPU_USAGE = Gauge("nika_system_cpu_usage_percent", "System CPU usage percent")
MEMORY_USAGE = Gauge("nika_system_memory_usage_bytes", "System memory usage in bytes")
DB_CONNECTIONS = Gauge(
    "nika_db_connections_active", "Number of active database pool connections"
)


def update_system_metrics():
    """Update CPU and Memory metrics in Prometheus."""
    try:
        CPU_USAGE.set(psutil.cpu_percent())
        MEMORY_USAGE.set(psutil.virtual_memory().used)
    except Exception:
        pass


# Expose as ASGI app
metrics_app = make_asgi_app()

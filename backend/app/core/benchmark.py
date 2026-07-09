"""
backend/app/core/benchmark.py
─────────────────────────────
Performance benchmarking suite to check YOLOv8 inference FPS, latency, and system overhead.
"""

import time

import numpy as np
import psutil
from PIL import Image

from app.core.logging import get_logger
from app.services.prediction import prediction_service

logger = get_logger(__name__)


def run_performance_benchmark(iterations: int = 100) -> dict:
    """Benchmark YOLOv8 inference speed, frame throughput, and system resource overhead."""
    logger.info(f"Starting performance benchmark with {iterations} iterations...")

    # 1. Warm up & ensure model is loaded
    try:
        prediction_service.load_model()
        prediction_service.warmup()
    except Exception as exc:
        logger.error(f"Cannot run benchmark: Model load failed: {exc}")
        return {"error": str(exc)}

    # Create a dummy image (e.g. 640x640 RGB image)
    img_array = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    pil_image = Image.fromarray(img_array)

    latencies = []

    cpu_before = psutil.cpu_percent()
    mem_before = psutil.virtual_memory().used

    start_time = time.perf_counter()

    for i in range(iterations):
        t_start = time.perf_counter()
        try:
            prediction_service.predict(pil_image)
            latencies.append((time.perf_counter() - t_start) * 1000.0)
        except Exception as exc:
            logger.error(f"Benchmark iteration {i} failed: {exc}")

    total_elapsed = time.perf_counter() - start_time

    cpu_after = psutil.cpu_percent()
    mem_after = psutil.virtual_memory().used

    if not latencies:
        return {"error": "All iterations failed."}

    avg_latency = sum(latencies) / len(latencies)
    fps = len(latencies) / total_elapsed

    metrics = {
        "iterations": len(latencies),
        "average_latency_ms": round(avg_latency, 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "throughput_fps": round(fps, 2),
        "cpu_load_change_percent": round(cpu_after - cpu_before, 2),
        "memory_change_mb": round((mem_after - mem_before) / (1024 * 1024), 2),
    }

    logger.info("Performance benchmark completed.")
    for key, value in metrics.items():
        logger.info(f"BENCHMARK: {key} = {value}")

    return metrics


if __name__ == "__main__":
    # Allow executing the script directly for quick local benchmarks
    run_performance_benchmark(50)

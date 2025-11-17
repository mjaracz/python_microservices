import time
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "Time spent processing request",
    ["method", "endpoint", "status"]
)

REQUEST_ERRORS = Counter(
    "api_request_errors_total",
    "Total number of error responses",
    ["method", "endpoint", "status"]
)

REQUEST_TOTAL = Counter(
    "api_request_total",
    "Total number of processed requests",
    ["method", "endpoint", "status"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()
        method = request.method
        endpoint = request.url.path
        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            REQUEST_ERRORS.labels(method, endpoint, status).inc()
            raise
        process_time = time.perf_counter() - start_time
        REQUEST_LATENCY.labels(method, endpoint, status).observe(process_time)
        REQUEST_TOTAL.labels(method, endpoint, status).inc()
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response

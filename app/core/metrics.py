import time

from prometheus_client import Counter, Histogram
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# prometheus.DefBuckets from client_golang, used by dashboard-be.
_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

request_counter = Counter(
    "server_requests_total",
    "Total number of requests by action and status code",
    ["action"],
)

request_duration = Histogram(
    "server_request_duration_seconds",
    "Request duration by action",
    ["action"],
    buckets=_BUCKETS,
)

error_counter = Counter(
    "server_errors_total",
    "Total number of errors by error message and status code",
    ["action", "error"],
)

GET_HEALTH_STATUS = "get_health_status"
AGENT_CHAT = "agent_chat"
UPLOAD_DOCUMENT = "upload_document"
DELETE_DOCUMENT = "delete_document"
GET_SESSION_HISTORY = "get_session_history"
GET_SESSION_SUMMARY = "get_session_summary"
GET_PROMPTS = "get_prompts"
SET_PROMPTS = "set_prompts"

_STATUS_ERRORS = {
    400: "BAD_REQUEST",
    401: "UNAUTHORISED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    429: "TOO_MANY_REQUESTS",
}


def track_action(action: str):
    """Mark a route handler so the metrics middleware records this action name."""

    def decorator(func):
        func._metrics_action = action
        return func

    return decorator


def push_error(action: str, error: str) -> None:
    error_counter.labels(action=action, error=error).inc()


def error_label(status_code: int) -> str:
    if status_code in _STATUS_ERRORS:
        return _STATUS_ERRORS[status_code]
    if status_code >= 500:
        return "INTERNAL_SERVER_ERROR"
    return f"HTTP_{status_code}"


def _record(scope: Scope, started_at: float, status_code: int, failed: bool) -> None:
    endpoint = scope.get("endpoint")
    action = getattr(endpoint, "_metrics_action", None)
    if not action:
        return

    request_counter.labels(action=action).inc()
    request_duration.labels(action=action).observe(time.perf_counter() - started_at)
    if failed and status_code < 400:
        push_error(action, "INTERNAL_SERVER_ERROR")
    elif status_code >= 400:
        push_error(action, error_label(status_code))


class PrometheusMiddleware:
    """Record request count, latency, and errors for handlers marked with track_action."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = time.perf_counter()
        status_code = 500
        failed = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            failed = True
            raise
        finally:
            _record(scope, started_at, status_code, failed)

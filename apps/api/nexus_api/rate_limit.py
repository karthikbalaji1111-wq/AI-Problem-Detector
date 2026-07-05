import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from nexus_api.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.settings = get_settings()
        self.history: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in {"/health", "/metrics"}:
            return await call_next(request)
        key = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        now = time.time()
        window = self.history[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.settings.rate_limit_per_minute:
            return Response("Rate limit exceeded", status_code=429)
        window.append(now)
        return await call_next(request)


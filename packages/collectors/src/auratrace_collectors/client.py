import time
from typing import Any

import httpx


class AuratraceTransport(httpx.HTTPTransport):
    def __init__(self, min_host_delay: float = 0.5, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cache: dict[str, httpx.Response] = {}
        self._last_request_time: dict[str, float] = {}
        self.min_host_delay = min_host_delay

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        url_key = str(request.url)

        if request.method == "GET" and url_key in self._cache:
            return self._cache[url_key]

        host = request.url.host

        for attempt in range(4):
            elapsed = time.time() - self._last_request_time.get(host, 0.0)
            if elapsed < self.min_host_delay:
                time.sleep(self.min_host_delay - elapsed)

            try:
                self._last_request_time[host] = time.time()
                response = super().handle_request(request)

                if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(2**attempt)
                    continue

                if response.is_success and request.method == "GET":
                    response.read()
                    self._cache[url_key] = response

                return response

            except httpx.TransportError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

        return response

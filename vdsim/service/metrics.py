"""In-process request metrics in the Prometheus text exposition format (no extra dependency)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict

# histogram bucket upper bounds in seconds (Prometheus convention: cumulative, plus +Inf)
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.started = time.time()
        self.requests = defaultdict(int)       # (method, route, status) -> count
        self.latency_sum = defaultdict(float)  # route -> seconds
        self.latency_count = defaultdict(int)
        self.latency_buckets = defaultdict(lambda: [0] * len(BUCKETS))
        self.in_flight = 0
        self.rejected = 0                      # requests refused because the worker limit was reached

    def observe(self, method, route, status, seconds):
        with self._lock:
            self.requests[(method, route, int(status))] += 1
            self.latency_sum[route] += seconds
            self.latency_count[route] += 1
            buckets = self.latency_buckets[route]
            for i, bound in enumerate(BUCKETS):
                if seconds <= bound:
                    buckets[i] += 1

    def change_in_flight(self, delta):
        with self._lock:
            self.in_flight += delta

    def reject(self):
        with self._lock:
            self.rejected += 1

    def render(self):
        def esc(value):
            return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        with self._lock:
            lines = ["# HELP motionengine_uptime_seconds Seconds since the service started.",
                     "# TYPE motionengine_uptime_seconds gauge",
                     f"motionengine_uptime_seconds {time.time() - self.started:.3f}",
                     "# HELP motionengine_requests_in_flight Requests currently being processed.",
                     "# TYPE motionengine_requests_in_flight gauge",
                     f"motionengine_requests_in_flight {self.in_flight}",
                     "# HELP motionengine_requests_rejected_total Requests refused by the concurrency limit.",
                     "# TYPE motionengine_requests_rejected_total counter",
                     f"motionengine_requests_rejected_total {self.rejected}",
                     "# HELP motionengine_requests_total HTTP requests by method, route and status.",
                     "# TYPE motionengine_requests_total counter"]
            for (method, route, status), n in sorted(self.requests.items()):
                lines.append(f'motionengine_requests_total{{method="{esc(method)}",route="{esc(route)}",'
                             f'status="{status}"}} {n}')
            lines += ["# HELP motionengine_request_duration_seconds Request latency by route.",
                      "# TYPE motionengine_request_duration_seconds histogram"]
            for route in sorted(self.latency_count):
                label = f'route="{esc(route)}"'
                for bound, n in zip(BUCKETS, self.latency_buckets[route]):
                    lines.append(f'motionengine_request_duration_seconds_bucket{{{label},le="{bound}"}} {n}')
                lines.append(f'motionengine_request_duration_seconds_bucket{{{label},le="+Inf"}} '
                             f"{self.latency_count[route]}")
                lines.append(f"motionengine_request_duration_seconds_sum{{{label}}} {self.latency_sum[route]:.6f}")
                lines.append(f"motionengine_request_duration_seconds_count{{{label}}} {self.latency_count[route]}")
        return "\n".join(lines) + "\n"

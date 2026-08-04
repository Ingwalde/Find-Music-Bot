from prometheus_client import Counter, Gauge, Histogram

external_api_requests_total = Counter(
    "bot_external_api_requests_total",
    "Total external API requests",
    ["service", "outcome"],  # outcome: success | error | breaker_open
)

external_api_latency_seconds = Histogram(
    "bot_external_api_latency_seconds",
    "External API request latency in seconds",
    ["service"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

circuit_breaker_open = Gauge(
    "bot_circuit_breaker_open",
    "1 when circuit breaker is open for a service, 0 otherwise",
    ["service"],
)

search_cache_hits_total = Counter(
    "bot_search_cache_hits_total",
    "Search cache hits",
)

search_cache_misses_total = Counter(
    "bot_search_cache_misses_total",
    "Search cache misses",
)

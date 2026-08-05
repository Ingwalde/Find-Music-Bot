# Prometheus Metrics

All metrics are exposed at `GET /metrics` on port 9090 (Prometheus text format).

## Metric Reference

### External API

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bot_external_api_requests_total` | Counter | `service`, `outcome` | Total external API calls. `service`: `deezer`, `spotify`, `genius`. `outcome`: `success`, `error`, `circuit_open`. |
| `bot_external_api_latency_seconds` | Histogram | `service` | Request latency per service. Buckets: default Prometheus (.005 → 10s). |
| `bot_circuit_breaker_open` | Gauge | `service` | `1` when the circuit breaker is open (service short-circuited), `0` when closed. |

### Cache

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bot_search_cache_hits_total` | Counter | — | PostgreSQL search result cache hits (24h TTL). |
| `bot_search_cache_misses_total` | Counter | — | PostgreSQL search result cache misses (live Deezer call made). |

### Rate Limiting

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bot_rate_limit_blocked_total` | Counter | — | Requests blocked by the per-user sliding-window rate limiter (both Redis and in-memory paths). |

### TLS / Infrastructure

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `bot_tls_cert_expiry_days` | Gauge | — | Days until the webhook TLS certificate expires. Updated on every `/metrics` scrape. Returns `-1` when the cert file is unreadable. No-op when `WEBHOOK_CERT_PATH` is not set (polling mode). |

---

## Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: find-music-bot
    static_configs:
      - targets: ["localhost:9090"]
    scrape_interval: 30s
```

---

## Example PromQL Queries

**API error rate per service (last 5 min):**
```promql
rate(bot_external_api_requests_total{outcome="error"}[5m])
  / rate(bot_external_api_requests_total[5m])
```

**P95 API latency per service:**
```promql
histogram_quantile(0.95,
  rate(bot_external_api_latency_seconds_bucket[5m])
)
```

**Services currently circuit-broken:**
```promql
bot_circuit_breaker_open == 1
```

**Search cache hit ratio:**
```promql
rate(bot_search_cache_hits_total[5m])
  / (rate(bot_search_cache_hits_total[5m]) + rate(bot_search_cache_misses_total[5m]))
```

**Rate limit blocks per minute:**
```promql
rate(bot_rate_limit_blocked_total[1m]) * 60
```

**TLS cert expiry alert (< 7 days):**
```promql
bot_tls_cert_expiry_days < 7
```

---

## Grafana Panel Suggestions

| Panel | Visualization | Query |
|-------|---------------|-------|
| API requests/sec by service | Time series | `rate(bot_external_api_requests_total[1m])` by `service` |
| API error rate | Stat (%) | error rate PromQL above |
| P95 latency by service | Time series | P95 PromQL above |
| Circuit breaker status | State timeline | `bot_circuit_breaker_open` by `service` |
| Cache hit ratio | Gauge (0–1) | cache hit ratio PromQL above |
| Rate limit blocks/min | Time series | blocks PromQL above |
| TLS cert expiry | Stat (days) | `bot_tls_cert_expiry_days` |

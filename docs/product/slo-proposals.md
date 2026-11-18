# Provisional MVP SLO Proposals

**Status**: Planning hypotheses only; not approved service commitments.

These initial targets assume a low-volume MVP. Baseline them in production-like staging with a representative document corpus, model/provider, and concurrency profile; review after the Phase 4 vertical slice and Phase 9 load/evaluation work.

| Measure | Proposed target | Measurement definition |
|---|---:|---|
| API availability | 99.5% monthly | Successful eligible API requests / all eligible API requests. Define exclusions before reporting; do not silently omit dependency failures. |
| Time to first validated answer token | p95 ≤ 3 seconds | Accepted chat request to first user-visible validated answer chunk. Progress events do not count; draft tokens remain server-side until grounding/citation validation. |
| Retrieval latency | p95 ≤ 1.5 seconds | Retrieval workflow entry to authorized, reranked evidence ready for prompt construction. Report cache-hit and cache-miss populations separately. |
| Ingestion completion | 95% indexed within 5 minutes | Verified upload completion to `indexed`, for a provisional benchmark envelope of files ≤25 MB and ≤100 pages/slides. This envelope is not an accepted upload policy. |
| Citation correctness | ≥95% | On a versioned human-reviewed evaluation set, cited source identifiers, locations, and evidence support the associated claims. Report citation coverage separately. |
| Cost per conversation | ≤$0.15 average | Embedding/model provider cost for a defined standard 10-turn test conversation. Publish model, prompt, token, retry, and cache assumptions; infrastructure cost is excluded initially. |

## Measurement Plan

- Emit request, retrieval, ingestion, and provider timings with correlation/trace IDs and explicit error categories.
- Attribute quality and cost to model, prompt, embedding/index, and retrieval configuration versions.
- Create a representative golden set before citation correctness becomes a release gate.
- Baseline cost from provider-reported usage where available; label estimates and exclude unmeasured token assumptions.
- Approve a workload envelope, file limits, exclusions, sampling policy, and target values with product/platform owners before production.


# API — The Signature Experiment Solver

Base: `https://justinahiggins614-cmyk.github.io/signature-experiment-solver/`

All feeds are static JSON, CORS-open, no key required. The authoritative
count lives in `experiment-manifest.json`; everything else derives from it.

## Feeds

| Feed | Contents |
|---|---|
| `experiment-manifest.json` | The ONE authoritative manifest: totals, ID range, index hash, engine version, honesty note |
| `api.json` | Site summary (derived from the manifest) |
| `data/index.json.gz` | Compact index: 14,925 rows of `[id, typeKey, seed, title, discipline]` |
| `data/experiments-catalog.json` | Full record list with deep links |
| `data/solver-catalog.json` | 240 solver types A–Z: type_id, model provenance, safety level, live record counts |
| `data/hashes.json.gz` | `{exp_id: sha256}` content hashes of canonical record JSON |
| `data/health.json` | Latest QA gate run |
| `ai-manifest.json` | AI-agent access description |
| `llms.txt` | Crawler/LLM summary |

## Schemas

- `experiment.schema.json` — JAH-EXP-RECORD/1.0 (the record standard)
- `solver-type.schema.json` — solver-type records
- `manifest.schema.json` — the manifest

## Deep links

- `?exp=JAH-EXP-000123` — open a record (permanent IDs, never reused)
- `?type=free-fall` — open a solver type's sample run
- `?verify=JAH-EXP-000123` — re-solve in-browser, compare content hash

## Reproducing a record (any language)

1. Take `typeKey`, `seed`, `params` from the index row.
2. `seedInput = typeKey + ":" + seed + ":" + JSON.stringify(params)`
3. `h = FNV-1a-32(seedInput)` → PRNG `mulberry32(h)` → run the type's model
   (`code/engine.js` is the reference implementation, SOLVER-ENGINE-V1).
4. Canonicalize the record (sort keys recursively, no whitespace), SHA-256 it,
   compare with `data/hashes.json.gz`.

Full spec: `docs/DETERMINISM.md`. Test vectors: `docs/test-vectors.json`.

## Honesty contract

Every record: `status=SOLVER-GENERATED`, `simulation_status=SIMULATED`,
`physical_status=NOT-PERFORMED`, `measured=false`. Numbers are solver
simulations from built-in models — never lab measurements. Quote a number
only with its model, seed, and units.

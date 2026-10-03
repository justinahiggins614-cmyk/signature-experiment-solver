# Changelog — The Signature Experiment Solver

## 2026-10-03 — Stress-test fix wave (record standard v1.0)
- **Authoritative manifest:** new `experiment-manifest.json` — the ONE count source
  (11,925 experiments, 240 solver types). Counter, api.json, sitemap all derive
  from it; `code/qa/check.py` build gates fail on any disagreement.
- **Loading states:** LOADING / LIVE / INDEX ERROR / OFFLINE—CACHED / NO DATA,
  20s timeout, Retry button, localStorage-cached manifest fallback. No more
  indefinite "…".
- **Record standard JAH-EXP-RECORD/1.0** (`experiment.schema.json`): every record
  now carries `status` SOLVER-GENERATED, `simulation_status` SIMULATED,
  `physical_status` NOT-PERFORMED, `measured` false, `data_status`,
  `solver_engine` SOLVER-ENGINE-V1, `seed_algorithm` FNV-1a-32,
  machine-readable `safety_level`, `null_hypothesis`, `type_id`.
- **Solver-type IDs:** JAH-EXP-TYPE-000001…000240 stamped in catalog order
  (`solver-type.schema.json`); A–Z machine-readable catalog at
  `data/solver-catalog.json`.
- **Determinism published:** `docs/DETERMINISM.md` spec, permanent test vectors
  (`docs/test-vectors.json`, byte-stable), per-record content hashes
  (`data/hashes.json.gz`), in-browser `?verify=JAH-EXP-######` re-solve check.
- **Honest Science strengthened:** formal "solved ≠ performed" definition on the
  page and in `methodology.html`; every number carries model + seed + units;
  "Run Experiment" clarified as running the solver's model, not physical execution.
- **Measured-data pathway:** per-record "Add my measurements" (device-local) with
  simulation-vs-observed comparison; simulation values never overwritten;
  record flips to `data_status: MIXED` on export.
- **Downloads:** JSON (with honesty note + observed data), CSV measurements, text.
- **AI hardened:** answers from the record only, NOT RECORDED when absent,
  "Sources: record …" on every answer, honors safety classification
  (refuses instructions on hazardous records), "Surprise me" skips hazardous types.
- **Catalog:** discipline filter, exact JAH-EXP-###### lookup hint, type cards show
  type ID + live record count + safety level, `?type=` deep links.
- **Machine-readable:** `ai-manifest.json`, `llms.txt`, `manifest.schema.json`,
  `methodology.html`, `data/health.json` from QA.
- **Drip:** every generation run now ends with the QA gates; exit 3 on failure.

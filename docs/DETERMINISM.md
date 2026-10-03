# Determinism Spec — The Signature Experiment Solver

Engine: **SOLVER-ENGINE-V1** (version 1.0). This document is the normative
specification. The engine code (`code/engine.js`) is the reference
implementation; if they ever disagree, this document wins and the code is
treated as a bug.

## 1. What "deterministic" means here

The same (solver type, seed, parameter overrides) ALWAYS produces the same
complete experiment record, on any device, in any browser, today or in ten
years. There is no network call, no clock read, no locale-dependent
formatting anywhere in the solve path.

## 2. Versioning promise

- **SOLVER-ENGINE-V1** is immutable. Bug fixes and new behavior go into
  SOLVER-ENGINE-V2 (a new engine ID and version number).
- Every record carries `solver_engine` + `solver_engine_version`, so any
  record can always be re-solved by the exact engine that made it.
- If `docs/test-vectors.json` ever regenerates with different `output_hash`
  values, the engine changed silently: that is a release-blocking bug.

## 3. Seed algorithm

- Seed input string: `typeKey + ":" + seed + ":" + JSON.stringify(params)`
- Hash: **FNV-1a-32** over the UTF-16 code units of that string
  (the standard JS implementation; see `fnv1a` in engine.js).
- PRNG: **mulberry32** seeded with the FNV-1a-32 output.
- Per-type archive seeds live in `data/state.json` → `type_seed`
  (e.g. free-fall = 1). A record's full provenance is
  (typeKey, type_seed, params).

## 4. Normalization

- Parameter values are parsed with `parseFloat` after regex extraction;
  defaults come from the solver-type definition (`code/solver_types.json`).
- All displayed numbers go through `fmt(x)`: 3 significant figures,
  trailing-zero trimmed, plain ASCII (`e` notation only for |x| ≥ 1e21,
  where JS switches automatically — never for solver outputs).
- No `Date`, `Math.random`, `performance.now`, or locale APIs in the solve path.

## 5. Input hash / output hash

- **INPUT-HASH** = `sha256` of the canonical JSON
  `{typeKey, seed, params}` (keys sorted recursively, no whitespace).
- **OUTPUT-HASH** = `sha256` of the canonical JSON of the complete record.
- Canonical form: `JSON.stringify` with keys sorted recursively,
  separators `(",", ":")`, UTF-8. Python reference: `code/seed.py`
  `canonical_bytes()`. Browser reference: the `canonical()` helper in
  index.html's verify view.
- Every archived record's output hash is published in
  `data/hashes.json.gz` (`{exp_id: hex}`), rebuilt by every drip run.
- `?verify=JAH-EXP-000123` re-solves the record in the browser and
  compares against the published hash: MATCH / MISMATCH.

## 6. Permanent test vectors

`docs/test-vectors.json` — 10 (type, seed, overrides) cases with their
`input_hash` and `output_hash` under SOLVER-ENGINE-V1. Regenerate with
`node code/make_test_vectors.js`; the file must come out byte-identical.
It is checked by `code/qa/check.py`.

## 7. What determinism does NOT claim

- Deterministic ≠ physically true. The models are textbook closed-form
  formulas (projectile motion, Ohm's law, Michaelis–Menten, …) with
  documented assumptions (`assumptions` field) and limitations
  (`limitations` field). A deterministic simulation is still a simulation:
  every record says so in `simulation_status`, `data_status`, and
  `data_type_note`.
- Deterministic ≠ validated. `total_validated_experiments` in the
  manifest counts records confirmed against real measurements. Today: 0.
  When a user adds measured data, the record becomes `data_status: MIXED`
  and the simulation values are never overwritten.

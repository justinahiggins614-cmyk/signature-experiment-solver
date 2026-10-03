#!/usr/bin/env node
/* Permanent determinism test vectors for SOLVER-ENGINE-V1.
   Regenerating must produce BYTE-IDENTICAL output_hash values.
   If any hash changes, the engine changed: bump the engine version. */
const E = require('../code/engine.js');
const crypto = require('crypto');
const fs = require('fs');
function csort(o) {
  if (Array.isArray(o)) return o.map(csort);
  if (o && typeof o === 'object') {
    const out = {};
    Object.keys(o).sort().forEach(function (k) { out[k] = csort(o[k]); });
    return out;
  }
  return o;
}
const cases = [
  ['free-fall', 1, {}], ['projectile-motion', 7, {}], ['pendulum-period', 42, {}],
  ['ohms-law', 3, { voltage: 9 }], ['acid-base-titration', 11, {}],
  ['photosynthesis-rate', 5, {}], ['bernoulli', 99, {}],
  ['half-life', 13, {}], ['universal-design', 2, {}], ['rocket-staging', 21, {}]
];
const vecs = cases.map(function (c) {
  const rec = E.solve(c[0], c[1], c[2], 'JAH-EXP-TEST');
  const canonical = JSON.stringify(csort(rec));
  const inputHash = crypto.createHash('sha256')
    .update(JSON.stringify(csort({ typeKey: c[0], seed: c[1], params: rec.params })), 'utf8').digest('hex');
  return {
    typeKey: c[0], seed: c[1], overrides: c[2],
    note: 'test IDs are placeholders; the hash covers all solver output fields',
    input_hash: 'sha256:' + inputHash,
    output_hash: 'sha256:' + crypto.createHash('sha256').update(canonical, 'utf8').digest('hex'),
    params: rec.params, title: rec.title, status: rec.status,
    solver_engine: rec.solver_engine, safety_level: rec.safety_level
  };
});
fs.writeFileSync('docs/test-vectors.json', JSON.stringify({
  engine: 'SOLVER-ENGINE-V1', seed_algorithm: 'FNV-1a-32', prng: 'mulberry32',
  generated: '2026-10-03', vectors: vecs
}, null, 1) + '\n');
console.log('wrote', vecs.length, 'vectors');

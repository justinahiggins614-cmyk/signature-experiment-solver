#!/usr/bin/env python3
"""Build gates for The Signature Experiment Solver.

Fails (exit 1) on ANY integrity problem:
- duplicate / missing / non-contiguous experiment IDs
- count disagreement between manifest, api, index, chunks, HTML stamp
- invalid solver-type records or duplicate type IDs
- index hash mismatch vs experiment-manifest.json
- content-hash sample mismatch (deterministic re-solve)
- invalid sitemap XML or URL count mismatch
- stale hard-coded counters in index.html
- JS syntax errors in engine.js / inline scripts

Usage: python3 code/qa/check.py [--quick]   (--quick skips the hash sample)
"""
import gzip, hashlib, json, os, random, re, subprocess, sys, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")
FAIL = []

def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" — " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAIL.append(name + (" — " + str(detail) if detail else ""))

def load(p):
    with open(p) as f:
        return json.load(f)

def main():
    quick = "--quick" in sys.argv
    # ---- chunks: IDs unique + contiguous ----
    manifest = load(os.path.join(DATA, "manifest.json"))
    rows = []
    for fn in manifest["chunks"]:
        with gzip.open(os.path.join(DATA, "chunks", fn), "rt") as fh:
            rows.extend(json.load(fh))
    ids = [r[0] for r in rows]
    check("chunk IDs unique", len(ids) == len(set(ids)),
          f"{len(ids) - len(set(ids))} dupes")
    nums = sorted(int(i.split("-")[2]) for i in ids)
    check("chunk IDs contiguous 1..N", nums == list(range(1, len(nums) + 1)),
          f"first={nums[0] if nums else None} last={nums[-1] if nums else None} n={len(nums)}")
    check("manifest count == chunk rows", manifest["count"] == len(rows),
          f"{manifest['count']} vs {len(rows)}")

    # ---- index ----
    with gzip.open(os.path.join(DATA, "index.json.gz"), "rt") as fh:
        idx = json.load(fh)
    check("index rows == chunk rows", len(idx) == len(rows), f"{len(idx)} vs {len(rows)}")
    check("index IDs match chunks", [r[0] for r in idx] == ids)

    # ---- authoritative manifest ----
    expm_path = os.path.join(ROOT, "experiment-manifest.json")
    check("experiment-manifest.json exists", os.path.exists(expm_path))
    if os.path.exists(expm_path):
        expm = load(expm_path)
        check("manifest total == chunk rows", expm["total_experiments"] == len(rows),
              f"{expm['total_experiments']} vs {len(rows)}")
        check("manifest earliest/latest", expm["earliest_exp_id"] == ids[0] and expm["latest_exp_id"] == ids[-1],
              f"{expm.get('earliest_exp_id')}..{expm.get('latest_exp_id')}")
        real_idx_hash = "sha256:" + hashlib.sha256(open(os.path.join(DATA, "index.json.gz"), "rb").read()).hexdigest()
        check("manifest index_hash matches", expm["index_hash"] == real_idx_hash)
        check("manifest schema_version", expm.get("schema_version") == "JAH-EXP-RECORD/1.0")
        check("manifest solver_engine", expm.get("solver_engine") == "SOLVER-ENGINE-V1")

    # ---- api.json derives from manifest ----
    api = load(os.path.join(ROOT, "api.json"))
    check("api.json count == chunk rows", api["experiments"] == len(rows),
          f"{api['experiments']} vs {len(rows)}")

    # ---- HTML stamp ----
    html = open(os.path.join(ROOT, "index.html")).read()
    m = re.search(r'<p class="staticcount">([\d,]+) solved experiment records', html)
    check("HTML static count stamped", bool(m))
    if m:
        check("HTML static count == chunk rows", int(m.group(1).replace(",", "")) == len(rows),
              f"stamped {m.group(1)} vs {len(rows)}")
    check("no stale hard-coded counters", not re.search(r"4,925|3,925|2,925", html))
    # only the live counter element + the stamp may carry counts
    check("counter element present", 'id="expcount"' in html)

    # ---- solver types ----
    types = load(os.path.join(ROOT, "code", "solver_types.json"))
    keys = [t["key"] for t in types]
    tids = [t.get("type_id") for t in types]
    check("solver types have required fields",
          all(all(k in t for k in ("key", "name", "discipline", "blurb", "keywords", "model", "params", "type_id")) for t in types))
    check("solver type keys unique", len(keys) == len(set(keys)))
    check("solver type_ids unique", len(tids) == len(set(tids)) and all(tids))
    check("solver type_ids sequential", sorted(tids) == ["JAH-EXP-TYPE-%06d" % i for i in range(1, len(types) + 1)])

    # ---- content-hash sample (deterministic re-solve) ----
    if not quick and os.path.exists(os.path.join(DATA, "hashes.json.gz")):
        with gzip.open(os.path.join(DATA, "hashes.json.gz"), "rt") as fh:
            hashes = json.load(fh)
        check("hashes cover all records", len(hashes) == len(rows), f"{len(hashes)} vs {len(rows)}")
        sample = random.Random(20261003).sample(rows, min(20, len(rows)))
        batch = json.dumps([[r[0], r[1], r[2]] for r in sample])
        out = subprocess.run(["node", "code/engine.js", "fullbatch", batch],
                             capture_output=True, text=True, cwd=ROOT)
        ok = out.returncode == 0
        mism = 0
        if ok:
            for rec in json.loads(out.stdout):
                canon = json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                if hashlib.sha256(canon).hexdigest() != hashes.get(rec["id"]):
                    mism += 1
        check("hash sample re-solve matches", ok and mism == 0, f"mismatches={mism}")
    else:
        print("SKIP hash sample (--quick or no hashes file)")

    # ---- sitemap ----
    sm_path = os.path.join(ROOT, "sitemap.xml")
    try:
        ET.parse(sm_path)
        sm_ok = True
    except Exception as e:
        sm_ok = False
    check("sitemap.xml valid XML", sm_ok)
    exp1 = os.path.join(ROOT, "sitemap-exp-1.xml")
    if os.path.exists(exp1):
        try:
            tree = ET.parse(exp1)
            urls = tree.getroot().findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            check("sitemap-exp-1 URL count == records", len(urls) == len(rows),
                  f"{len(urls)} vs {len(rows)}")
        except Exception as e:
            check("sitemap-exp-1 parseable", False, str(e)[:100])

    # ---- JS syntax ----
    r = subprocess.run(["node", "--check", "code/engine.js"], capture_output=True, cwd=ROOT)
    check("engine.js node --check", r.returncode == 0)
    scripts = re.findall(r"<script>([\s\S]*?)</script>", html)
    js_ok = True
    import tempfile
    for i, s in enumerate(scripts):
        if not s.strip():
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
            tf.write(s)
            tfp = tf.name
        rr = subprocess.run(["node", "--check", tfp],
                            capture_output=True, text=True, cwd=ROOT)
        os.unlink(tfp)
        if rr.returncode != 0:
            js_ok = False
            print("   inline script", i, ":", rr.stderr[:200])
    check("inline scripts node --check", js_ok, f"{len(scripts)} blocks")

    # ---- deep-link spot check ----
    for spot in (ids[0], ids[len(ids) // 2], ids[-1]):
        check(f"deep link target {spot} in index", any(r[0] == spot for r in idx))

    print()
    if FAIL:
        print(f"{len(FAIL)} GATE(S) FAILED:")
        for f in FAIL:
            print(" -", f)
        sys.exit(1)
    print("ALL GATES PASS")

if __name__ == "__main__":
    main()

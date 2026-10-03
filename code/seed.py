#!/usr/bin/env python3
"""Seed / drip the Experiment Solver archive.

Generates experiment rows via the deterministic JS engine
(node code/engine.js batch), appends compact rows to gz chunks,
and rebuilds manifest + index + sitemap + api.json.

Rows are compact [id, typeKey, seed] — the full experiment is
re-solved client-side deterministically, so zero storage per record.

Usage:
  python3 code/seed.py --per-type 8     # initial seed
  python3 code/drip.py --n 1000         # 2h drip
"""
import argparse, gzip, hashlib, json, os, subprocess, sys
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CODE = os.path.join(ROOT, "code")
CHUNKS = os.path.join(DATA, "chunks")
CHUNK_SIZE = 150
SITE = "https://justinahiggins614-cmyk.github.io/signature-experiment-solver/"

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError("node failed: " + r.stderr[:800])
    return r.stdout

def load_types():
    return json.load(open(os.path.join(ROOT, "code", "solver_types.json")))

def load_state():
    p = os.path.join(DATA, "state.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {"next_id": 1, "type_seed": {}, "type_idx": 0}

def save_state(s):
    json.dump(s, open(os.path.join(DATA, "state.json"), "w"), indent=1)

def load_manifest():
    p = os.path.join(DATA, "manifest.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {"chunks": [], "count": 0}

def save_manifest(m):
    json.dump(m, open(os.path.join(DATA, "manifest.json"), "w"), indent=1)

def append_rows(new_rows):
    """new_rows: list of [id, typeKey, seed]. Appends to chunks, returns manifest."""
    manifest = load_manifest()
    chunks = manifest["chunks"]
    os.makedirs(CHUNKS, exist_ok=True)
    buf = []
    if chunks:
        last = chunks[-1]
        with gzip.open(os.path.join(CHUNKS, last), "rt") as fh:
            buf = json.load(fh)
        if len(buf) < CHUNK_SIZE:
            chunks.pop()
        else:
            buf = []
    for row in new_rows:
        buf.append(row)
        if len(buf) >= CHUNK_SIZE:
            fn = "exp-c%05d.json.gz" % len(chunks)
            with gzip.open(os.path.join(CHUNKS, fn), "wt") as fh:
                json.dump(buf, fh)
            chunks.append(fn)
            buf = []
    if buf:
        fn = "exp-c%05d.json.gz" % len(chunks)
        with gzip.open(os.path.join(CHUNKS, fn), "wt") as fh:
            json.dump(buf, fh)
        chunks.append(fn)
    manifest["count"] += len(new_rows)
    manifest["chunks"] = chunks
    save_manifest(manifest)
    return manifest

def canonical_bytes(obj):
    """Canonical serialization for content hashing: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

def build_hashes(idx_rows):
    """Re-solve every archived record deterministically and hash the canonical form.
    Returns {exp_id: sha256_hex}. Stored in data/hashes.json.gz."""
    hashes = {}
    for i in range(0, len(idx_rows), 2000):
        batch = json.dumps([[r[0], r[1], r[2]] for r in idx_rows[i:i + 2000]])
        out = sh(["node", "code/engine.js", "fullbatch", batch])
        for rec in json.loads(out):
            hashes[rec["id"]] = hashlib.sha256(canonical_bytes(rec)).hexdigest()
    with gzip.open(os.path.join(DATA, "hashes.json.gz"), "wt") as fh:
        json.dump(hashes, fh)
    return hashes

def build_experiment_manifest(manifest, idx_rows):
    """Authoritative experiment-manifest.json — the ONE count source.
    Every visible counter, the API, and the sitemap derive from this."""
    count = manifest["count"]
    idx_path = os.path.join(DATA, "index.json.gz")
    idx_hash = hashlib.sha256(open(idx_path, "rb").read()).hexdigest()
    hashes_path = os.path.join(DATA, "hashes.json.gz")
    hashes_hash = hashlib.sha256(open(hashes_path, "rb").read()).hexdigest()
    types = load_types()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    m = {
        "site_id": "SIGNATURE-EXPERIMENT-SOLVER",
        "site_name": "The Signature Experiment Solver",
        "site_version": "1.0",
        "archive_version": "2026-10-03",
        "schema_version": "JAH-EXP-RECORD/1.0",
        "total_experiments": count,
        "total_solver_types": len(types),
        "total_simulations": count,
        "total_validated_experiments": 0,
        "earliest_exp_id": idx_rows[0][0] if idx_rows else None,
        "latest_exp_id": idx_rows[-1][0] if idx_rows else None,
        "index_version": "1.0",
        "index_hash": "sha256:" + idx_hash,
        "hashes_file": "data/hashes.json.gz",
        "hashes_hash": "sha256:" + hashes_hash,
        "solver_engine": "SOLVER-ENGINE-V1",
        "solver_engine_version": "1.0",
        "seed_algorithm": "FNV-1a-32",
        "prng_algorithm": "mulberry32",
        "chunk_size": CHUNK_SIZE,
        "chunk_count": len(manifest["chunks"]),
        "goal": 1000000,
        "disciplines": sorted(set(t["discipline"] for t in types)),
        "last_updated": now,
        "honesty": "All numeric results are solver-computed simulations, labeled as such; never presented as measured lab data.",
        "license": "Original solver-generated works by the Signature system.",
        "canonical_url": SITE,
        "deep_link_pattern": SITE + "?exp=JAH-EXP-000001",
    }
    json.dump(m, open(os.path.join(ROOT, "experiment-manifest.json"), "w"), indent=1)
    return m

def rebuild_derived(manifest):
    count = manifest["count"]
    # gather all rows (id,type,seed) for the index
    all_rows = []
    for fn in manifest["chunks"]:
        with gzip.open(os.path.join(CHUNKS, fn), "rt") as fh:
            all_rows.extend(json.load(fh))
    # index via node batch (titles + disciplines)
    idx_rows = []
    for i in range(0, len(all_rows), 2000):
        batch = json.dumps([[r[0], r[1], r[2]] for r in all_rows[i:i+2000]])
        out = sh(["node", "code/engine.js", "batch", batch])
        idx_rows.extend(json.loads(out))
    with gzip.open(os.path.join(DATA, "index.json.gz"), "wt") as fh:
        json.dump(idx_rows, fh)
    # content hashes for every record (deterministic re-solve + canonical hash)
    build_hashes(idx_rows)
    # authoritative manifest — the ONE count source
    exp_manifest = build_experiment_manifest(manifest, idx_rows)
    # standardized machine feed + static bot-readable batch pages
    import build_static
    build_static.build_feed(idx_rows)
    build_static.build_solver_catalog(idx_rows)
    static_pages = build_static.build_pages()
    # api.json derives from the authoritative manifest (never hand-typed)
    api = {
        "site": exp_manifest["site_name"],
        "url": SITE,
        "experiments": exp_manifest["total_experiments"],
        "goal": exp_manifest["goal"],
        "solver_types": exp_manifest["total_solver_types"],
        "disciplines": exp_manifest["disciplines"],
        "chunk_size": CHUNK_SIZE,
        "manifest": "experiment-manifest.json",
        "data_manifest": "data/manifest.json",
        "index": "data/index.json.gz",
        "index_hash": exp_manifest["index_hash"],
        "catalog_feed": "data/experiments-catalog.json",
        "static_pages": "static/index.html",
        "deep_link": exp_manifest["deep_link_pattern"],
        "solver_engine": exp_manifest["solver_engine"],
        "title_status": "PROVISIONAL — awaiting Manon's confirmation",
        "honesty": exp_manifest["honesty"],
        "last_updated": exp_manifest["last_updated"],
    }
    json.dump(api, open(os.path.join(ROOT, "api.json"), "w"), indent=1)
    # sitemap (sharded, 50k per file)
    build_sitemap(idx_rows, static_pages)
    # stamp static count into index.html
    stamp_count(count)
    return count

def build_sitemap(idx_rows, static_pages=None):
    per = 50000
    files = []
    for i in range(0, len(idx_rows), per):
        n = i // per + 1
        fn = "sitemap-exp-%d.xml" % n
        urls = []
        for r in idx_rows[i:i+per]:
            urls.append("  <url><loc>%s?exp=%s</loc></url>" % (SITE, r[0]))
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
               "\n".join(urls) + "\n</urlset>\n")
        open(os.path.join(ROOT, fn), "w").write(xml)
        files.append(fn)
    # index
    entries = "\n".join(
        '  <sitemap><loc>%s%s</loc></sitemap>' % (SITE, f) for f in files)
    entries += '\n  <sitemap><loc>%spages.xml</loc></sitemap>' % SITE
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        entries + "\n</sitemapindex>\n")
    # static pages sitemap (home + browse views + pre-rendered experiment batch pages)
    static_entries = ['  <url><loc>%s%s</loc></url>\n' % (SITE, pg)
                      for pg in ["", "?browse=az", "?browse=latest",
                                 "methodology.html", "static/index.html"] +
                      ["static/" + f for f in (static_pages or [])]]
    open(os.path.join(ROOT, "pages.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(static_entries) + "</urlset>\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n" % SITE)
    # remove stale shard files beyond current set
    import glob
    for f in glob.glob(os.path.join(ROOT, "sitemap-exp-*.xml")):
        if os.path.basename(f) not in files:
            os.remove(f)

def stamp_count(count):
    p = os.path.join(ROOT, "index.html")
    if not os.path.exists(p):
        return
    h = open(p).read()
    marker = "<!--STATIC-COUNT-->"
    stamp = ('<p class="staticcount">%s solved experiment records and counting — '
             'marching to 1,000,000.</p>' % f"{count:,}")
    import re
    pat = re.escape(marker) + r"\n<p class=\"staticcount\">.*?</p>"
    if re.search(pat, h):
        # replace the stamped line in place (idempotent)
        h = re.sub(pat, marker + "\n" + stamp, h, count=1)
    else:
        h = h.replace(marker, marker + "\n" + stamp, 1)
    # collapse any stray duplicate stamp lines to exactly one
    dup = r"(<p class=\"staticcount\">.*?</p>)\n<p class=\"staticcount\">.*?</p>"
    while re.search(dup, h):
        h = re.sub(dup, r"\1", h, count=1)
    # re-stamp the hero counter chip's initial content (what shows before JS loads)
    h = re.sub(r'(<span id="expcount">)[^<]*(</span>)',
               r"\g<1>%s\g<2>" % f"{count:,}", h, count=1)
    open(p, "w").write(h)

def generate(n, per_type=None):
    """Generate n new experiment rows. per_type mode: K per type (seed)."""
    types = load_types()
    state = load_state()
    ts = state.setdefault("type_seed", {})
    new_rows = []
    if per_type:
        for t in types:
            key = t["key"]
            s0 = ts.get(key, 1)
            for j in range(per_type):
                seed = s0 + j
                eid = "JAH-EXP-%06d" % state["next_id"]
                new_rows.append([eid, key, seed])
                state["next_id"] += 1
            ts[key] = s0 + per_type
            print(f"  {key}: ids {state['next_id']-per_type}..{state['next_id']-1}", flush=True)
    else:
        idx = state.get("type_idx", 0)
        for _ in range(n):
            t = types[idx % len(types)]
            key = t["key"]
            seed = ts.get(key, 1)
            eid = "JAH-EXP-%06d" % state["next_id"]
            new_rows.append([eid, key, seed])
            ts[key] = seed + 1
            state["next_id"] += 1
            idx += 1
        state["type_idx"] = idx
    save_state(state)
    manifest = append_rows(new_rows)
    count = rebuild_derived(manifest)
    print(f"total: {count}")
    # Build gate: fail LOUDLY on any integrity problem (never silent).
    qa = subprocess.run([sys.executable, os.path.join(CODE, "qa", "check.py"), "--quick"],
                        cwd=ROOT)
    if qa.returncode != 0:
        print("QA GATES FAILED — investigate before committing.", flush=True)
        raise SystemExit(3)
    print("QA gates pass.", flush=True)
    return count

def repo_size_ok():
    total = 0
    for dp, _, fns in os.walk(DATA):
        for f in fns:
            total += os.path.getsize(os.path.join(dp, f))
    gb = total / (1024 ** 3)
    print(f"data dir: {gb:.2f} GB")
    return gb < 0.8

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-type", type=int, default=0)
    ap.add_argument("--n", type=int, default=1000)
    a = ap.parse_args()
    if not repo_size_ok():
        print("REPO-SIZE GUARD TRIPPED (>0.8GB) — not generating")
        sys.exit(2)
    if a.per_type:
        generate(0, per_type=a.per_type)
    else:
        generate(a.n)

if __name__ == "__main__":
    main()

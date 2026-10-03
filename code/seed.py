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
import argparse, gzip, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
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
    # standardized machine feed + static bot-readable batch pages
    import build_static
    build_static.build_feed(idx_rows)
    static_pages = build_static.build_pages()
    # api.json
    types = load_types()
    api = {
        "site": "The Signature Experiment Solver",
        "url": SITE,
        "experiments": count,
        "goal": 1000000,
        "solver_types": len(types),
        "disciplines": sorted(set(t["discipline"] for t in types)),
        "chunk_size": CHUNK_SIZE,
        "manifest": "data/manifest.json",
        "index": "data/index.json.gz",
        "catalog_feed": "data/experiments-catalog.json",
        "static_pages": "static/index.html",
        "deep_link": SITE + "?exp=JAH-EXP-000001",
        "title_status": "PROVISIONAL — awaiting Manon's confirmation",
        "honesty": "All numeric results are solver-computed simulations, labeled as such; never presented as measured lab data.",
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
                                 "static/index.html"] +
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

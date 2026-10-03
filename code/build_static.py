#!/usr/bin/env python3
"""Build static bot-readable experiment batch pages + experiments-catalog.json feed.

Called from seed.py rebuild_derived() on every 2h drip (cheap: a few seconds for
~5k records). Writes:
  static/exp-NNNNNN-NNNNNN.html  — pre-rendered tables: ID, title, discipline,
                                   conclusion + deep link (250 records per page)
  static/index.html               — index of all batch pages
  data/experiments-catalog.json   — standardized machine-readable feed
"""
import json
import os
import gzip
import subprocess
import html
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
STATIC = os.path.join(ROOT, "static")
SITE = "https://justinahiggins614-cmyk.github.io/signature-experiment-solver/"
PER_PAGE = 250

NODE_HELPER = r"""
var E=require('./code/engine.js');
var rows=JSON.parse(process.argv[1]);
var out=rows.map(function(r){
  var rec=E.solve(r[1],r[2],{});
  return {id:r[0],title:rec.title,discipline:rec.discipline||'',
    conclusion:rec.conclusion||'',
    url:'https://justinahiggins614-cmyk.github.io/signature-experiment-solver/?exp='+r[0]};
});
process.stdout.write(JSON.stringify(out));
"""


def all_rows():
    manifest = json.load(open(os.path.join(DATA, "manifest.json")))
    rows = []
    for fn in manifest["chunks"]:
        with gzip.open(os.path.join(DATA, "chunks", fn), "rt") as fh:
            rows.extend(json.load(fh))
    # numeric ID order (guards against any non-catalog row forms)
    rows.sort(key=lambda r: int(r[0].split("-")[-1]) if r[0].split("-")[-1].isdigit() else 0)
    return rows


def solve_batch(batch):
    p = subprocess.run(["node", "-e", NODE_HELPER, json.dumps(batch)],
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    if p.returncode != 0:
        raise RuntimeError("node solve failed: " + p.stderr[:500])
    return json.loads(p.stdout)


def page_html(num_from, num_to, recs, count):
    rows = []
    for r in recs:
        rows.append(
            '<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>SIMULATION</td></tr>' % (
                html.escape(r["url"]), html.escape(r["id"]),
                html.escape(r["title"]), html.escape(r["discipline"]),
                html.escape(r["conclusion"])))
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Solved experiments %d-%d - The Signature Experiment Solver</title>'
        '<meta name="description" content="Static index of solved experiments %d to %d '
        'with conclusions, for search engines and AI crawlers.">'
        '<link rel="canonical" href="%sstatic/exp-%06d-%06d.html">'
        '<style>body{font-family:Georgia,serif;max-width:1100px;margin:0 auto;'
        'padding:16px;line-height:1.5}'
        'table{border-collapse:collapse;width:100%%}th,td{border:1px solid #ccc;'
        'padding:6px 8px;vertical-align:top}th{background:#eef4ee;text-align:left}'
        'td:first-child{white-space:nowrap}</style></head><body>'
        '<p><a href="%s">&larr; The Signature Experiment Solver</a> &middot; '
        '<a href="index.html">Static batch index</a></p>'
        '<h1>Solved experiments %d-%d</h1>'
        '<p>%d of %d solved experiment records. Numeric tables are solver-computed '
        'simulations, labeled as such - not laboratory-measured data.</p>'
        '<table><tr><th>ID</th><th>Title</th><th>Discipline</th><th>Conclusion</th><th>Status</th></tr>'
        '%s</table></body></html>'
        % (num_from, num_to, num_from, num_to, SITE, num_from, num_to,
           SITE, num_from, num_to, len(recs), count, "".join(rows)))


def build_pages():
    """(Re)build all static batch pages. Returns list of page filenames."""
    os.makedirs(STATIC, exist_ok=True)
    rows = all_rows()
    pages = []
    for i in range(0, len(rows), PER_PAGE):
        batch = rows[i:i + PER_PAGE]
        recs = solve_batch(batch)
        n0 = int(batch[0][0].split("-")[-1])
        n1 = int(batch[-1][0].split("-")[-1])
        fn = "exp-%06d-%06d.html" % (n0, n1)
        open(os.path.join(STATIC, fn), "w").write(page_html(n0, n1, recs, len(rows)))
        pages.append(fn)
    # static index page
    links = "".join(
        '<li><a href="%s">Experiments %s</a></li>' % (f, f[4:-5].replace("-", "-"))
        for f in pages)
    idx = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Static experiment batch index - The Signature Experiment Solver</title>'
        '<meta name="description" content="Static index of solved experiment batches '
        'for search engines and AI crawlers.">'
        '<link rel="canonical" href="%sstatic/index.html"></head><body>'
        '<p><a href="%s">&larr; The Signature Experiment Solver</a></p>'
        '<h1>Static experiment batch index</h1>'
        '<p>%d solved experiments in %d static pages - IDs, titles and conclusions, '
        'pre-rendered for crawlers that do not run JavaScript.</p><ul>%s</ul></body></html>'
        % (SITE, SITE, len(rows), len(pages), links))
    open(os.path.join(STATIC, "index.html"), "w").write(idx)
    return pages


def build_feed(idx_rows):
    """Standardized machine-readable catalog feed."""
    feed = {
        "site": "The Signature Experiment Solver",
        "url": SITE,
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "experiments": len(idx_rows),
        "goal": 1000000,
        "deep_link_pattern": SITE + "?exp=JAH-EXP-000001",
        "records": [
            {"id": r[0], "type": r[1], "seed": r[2], "title": r[3],
             "discipline": r[4], "deep_link": SITE + "?exp=" + r[0]}
            for r in idx_rows
        ],
    }
    with open(os.path.join(DATA, "experiments-catalog.json"), "w") as fh:
        json.dump(feed, fh, indent=1)
    return feed


def build_solver_catalog(idx_rows):
    """A–Z machine-readable solver-type catalog: every type with its permanent
    ID, model provenance, safety classification, and live record count."""
    types = json.load(open(os.path.join(ROOT, "code", "solver_types.json")))
    counts = {}
    for r in idx_rows:
        counts[r[1]] = counts.get(r[1], 0) + 1
    # safety levels from the engine (deterministic rule-based classifier)
    try:
        out = subprocess.run(["node", "-e",
            "var E=require('./code/engine.js');var ts=require('./code/solver_types.json');"
            "console.log(JSON.stringify(ts.map(function(t){return [t.key,E.safetyLevel(t,null)];})))"],
            capture_output=True, text=True, cwd=ROOT, timeout=60)
        safety = dict(json.loads(out.stdout)) if out.returncode == 0 else {}
    except Exception:
        safety = {}
    catalog = {
        "site": "The Signature Experiment Solver",
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "solver_engine": "SOLVER-ENGINE-V1",
        "total_types": len(types),
        "types": [
            {"type_id": t["type_id"], "key": t["key"], "name": t["name"],
             "discipline": t["discipline"], "blurb": t["blurb"],
             "keywords": t.get("keywords", []), "model": t.get("model", ""),
             "modelName": t.get("modelName", ""),
             "safety_level": safety.get(t["key"], "SAFE-EDUCATIONAL"),
             "solved_records": counts.get(t["key"], 0),
             "deep_link": SITE + "?type=" + t["key"]}
            for t in sorted(types, key=lambda t: t["name"].lower())
        ],
    }
    with open(os.path.join(DATA, "solver-catalog.json"), "w") as fh:
        json.dump(catalog, fh, indent=1)
    return catalog


if __name__ == "__main__":
    pages = build_pages()
    print("static pages:", len(pages))

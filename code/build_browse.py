#!/usr/bin/env python3
"""Build browse.html: the full experiment-archive A-Z browse page.

Theme, JAH Network nav, pill tab bar, and hero styling are copied verbatim
from index.html at build time so the look never drifts. The shared nav is
placed just above the footer (never at the top), and the archive tab carries
the active state on the tab bar. Re-run after any index.html theme/nav/tab-bar
change to keep browse.html in sync:

    python3 code/build_browse.py

The page carries the same <!--STATIC-COUNT--> stamp marker as
index.html so seed.stamp_count() re-stamps both after every drip run.
Record data is lazy-loaded: code/solver_types.json (types) and
data/index.json.gz (compact [id,type,seed,title,discipline] rows) are
fetched only when the visitor first opens a list; gz chunks are never
fetched here - per-experiment views live on index.html (?exp=JAH-EXP-######).
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://justinahiggins614-cmyk.github.io/signature-experiment-solver/"

COUNT = json.load(open(os.path.join(ROOT, "data", "state.json")))["next_id"] - 1
COUNT_S = f"{COUNT:,}"


def extract_style(index_html):
    m = re.search(r"<style>.*?</style>", index_html, re.S)
    assert m, "no <style> block found in index.html"
    return m.group(0)


def extract_nav(index_html):
    m = re.search(r'<nav class="jahnet".*?</nav>', index_html, re.S)
    assert m, "no jahnet nav found in index.html"
    return m.group(0)


def extract_tabbar(index_html):
    # Manon's 2026-10-04 order: the same pill tab bar lives on index.html AND
    # the archive page, right after </header>. On the archive page the
    # "1 Million Archive" tab carries class "on".
    m = re.search(r'<!-- JAH TAB BAR.*?<style>(.*?)</style>', index_html, re.S)
    assert m, "no JAH TAB BAR style block found in index.html"
    style = "<style>" + m.group(1) + "</style>"
    n = re.search(r'<nav class="jtabbar" aria-label="Site sections">.*?</nav>', index_html, re.S)
    assert n, "no jtabbar nav found in index.html"
    tab = n.group(0)
    tab = tab.replace('<a class="jtab on" href="index.html">', '<a class="jtab" href="index.html">')
    assert '<a class="jtab on" href="index.html">' not in tab
    tab = tab.replace('<a class="jtab" href="browse.html">', '<a class="jtab on" href="browse.html">')
    assert '<a class="jtab on" href="browse.html">' in tab
    return style, tab


BROWSE_CSS = """
/* ---- browse.html additions (appended, never restyling index.html) ---- */
.browsesec{margin:26px 0}
.letterdet{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0}
.letterdet>summary{cursor:pointer;padding:10px 14px;font-family:Arial;font-weight:bold;font-size:1.05em;list-style:none}
.letterdet>summary::-webkit-details-marker{display:none}
.letterdet>summary:before{content:"\\25B6";margin-right:8px;color:var(--accent);font-size:.8em}
.letterdet[open]>summary:before{content:"\\25BC"}
.letterdet .lbody{padding:4px 14px 12px}
.tdet{border-top:1px solid var(--line);padding:6px 0}
.tdet>summary{cursor:pointer;font-family:Arial;list-style:none;padding:4px 0}
.tdet>summary::-webkit-details-marker{display:none}
.tdet .tname{font-weight:bold}
.explist{list-style:none;margin:8px 0 8px 12px;padding:0;font-family:Arial;font-size:.92em}
.explist li{margin:5px 0;line-height:1.45}
.explist .eid{color:var(--muted);font-size:.85em}
.bsearchwrap{position:relative;margin:14px 0}
#bsearch{width:100%;padding:12px 14px;font-size:1em;border:2px solid var(--line);border-radius:10px;font-family:Arial}
#bresults{margin:10px 0 0}
.bloadstatus{font-family:Arial;font-size:.82em;color:var(--muted);margin-left:8px}
.bloadstatus.loading{color:var(--warn)}
.bloadstatus.ready{color:var(--accent)}
.bloadstatus.error{color:var(--danger)}
.muted{color:var(--muted);font-weight:normal;font-size:.85em}
.capnote{font-family:Arial;font-size:.82em;color:var(--muted);margin:8px 0}
"""

JS = r"""
var TYPES=null, INDEX=null, BYTYPE=null, MANI=null;
var LOADSTATE="IDLE", WAITERS=[];
function E(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function setBLoad(s,msg){
  LOADSTATE=s;
  var el=document.getElementById("bloadstatus");if(!el)return;
  el.className="bloadstatus "+s.toLowerCase();
  el.textContent=s==="READY"?"DATA READY":s==="LOADING"?"LOADING DATA\u2026":s+(msg?" \u2014 "+msg:"");
  var rb=document.getElementById("bretry");if(rb)rb.style.display=(s==="ERROR")?"":"none";
}
function gzResp(r){var s=r.body.pipeThrough(new DecompressionStream("gzip"));return new Response(s).text();}
function fetchTimeout(url,ms){
  return new Promise(function(res,rej){
    var t=setTimeout(function(){rej(new Error("timeout after "+ms+"ms"));},ms||20000);
    fetch(url).then(function(r){clearTimeout(t);res(r);},function(e){clearTimeout(t);rej(e);});
  });
}
function ensureData(cb){
  if(TYPES&&INDEX){cb(null);return;}
  WAITERS.push(cb);
  if(LOADSTATE==="LOADING")return;
  if(LOADSTATE==="ERROR"){var w=WAITERS;WAITERS=[];for(var i=0;i<w.length;i++)w[i](new Error("load failed"));return;}
  LOADSTATE="LOADING";setBLoad("LOADING");
  var pT=fetchTimeout("code/solver_types.json",20000).then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return r.json();});
  var pI=fetchTimeout("data/index.json.gz",20000).then(function(r){if(!r.ok)throw new Error("HTTP "+r.status);return gzResp(r);}).then(function(t){return JSON.parse(t);});
  var pM=fetchTimeout("experiment-manifest.json",20000).then(function(r){return r.ok?r.json():null;}).catch(function(){return null;});
  Promise.all([pT,pI,pM]).then(function(v){
    TYPES=v[0];INDEX=v[1];MANI=v[2];
    BYTYPE={};
    for(var i=0;i<INDEX.length;i++){var r=INDEX[i];(BYTYPE[r[1]]=BYTYPE[r[1]]||[]).push(r);}
    setBLoad("READY");
    paintBCount(MANI&&MANI.total_experiments?MANI.total_experiments:INDEX.length);
    var w=WAITERS;WAITERS=[];for(var j=0;j<w.length;j++)w[j](null);
  },function(e){
    LOADSTATE="ERROR";setBLoad("ERROR",String(e&&e.message||e));
    var w=WAITERS;WAITERS=[];for(var i=0;i<w.length;i++)w[i](e);
  });
}
function paintBCount(c){
  var el=document.getElementById("expcount");if(el)el.textContent=Number(c).toLocaleString();
  var bar=document.getElementById("expbar");if(bar)bar.style.width=Math.min(100,Number(c)/10000)+"%";
  var sr=document.getElementById("countsrc");if(sr)sr.textContent="Count source: experiment-manifest.json";
}
function letterOf(name){var c=String(name||"").trim().charAt(0).toUpperCase();return(c>="A"&&c<="Z")?c:"#";}
function expLink(r){return '<li><a href="index.html?exp='+E(r[0])+'">'+E(r[0])+'</a> <span class="eid">'+E(r[3])+'</span> <span class="pill">'+E(r[4])+'</span></li>';}
function renderTypeLetters(){
  var host=document.getElementById("typeletters");if(!host||host.getAttribute("data-built"))return;
  host.setAttribute("data-built","1");
  var groups={};
  TYPES.slice().sort(function(a,b){return a.name<b.name?-1:1;}).forEach(function(t){
    var L=letterOf(t.name);(groups[L]=groups[L]||[]).push(t);
  });
  var order=Object.keys(groups).sort(function(a,b){return a==="#"?1:b==="#"?-1:a<b?-1:1;});
  host.innerHTML=order.map(function(L){
    var ts=groups[L];
    var inner=ts.map(function(t){
      var n=(BYTYPE[t.key]||[]).length;
      return '<details class="tdet" data-tkey="'+E(t.key)+'"><summary><span class="tname">'+E(t.name)+'</span> '+
        '<span class="pill">'+E(t.discipline)+'</span> <span class="pill id">'+n+' solved</span></summary>'+
        '<div class="tbody"><p class="muted">'+E(t.blurb||"")+' <a href="index.html?type='+E(t.key)+'">Open solver type \u2192</a></p><div class="tlist"></div></div></details>';
    }).join("");
    return '<details class="letterdet"><summary>'+(L==="#"?"#":E(L))+' <span class="muted">'+ts.length+' solver types</span></summary><div class="lbody">'+inner+'</div></details>';
  }).join("");
}
function renderNameLetters(){
  var host=document.getElementById("nameletters");if(!host||host.getAttribute("data-built"))return;
  host.setAttribute("data-built","1");
  var groups={};
  for(var i=0;i<INDEX.length;i++){var r=INDEX[i];var L=letterOf(r[3]);(groups[L]=groups[L]||[]).push(r);}
  var order=Object.keys(groups).sort(function(a,b){return a==="#"?1:b==="#"?-1:a<b?-1:1;});
  host.innerHTML=order.map(function(L){
    return '<details class="letterdet" data-nletter="'+E(L)+'"><summary>'+(L==="#"?"#":E(L))+' <span class="muted">'+groups[L].length.toLocaleString()+' experiments</span></summary><div class="lbody"><div class="nlist"></div></div></details>';
  }).join("");
}
function fillTypeBody(det){
  var body=det.querySelector(".tlist");if(!body||body.getAttribute("data-done"))return;
  body.setAttribute("data-done","1");
  var rows=BYTYPE[det.getAttribute("data-tkey")]||[];
  body.innerHTML='<ul class="explist">'+rows.map(expLink).join("")+'</ul>';
}
function fillNameBody(det){
  var body=det.querySelector(".nlist");if(!body||body.getAttribute("data-done"))return;
  body.setAttribute("data-done","1");
  var L=det.getAttribute("data-nletter");
  var rows=INDEX.filter(function(r){return letterOf(r[3])===L;});
  var cap=400, shown=rows.slice(0,cap);
  body.innerHTML='<ul class="explist">'+shown.map(expLink).join("")+'</ul>'+
    (rows.length>cap?'<p class="capnote">Showing '+cap+' of '+rows.length.toLocaleString()+' \u2014 use the search box above to narrow it down.</p>':"");
}
function doSearch(q){
  var host=document.getElementById("bresults");
  q=String(q||"").trim().toLowerCase();
  if(!q){host.innerHTML="";return;}
  var hits=[],qn=q.replace(/^jah-exp-?/,"");
  for(var i=0;i<INDEX.length&&hits.length<200;i++){
    var r=INDEX[i];
    if(r[0].toLowerCase().indexOf(q)>=0||r[0].toLowerCase().indexOf(qn)>=0||r[3].toLowerCase().indexOf(q)>=0||r[4].toLowerCase().indexOf(q)>=0)hits.push(r);
  }
  host.innerHTML='<p class="capnote">'+hits.length+(hits.length>=200?"+":"")+' matching experiment'+(hits.length===1?"":"s")+'</p>'+
    '<ul class="explist">'+hits.slice(0,60).map(expLink).join("")+'</ul>'+
    (hits.length>60?'<p class="capnote">Showing first 60 \u2014 refine your search.</p>':"");
}
document.addEventListener("DOMContentLoaded",function(){
  document.getElementById("bretry").onclick=function(){LOADSTATE="IDLE";TYPES=null;INDEX=null;BYTYPE=null;document.getElementById("typeletters").removeAttribute("data-built");document.getElementById("nameletters").removeAttribute("data-built");ensureData(function(e){if(!e){renderTypeLetters();renderNameLetters();}});};
  document.getElementById("bsearch").addEventListener("input",function(ev){
    var q=ev.target.value;
    ensureData(function(e){if(!e)doSearch(q);});
  });
  document.addEventListener("toggle",function(ev){
    var det=ev.target;
    if(!(det instanceof HTMLDetailsElement)||!det.open)return;
    if(det.classList.contains("tdet")||det.classList.contains("letterdet")){
      ensureData(function(e){if(e)return;
        renderTypeLetters();renderNameLetters();
        if(det.classList.contains("tdet"))fillTypeBody(det);
        else if(det.getAttribute("data-nletter"))fillNameBody(det);
      });
    }
  },true);
});
"""

BODY_TMPL = """<body>
<a class="skip" href="#browse">Skip to the archive</a>
<div class="wrap">
<header class="hero">
<div class="wrap">
<div class="kick">SITE 21 OF 31 &middot; THE JAH NETWORK</div>
<h1>&#128218; Browse the Full Experiment Archive</h1>
<p class="sub">Every solved experiment the Signature Experiment Solver has ever run &mdash; the full catalog, A&ndash;Z by solver type and A&ndash;Z by experiment name. Open any record for its hypothesis, Universal Matrix, findings, charts, and conclusion.</p>
<details class="statscoll" open><summary>Archive statistics</summary><div class="counter" role="status" aria-live="polite">
<span class="big"><span id="expcount">{count}</span> / 1,000,000</span>
<div class="bar" aria-hidden="true"><i id="expbar"></i></div>
<span>solved experiments</span><br>
<span id="bloadstatus" class="bloadstatus ready" role="status" aria-live="polite">DATA READY</span>
<span id="countsrc" class="countsrc"></span>
<button class="btn ghost small" id="bretry" style="display:none;margin-top:8px">&#8635; Retry loading</button>
</div></details>
<!--STATIC-COUNT-->
<p class="staticcount">{count} solved experiment records and counting &mdash; marching to 1,000,000.</p>
<p><a class="btn go" href="index.html">&#9889; Back to the solver</a> <a class="btn ghost" href="methodology.html">How it works</a></p>
</div>
</header>
{tabbarstyle}
{tabbar}


<main id="browse">
<section class="block browsesec" aria-label="Search the archive">
<h2 class="sec">Search the Archive</h2>
<div class="bsearchwrap"><input id="bsearch" type="search" placeholder="Search experiment titles, IDs, disciplines&hellip;" aria-label="Search solved experiments"><div id="bresults" role="status"></div></div>
</section>

<section class="block browsesec" aria-label="Browse by solver type">
<h2 class="sec">Browse by Solver Type <span class="pill">240 solver types</span></h2>
<p style="font-family:Arial;color:var(--muted)">Open a letter, then a solver type, to see every experiment ever solved with it. Records open in the solver with the full <b>SIMULATION</b> view.</p>
<div id="typeletters"><p class="muted">Open any letter below to load the type index&hellip;</p></div>
</section>

<section class="block browsesec" aria-label="Browse by experiment name">
<h2 class="sec">Browse by Experiment Name</h2>
<p style="font-family:Arial;color:var(--muted)">Every solved experiment, A&ndash;Z by its title.</p>
<div id="nameletters"><p class="muted">Open any letter below to load the experiment index&hellip;</p></div>
</section>
</main>

{nav}
<footer class="block" style="margin-top:26px">
<p style="font-family:Arial;color:var(--muted)"><a href="index.html">The Signature Experiment Solver</a> &middot; <a href="methodology.html">methodology</a> &middot; <a href="experiment-manifest.json">experiment-manifest.json</a> (authoritative count) &middot; <a href="api.json">api.json</a> &middot; <a href="sitemap.xml">sitemap</a></p>
<p style="font-family:Arial;color:var(--muted)"><b>Honest science:</b> every record is a solver-computed <b>SIMULATION</b>, labeled as such &mdash; never presented as laboratory-measured data. See <a href="methodology.html">methodology.html</a>.</p>
</footer>
</div>
<script>
{js}
</script>
</body>
</html>
"""

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<script>try{{if(localStorage.getItem("jah-theme")==="dark")document.documentElement.setAttribute("data-theme","dark")}}catch(e){{}}</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Browse the Full Experiment Archive A-Z — The Signature Experiment Solver</title>
<meta name="description" content="The full catalog of every solved experiment from The Signature Experiment Solver: browse A-Z by solver type and A-Z by experiment name. Thousands of solved experiments marching to 1,000,000.">
<link rel="canonical" href="{site}browse.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Browse the Full Experiment Archive A-Z — The Signature Experiment Solver">
<meta property="og:description" content="The full catalog of every solved experiment: browse A-Z by solver type and A-Z by experiment name.">
<meta property="og:url" content="{site}browse.html">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Browse the Full Experiment Archive A-Z — The Signature Experiment Solver">
<meta name="twitter:description" content="The full catalog of every solved experiment: browse A-Z by solver type and A-Z by experiment name.">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"CollectionPage","name":"Browse the Full Experiment Archive",
"url":"{site}browse.html","isPartOf":{{"@type":"WebSite","name":"The Signature Experiment Solver","url":"{site}"}},
"description":"The full A-Z catalog of solved experiments from The Signature Experiment Solver."}}
</script>
{style}
<style>{browse_css}</style>
</head>
"""


def build():
    index_html = open(os.path.join(ROOT, "index.html")).read()
    style = extract_style(index_html)
    nav = extract_nav(index_html)
    tabbarstyle, tabbar = extract_tabbar(index_html)
    # the self page is the experiment solver root in the shared nav; keep the
    # "YOU ARE HERE" marker on the solver entry (browse is a sub-page of it)
    html = (HEAD.format(site=SITE, style=style, browse_css=BROWSE_CSS) +
            BODY_TMPL.format(nav=nav, count=COUNT_S, js=JS,
                             tabbarstyle=tabbarstyle, tabbar=tabbar))
    out = os.path.join(ROOT, "browse.html")
    open(out, "w").write(html)
    print("wrote", out, "(count %s)" % COUNT_S)


if __name__ == "__main__":
    build()

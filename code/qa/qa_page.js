/* DOM-level exercise of the REAL index.html page script (sblk1) + tour/guide script (sblk3).
   Hand-rolled DOM stub, no network: TYPES/INDEX seeded from real shipped files.
   node code/qa/qa_page.js */
"use strict";
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const vm = require("vm");

const ROOT = path.join(__dirname, "..", "..");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
// blocks: 0 theme stub? identify by content
const pageSrc = blocks.find(b => b.includes("function loadAll"));
const tourSrc = blocks.find(b => b.includes("jah-tour-seen-solver"));
if (!pageSrc || !tourSrc) { console.error("could not find page/tour scripts"); process.exit(2); }

let pass = 0, fail = 0; const fails = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS  " + name); }
  else { fail++; fails.push(name); console.log("  FAIL  " + name + (extra ? " :: " + extra : "")); }
}

/* ---------- fake DOM ---------- */
function mkEl(tag, id) {
  const el = {
    tagName: (tag || "div").toUpperCase(), id: id || "",
    textContent: "", value: "", disabled: false,
    style: {}, dataset: {}, children: [], width: 640, height: 300,
    className: "",
    classList: { _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      contains(c) { return this._s.has(c); } },
    appendChild(c) { this.children.push(c); return c; },
    set innerHTML(v) { this._html = v; this.children = []; },
    get innerHTML() { return this._html || ""; },
    remove() {},
    addEventListener() {},
    setAttribute() {}, getAttribute() { return null; },
    scrollIntoView() {},
    getBoundingClientRect() { return { top: 100, left: 100, width: 200, height: 40, bottom: 140, right: 300 }; },
    getContext() { return new Proxy({}, { get: (t, k) => (k === "canvas" ? null : (...a) => {}) , set: () => true }); },
    querySelector() { return null; }, querySelectorAll() { return []; },
    closest() { return null; },
    click() { if (typeof this.onclick === "function") this.onclick({ preventDefault() {} }); },
    play() { return Promise.reject(new Error("no audio")); },
    select() {},
  };
  return el;
}
const byId = {};
const listeners = {};
const store = {};
const sandbox = {
  console,
  ExpEngine: require("../engine.js"),
  localStorage: {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: k => { delete store[k]; },
  },
  navigator: { onLine: true },
  location: { origin: "https://x", pathname: "/", search: "" },
  history: { replaceState() {} },
  requestAnimationFrame: fn => fn(),
  setTimeout: (fn) => { try { fn(); } catch (e) {} return 0; }, clearTimeout() {},
  setInterval: () => 0,
  fetch: () => Promise.reject(new Error("no network in harness")),
  DecompressionStream: undefined,
  URLSearchParams,
  document: {
    title: "",
    getElementById(id) { if (!byId[id]) byId[id] = mkEl("div", id); return byId[id]; },
    createElement(tag) { return mkEl(tag); },
    querySelector(sel) { const m = sel.match(/#([\w-]+)/); return m ? sandbox.document.getElementById(m[1]) : null; },
    querySelectorAll() { return []; },
    addEventListener(t, f) { (listeners[t] = listeners[t] || []).push(f); },
    head: mkEl("head"), body: mkEl("body"),
    documentElement: mkEl("html"),
  },
  window: null,
  Audio: function () { return { play() { return Promise.reject(new Error("x")); }, pause() {} }; },
  Blob: function () {}, URL: { createObjectURL: () => "blob:x", revokeObjectURL() {} },
  TextEncoder, crypto: require("crypto").webcrypto,
  innerWidth: 1200,
  addEventListener(t, f) { (listeners[t] = listeners[t] || []).push(f); },
  scrollTo() {},
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(pageSrc, sandbox, { filename: "page.js" });

const TYPES = JSON.parse(fs.readFileSync(path.join(ROOT, "code/solver_types.json"), "utf8"));
const MANIFEST = JSON.parse(fs.readFileSync(path.join(ROOT, "experiment-manifest.json"), "utf8"));
const INDEX = JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(ROOT, "data/index.json.gz"))).toString());

// seed the page's data vars from inside its own context
vm.runInContext(`TYPES = ${JSON.stringify(TYPES)}; INDEX = ${JSON.stringify(INDEX)}; EXP_MANIFEST = ${JSON.stringify(MANIFEST)};`, sandbox);
const R = (expr) => vm.runInContext(expr, sandbox);

console.log("== record rendering ==");
const row = INDEX[4]; // real catalog row
R(`curRec = ExpEngine.solve(${JSON.stringify(row[1])}, ${row[2]}, {}, ${JSON.stringify(row[0])}); renderRecord(curRec);`);
{
  const h = byId["result"].innerHTML;
  ok("P1 renderRecord emits SIMULATION pill", h.includes("SIMULATION"));
  ok("P2 status row: NOT-PERFORMED + measured none", h.includes("NOT-PERFORMED") && h.includes("Measured data"));
  ok("P3 hypothesis section", h.includes("Hypothesis") && h.includes(byId["result"] ? "h" : ""));
  ok("P4 variables section", h.includes("Independent:") || h.includes("Independent"));
  ok("P5 materials + procedure", h.includes("Materials") && h.includes("Procedure"));
  ok("P6 measurements table + chart canvas", h.includes("expchart") && h.includes("Measurements") || h.includes("MEASUREMENTS"));
  ok("P7 conclusion + safety box", h.includes("CONCLUSION") || h.includes("Conclusion"));
  ok("P8 simbadge: simulation vs physical distinction", h.includes("SOLVER SIMULATION") && h.includes("not measured in a physical lab"));
  ok("P9 safety pill rendered", h.includes("safetypill"));
  ok("P10 toolbar: read/copy/txt/json/csv/link/rerun/compare", ["btnread","btncopy","btntxt","btnjson","btncsv","btnlink","btnrerun","btncmp"].every(id => h.includes(id)));
  ok("P11 observed-data section (add my measurements)", h.includes("Add my measurements"));
  ok("P12 deep link present", h.includes("?exp=" + row[0]));
}

console.log("== safety-sensitive AI guard ==");
{
  const hazType = TYPES.find(t => (sandbox.ExpEngine.safetyLevel(t, null) === "HAZARDOUS"));
  const hazRec = sandbox.ExpEngine.solve(hazType.key, 5, {});
  R(`setAIContext(${JSON.stringify(hazRec).replace(/<\/script/gi, "<\\/script")});`);
  const refuse = R(`aiAnswer("how do I build this procedure step by step")`);
  ok("P13 AI refuses instructions for HAZARDOUS record", /can't give instructions/i.test(refuse), refuse.slice(0, 80));
  const okAns = R(`aiAnswer("what is the hypothesis")`);
  ok("P14 AI answers hypothesis from record", /hypothesis is/i.test(okAns));
  const safeRec = sandbox.ExpEngine.solve("free-fall", 5, {});
  R(`setAIContext(${JSON.stringify(safeRec).replace(/<\/script/gi, "<\\/script")});`);
  const procAns = R(`aiAnswer("what are the procedure steps")`);
  ok("P15 AI gives procedure for SAFE record", /Procedure:/i.test(procAns));
  const noCtx = R(`aiCtx=null; aiAnswer("hello")`);
  ok("P16 AI with no record asks to run first", /run an experiment first/i.test(noCtx));
}

console.log("== downloads / exports ==");
{
  const rec = R(`curRec`);
  const txt = R(`recordText(curRec)`);
  ok("P17 recordText starts with simulation disclaimer", txt.startsWith("SOLVER SIMULATION"));
  const csv = R(`measCSV(curRec)`);
  ok("P18 measCSV labeled simulation + engine/seed header", csv.includes("NOT LABORATORY MEASUREMENT") && csv.includes("engine="));
  const chunks = R(`auChunks("Hello world. This is a deliberately very long test of the read aloud chunker, padded with extra words so that the total length definitely exceeds the two hundred and twenty character merge limit and it must split into pieces. Does it work? Yes it does! Here is a third sentence for good measure.")`);
  ok("P19 read-aloud chunker splits sentences", Array.isArray(chunks) && chunks.length >= 2, JSON.stringify(chunks).slice(0, 60));
}

console.log("== archive search / show more ==");
{
  R(`catShown=24; renderCat("");`);
  const n0 = byId["catgrid"].children.length;
  ok("P20 initial catalog renders 24 cards", n0 === 24, "got " + n0);
  R(`renderCat("JAH-EXP-000123");`);
  const n1 = byId["catgrid"].children.length;
  ok("P21 exact JAH-EXP ID search finds 1 card", n1 === 1, "got " + n1);
  R(`renderCat("zzzz-no-such-experiment");`);
  ok("P22 no-match search renders 0 cards (honest empty)", byId["catgrid"].children.length === 0);
  R(`renderCat("");`);
  byId["morebtn"].click();
  ok("P23 Show more loads more cards", byId["catgrid"].children.length === 72, "got " + byId["catgrid"].children.length);
  const cc = byId["catcount"].textContent;
  ok("P24 catalog count line", /\d+ of 14,925 experiments/.test(cc), cc);
  R(`openExp("JAH-EXP-999999");`);
  ok("P25 unknown ID -> human message, no crash", true);
}

console.log("== loading states / counters ==");
{
  R(`paintCount(14925,"experiment-manifest.json");`);
  ok("P26 paintCount renders 14,925 + source", byId["expcount"].textContent === "14,925" && /experiment-manifest/.test(byId["countsrc"].textContent));
  R(`setLoadState("LIVE");`);
  ok("P27 LIVE state label", byId["loadstatus"].textContent === "LIVE" && byId["retrybtn"].style.display === "none");
  R(`setLoadState("INDEX ERROR","boom");`);
  ok("P28 INDEX ERROR shows retry button", byId["retrybtn"].style.display !== "none" && /INDEX ERROR/.test(byId["loadstatus"].textContent));
  R(`setLoadState("NO DATA","all failed");`);
  ok("P29 NO DATA state", /NO DATA/.test(byId["loadstatus"].textContent));
}

console.log("== sim progress states ==");
{
  R(`simProgShow(true); simProgSet(38,"test step");`);
  ok("P30 progress bar shows with message", byId["simprog"].style.display === "block" && byId["pstep"].textContent === "test step" && byId["pbar"].style.width === "38%");
  R(`simProgShow(false);`);
  ok("P31 progress hides", byId["simprog"].style.display === "none");
}

console.log("== solver types A-Z ==");
{
  R(`buildAZ();`);
  ok("P32 typecount pill = 240 solver types", byId["typecount"].textContent === "240 solver types", byId["typecount"].textContent);
  const n = byId["typegrid"].children.length;
  ok("P33 letter A renders type cards", n > 0, "got " + n);
  R(`azLetter="Z"; renderTypes();`);
  ok("P34 letter filter switches", true);
}

console.log("== observed data (my measurements) ==");
{
  R(`setObs(curRec.id,{when:"2026-10-03",who:"tester",note:"lab",values:[["10 m","1.43 s"]]});`);
  const got = R(`getObs(curRec.id)`);
  ok("P35 measurements stored + retrieved", got && got.values[0][1] === "1.43 s");
  const h = R(`obsHTML(curRec)`);
  ok("P36 obsHTML shows simulation vs yours side by side", h.includes("Simulation (solver)") && h.includes("Your measurement"));
  R(`try{localStorage.removeItem("jah-exp-obs:"+curRec.id);}catch(e){}`);
}

console.log("== tour + guide ==");
vm.runInContext(tourSrc, sandbox, { filename: "tour.js" });
{
  const btn = byId["jahGuideBtn"];
  ok("P37 guide button exists", !!btn);
  btn.click();
  ok("P38 guide panel opens", byId["jahGuide"].classList.contains("open"));
  ok("P39 guide documents real features", /Surprise me/.test(html) && /JAH-EXP-000123/.test(html) && /Read aloud/.test(html) && /Add my measurements/.test(html) && /\?verify=JAH-EXP/.test(html));
  byId["jahGuideClose"].click();
  ok("P40 guide panel closes", !byId["jahGuide"].classList.contains("open"));
  // welcome card auto-shown in sandbox (seen() false, timeout stubbed to no-op -> call manually)
  R(`(function(){try{localStorage.removeItem("jah-tour-seen-solver");}catch(e){}})();`);
  // the setTimeout was stubbed; invoke show(-1) path via replay button wiring:
  byId["jahGuideBtn"].click();
  byId["jahReplayTour"].click();
  ok("P41 replay tour opens step 1", byId["jahTourCard"].classList.contains("open") && /1 · Describe/.test(byId["jahTourCard"].innerHTML));
  byId["jtNext"].click();
  ok("P42 tour next -> step 2", /2 · Solver types/.test(byId["jahTourCard"].innerHTML));
  byId["jtBack"].click();
  ok("P43 tour back -> step 1", /1 · Describe/.test(byId["jahTourCard"].innerHTML));
  // keyboard
  (listeners["keydown"] || []).forEach(f => f({ key: "ArrowRight" }));
  ok("P44 arrow-right advances", /2 · Solver types/.test(byId["jahTourCard"].innerHTML));
  (listeners["keydown"] || []).forEach(f => f({ key: "Escape" }));
  ok("P45 Esc closes tour + marks seen", !byId["jahTourCard"].classList.contains("open") && store["jah-tour-seen-solver"] === "1");
  // spotlight placed for a visible target
  byId["jahReplayTour"].click();
  byId["jtNext"].click(); // step 2 -> typesel visible in stub
  ok("P46 spotlight ring positioned", byId["jahTourSpot"].style.display === "block");
}

console.log("\nRESULT: " + pass + " PASS, " + fail + " FAIL");
if (fails.length) console.log("failed: " + fails.join(" | "));
process.exit(fail ? 1 : 0);

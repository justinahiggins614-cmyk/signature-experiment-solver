/* =====================================================================
   THE SIGNATURE EXPERIMENT SOLVER — deterministic solver engine.
   Runs identically in Node (drip/seed) and in the browser.
   solve(typeKey, seed, overrides) -> full experiment record.
   solveText(text) -> best-matching type + extracted params.
   All numeric results are COMPUTED from built-in models and labeled
   as solver simulations — never presented as measured lab data.
   ===================================================================== */
(function (root, factory) {
  var E = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = E;
  else root.ExpEngine = E;
})(typeof self !== "undefined" ? self : this, function () {

  "use strict";

  /* ---------------- utils ---------------- */
  function fnv1a(str) {
    var h = 0x811c9dc5;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 0x01000193);
    }
    return h >>> 0;
  }
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function pick(rng, arr) { return arr[Math.floor(rng() * arr.length)]; }
  function fmt(v, unit) {    var s;
    if (Math.abs(v) >= 1000) s = v.toFixed(0);
    else if (Math.abs(v) >= 100) s = v.toFixed(1);
    else if (Math.abs(v) >= 10) s = v.toFixed(2);
    else s = v.toFixed(3);
    s = s.replace(/\.?0+$/, "");
    return s + (unit ? " " + unit : "");
  }
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function pad6(n) { var s = String(n); while (s.length < 6) s = "0" + s; return s; }

  /* ---------------- types ---------------- */
  var TYPES_ARR = null, TYPES_MAP = null;
  function loadTypes() {
    if (TYPES_MAP) return TYPES_MAP;
    var arr = null;
    try {
      if (typeof window !== "undefined" && window.EXP_TYPES) arr = window.EXP_TYPES;
      else if (typeof require !== "undefined") {
        var fs = require("fs"), path = require("path");
        var p = path.join(__dirname, "solver_types.json");
        arr = JSON.parse(fs.readFileSync(p, "utf8"));
      }
    } catch (e) { arr = []; }
    TYPES_ARR = arr || [];
    TYPES_MAP = {};
    for (var i = 0; i < TYPES_ARR.length; i++) TYPES_MAP[TYPES_ARR[i].key] = TYPES_ARR[i];
    // hidden universal design type — carries a real generic model so EVERY
    // input gets an actual matrix run, never a dead-end blueprint.
    TYPES_MAP["universal-design"] = {
      key: "universal-design", name: "Universal Matrix Runner",
      discipline: "All Sciences", blurb: "Runs any experiment as a live simulation matrix.",
      keywords: [], model: "umatrix",
      params: [
        { name: "magnitude", label: "Input magnitude", unit: "units", default: 100,
          extract: ["(\\d+(?:\\.\\d+)?)\\s*(?:mph|m\\/s|km\\/h|m|kg|g|ml|l|c|°c|degrees|v|w)?"],
          min: 0.001, max: 1000000000 }
      ],
      subject: "your test system", apparatus: "measuring tools, notebook, safety gear", safety: null
    };
    return TYPES_MAP;
  }
  function typeOf(key) { loadTypes(); return TYPES_MAP[key] || null; }
  function allTypes() { loadTypes(); return TYPES_ARR; }

  var SIM_LABEL = "SOLVER SIMULATION — every number below is computed from the built-in model for illustration. It is not laboratory-measured data.";

  /* ---------------- measurement models ----------------
     Each returns {columns:[..], rows:[[x,y]..], dep, depUnit, trend, keyStat, chart:'line'|'bar'} */
  var G = 9.8;
  var MODELS = {
    "gravity-drop": function (p) {
      var h0 = p.height, rows = [], n = 6;
      for (var i = 0; i < n; i++) {
        var h = +(h0 * (0.4 + 0.24 * i)).toFixed(2);
        rows.push([h, +(Math.sqrt(2 * h / G)).toFixed(3)]);
      }
      return { columns: ["Drop height (m)", "Fall time (s)"], rows: rows, dir: 1,
        dep: "fall time", depUnit: "s", trend: "grows with the square root of the drop height",
        keyStat: "predicted fall time " + fmt(Math.sqrt(2 * h0 / G), "s") + " for " + fmt(h0, "m"), chart: "line" };
    },
    "projectile": function (p) {
      var v = p.velocity, rows = [];
      for (var a = 15; a <= 75; a += 10) {
        var r = v * v * Math.sin(2 * a * Math.PI / 180) / G;
        rows.push([a, +r.toFixed(2)]);
      }
      var rmax = v * v / G;
      return { columns: ["Launch angle (deg)", "Range (m)"], rows: rows, dir: 1,
        dep: "range", depUnit: "m", trend: "peaks near a 45° launch angle",
        keyStat: "max range " + fmt(rmax, "m") + " at 45° with " + fmt(v, "m/s"), chart: "line" };
    },
    "pendulum": function (p) {
      var rows = [], L0 = p.length;
      for (var i = 0; i < 6; i++) {
        var L = L0 * (0.5 + 0.25 * i);
        rows.push([+L.toFixed(2), +(2 * Math.PI * Math.sqrt(L / G)).toFixed(3)]);
      }
      return { columns: ["Length (m)", "Period (s)"], rows: rows, dir: 0,
        dep: "period", depUnit: "s", trend: "grows with the square root of the length",
        keyStat: "period " + fmt(2 * Math.PI * Math.sqrt(L0 / G), "s") + " at " + fmt(L0, "m"), chart: "line" };
    },
    "hooke": function (p) {
      var k = p.k, rows = [];
      for (var m = 0.1; m <= 1.01; m += 0.15) {
        var F = m * G, x = F / k;
        rows.push([+m.toFixed(2), +(x * 100).toFixed(2)]);
      }
      return { columns: ["Mass (kg)", "Stretch (cm)"], rows: rows, dir: 1,
        dep: "stretch", depUnit: "cm", trend: "grows in direct proportion to the hanging mass",
        keyStat: "stretch " + fmt((1 * G / k) * 100, "cm") + " per kilogram at k=" + fmt(k, "N/m"), chart: "line" };
    },
    "cooling": function (p) {
      var T0 = p.t0 != null ? p.t0 : p.start_amplitude != null ? p.start_amplitude : 90;
      var Ts = 20, kk = 0.08, rows = [];
      for (var t = 0; t <= 30; t += 5) rows.push([t, +(Ts + (T0 - Ts) * Math.exp(-kk * t)).toFixed(1)]);
      return { columns: ["Time (min)", "Temperature (°C)"], rows: rows, dir: 1,
        dep: "temperature", depUnit: "°C", trend: "falls fast at first, then levels toward room temperature",
        keyStat: "about " + fmt(Ts + (T0 - Ts) * Math.exp(-kk * 10), "°C") + " after 10 min from " + fmt(T0, "°C"), chart: "line" };
    },
    "exponential-decay": function (p) {
      var h = p.halflife, rows = [];
      for (var r = 0; r <= 8; r++) rows.push([r, +(100 * Math.pow(0.5, r / h)).toFixed(1)]);
      return { columns: ["Round", "Remaining (%)"], rows: rows, dir: -1,
        dep: "remaining amount", depUnit: "%", trend: "halves every " + fmt(h, "rounds"),
        keyStat: "half-life " + fmt(h, "rounds") + " — " + fmt(100 * Math.pow(0.5, 4 / h), "%") + " left after 4 rounds", chart: "line" };
    },
    "titration": function (p) {
      var rows = [], eq = 25;
      for (var v = 0; v <= 50; v += 5) {
        var ph = 3 + 9 / (1 + Math.exp(-(v - eq) / 2.5)) - (v < eq ? (eq - v) * 0.04 : 0);
        rows.push([v, +ph.toFixed(2)]);
      }
      return { columns: ["Base added (mL)", "pH"], rows: rows, dir: -1,
        dep: "pH", depUnit: "", trend: "jumps sharply at the equivalence point",
        keyStat: "equivalence near " + fmt(eq, "mL") + " of base", chart: "line" };
    },
    "rate-temp": function (p) {
      var T0 = p.t0 != null ? p.t0 : 20, base = 120, rows = [];
      for (var T = T0; T <= T0 + 40; T += 10) rows.push([T, +(base / Math.pow(2, (T - T0) / 10)).toFixed(1)]);
      return { columns: ["Temperature (°C)", "Reaction time (s)"], rows: rows, dir: 0,
        dep: "reaction time", depUnit: "s", trend: "roughly halves for each 10 °C rise",
        keyStat: fmt(base, "s") + " at " + fmt(T0, "°C") + " → " + fmt(base / 16, "s") + " at " + fmt(T0 + 40, "°C"), chart: "line" };
    },
    "osmosis": function (p) {
      var rows = [];
      for (var c = 0; c <= 20; c += 4) rows.push([c, +(-1.1 * c).toFixed(1)]);
      return { columns: ["Salt (%)", "Mass change (%)"], rows: rows, dir: -1,
        dep: "mass change", depUnit: "%", trend: "turns from gain to loss as salt rises",
        keyStat: "near zero change around " + fmt(1, "%") + " salt (isotonic point)", chart: "line" };
    },
    "circuit": function (p) {
      var R = p.resistance != null ? p.resistance : (p.load || 100), rows = [];
      for (var V = 1; V <= 10; V++) rows.push([V, +(V / R * 1000).toFixed(2)]);
      return { columns: ["Voltage (V)", "Current (mA)"], rows: rows, dir: -1,
        dep: "current", depUnit: "mA", trend: "rises in direct proportion to the voltage",
        keyStat: fmt(1000 / R, "mA") + " per volt at " + fmt(R, "Ω"), chart: "line" };
    },
    "optics": function (p) {
      var f = p.f, rows = [];
      for (var i = 0; i < 6; i++) {
        var d_o = f * (1.5 + 0.5 * i);
        var d_i = 1 / (1 / f - 1 / d_o);
        rows.push([+d_o.toFixed(1), +d_i.toFixed(1)]);
      }
      return { columns: ["Object dist (cm)", "Image dist (cm)"], rows: rows, dir: 1,
        dep: "image distance", depUnit: "cm", trend: "shrinks toward the focal length as the object recedes",
        keyStat: "focal length " + fmt(f, "cm"), chart: "line" };
    },
    "linear": function (p, rng, T) {
      var pk = T.params[0], x0 = p[pk.name] != null ? p[pk.name] : pk.default;
      var k = 0.6 + rng() * 0.8, rows = [];
      for (var i = 0; i < 6; i++) {
        var x = x0 * (0.5 + 0.3 * i);
        rows.push([+x.toFixed(2), +(k * x).toFixed(2)]);
      }
      return { columns: [pk.label + (pk.unit ? " (" + pk.unit + ")" : ""), "Outcome (model units)"], rows: rows, dir: -1,
        dep: "outcome", depUnit: "", trend: "rises steadily with " + pk.label.toLowerCase(),
        keyStat: "illustrative slope " + k.toFixed(2) + " per " + pk.unit, chart: "line" };
    },
    "survey": function (p, rng, T) {
      var pk0 = T.params[0];
      var n = pk0 && p[pk0.name] != null ? Math.round(p[pk0.name]) : 24;
      var cats = ["Group A", "Group B", "Group C", "Group D"];
      var w = [rng(), rng(), rng(), rng()], tot = w[0] + w[1] + w[2] + w[3], rows = [];
      for (var i = 0; i < 4; i++) rows.push([cats[i], Math.round(w[i] / tot * n)]);
      return { columns: ["Group", "Count (of " + n + ")"], rows: rows, dir: 1,
        dep: "group counts", depUnit: "", trend: "splits across the groups in the seeded pattern",
        keyStat: "largest group " + rows.slice().sort(function (a, b) { return b[1] - a[1]; })[0][0] +
          " with " + rows.slice().sort(function (a, b) { return b[1] - a[1]; })[0][1] + " of " + n, chart: "bar" };
    },
    "design": function () { return null; },
    /* Universal matrix: generic saturating-response model for inputs that match
       no domain model. x sweeps the extracted input magnitude; the response rises
       steeply then levels off. Clearly labeled as illustrative — never a prediction. */
    "umatrix": function (p, rng, T) {
      var x0 = p.magnitude != null ? p.magnitude : 100;
      var unit = p._unit || "units";
      var A = 100, k = 1.4 / x0, rows = [], n = 5;
      for (var i = 0; i < n; i++) {
        var x = x0 * (0.5 + 0.25 * i);
        var y = A * (1 - Math.exp(-k * x));
        rows.push([+x.toFixed(2), +y.toFixed(2)]);
      }
      return {
        columns: ["Input magnitude (" + unit + ")", "Response (model units)"],
        rows: rows, dir: 1, dep: "system response", depUnit: "units",
        trend: "rises steeply at first, then levels off (saturating response)",
        keyStat: "response " + fmt(A * (1 - Math.exp(-k * x0)), "units") +
          " at the stated input of " + fmt(x0, unit) +
          " — generic model; treat as illustration, not prediction",
        chart: "line", generic: true
      };
    }
  };

  /* ---------------- universal matrix ----------------
     Every run — matched type or not — becomes a visible parameters × trials
     matrix: the model's own settings sweep × 3 seeded trials each with small
     measurement jitter. Findings and conclusion are derived from the matrix. */
  var DANGER_RES = [
    /uranium/i, /plutonium/i, /nuclear/i, /\bbomb\b/i, /explosive/i, /gunpowder/i,
    /\btnt\b/i, /nitroglycerin/i, /dynamite/i, /cyanide/i, /anthrax/i,
    /bleach.*ammonia|ammonia.*bleach/i, /chlorine gas/i, /mustard gas/i,
    /suicide/i, /kill (myself|him|her|them|people)/i, /bioweapon/i
  ];
  function dangerNote(query) {
    var q = String(query || "");
    for (var i = 0; i < DANGER_RES.length; i++) {
      if (DANGER_RES[i].test(q)) {
        return "⚠ DO NOT ATTEMPT THIS EXPERIMENT. It involves materials or conditions " +
          "that are dangerous or illegal to handle outside a licensed facility. " +
          "What you see here is a PURE COMPUTER SIMULATION for illustration only — " +
          "no real uranium, explosives, or hazardous materials were used, and none should be.";
      }
    }
    return null;
  }
  var UNIT_WORDS = ["mph", "m/s", "km/h", "km", "m", "cm", "mm", "kg", "g", "mg",
    "ml", "l", "°c", "c", "v", "w", "hz", "s", "min", "hours"];
  function detectUnit(query) {
    var m = String(query || "").toLowerCase().match(/(\d+(?:\.\d+)?)\s*(mph|m\/s|km\/h|km|cm|mm|kg|mg|ml|°c|hz|min|hours|v|w)\b/);
    if (m) return m[2] === "c" ? "°C" : m[2];
    return null;
  }
  function extractParams(T, low) {
    var params = {}, phit = 0;
    (T.params || []).forEach(function (p) {
      var v = p.default;
      for (var e = 0; e < p.extract.length; e++) {
        var m = low.match(new RegExp(p.extract[e], "i"));
        if (m) { v = parseFloat(m[1]); phit += 2; break; }
      }
      params[p.name] = v;
    });
    return { params: params, phit: phit };
  }
  /* Build the trials matrix from a model's own sweep table. Deterministic. */
  function buildMatrix(T, params, rng, query) {
    var meas = MODELS[T.model](params, rng, T);
    var rows = [], i, j;
    for (i = 0; i < meas.rows.length; i++) {
      var x = meas.rows[i][0], y = meas.rows[i][1], trials = [];
      for (j = 0; j < 3; j++) {
        var jit = 1 + (rng() * 2 - 1) * 0.015;
        var t = y * jit;
        if (meas.chart === "bar") t = Math.max(0, Math.round(t));
        else t = +t.toFixed(3);
        trials.push(t);
      }
      var mean = trials[0] + trials[1] + trials[2];
      mean = meas.chart === "bar" ? Math.round(mean / 3) : +(mean / 3).toFixed(3);
      rows.push({ setting: x, trials: trials, mean: mean });
    }
    return { meas: meas, rows: rows, nTrials: 3,
      dep: meas.dep, depUnit: meas.depUnit, generic: !!meas.generic };
  }
  var MODEL_INSIGHT = {
    "gravity-drop": "Doubling the drop height does NOT double the fall time — the square-root law keeps returns diminishing.",
    "projectile": "The 45° launch angle wins in a vacuum; air drag would pull the real optimum a few degrees lower.",
    "pendulum": "The period depends on length, not on the mass of the bob — a classic, testable prediction.",
    "hooke": "Stretch stays proportional to load only inside the elastic limit; past it, the spring deforms permanently.",
    "cooling": "The fastest temperature change happens in the first minutes — early readings matter most.",
    "exponential-decay": "After about 7 half-lives, less than 1% remains — the tail is long but thin.",
    "titration": "Most of the pH action happens within a few mL of the equivalence point — titrate slowly there.",
    "rate-temp": "A 10 °C rise roughly halves the reaction time — the Q10 rule of thumb in action.",
    "osmosis": "The isotonic point (near-zero mass change) is the single most informative reading.",
    "circuit": "Current tracks voltage linearly here — the signature of an ohmic resistor.",
    "optics": "As the object moves far away, the image settles at the focal length.",
    "linear": "The steady slope is the model's whole story — check whether real data bends away from the line.",
    "survey": "The seeded split is illustrative; a real survey's uncertainty shrinks with the square root of sample size.",
    "umatrix": "No domain model matched this description, so the Universal Matrix used its generic saturating-response model — every number illustrates the method, not a prediction."
  };
  function buildFindings(T, matrix, rng, danger) {
    var F = [], rows = matrix.rows, dep = matrix.dep, unit = matrix.depUnit;
    var means = rows.map(function (r) { return r.mean; });
    var imax = 0, imin = 0, i;
    for (i = 1; i < means.length; i++) {
      if (means[i] > means[imax]) imax = i;
      if (means[i] < means[imin]) imin = i;
    }
    var spread = 0;
    rows.forEach(function (r) {
      var lo = Math.min(r.trials[0], r.trials[1], r.trials[2]);
      var hi = Math.max(r.trials[0], r.trials[1], r.trials[2]);
      var m = r.mean || 1;
      spread = Math.max(spread, (hi - lo) / Math.abs(m));
    });
    spread = +(spread * 100).toFixed(1);
    if (danger) F.push("SAFETY FIRST: " + danger);
    F.push("Across " + rows.length + " matrix settings, " + dep + " " + matrix.meas.trend +
      " — from " + fmt(rows[0].mean, unit) + " at the low setting to " +
      fmt(rows[rows.length - 1].mean, unit) + " at the high setting.");
    F.push("Strongest response at setting " + fmt(rows[imax].setting) +
      ": " + fmt(rows[imax].mean, unit) + ". Weakest at " + fmt(rows[imin].setting) +
      ": " + fmt(rows[imin].mean, unit) + ".");
    F.push("Repeatability: the three trials at each setting agreed within ±" + spread +
      "% — " + (spread < 3 ? "high consistency; the model signal dominates the noise." :
        spread < 8 ? "good consistency; readings are stable." :
        "moderate scatter; more trials would tighten the means."));
    var insight = MODEL_INSIGHT[T.model] || MODEL_INSIGHT["linear"];
    F.push(insight);
    F.push("Key number: " + matrix.meas.keyStat + ".");
    return F;
  }

  /* ---------------- text builders ---------------- */
  var CTRL_BANK = ["room temperature", "humidity", "the same batch of materials",
    "the same operator", "instrument calibration", "lighting conditions",
    "time of day", "surface cleanliness", "warm-up runs"];
  var HYP = [
    "If {pl} is increased, then {dep} will {trendword}, because the underlying physical relationship links them directly.",
    "Increasing {pl} causes {dep} to {trendword}. This experiment tests that link across {n} settings.",
    "The working hypothesis: {dep} {trendword} as {pl} rises, following the {modelname} relationship."
  ];
  function trendWord(meas) {
    if (!meas) return "change";
    if (meas.dir === -1) return "decrease";
    if (meas.dir === 0) return "change sharply";
    return "increase";
  }

  function buildRecord(T, seed, params, query, customId) {
    var rng = mulberry32(fnv1a(T.key + ":" + seed + ":" + JSON.stringify(params)));
    var id = customId || ("JAH-EXP-" + pad6(seed));
    var pk = T.params[0] || null;
    var pl = pk ? pk.label : "test condition";
    var unit = (pk && pk.unit) ? pk.unit : (params._unit || "");
    var pval = pk ? fmt(params[pk.name], unit) : "";
    var danger = dangerNote(query);
    var matrix = buildMatrix(T, params, rng, query);
    var meas = matrix.meas;
    var dep = meas.dep;
    var trend = meas.trend;
    var tw = trendWord(meas);

    var title, question, hypothesis;
    if (T.key === "universal-design") {
      var qs = String(query || "custom experiment");
      title = "Universal Matrix Run — " + (qs.length > 64 ? qs.slice(0, 64) + "…" : qs);
      question = "What happens when: " + qs + "?";
      hypothesis = "The Universal Matrix sweeps the stated input magnitude across five " +
        "levels and three trials each. Expect the system response to rise steeply at " +
        "first and then level off (saturating response) — " + meas.keyStat + ".";
    } else {
      title = T.name + " — " + T.subject + (pk ? " at " + pval : "");
      question = "How does " + pl.toLowerCase() + " affect " + dep + " for " + T.subject + "?";
      hypothesis = pick(rng, HYP).replace("{pl}", pl).replace("{dep}", dep)
        .replace("{trendword}", tw).replace("{n}", meas.rows.length)
        .replace("{modelname}", T.model);
    }

    var ctrls = [];
    var cb = CTRL_BANK.slice();
    while (ctrls.length < 3 && cb.length) ctrls.push(cb.splice(Math.floor(rng() * cb.length), 1)[0]);

    var materials = [];
    T.apparatus.split(",").forEach(function (a) { materials.push(a.trim()); });
    materials.push(T.key === "universal-design" ? "the system under test" : T.subject,
      "lab notebook and pen", "safety goggles");
    if (danger || T.safety) materials.push("gloves (see safety notes)");

    var subjWord = T.key === "universal-design" ? "test system" : T.subject;
    var steps = [
      "⚗ MATRIX SETUP — lock the chamber: " + T.apparatus + ", plus " + subjWord + ", safety gear, and a lab notebook.",
      pk ? "Dial " + pl.toLowerCase() + " to the base value of " + pval + " — the matrix sweeps five levels around it." : "Define the starting condition and record it.",
      "Calibrate: zero every instrument, then run 3 back-to-back trials at each of the 5 matrix settings (" + matrix.rows.length * 3 + " readings total).",
      "Log every trial reading into the matrix grid below — no cherry-picking.",
      "Average the 3 trials per setting; keep " + ctrls.join(", ") + " constant throughout.",
      "Read the findings list: trend, strongest setting, repeatability, key number.",
      "Write the conclusion from the findings — the matrix decides, not the hypothesis."
    ];

    var findings = buildFindings(T, matrix, rng, danger);
    var results = "The matrix ran " + matrix.rows.length + " settings × " +
      matrix.nTrials + " trials (" + (matrix.rows.length * matrix.nTrials) +
      " readings). " + findings[1];
    var conclusion;
    if (matrix.generic) {
      conclusion = "The Universal Matrix completed a full run: " + dep + " " +
        trendWord(trend) + "d across the sweep, " + meas.keyStat.charAt(0).toLowerCase() +
        meas.keyStat.slice(1) + ". Because no domain model matched this description, " +
        "these are illustrative numbers from the generic saturating-response model — " +
        "a demonstration of method, not a prediction about the real world.";
    } else {
      conclusion = "The hypothesis was supported: " + dep + " " + trendWord(trend) + "d as " +
        pl.toLowerCase() + " increased. " + meas.keyStat.charAt(0).toUpperCase() + meas.keyStat.slice(1) +
        ". These are solver-computed values from the " + T.model + " model — illustrative, not lab-measured.";
    }

    return {
      id: id, type: T.key, typeName: T.name, discipline: T.discipline,
      title: title, query: query || title, seed: seed, params: params,
      question: question, hypothesis: hypothesis,
      variables: {
        independent: pl + (unit ? " (" + unit + ")" : ""),
        dependent: dep + (meas.depUnit ? " (" + meas.depUnit + ")" : ""),
        controlled: ctrls
      },
      materials: materials, procedure: steps,
      measurements: {
        columns: meas.columns, rows: meas.rows, chart: meas.chart,
        note: SIM_LABEL
      },
      matrix: {
        columns: [meas.columns[0], "Trial 1", "Trial 2", "Trial 3", "Mean " + (meas.depUnit ? "(" + meas.depUnit + ")" : "")],
        rows: matrix.rows.map(function (r) { return [r.setting].concat(r.trials, [r.mean]); }),
        nTrials: matrix.nTrials, generic: matrix.generic
      },
      findings: findings,
      results: results, conclusion: conclusion,
      safety: danger || T.safety || "Standard lab care: goggles on, tidy bench, clean spills promptly, adult supervision for young scientists.",
      sim: true,
      simLabel: (matrix.generic ? "UNIVERSAL MATRIX — " : "") + SIM_LABEL
    };
  }

  function solve(typeKey, seed, overrides, idOverride) {
    var T = typeOf(typeKey);
    if (!T) return null;
    var params = {};
    T.params.forEach(function (p) {
      var v = (overrides && overrides[p.name] != null) ? overrides[p.name] : p.default;
      if (p.min != null) v = Math.max(p.min, v);
      if (p.max != null) v = Math.min(p.max, v);
      params[p.name] = v;
    });
    return buildRecord(T, seed, params, null, idOverride || null);
  }

  /* ---------------- free-text solving ---------------- */
  function solveText(text) {
    loadTypes();
    var low = String(text).toLowerCase();
    var best = null, bestScore = 0, i, k;
    for (i = 0; i < TYPES_ARR.length; i++) {
      var T = TYPES_ARR[i], score = 0;
      for (k = 0; k < T.keywords.length; k++) {
        var kw = T.keywords[k].toLowerCase();
        if (kw.indexOf(" ") >= 0) { if (low.indexOf(kw) >= 0) score += 3; }
        else if (new RegExp("\\b" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(low)) score += 2;
      }
      score += extractParams(T, low).phit;
      if (score > bestScore) { bestScore = score; best = T; }
    }
    var seed = fnv1a("q:" + low) % 1000000;
    var chosen = (best && bestScore >= 3) ? best : TYPES_MAP["universal-design"];
    var ep = extractParams(chosen, low);
    var unit = detectUnit(text);
    if (unit) ep.params._unit = unit;
    var rec = buildRecord(chosen, seed, ep.params, text,
      "JAH-EXP-C" + (100000 + (seed % 899999)));
    rec.matchedType = (chosen === best) ? best.key : null;
    return rec;
  }

  function titleFor(typeKey, seed) {
    var T = typeOf(typeKey);
    if (!T) return typeKey + " #" + seed;
    var pk = T.params[0];
    return T.name + " — " + T.subject + (pk ? " at " + fmt(pk.default, pk.unit) : "");
  }

  /* ---------------- node CLI ---------------- */
  function cli(argv) {
    var cmd = argv[2];
    function out(o) { process.stdout.write(JSON.stringify(o)); }
    if (cmd === "solve") {
      var T = typeOf(argv[3]), seed = parseInt(argv[4], 10);
      var ov = argv[5] ? JSON.parse(argv[5]) : null;
      var params = {};
      T.params.forEach(function (p) {
        params[p.name] = (ov && ov[p.name] != null) ? ov[p.name] : p.default;
      });
      out(buildRecord(T, seed, params, null, null));
    } else if (cmd === "solvetext") {
      out(solveText(argv.slice(3).join(" ")));
    } else if (cmd === "title") {
      out({ title: titleFor(argv[3], parseInt(argv[4], 10)) });
    } else if (cmd === "batch") {
      // argv[3] = JSON array of [id, typeKey, seed]
      var rows = JSON.parse(argv[3]);
      out(rows.map(function (r) {
        return [r[0], r[1], r[2], titleFor(r[1], r[2]), (typeOf(r[1]) || {}).discipline || ""];
      }));
    } else if (cmd === "types") {
      out(allTypes().map(function (t) { return t.key; }));
    } else if (cmd === "typeinfo") {
      out(typeOf(argv[3]));
    }
  }
  if (typeof require !== "undefined" && require.main === module) cli(process.argv);

  return {
    solve: solve, solveText: solveText, titleFor: titleFor,
    typeOf: typeOf, allTypes: allTypes, esc: esc, fmt: fmt, SIM_LABEL: SIM_LABEL
  };
});

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
  function fmt(v, unit) {
    var s;
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
    // hidden universal design type
    TYPES_MAP["universal-design"] = {
      key: "universal-design", name: "Universal Experiment Designer",
      discipline: "All Sciences", blurb: "Turns any question into a full experimental plan.",
      keywords: [], model: "design", params: [],
      subject: "your test subject", apparatus: "measuring tools, notebook, safety gear", safety: null
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
    "design": function () { return null; }
  };

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
    var id = customId || ("JAH-EXP-" + String(seed).padStart(6, "0"));
    var pk = T.params[0] || null;
    var pl = pk ? pk.label : "test condition";
    var pval = pk ? fmt(params[pk.name], pk.unit) : "";
    var meas = T.model === "design" ? null : MODELS[T.model](params, rng, T);
    var dep = meas ? meas.dep : "the measured outcome";
    var trend = meas ? meas.trend : "follow the planned analysis";
    var tw = trendWord(meas);

    var title = T.name + " — " + T.subject + (pk ? " at " + pval : "");
    var question = "How does " + pl.toLowerCase() + " affect " + dep + " for " + T.subject + "?";
    var hypothesis = pick(rng, HYP).replace("{pl}", pl).replace("{dep}", dep)
      .replace("{trendword}", tw).replace("{n}", meas ? meas.rows.length : 6)
      .replace("{modelname}", T.model);

    var ctrls = [];
    var cb = CTRL_BANK.slice();
    while (ctrls.length < 3 && cb.length) ctrls.push(cb.splice(Math.floor(rng() * cb.length), 1)[0]);

    var materials = [];
    T.apparatus.split(",").forEach(function (a) { materials.push(a.trim()); });
    materials.push(T.subject, "lab notebook and pen", "safety goggles");
    if (T.safety) materials.push("gloves (see safety notes)");

    var steps = [
      "Gather everything: " + T.apparatus + ", plus " + T.subject + ", safety gear, and a lab notebook.",
      pk ? "Set " + pl.toLowerCase() + " to the starting value of " + pval + "." : "Define the starting condition and record it.",
      "Prepare the " + T.subject + " and zero every measuring instrument.",
      "Run trial 1 and record " + dep + " carefully in the data table.",
      "Repeat for at least 3 trials at this setting; keep " + ctrls.join(", ") + " constant.",
      pk ? "Change " + pl.toLowerCase() + " to the next value and repeat all trials." : "Change one condition at a time and repeat all trials.",
      "Average the repeats, tabulate " + dep + " against the changing condition, and plot the trend.",
      "Compare the pattern with the model prediction, then write the conclusion below."
    ];

    var results, conclusion;
    if (meas) {
      var first = meas.rows[0], last = meas.rows[meas.rows.length - 1];
      results = "Across " + meas.rows.length + " settings, " + dep + " " + trend + " — from " +
        fmt(first[1], meas.depUnit) + " at the low end to " + fmt(last[1], meas.depUnit) +
        " at the high end. Key finding: " + meas.keyStat + ".";
      conclusion = "The hypothesis was supported: " + dep + " " + trendWord(trend) + "d as " +
        pl.toLowerCase() + " increased. " + meas.keyStat.charAt(0).toUpperCase() + meas.keyStat.slice(1) +
        ". These are solver-computed values from the " + T.model + " model — illustrative, not lab-measured.";
    } else {
      results = "This is a design blueprint: run the procedure, fill the data table with your own measurements, and the pattern will emerge from real data.";
      conclusion = "Once run, compare the measured trend against the hypothesis and note any controlled variables that drifted.";
    }

    return {
      id: id, type: T.key, typeName: T.name, discipline: T.discipline,
      title: title, query: query || title, seed: seed, params: params,
      question: question, hypothesis: hypothesis,
      variables: {
        independent: pl + (pk && pk.unit ? " (" + pk.unit + ")" : ""),
        dependent: dep + (meas && meas.depUnit ? " (" + meas.depUnit + ")" : ""),
        controlled: ctrls
      },
      materials: materials, procedure: steps,
      measurements: meas ? {
        columns: meas.columns, rows: meas.rows, chart: meas.chart,
        note: SIM_LABEL
      } : null,
      results: results, conclusion: conclusion,
      safety: T.safety || "Standard lab care: goggles on, tidy bench, clean spills promptly, adult supervision for young scientists.",
      sim: T.model !== "design",
      simLabel: SIM_LABEL
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
    var best = null, bestScore = 0, bestParams = null;
    for (var i = 0; i < TYPES_ARR.length; i++) {
      var T = TYPES_ARR[i], score = 0;
      for (var k = 0; k < T.keywords.length; k++) {
        var kw = T.keywords[k].toLowerCase();
        if (kw.indexOf(" ") >= 0) { if (low.indexOf(kw) >= 0) score += 3; }
        else if (new RegExp("\\b" + kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(low)) score += 2;
      }
      var params = {}, phit = 0;
      T.params.forEach(function (p) {
        var v = p.default;
        for (var e = 0; e < p.extract.length; e++) {
          var m = low.match(new RegExp(p.extract[e], "i"));
          if (m) { v = parseFloat(m[1]); phit += 2; break; }
        }
        params[p.name] = v;
      });
      score += phit;
      if (score > bestScore) { bestScore = score; best = T; bestParams = params; }
    }
    var seed = fnv1a("q:" + low) % 1000000;
    if (!best || bestScore < 3) {
      var U = TYPES_MAP["universal-design"];
      var rec = buildRecord(U, seed, {}, text, "JAH-EXP-C" + (100000 + (seed % 899999)));
      rec.matchedType = null;
      return rec;
    }
    var rec2 = buildRecord(best, seed, bestParams, text, "JAH-EXP-C" + (100000 + (seed % 899999)));
    rec2.matchedType = best.key;
    return rec2;
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

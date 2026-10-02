#!/usr/bin/env python3
"""Generate code/solver_types.json — ~300 deterministic experiment-solver types.

Each type: key, name, discipline, blurb, keywords, model family, params
(with defaults + extraction regexes), subject noun, apparatus, safety note.
Run: python3 code/solver_types_gen.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUM = r"(\d+(?:\.\d+)?)"

def P(name, label, unit, default, extracts, lo=None, hi=None):
    return {"name": name, "label": label, "unit": unit, "default": default,
            "extract": extracts, "min": lo, "max": hi}

M = P  # short alias

TYPES = []
def T(key, name, disc, blurb, keywords, model, params, subject, apparatus, safety=None):
    TYPES.append({"key": key, "name": name, "discipline": disc, "blurb": blurb,
                  "keywords": keywords, "model": model, "params": params,
                  "subject": subject, "apparatus": apparatus, "safety": safety})

# ---------------- PHYSICS ----------------
PHYS = "Physics"
T("free-fall", "Free-Fall Gravity Drop", PHYS,
  "Drop objects from measured heights and time their fall.",
  ["drop", "fall", "gravity", "free fall", "freefall", "height", "drop a ball", "falling"],
  "gravity-drop",
  [M("height", "Drop height", "m", 10, [rf"from {NUM}\s*m", rf"{NUM}\s*m(?:eter)?s?\b.*(?:drop|fall|height)", rf"height(?: of)? {NUM}\s*m"], 0.5, 120)],
  "steel ball", "measuring tape, stopwatch, release clamp")
T("projectile-motion", "Projectile Launch Angle", PHYS,
  "Launch projectiles at angles and measure range.",
  ["projectile", "launch", "angle", "cannon", "catapult", "range", "trajectory"],
  "projectile",
  [M("velocity", "Launch speed", "m/s", 20, [rf"{NUM}\s*m/s", rf"speed(?: of)? {NUM}"], 1, 200),
   M("angle", "Launch angle", "deg", 45, [rf"{NUM}\s*deg(?:ree)?s?", rf"angle(?: of)? {NUM}"], 5, 85)],
  "foam dart", "protractor launcher, measuring tape, level ground")
T("pendulum-period", "Pendulum Period vs Length", PHYS,
  "Swing pendulums of different lengths and time the period.",
  ["pendulum", "swing", "period", "grandfather clock", "oscillat"],
  "pendulum",
  [M("length", "String length", "m", 1.0, [rf"{NUM}\s*m(?:eter)?s?", rf"length(?: of)? {NUM}"], 0.1, 5)],
  "brass bob", "string, support stand, stopwatch, protractor")
T("hookes-law", "Hooke's Law Spring Stretch", PHYS,
  "Hang masses on springs and measure stretch.",
  ["spring", "hooke", "stretch", "elastic", "k constant"],
  "hooke",
  [M("k", "Spring constant", "N/m", 50, [rf"k\s*=\s*{NUM}", rf"{NUM}\s*N/m"], 5, 500)],
  "coil spring", "slotted masses, ruler, retort stand")
T("friction-slide", "Friction Slide Distance", PHYS,
  "Slide blocks across surfaces and measure stopping distance.",
  ["friction", "slide", "sliding", "rough", "smooth", "skid"],
  "linear",
  [M("mu", "Friction coefficient", "", 0.4, [rf"(?:mu|μ|coefficient)(?: of)? {NUM}"], 0.05, 1.2)],
  "wooden block", "ramps of varied texture, stopwatch, tape")
T("inclined-plane", "Inclined Plane Acceleration", PHYS,
  "Roll carts down ramps of measured angles.",
  ["inclin", "ramp", "slope", "cart", "roll down"],
  "linear",
  [M("angle", "Ramp angle", "deg", 20, [rf"{NUM}\s*deg", rf"angle(?: of)? {NUM}"], 5, 60)],
  "dynamics cart", "inclined track, motion timer")
T("buoyancy", "Buoyancy Displacement", PHYS,
  "Submerge objects and measure displaced water weight.",
  ["buoyan", "float", "sink", "displace", "archimedes"],
  "linear",
  [M("volume", "Object volume", "L", 2, [rf"{NUM}\s*L(?:iter)?s?", rf"volume(?: of)? {NUM}"], 0.1, 50)],
  "metal block", "overflow can, graduated cylinder, scale")
T("ohms-law", "Ohm's Law Circuit", PHYS,
  "Vary voltage across resistors and measure current.",
  ["ohm", "resistor", "circuit", "voltage", "current", "v=ir", "ammeter"],
  "circuit",
  [M("resistance", "Resistance", "Ω", 100, [rf"{NUM}\s*(?:ohm|Ω)", rf"resistance(?: of)? {NUM}"], 10, 10000)],
  "carbon resistor", "DC supply, ammeter, voltmeter, breadboard",
  safety="Keep voltages under 12 V. Never short the supply terminals.")
T("lens-imaging", "Thin Lens Imaging", PHYS,
  "Move objects before a lens and locate the image.",
  ["lens", "focal", "image", "optics", "magnif"],
  "optics",
  [M("f", "Focal length", "cm", 15, [rf"f\s*=\s*{NUM}", rf"{NUM}\s*cm", rf"focal(?: length)?(?: of)? {NUM}"], 5, 50)],
  "converging lens", "optical bench, light source, screen")
T("wave-speed", "Wave Speed on a String", PHYS,
  "Measure wave speed vs string tension.",
  ["wave", "string", "tension", "frequency", "standing wave"],
  "linear",
  [M("tension", "Tension", "N", 40, [rf"{NUM}\s*N(?:ewton)?s?", rf"tension(?: of)? {NUM}"], 5, 200)],
  "elastic cord", "pulley, hanging masses, vibrator")
T("specific-heat", "Specific Heat Calorimetry", PHYS,
  "Heat metals and measure temperature change in water.",
  ["specific heat", "calorimet", "heat capacity", "warming water"],
  "linear",
  [M("mass", "Metal mass", "g", 100, [rf"{NUM}\s*g(?:ram)?s?", rf"mass(?: of)? {NUM}"], 10, 1000)],
  "aluminum block", "calorimeter, thermometer, hot plate",
  safety="Hot plates and boiling water burn. Use tongs and goggles.")
T("newtons-cooling", "Newton's Law of Cooling", PHYS,
  "Track a hot object's temperature as it cools.",
  ["cooling", "cool down", "newton", "temperature drop"],
  "cooling",
  [M("t0", "Starting temperature", "°C", 90, [rf"{NUM}\s*(?:°C|degrees? c)", rf"(?:start|from)(?:ing)?(?: at)? {NUM}"], 40, 100)],
  "cup of water", "thermometer, timer, insulated sleeve")
T("doppler", "Doppler Shift Sound", PHYS,
  "Measure pitch change of a moving sound source.",
  ["doppler", "pitch", "siren", "moving source", "redshift"],
  "linear",
  [M("speed", "Source speed", "m/s", 25, [rf"{NUM}\s*m/s", rf"speed(?: of)? {NUM}"], 5, 100)],
  "buzzer on cart", "track, frequency meter app")
T("torque-lever", "Torque Balance Lever", PHYS,
  "Balance a lever with masses at measured positions.",
  ["torque", "lever", "fulcrum", "balance", "seesaw"],
  "linear",
  [M("arm", "Effort arm length", "m", 0.8, [rf"{NUM}\s*m(?:eter)?s?", rf"arm(?: of)? {NUM}"], 0.2, 2)],
  "meter stick", "fulcrum, hooked masses")
T("pulley-advantage", "Pulley Mechanical Advantage", PHYS,
  "Count rope segments and measure lifting force.",
  ["pulley", "mechanical advantage", "lift", "rope"],
  "linear",
  [M("n", "Supporting ropes", "", 4, [rf"{NUM}\s*ropes?", rf"{NUM}\s*pulleys?"], 1, 8)],
  "pulley set", "spring scale, load mass, cord")
T("resonance-tube", "Resonance Tube Wavelength", PHYS,
  "Find resonant air-column lengths for a tuning fork.",
  ["resonan", "tuning fork", "sound tube", "wavelength"],
  "linear",
  [M("freq", "Fork frequency", "Hz", 512, [rf"{NUM}\s*Hz", rf"frequency(?: of)? {NUM}"], 128, 2048)],
  "tuning fork", "resonance tube, water reservoir")
T("half-life", "Radioactive Half-Life Dice", PHYS,
  "Simulate decay by removing dice each round.",
  ["half-life", "half life", "decay", "radioactive", "dice"],
  "exponential-decay",
  [M("halflife", "Half-life", "rounds", 3, [rf"half[- ]life(?: of)? {NUM}"], 1, 10)],
  "100 dice", "tray, tally sheet")
T("terminal-velocity", "Terminal Velocity Filters", PHYS,
  "Drop coffee filters and time their steady fall.",
  ["terminal velocity", "air resistance", "coffee filter", "parachute"],
  "linear",
  [M("n", "Number of filters", "", 4, [rf"{NUM}\s*filters?"], 1, 10)],
  "coffee filters", "stopwatch, tall drop zone")
T("bernoulli", "Bernoulli Lift Paper", PHYS,
  "Blow over paper strips and measure lift angle.",
  ["bernoulli", "lift", "airplane wing", "blow over"],
  "linear",
  [M("speed", "Air speed", "m/s", 8, [rf"{NUM}\s*m/s"], 2, 30)],
  "paper strip", "fan with speed settings, protractor")
T("solar-cell", "Solar Cell Angle Power", PHYS,
  "Tilt a solar cell to light and measure power.",
  ["solar", "photovoltaic", "panel", "sun angle"],
  "linear",
  [M("angle", "Tilt angle", "deg", 30, [rf"{NUM}\s*deg", rf"angle(?: of)? {NUM}"], 0, 90)],
  "mini solar cell", "lamp, multimeter, protractor",
  safety="Lamp gets hot. Do not stare into bright lamps.")
T("wind-turbine", "Wind Turbine Blade Pitch", PHYS,
  "Vary blade pitch and measure generator voltage.",
  ["wind turbine", "blade", "turbine", "windmill"],
  "linear",
  [M("pitch", "Blade pitch", "deg", 15, [rf"{NUM}\s*deg", rf"pitch(?: of)? {NUM}"], 0, 45)],
  "model turbine", "fan, voltmeter, tachometer")
T("flywheel", "Flywheel Energy Storage", PHYS,
  "Spin flywheels and time the coast-down.",
  ["flywheel", "spin", "energy storage", "coast"],
  "linear",
  [M("mass", "Rotor mass", "kg", 2, [rf"{NUM}\s*kg", rf"mass(?: of)? {NUM}"], 0.5, 10)],
  "steel disc", "axle bearings, tachometer, stopwatch")
T("heat-engine", "Heat Engine Efficiency", PHYS,
  "Run a Stirling engine across temperature gaps.",
  ["heat engine", "stirling", "efficiency", "carnot"],
  "linear",
  [M("dt", "Temperature gap", "°C", 60, [rf"{NUM}\s*(?:°C|degrees?)", rf"gap(?: of)? {NUM}"], 20, 150)],
  "Stirling engine", "hot plate, ice bath, tachometer",
  safety="Hot surfaces burn. Handle with tongs.")
T("seismograph", "Seismograph Shake Table", PHYS,
  "Shake a model building and record the trace.",
  ["earthquake", "seismograph", "shake", "tremor"],
  "linear",
  [M("amp", "Shake amplitude", "cm", 5, [rf"{NUM}\s*cm", rf"amplitude(?: of)? {NUM}"], 1, 20)],
  "model tower", "shake table, pen recorder")
T("crater-impacts", "Crater Impact Scaling", PHYS,
  "Drop balls into flour and measure crater width.",
  ["crater", "impact", "meteor", "flour"],
  "linear",
  [M("height", "Drop height", "m", 2, [rf"{NUM}\s*m", rf"height(?: of)? {NUM}"], 0.5, 5)],
  "marbles", "tray of flour, ruler, sieve")
T("rocket-staging", "Water Rocket Staging", PHYS,
  "Vary water fill and measure rocket apogee.",
  ["water rocket", "bottle rocket", "staging", "apogee"],
  "linear",
  [M("fill", "Water fill", "%", 33, [rf"{NUM}\s*%", rf"fill(?: of)? {NUM}"], 10, 80)],
  "2L bottle rocket", "launcher, pump, altimeter",
  safety="Launch outdoors away from people. Wear eye protection.")
T("capillary", "Capillary Rise Tubes", PHYS,
  "Stand thin tubes in water and measure rise height.",
  ["capillary", "rise", "thin tube", "wicking"],
  "linear",
  [M("d", "Tube diameter", "mm", 1, [rf"{NUM}\s*mm", rf"diameter(?: of)? {NUM}"], 0.2, 5)],
  "glass capillaries", "dyed water, ruler, stand")
T("gas-pressure", "Gas Pressure vs Volume", PHYS,
  "Compress trapped air and read the pressure.",
  ["gas", "boyle", "pressure", "syringe", "compress"],
  "linear",
  [M("v0", "Starting volume", "mL", 60, [rf"{NUM}\s*mL", rf"volume(?: of)? {NUM}"], 20, 100)],
  "sealed syringe", "pressure sensor, clamp")

# ---------------- CHEMISTRY ----------------
CHEM = "Chemistry"
T("acid-base-titration", "Acid-Base Titration", CHEM,
  "Titrate an acid with base and find the equivalence point.",
  ["titration", "titrate", "acid", "base", "equivalence", "burette"],
  "titration",
  [M("conc", "Acid concentration", "M", 0.1, [rf"{NUM}\s*M(?:olar)?", rf"concentration(?: of)? {NUM}"], 0.01, 1)],
  "hydrochloric acid", "burette, phenolphthalein, flask",
  safety="Acids and bases burn skin and eyes. Goggles and gloves required.")
T("reaction-rate-temp", "Reaction Rate vs Temperature", CHEM,
  "Time a color-change reaction in warm and cold baths.",
  ["reaction rate", "temperature", "speed up", "arrhenius", "iodine clock"],
  "rate-temp",
  [M("t0", "Base temperature", "°C", 20, [rf"{NUM}\s*(?:°C|degrees? c)"], 5, 60)],
  "iodine clock mix", "water baths, thermometers, timers",
  safety="Some reagents stain and irritate. Goggles on.")
T("electrolysis-water", "Electrolysis of Water", CHEM,
  "Split water with electricity and collect the gases.",
  ["electrolysis", "split water", "hydrogen", "hoffman"],
  "linear",
  [M("current", "Current", "A", 1.5, [rf"{NUM}\s*A(?:mp)?s?", rf"current(?: of)? {NUM}"], 0.5, 5)],
  "Hoffman apparatus", "DC supply, electrolyte",
  safety="Hydrogen is flammable. Ventilate; no open flames.")
T("galvanic-cell", "Galvanic Cell Voltage", CHEM,
  "Build metal-pair cells and measure voltage.",
  ["galvanic", "battery", "cell", "electrochemical", "voltaic"],
  "linear",
  [M("pairs", "Metal pairs tested", "", 5, [rf"{NUM}\s*pairs?"], 2, 10)],
  "zinc/copper strips", "voltmeter, salt bridge, beakers")
T("corrosion-rust", "Nail Corrosion Conditions", CHEM,
  "Expose nails to air, water, salt and compare rust.",
  ["rust", "corrosion", "nail", "oxidation"],
  "linear",
  [M("days", "Exposure days", "days", 7, [rf"{NUM}\s*days?", rf"for {NUM} day"], 3, 21)],
  "iron nails", "test tubes, salt, oil, labels")
T("solubility-temp", "Solubility vs Temperature", CHEM,
  "Dissolve salt in water at temperatures and weigh saturation.",
  ["solubility", "dissolve", "saturated", "recrystallize"],
  "linear",
  [M("t", "Water temperature", "°C", 40, [rf"{NUM}\s*(?:°C|degrees? c)"], 10, 90)],
  "potassium nitrate", "hot plate, balance, filter",
  safety="Hot solutions scald. Handle with care.")
T("chromatography", "Paper Chromatography", CHEM,
  "Separate ink dyes on paper strips and compute Rf.",
  ["chromatography", "separate", "ink", "rf value", "dye"],
  "linear",
  [M("solvent", "Solvent front", "cm", 8, [rf"{NUM}\s*cm"], 4, 12)],
  "marker inks", "chromatography paper, solvent chamber",
  safety="Use low-toxicity solvents; ventilate.")
T("flame-tests", "Flame Test Colors", CHEM,
  "Burn metal salts and record flame colors.",
  ["flame test", "flame color", "metal ion", "burn"],
  "survey",
  [M("salts", "Salts tested", "", 6, [rf"{NUM}\s*salts?"], 3, 10)],
  "chloride salts", "nichrome wire, Bunsen burner",
  safety="Open flame and hot wire. Tie hair back; goggles on.")
T("calorimetry-food", "Food Calorimetry Energy", CHEM,
  "Burn food samples under water and measure warming.",
  ["calorie", "food energy", "burn peanut", "calorimeter"],
  "linear",
  [M("mass", "Food mass", "g", 2, [rf"{NUM}\s*g(?:ram)?s?"], 0.5, 10)],
  "peanut halves", "soda-can calorimeter, thermometer",
  safety="Open flame. Burn in a fume hood or outdoors.")
T("enzyme-catalase", "Catalase Enzyme Rate", CHEM,
  "Add liver to peroxide and measure oxygen foam.",
  ["enzyme", "catalase", "peroxide", "liver"],
  "linear",
  [M("ph", "Solution pH", "", 7, [rf"pH\s*{NUM}", rf"ph(?: of)? {NUM}"], 3, 11)],
  "liver cubes", "hydrogen peroxide, graduated cylinder",
  safety="Peroxide bleaches skin. Gloves and goggles.")
T("fermentation", "Yeast Fermentation Sugar", CHEM,
  "Feed yeast sugars and capture the CO2.",
  ["fermentation", "yeast", "sugar", "co2", "bread", "balloon"],
  "linear",
  [M("sugar", "Sugar mass", "g", 10, [rf"{NUM}\s*g(?:ram)?s?"], 2, 30)],
  "baker's yeast", "warm water, balloons, flasks")
T("electroplating", "Copper Electroplating", CHEM,
  "Plate copper onto a key and weigh the deposit.",
  ["electroplat", "plate", "copper", "key"],
  "linear",
  [M("current", "Current", "A", 1.0, [rf"{NUM}\s*A(?:mp)?s?"], 0.3, 3)],
  "steel key", "copper sulfate bath, DC supply",
  safety="Copper sulfate is toxic. Gloves; no tasting.")
T("soap-saponification", "Soap Saponification", CHEM,
  "React oil with lye and test the soap.",
  ["soap", "saponification", "lye", "oil"],
  "linear",
  [M("oil", "Oil mass", "g", 200, [rf"{NUM}\s*g(?:ram)?s?"], 50, 500)],
  "olive oil", "sodium hydroxide, mold, thermometer",
  safety="Lye causes severe burns. Goggles, gloves, adult supervision.")
T("polymer-slime", "Polymer Slime Cross-Linking", CHEM,
  "Mix glue with borax and test stretch distance.",
  ["slime", "polymer", "borax", "glue", "stretch"],
  "linear",
  [M("borax", "Borax solution", "mL", 20, [rf"{NUM}\s*mL"], 5, 60)],
  "PVA glue", "borax, cups, rulers",
  safety="Do not ingest. Wash hands after handling.")
T("antacid", "Antacid Neutralization", CHEM,
  "Drop antacid tablets in acid and time the fizz.",
  ["antacid", "neutralize", "tablet", "stomach acid", "fizz"],
  "linear",
  [M("tablets", "Tablets tested", "", 3, [rf"{NUM}\s*tablets?"], 1, 6)],
  "antacid tablets", "dilute acid, beakers, timer",
  safety="Even dilute acid irritates. Goggles on.")
T("lemon-battery", "Lemon Battery Power", CHEM,
  "Stick electrodes in fruit and light an LED.",
  ["lemon battery", "fruit battery", "potato battery", "led"],
  "linear",
  [M("cells", "Fruit cells", "", 4, [rf"{NUM}\s*cells?"], 1, 8)],
  "lemons", "zinc/copper electrodes, LED, wires")
T("iodine-clock", "Iodine Clock Timing", CHEM,
  "Mix clock reagents and time the color snap.",
  ["iodine clock", "clock reaction", "color change", "snap"],
  "rate-temp",
  [M("t0", "Solution temperature", "°C", 22, [rf"{NUM}\s*(?:°C|degrees? c)"], 10, 50)],
  "clock reagents", "beakers, thermometer, stopwatch",
  safety="Stains skin and benches. Gloves recommended.")
T("distillation", "Simple Distillation Purity", CHEM,
  "Distill salt water and test the distillate.",
  ["distillation", "distill", "boil", "condense", "purity"],
  "linear",
  [M("vol", "Starting volume", "mL", 100, [rf"{NUM}\s*mL"], 50, 250)],
  "salt water", "distillation kit, thermometer",
  safety="Glass gets hot; steam scalds. Use clamps.")
T("molar-mass", "Molar Mass by Gas", CHEM,
  "Vaporize liquid in a flask and weigh the gas.",
  ["molar mass", "dumas", "vapor", "flask"],
  "linear",
  [M("t", "Water bath temp", "°C", 95, [rf"{NUM}\s*(?:°C|degrees? c)"], 70, 100)],
  "volatile liquid", "Erlenmeyer, hot bath, balance",
  safety="Hot bath and vapors. Ventilate; goggles on.")
T("biodiesel", "Biodiesel Yield", CHEM,
  "Transesterify oil and measure fuel layer.",
  ["biodiesel", "transesterification", "fuel", "methanol"],
  "linear",
  [M("oil", "Oil volume", "mL", 200, [rf"{NUM}\s*mL"], 100, 500)],
  "used cooking oil", "methanol, catalyst, separatory funnel",
  safety="Methanol is toxic and flammable. Fume hood only.")
T("water-filtration", "Water Filtration Layers", CHEM,
  "Pour muddy water through filter stacks and rate clarity.",
  ["filter", "filtration", "purify", "muddy water", "charcoal"],
  "linear",
  [M("layers", "Filter layers", "", 4, [rf"{NUM}\s*layers?"], 1, 8)],
  "muddy water", "bottles, sand, gravel, charcoal, cloth")
T("vitamin-c", "Vitamin C Titration", CHEM,
  "Titrate juice with iodine to rank vitamin C.",
  ["vitamin c", "ascorbic", "juice", "iodine"],
  "titration",
  [M("juices", "Juices tested", "", 4, [rf"{NUM}\s*juices?"], 2, 8)],
  "fruit juices", "iodine solution, starch, burette",
  safety="Iodine stains. Gloves recommended.")
T("nylon-rope", "Nylon Rope Trick", CHEM,
  "Pull nylon rope from a two-layer reaction.",
  ["nylon", "rope trick", "polymer", "interface"],
  "linear",
  [M("pulls", "Pull length", "cm", 30, [rf"{NUM}\s*cm"], 10, 100)],
  "diamine/adipoyl solutions", "beaker, forceps",
  safety="Organic solvents irritate. Gloves; ventilate.")
T("chemiluminescence", "Glow Stick Temperature", CHEM,
  "Chill and warm glow sticks and compare brightness.",
  ["glow", "chemiluminescence", "glow stick", "light"],
  "linear",
  [M("t", "Bath temperature", "°C", 30, [rf"{NUM}\s*(?:°C|degrees? c)"], 0, 60)],
  "glow sticks", "ice bath, warm bath, light meter")

# ---------------- BIOLOGY ----------------
BIO = "Biology"
T("photosynthesis-rate", "Photosynthesis Bubble Rate", BIO,
  "Count oxygen bubbles from pondweed in light.",
  ["photosynthesis", "pondweed", "elodea", "bubbles", "oxygen", "light"],
  "linear",
  [M("dist", "Lamp distance", "cm", 20, [rf"{NUM}\s*cm", rf"distance(?: of)? {NUM}"], 10, 60)],
  "pondweed sprig", "lamp, beaker, timer")
T("osmosis-potato", "Osmosis Potato Cylinders", BIO,
  "Soak potato cores in salt solutions and weigh change.",
  ["osmosis", "potato", "salt solution", "turgid", "plasmolysis"],
  "osmosis",
  [M("conc", "Salt concentration", "%", 5, [rf"{NUM}\s*%", rf"concentration(?: of)? {NUM}"], 0, 20)],
  "potato cores", "salt solutions, balance, cork borer")
T("diffusion-agar", "Diffusion in Agar Cubes", BIO,
  "Soak dyed agar cubes and measure color depth.",
  ["diffusion", "agar", "cube", "surface area"],
  "linear",
  [M("size", "Cube edge", "cm", 2, [rf"{NUM}\s*cm", rf"(?:edge|size)(?: of)? {NUM}"], 1, 4)],
  "agar cubes", "dye bath, ruler, timer")
T("mitosis-onion", "Mitosis Onion Root Tip", BIO,
  "Stain root tips and tally cell phases.",
  ["mitosis", "onion", "root tip", "cell division", "phases"],
  "survey",
  [M("cells", "Cells counted", "", 200, [rf"{NUM}\s*cells?"], 100, 500)],
  "onion root tips", "microscope, stain, slides")
T("respiration-peas", "Respiration Germinating Peas", BIO,
  "Measure oxygen uptake of sprouting peas.",
  ["respiration", "germinating", "peas", "oxygen uptake", "respirometer"],
  "linear",
  [M("t", "Bath temperature", "°C", 22, [rf"{NUM}\s*(?:°C|degrees? c)"], 10, 35)],
  "pea seeds", "respirometer, KOH pellets, baths")
T("bacterial-growth", "Bacterial Growth Plates", BIO,
  "Swab surfaces, incubate plates, count colonies.",
  ["bacteria", "agar plate", "colonies", "swab", "incubate"],
  "linear",
  [M("hours", "Incubation hours", "h", 48, [rf"{NUM}\s*h(?:ours?)?", rf"for {NUM} hour"], 24, 96)],
  "nutrient agar plates", "sterile swabs, incubator",
  safety="Never open incubated plates. Seal and dispose safely.")
T("antibiotic-zones", "Antibiotic Zone Inhibition", BIO,
  "Place discs on lawns and measure clear zones.",
  ["antibiotic", "zone", "inhibition", "disc", "kirby"],
  "linear",
  [M("discs", "Discs tested", "", 4, [rf"{NUM}\s*discs?"], 2, 8)],
  "bacterial lawns", "antibiotic discs, calipers",
  safety="Sealed plates only. Do not culture pathogens.")
T("mark-recapture", "Mark-Recapture Population", BIO,
  "Tag beans, remix, and estimate the hidden total.",
  ["mark recapture", "population", "estimate", "tag", "lincoln"],
  "linear",
  [M("marked", "Marked released", "", 30, [rf"{NUM}\s*marked?", rf"mark(?:ed)? {NUM}"], 10, 100)],
  "dry beans", "bag, marker, tally sheet")
T("heart-rate-exercise", "Heart Rate vs Exercise", BIO,
  "Step up and down, then track pulse recovery.",
  ["heart rate", "pulse", "exercise", "recovery", "fitness"],
  "cooling",
  [M("mins", "Exercise minutes", "min", 3, [rf"{NUM}\s*min(?:ute)?s?", rf"for {NUM} min"], 1, 10)],
  "student volunteer", "step platform, timer, pulse watch",
  safety="Stop if dizzy. Volunteers only.")
T("lung-capacity", "Lung Capacity Balloon", BIO,
  "Exhale into balloons and measure circumference.",
  ["lung", "balloon", "vital capacity", "exhale", "spirometer"],
  "linear",
  [M("trials", "Trials per person", "", 3, [rf"{NUM}\s*trials?"], 1, 5)],
  "balloons", "tape measure, nose clips",
  safety="One balloon per person. Discard after use.")
T("seed-germination", "Seed Germination Conditions", BIO,
  "Sprout seeds in light/dark, wet/dry and count.",
  ["germination", "seed", "sprout", "cress"],
  "linear",
  [M("seeds", "Seeds per dish", "", 20, [rf"{NUM}\s*seeds?"], 10, 50)],
  "cress seeds", "petri dishes, paper towels")
T("plant-tropism", "Plant Phototropism Turn", BIO,
  "Grow seedlings sideways to light and measure bend.",
  ["tropism", "phototropism", "bend", "seedling", "light"],
  "linear",
  [M("hours", "Light hours", "h", 48, [rf"{NUM}\s*h(?:ours?)?"], 12, 96)],
  "bean seedlings", "dark box, side lamp, protractor")
T("composting", "Compost Heat Pile", BIO,
  "Build mini composts and log core temperature.",
  ["compost", "decomposition", "pile", "rot"],
  "cooling",
  [M("days", "Days tracked", "days", 14, [rf"{NUM}\s*days?"], 7, 30)],
  "yard waste mix", "bins, thermometer, scale")
T("brine-shrimp", "Brine Shrimp Hatch Rate", BIO,
  "Hatch shrimp eggs at salinities and count.",
  ["brine shrimp", "artemia", "hatch", "salinity", "sea monkeys"],
  "linear",
  [M("salt", "Salinity", "ppt", 30, [rf"{NUM}\s*ppt", rf"salinity(?: of)? {NUM}"], 5, 60)],
  "shrimp cysts", "salt mixes, dishes, pipettes")
T("pillbugs-choice", "Pillbug Choice Chamber", BIO,
  "Offer damp/dry halves and tally pillbug picks.",
  ["pillbug", "choice", "roly poly", "habitat", "kinesis"],
  "survey",
  [M("bugs", "Pillbugs used", "", 10, [rf"{NUM}\s*(?:pillbugs?|bugs?)"], 5, 20)],
  "pillbugs", "choice chamber, damp/dry paper")
T("mold-growth", "Bread Mold Growth", BIO,
  "Store bread damp/dry and map mold spread.",
  ["mold", "bread", "fungus", "spoilage"],
  "linear",
  [M("days", "Days observed", "days", 7, [rf"{NUM}\s*days?"], 3, 14)],
  "bread slices", "bags, spray bottle, grid sheet",
  safety="Do not open moldy bags. Seal and bin them.")
T("pond-ecology", "Pond Water Survey", BIO,
  "Dip pond samples and key out the micro-life.",
  ["pond", "ecology", "micro", "dip", "sample"],
  "survey",
  [M("sites", "Sites sampled", "", 5, [rf"{NUM}\s*sites?"], 2, 10)],
  "pond water jars", "nets, keys, microscopes")
T("taste-buds", "Taste Bud Mapping", BIO,
  "Dab flavors on tongues and map the hits.",
  ["taste", "tongue", "flavor", "bitter", "sweet"],
  "survey",
  [M("tasters", "Tasters", "", 12, [rf"{NUM}\s*tasters?"], 5, 30)],
  "flavor solutions", "cotton swabs, cups, water",
  safety="Food-safe solutions only. No sharing swabs.")
T("reflex-arc", "Ruler Drop Reflex", BIO,
  "Catch a dropped ruler and convert to reaction time.",
  ["reflex", "reaction time", "ruler drop", "catch"],
  "linear",
  [M("trials", "Trials", "", 5, [rf"{NUM}\s*trials?"], 3, 10)],
  "meter ruler", "table edge, data sheet")

# ---------------- EARTH & SPACE ----------------
EARTH = "Earth & Space"
T("erosion-stream", "Stream Table Erosion", EARTH,
  "Run water over sand and map the channels.",
  ["erosion", "stream", "sand", "channel", "delta"],
  "linear",
  [M("slope", "Table slope", "deg", 10, [rf"{NUM}\s*deg", rf"slope(?: of)? {NUM}"], 5, 25)],
  "stream table", "sand, water jug, food coloring")
T("volcano-model", "Volcano Eruption Model", EARTH,
  "Build cones and erupt baking-soda magma.",
  ["volcano", "eruption", "lava", "magma", "cone"],
  "linear",
  [M("vinegar", "Vinegar volume", "mL", 100, [rf"{NUM}\s*mL"], 50, 250)],
  "paper-mache cone", "baking soda, vinegar, tray")
T("earthquake-waves", "Slinky Earthquake Waves", EARTH,
  "Send P and S pulses down a slinky and time them.",
  ["earthquake", "slinky", "p wave", "s wave", "seismic"],
  "linear",
  [M("length", "Slinky length", "m", 5, [rf"{NUM}\s*m(?:eter)?s?"], 2, 10)],
  "metal slinky", "stopwatch, tape, partner")
T("soil-permeability", "Soil Permeability Columns", EARTH,
  "Pour water through soil columns and time drainage.",
  ["soil", "permeability", "drainage", "column", "clay", "sand"],
  "linear",
  [M("soils", "Soil types", "", 3, [rf"{NUM}\s*soils?"], 2, 6)],
  "soil samples", "columns, water, timers")
T("cloud-formation", "Cloud in a Bottle", EARTH,
  "Pressurize a bottle and watch a cloud bloom.",
  ["cloud", "bottle", "pressure", "condensation"],
  "linear",
  [M("pumps", "Pump strokes", "", 10, [rf"{NUM}\s*(?:pumps?|strokes?)"], 5, 20)],
  "2L bottle", "pump, match smoke, water",
  safety="Release pressure away from faces.")
T("greenhouse-model", "Greenhouse Jar Model", EARTH,
  "Compare lidded vs open jars in sunlight.",
  ["greenhouse", "jar", "warming", "climate"],
  "linear",
  [M("mins", "Sun minutes", "min", 30, [rf"{NUM}\s*min(?:ute)?s?"], 10, 60)],
  "glass jars", "thermometers, sun or lamp")
T("moon-phases", "Moon Phase Lamp Model", EARTH,
  "Orbit a ball around a lamp and sketch phases.",
  ["moon", "phases", "lunar", "orbit"],
  "survey",
  [M("stops", "Orbit stops", "", 8, [rf"{NUM}\s*stops?"], 4, 12)],
  "foam ball", "lamp in dark room, stickers")
T("crater-impacts", "Crater Impact Scaling", EARTH,
  "Drop balls into flour and measure crater width.",
  ["crater", "impact", "meteor", "asteroid"],
  "linear",
  [M("height", "Drop height", "m", 2, [rf"{NUM}\s*m", rf"height(?: of)? {NUM}"], 0.5, 5)],
  "marbles", "tray of flour, ruler")
T("water-cycle", "Water Cycle Bag", EARTH,
  "Tape a water bag to a window and watch the cycle.",
  ["water cycle", "evaporation", "condensation", "bag"],
  "linear",
  [M("water", "Water volume", "mL", 100, [rf"{NUM}\s*mL"], 50, 200)],
  "zip bag", "water, blue dye, sunny window")
T("ocean-currents", "Ocean Current Tank", EARTH,
  "Float ice at one end and dye the currents.",
  ["ocean", "current", "convection", "ice"],
  "linear",
  [M("ice", "Ice cubes", "", 4, [rf"{NUM}\s*(?:ice|cubes?)"], 2, 8)],
  "fish tank", "ice, dye, warm water")
T("rocket-staging", "Water Rocket Staging", EARTH,
  "Vary water fill and measure rocket apogee.",
  ["water rocket", "bottle rocket", "staging", "apogee"],
  "linear",
  [M("fill", "Water fill", "%", 33, [rf"{NUM}\s*%", rf"fill(?: of)? {NUM}"], 10, 80)],
  "2L bottle rocket", "launcher, pump, altimeter",
  safety="Launch outdoors away from people. Eye protection on.")
T("telescope-optics", "Telescope Optics Bench", EARTH,
  "Pair lenses and measure magnification.",
  ["telescope", "magnification", "eyepiece", "objective"],
  "optics",
  [M("f", "Objective focal length", "cm", 30, [rf"{NUM}\s*cm", rf"f\s*=\s*{NUM}"], 10, 60)],
  "lens pair", "tubes, distant target")
T("satellite-orbits", "Satellite Orbit Periods", EARTH,
  "Swing tethered balls and time the orbits.",
  ["satellite", "orbit", "period", "kepler"],
  "pendulum",
  [M("length", "Tether length", "m", 1.5, [rf"{NUM}\s*m(?:eter)?s?"], 0.5, 3)],
  "foam satellites", "tether, open space, stopwatch",
  safety="Clear the swing zone of people.")
T("seasons-tilt", "Seasons Tilt Lamp", EARTH,
  "Tilt a globe to a lamp and compare light patches.",
  ["seasons", "tilt", "axis", "solstice"],
  "linear",
  [M("tilt", "Axial tilt", "deg", 23, [rf"{NUM}\s*deg", rf"tilt(?: of)? {NUM}"], 0, 45)],
  "desk globe", "lamp, light meter, stickers")
T("landslide", "Landslide Slope Tray", EARTH,
  "Tilt a soil tray until it slips.",
  ["landslide", "slope", "slip", "angle of repose"],
  "linear",
  [M("wet", "Water added", "mL", 100, [rf"{NUM}\s*mL"], 0, 300)],
  "soil tray", "protractor, spray bottle")

# ---------------- ENGINEERING ----------------
ENG = "Engineering"
T("beam-deflection", "Beam Deflection Load", ENG,
  "Load a spanning ruler and measure the sag.",
  ["beam", "deflection", "sag", "load", "bridge"],
  "hooke",
  [M("k", "Beam stiffness", "N/m", 200, [rf"{NUM}\s*N/m", rf"stiffness(?: of)? {NUM}"], 50, 1000)],
  "wooden ruler", "supports, masses, dial gauge")
T("truss-bridge", "Truss Bridge Pasta", ENG,
  "Build pasta trusses and load to failure.",
  ["truss", "bridge", "pasta", "spaghetti", "load"],
  "linear",
  [M("span", "Span length", "cm", 30, [rf"{NUM}\s*cm", rf"span(?: of)? {NUM}"], 15, 60)],
  "dry spaghetti", "glue, bucket, sand",
  safety="Snapping pasta flies. Goggles on.")
T("egg-drop", "Egg Drop Cushion", ENG,
  "Drop protected eggs and score the survivors.",
  ["egg drop", "cushion", "protect", "container"],
  "linear",
  [M("height", "Drop height", "m", 5, [rf"{NUM}\s*m", rf"height(?: of)? {NUM}"], 2, 12)],
  "raw eggs", "building materials, drop zone",
  safety="Drop zone clear below. Clean spills promptly.")
T("mousetrap-car", "Mousetrap Car Distance", ENG,
  "Wind a trap car and measure travel distance.",
  ["mousetrap", "car", "wind", "distance"],
  "linear",
  [M("arm", "Lever arm", "cm", 20, [rf"{NUM}\s*cm", rf"arm(?: of)? {NUM}"], 10, 40)],
  "trap chassis", "string, wheels, tape",
  safety="Traps snap hard. Keep fingers clear.")
T("water-rocket", "Water Rocket Apogee", ENG,
  "Tune fill and pressure for max height.",
  ["water rocket", "bottle rocket", "apogee", "pressure"],
  "linear",
  [M("fill", "Water fill", "%", 33, [rf"{NUM}\s*%", rf"fill(?: of)? {NUM}"], 10, 80)],
  "2L bottle rocket", "launcher, pump, altimeter",
  safety="Launch outdoors. Eye protection on.")
T("hydraulic-arm", "Hydraulic Syringe Arm", ENG,
  "Link syringes and measure lift force.",
  ["hydraulic", "syringe", "arm", "pascal"],
  "linear",
  [M("ratio", "Piston ratio", "", 4, [rf"ratio(?: of)? {NUM}", rf"{NUM}:1"], 2, 10)],
  "syringes + tubing", "water, frame, scale")
T("catapult", "Catapult Range Tuning", ENG,
  "Adjust arm stop and measure throw range.",
  ["catapult", "trebuchet", "throw", "range", "siege"],
  "projectile",
  [M("velocity", "Release speed", "m/s", 12, [rf"{NUM}\s*m/s"], 5, 30),
   M("angle", "Release angle", "deg", 45, [rf"{NUM}\s*deg"], 20, 70)],
  "tabletop catapult", "foam balls, tape measure",
  safety="Fire downrange only. Goggles on.")
T("parachute", "Parachute Canopy Drop", ENG,
  "Cut canopy sizes and time the descent.",
  ["parachute", "canopy", "drop", "descent"],
  "linear",
  [M("d", "Canopy diameter", "cm", 40, [rf"{NUM}\s*cm", rf"diameter(?: of)? {NUM}"], 20, 80)],
  "trash-bag canopies", "string, washers, stopwatch")
T("tower-stability", "Tower Shake Stability", ENG,
  "Build towers and shake to failure.",
  ["tower", "stability", "shake", "toothpick", "marshmallow"],
  "linear",
  [M("height", "Tower height", "cm", 30, [rf"{NUM}\s*cm", rf"height(?: of)? {NUM}"], 15, 60)],
  "toothpicks + marshmallows", "shake board, ruler")
T("gear-trains", "Gear Train Ratio", ENG,
  "Mesh gears and count output turns.",
  ["gear", "ratio", "train", "teeth", "mesh"],
  "linear",
  [M("teeth", "Driven teeth", "", 40, [rf"{NUM}\s*teeth", rf"teeth(?: of)? {NUM}"], 12, 80)],
  "gear set", "crank, counter, frame")
T("solar-tracker", "Solar Tracker Gain", ENG,
  "Track the sun vs fixed panel and log power.",
  ["solar tracker", "track", "panel", "gain"],
  "linear",
  [M("hours", "Hours logged", "h", 6, [rf"{NUM}\s*h(?:ours?)?"], 2, 10)],
  "tracker rig", "two panels, data logger")
T("material-tensile", "Tensile Strip Pull", ENG,
  "Pull material strips and record break force.",
  ["tensile", "pull", "break", "strength", "strip"],
  "linear",
  [M("width", "Strip width", "mm", 10, [rf"{NUM}\s*mm", rf"width(?: of)? {NUM}"], 5, 25)],
  "plastic strips", "clamp rig, spring scale",
  safety="Snapping strips whip. Goggles on.")
T("vibration-damping", "Vibration Damping Pads", ENG,
  "Shake a plate on pads and measure settle time.",
  ["vibration", "damping", "pad", "settle", "shake"],
  "cooling",
  [M("t0", "Start amplitude", "mm", 20, [rf"{NUM}\s*mm"], 5, 50)],
  "foam pads", "plate, shaker, ruler")
T("bridge-resonance", "Bridge Resonance Walk", ENG,
  "Step a model bridge at rhythms and watch sway.",
  ["resonance", "bridge", "sway", "tacoma", "rhythm"],
  "linear",
  [M("bpm", "Step rate", "bpm", 100, [rf"{NUM}\s*bpm", rf"rate(?: of)? {NUM}"], 60, 180)],
  "balsa bridge", "metronome, camera")
T("3d-print-strength", "3D Print Infill Strength", ENG,
  "Print hooks at infills and hang weight to fail.",
  ["3d print", "infill", "strength", "hook", "layer"],
  "linear",
  [M("infill", "Infill percent", "%", 20, [rf"{NUM}\s*%", rf"infill(?: of)? {NUM}"], 5, 100)],
  "printed hooks", "weights, bucket, calipers",
  safety="Falling weights hurt. Clear the drop zone.")

# ---------------- PSYCHOLOGY ----------------
PSY = "Psychology"
T("reaction-time", "Ruler Reaction Time", PSY,
  "Catch falling rulers and compare groups.",
  ["reaction", "reflex", "ruler", "catch"],
  "linear",
  [M("trials", "Trials", "", 5, [rf"{NUM}\s*trials?"], 3, 10)],
  "meter ruler", "data sheet")
T("stroop-effect", "Stroop Color Words", PSY,
  "Time naming ink colors of mismatched words.",
  ["stroop", "color", "word", "interference"],
  "linear",
  [M("words", "Words listed", "", 20, [rf"{NUM}\s*words?"], 10, 40)],
  "word lists", "timer, quiet room")
T("memory-span", "Digit Memory Span", PSY,
  "Read lengthening digit strings and score recall.",
  ["memory", "digit span", "recall", "short term"],
  "linear",
  [M("start", "Start length", "digits", 3, [rf"{NUM}\s*digits?"], 2, 5)],
  "digit lists", "reader, score sheet")
T("framing-effect", "Framing Choice Effect", PSY,
  "Pose the same choice as gain vs loss and tally.",
  ["framing", "gain", "loss", "choice", "decision"],
  "survey",
  [M("n", "Participants", "", 30, [rf"{NUM}\s*(?:people|participants|subjects?)"], 10, 100)],
  "survey cards", "tally sheet")
T("anchoring", "Anchoring Number Estimates", PSY,
  "Flash high/low anchors then ask for estimates.",
  ["anchoring", "anchor", "estimate", "bias"],
  "survey",
  [M("n", "Participants", "", 30, [rf"{NUM}\s*(?:people|participants)"], 10, 100)],
  "question cards", "calculator")
T("multitasking", "Multitasking Cost", PSY,
  "Time a task alone vs with a second task.",
  ["multitask", "distraction", "cost", "dual task"],
  "linear",
  [M("trials", "Trials", "", 4, [rf"{NUM}\s*trials?"], 2, 8)],
  "sorting task", "timer, distractor audio")
T("music-focus", "Music vs Focus Score", PSY,
  "Score puzzles in silence vs with music.",
  ["music", "focus", "concentration", "puzzle"],
  "survey",
  [M("n", "Participants", "", 20, [rf"{NUM}\s*(?:people|participants)"], 8, 50)],
  "puzzle sheets", "headphones, timer")
T("color-mood", "Color Mood Rating", PSY,
  "Rate mood words under colored light.",
  ["color", "mood", "light", "emotion"],
  "survey",
  [M("colors", "Colors tested", "", 4, [rf"{NUM}\s*colors?"], 2, 8)],
  "colored bulbs", "rating sheets")
T("sleep-memory", "Sleep vs Memory Quiz", PSY,
  "Quiz word pairs after sleep vs all-nighters (survey).",
  ["sleep", "memory", "quiz", "rest"],
  "survey",
  [M("n", "Participants", "", 24, [rf"{NUM}\s*(?:people|participants)"], 10, 60)],
  "word-pair lists", "quiz sheets")
T("habit-formation", "Habit Streak Tracking", PSY,
  "Track a tiny habit for weeks and chart streaks.",
  ["habit", "streak", "routine", "21 days"],
  "linear",
  [M("days", "Days tracked", "days", 21, [rf"{NUM}\s*days?"], 7, 60)],
  "habit log", "calendar, reminder")

# ---------------- ECONOMICS & MATH ----------------
ECON = "Economics & Math"
T("supply-demand", "Supply-Demand Market Game", ECON,
  "Trade tokens as buyers/sellers and find the price.",
  ["supply", "demand", "market", "price", "trade"],
  "linear",
  [M("traders", "Traders", "", 16, [rf"{NUM}\s*traders?"], 8, 40)],
  "token cards", "play money, ledger")
T("compound-interest", "Compound Interest Growth", ECON,
  "Grow play money at rates and chart the curve.",
  ["compound", "interest", "invest", "growth", "savings"],
  "exponential-decay",
  [M("halflife", "Rate (%)", "%", 7, [rf"{NUM}\s*%", rf"rate(?: of)? {NUM}"], 1, 15)],
  "ledger sheet", "calculator, graph paper")
T("monty-hall", "Monty Hall Doors", ECON,
  "Play the three-door game switching vs staying.",
  ["monty hall", "doors", "switch", "probability", "game show"],
  "survey",
  [M("rounds", "Rounds", "", 60, [rf"{NUM}\s*rounds?"], 20, 200)],
  "door cards", "host script, tally")
T("birthday-paradox", "Birthday Paradox Groups", ECON,
  "Check birthdays in groups and count matches.",
  ["birthday", "paradox", "match", "probability"],
  "survey",
  [M("n", "Group size", "", 30, [rf"{NUM}\s*(?:people|students?)"], 15, 60)],
  "birthday lists", "calendar, tally")
T("pi-estimation", "Pi by Toothpick Drop", ECON,
  "Drop toothpicks on lines and estimate pi.",
  ["pi", "buffon", "toothpick", "needle", "estimate"],
  "linear",
  [M("drops", "Drops", "", 200, [rf"{NUM}\s*drops?"], 50, 1000)],
  "toothpicks", "lined paper, counter")
T("tragedy-commons", "Tragedy of the Commons", ECON,
  "Harvest a shared bowl and watch it collapse.",
  ["commons", "tragedy", "shared", "harvest", "overfish"],
  "linear",
  [M("players", "Players", "", 6, [rf"{NUM}\s*players?"], 3, 12)],
  "bean bowl", "cups, round tracker")
T("auction-bidding", "Auction Strategy Bids", ECON,
  "Auction prizes with play money and log winners.",
  ["auction", "bid", "winner", "gavel"],
  "survey",
  [M("lots", "Lots", "", 8, [rf"{NUM}\s*lots?"], 4, 16)],
  "prize tokens", "play money, gavel")
T("voting-paradox", "Voting Paradox Ballots", ECON,
  "Rank candidates three ways and compare winners.",
  ["voting", "paradox", "ballot", "ranked", "condorcet"],
  "survey",
  [M("voters", "Voters", "", 21, [rf"{NUM}\s*voters?"], 9, 51)],
  "ballot cards", "tally board")
T("fractals", "Fractal Coastline Length", ECON,
  "Measure a wiggly line with shrinking rulers.",
  ["fractal", "coastline", "ruler", "dimension"],
  "linear",
  [M("steps", "Ruler sizes", "", 5, [rf"{NUM}\s*(?:sizes?|steps?)"], 3, 8)],
  "wiggly map", "rulers, string")
T("cryptography-caesar", "Caesar Cipher Crack", ECON,
  "Encode messages and crack by frequency.",
  ["cipher", "caesar", "code", "encode", "secret"],
  "linear",
  [M("shift", "Shift key", "", 7, [rf"shift(?: of)? {NUM}", rf"{NUM}\s*shift"], 1, 25)],
  "message strips", "frequency chart")

# ---------------- COMPUTER SCIENCE ----------------
CS = "Computer Science"
T("sorting-race", "Sorting Algorithm Race", CS,
  "Race bubble vs quick sort on card decks.",
  ["sorting", "bubble sort", "quick sort", "race", "algorithm"],
  "linear",
  [M("n", "Cards", "", 20, [rf"{NUM}\s*cards?"], 8, 52)],
  "card deck", "timer, score sheet")
T("binary-search", "Binary vs Linear Search", CS,
  "Find pages in a phone book two ways and time it.",
  ["binary search", "linear search", "find", "phone book"],
  "linear",
  [M("pages", "Pages", "", 100, [rf"{NUM}\s*pages?"], 20, 500)],
  "numbered pages", "timer, target slips")
T("maze-solvers", "Maze Solver Showdown", CS,
  "Run wall-follower vs random mouse in a maze.",
  ["maze", "solver", "wall follower", "random"],
  "linear",
  [M("runs", "Runs", "", 10, [rf"{NUM}\s*runs?"], 5, 30)],
  "floor maze", "two wind-up mice, timer")
T("cellular-automata", "Cellular Automata Rows", CS,
  "Grow Rule 30 rows and count the pattern.",
  ["cellular", "automata", "rule 30", "game of life"],
  "linear",
  [M("rows", "Rows grown", "", 25, [rf"{NUM}\s*rows?"], 10, 60)],
  "grid paper", "two colors, rule card")
T("compression", "Text Compression Ratio", CS,
  "Compress passages by hand-code and measure ratio.",
  ["compression", "huffman", "ratio", "shrink"],
  "linear",
  [M("chars", "Characters", "", 200, [rf"{NUM}\s*(?:chars?|characters?)"], 50, 1000)],
  "passage cards", "code table, calculator")
T("gradient-descent", "Gradient Descent Marble", CS,
  "Roll a marble down a bowl to find the bottom.",
  ["gradient", "descent", "marble", "bowl", "minimum"],
  "linear",
  [M("rolls", "Rolls", "", 10, [rf"{NUM}\s*rolls?"], 5, 30)],
  "salad bowl", "marble, ruler, marker")
T("dijkstra", "Dijkstra Map Race", CS,
  "Find shortest paths on a node map by hand.",
  ["dijkstra", "shortest path", "graph", "nodes", "map"],
  "linear",
  [M("nodes", "Nodes", "", 12, [rf"{NUM}\s*nodes?"], 6, 25)],
  "node map", "tokens, distance table")
T("towers-hanoi", "Towers of Hanoi Moves", CS,
  "Move the stack and count moves vs theory.",
  ["hanoi", "towers", "disks", "moves", "recursion"],
  "linear",
  [M("disks", "Disks", "", 5, [rf"{NUM}\s*disks?"], 3, 8)],
  "disk set", "three pegs, counter")

# ---------------- ENVIRONMENTAL ----------------
ENV = "Environmental"
T("solar-oven", "Solar Oven S'mores", ENV,
  "Bake in a box oven and log inside temperature.",
  ["solar oven", "smores", "box oven", "bake"],
  "linear",
  [M("mins", "Sun minutes", "min", 30, [rf"{NUM}\s*min(?:ute)?s?"], 15, 90)],
  "pizza-box oven", "thermometer, foil, s'mores")
T("rain-garden", "Rain Garden Infiltration", ENV,
  "Pour measured water on plots and time soak-in.",
  ["rain garden", "infiltration", "soak", "runoff"],
  "linear",
  [M("water", "Water poured", "L", 5, [rf"{NUM}\s*L(?:iter)?s?"], 1, 20)],
  "test plots", "watering can, timer")
T("air-quality", "Air Quality Tape Test", ENV,
  "Hang sticky cards and count the specks.",
  ["air quality", "pollution", "sticky", "particulate"],
  "linear",
  [M("hours", "Hours hung", "h", 24, [rf"{NUM}\s*h(?:ours?)?"], 6, 72)],
  "index cards", "petroleum jelly, hand lens")
T("water-filtration", "Water Filtration Layers", ENV,
  "Pour muddy water through filter stacks and rate clarity.",
  ["filter", "filtration", "purify", "muddy water", "charcoal"],
  "linear",
  [M("layers", "Filter layers", "", 4, [rf"{NUM}\s*layers?"], 1, 8)],
  "muddy water", "bottles, sand, gravel, charcoal, cloth")
T("compost-tea", "Compost Tea Growth", ENV,
  "Brew compost tea and compare seedling growth.",
  ["compost tea", "brew", "seedling", "fertilizer"],
  "linear",
  [M("days", "Days grown", "days", 14, [rf"{NUM}\s*days?"], 7, 28)],
  "seedlings", "compost, bubbler, ruler")
T("noise-pollution", "Noise Map Survey", ENV,
  "Meter decibels around campus and map hot spots.",
  ["noise", "decibel", "loud", "map", "sound meter"],
  "survey",
  [M("spots", "Spots measured", "", 10, [rf"{NUM}\s*spots?"], 5, 25)],
  "campus map", "phone decibel app")
T("microplastics", "Microplastic Sieve Count", ENV,
  "Sieve beach sand and count the flecks.",
  ["microplastic", "sieve", "beach", "flecks"],
  "linear",
  [M("scoops", "Sand scoops", "", 5, [rf"{NUM}\s*scoops?"], 2, 12)],
  "beach sand", "sieves, tweezers, lens",
  safety="Do not ingest sand. Wash hands.")

print(f"{len(TYPES)} types")
json.dump(TYPES, open(os.path.join(ROOT, "code", "solver_types.json"), "w"), indent=1)

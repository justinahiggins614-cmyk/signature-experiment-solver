#!/usr/bin/env python3
"""Build the 31-site JAH NETWORK nav and inject it into index.html."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/"
# (repo, label, path_suffix) — canonical network order
SITES = [
    ("signature-math", "Signature Math", ""),
    ("jah-calculator", "Signature Universal Paradox Immune Calculator", ""),
    ("jah-dictionary", "The Signature Dictionary", ""),
    ("jah-wiki", "JAH Wiki", ""),
    ("jah-n-wiki-leaks", "JAH-N Wiki Leaks", ""),
    ("signature-llama", "Signature Llama", ""),
    ("jah-ai-models", "The Signature AI Phone Book", ""),
    ("cyber-patent-catalog", "Globally Rejustered Patent Catalog", ""),
    ("signature-one-archive", "Signature Spec Catalog Pending Patents", "specs.html"),
    ("jah-computer-systems", "The Signature PC System Depository", ""),
    ("signature-books", "The Signature Book Depository", ""),
    ("signature-comics", "The Signature Comic Store", ""),
    ("signature-newspapers", "The Signature Global Newspaper Archive", ""),
    ("signature-backend", "The Signature AI Mix and Match Generator", ""),
    ("signature-boundless-generators", "The Signature Boundless Generator Archive", ""),
    ("signature-ai-mixlab", "The Signature AI Mix Lab", ""),
    ("signature-ai-olypics", "AI Olympics", ""),
    ("signature-chip-maker", "The Signature Computer Chip Maker and Archive", ""),
    ("signature-app-archive", "The Signature App Archive", ""),
    ("signature-ai-robot-matcher", "The Signature AI to Robot Matcher", ""),
    ("signature-experiment-solver", "The Signature Experiment Solver", ""),
    ("signature-ai-image-video-maker", "Signature AI Pixel", ""),
    ("signature-ai-song-maker", "Signature Music Studio", ""),
    ("signature-fixit", "The Signature Mr Fix-It", ""),
    ("signature-university", "The Signature University", ""),
    ("signature-cyber-mega-mall", "The Signature Cyber Mega-Mall", ""),
    ("signature-3d-print", "The Signature 3D Print Mega Mall", ""),
    ("signature-earth", "Signature Earth", ""),
    ("signature-flight-school", "The Signature Flight School", ""),
    ("signature-game-store", "The Signature Game Store", ""),
    ("signature-website-creator", "The Signature Website Creator", ""),
]
SELF = "signature-experiment-solver"

def nav_html():
    parts = ['<nav class="jahnet" aria-label="The JAH Network"><span class="jahnet-t">THE JAH NETWORK</span>']
    for i, (repo, label, suffix) in enumerate(SITES, 1):
        url = BASE + repo + "/" + suffix
        if repo == SELF:
            parts.append('<a href="%s" class="here" aria-current="page">%d %s — YOU ARE HERE</a>' % (url, i, label))
        else:
            parts.append('<a href="%s">%d %s</a>' % (url, i, label))
    parts.append("</nav>")
    return "".join(parts)

def main():
    import re
    p = os.path.join(ROOT, "index.html")
    h = open(p).read()
    nav = nav_html()
    if "<!--NAV-TOP-->" in h or "<!--NAV-BOTTOM-->" in h:
        h = h.replace("<!--NAV-TOP-->", nav)
        h = h.replace("<!--NAV-BOTTOM-->", nav)
    else:
        # Rebuild path: replace previously injected nav blocks.
        h2, n = re.subn(r'<nav class="jahnet" aria-label="The JAH Network">.*?</nav>', nav, h, flags=re.S)
        if n == 0:
            raise SystemExit("no nav placeholder or nav block found in index.html")
        h = h2
        print("replaced %d existing nav block(s)" % n)
    open(p, "w").write(h)
    print("nav injected (%d sites)" % len(SITES))

if __name__ == "__main__":
    main()

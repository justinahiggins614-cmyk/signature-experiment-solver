#!/usr/bin/env python3
"""Build the 24-site JAH NETWORK nav and inject it into index.html."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/"
# (repo, label, path_suffix)
SITES = [
    ("jah-ai-models", "The Signature AI Phone Book", ""),
    ("jah-calculator", "Signature Universal Paradox Immune Calculator", ""),
    ("jah-dictionary", "The Signature Dictionary", ""),
    ("jah-wiki", "JAH Wiki", ""),
    ("jah-n-wiki-leaks", "JAH-N Wiki", ""),
    ("cyber-patent-catalog", "Globally Rejustered Patent Catalog", ""),
    ("signature-one-archive", "Signature Spec Catalog Pending Patents", "specs.html"),
    ("signature-llama", "Signature Llama: The Fully Cyber Utilizable AI", ""),
    ("jah-computer-systems", "The Signature PC System Depository", ""),
    ("signature-cyber-mega-mall", "The Signature Cyber Mega-Mall", ""),
    ("signature-university", "Signature University", ""),
    ("signature-books", "The Signature Book Depository", ""),
    ("signature-comics", "The Signature Comic Store", ""),
    ("signature-newspapers", "The Signature Global Newspaper Archive", ""),
    ("signature-3d-print", "The Signature 3D Print Depository", ""),
    ("signature-backend", "Signature Backend", ""),
    ("signature-boundless-generators", "The Signature Boundless Generator Archive", ""),
    ("signature-ai-mixlab", "The Signature AI Mix Lab", ""),
    ("signature-ai-olypics", "AI Olypics", ""),
    ("signature-chip-maker", "The Signature Computer Chip Maker and Archive", ""),
    ("signature-app-archive", "The Signature App Archive", ""),
    ("signature-ai-robot-matcher", "The Signature AI Robot Matcher", ""),
    ("signature-experiment-solver", "The Signature Experiment Solver", ""),
    ("signature-ai-image-video-maker", "The Signature AI Image And Video Maker", ""),
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
    p = os.path.join(ROOT, "index.html")
    h = open(p).read()
    nav = nav_html()
    h = h.replace("<!--NAV-TOP-->", nav)
    h = h.replace("<!--NAV-BOTTOM-->", nav)
    open(p, "w").write(h)
    print("nav injected (%d sites)" % len(SITES))

if __name__ == "__main__":
    main()

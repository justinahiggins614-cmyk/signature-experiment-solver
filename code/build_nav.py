#!/usr/bin/env python3
"""Build the 27-site JAH NETWORK nav and inject it into index.html."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/"
# (repo, label, path_suffix)
SITES = [
    ("jah-ai-models", "The Signature AI Phone Book", ""),
    ("jah-calculator", "Calculator", ""),
    ("jah-dictionary", "Dictionary", ""),
    ("jah-wiki", "JAH Wiki", ""),
    ("jah-n-wiki-leaks", "JAH-N Wiki", ""),
    ("cyber-patent-catalog", "Patent Catalog", ""),
    ("signature-one-archive", "Spec Catalog", "specs.html"),
    ("signature-llama", "Signature Llama", ""),
    ("jah-computer-systems", "PC Depository", ""),
    ("signature-cyber-mega-mall", "Cyber Mega-Mall", ""),
    ("signature-university", "Signature University", ""),
    ("signature-books", "Book Depository", ""),
    ("signature-comics", "Comic Store", ""),
    ("signature-newspapers", "Global Newspaper Archive", ""),
    ("signature-3d-print", "3D Print Depository", ""),
    ("signature-backend", "Mad Scientist Lab", ""),
    ("signature-boundless-generators", "Boundless Generator Archive", ""),
    ("signature-ai-mixlab", "AI Mix Lab", ""),
    ("signature-ai-olypics", "AI Olypics", ""),
    ("signature-chip-maker", "Chip Maker and Archive", ""),
    ("signature-app-archive", "App Archive", ""),
    ("signature-ai-robot-matcher", "AI Robot Matcher", ""),
    ("signature-experiment-solver", "Experiment Solver", ""),
    ("signature-ai-image-video-maker", "Signature AI Pixel", ""),
    ("signature-ai-video-maker", "Video Maker AI", ""),
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

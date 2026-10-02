#!/usr/bin/env python3
"""2h drip: +1,000 solved experiments. Called by cron `jah-experiment-drip`."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from seed import generate, repo_size_ok

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    a = ap.parse_args()
    if not repo_size_ok():
        print("REPO-SIZE GUARD TRIPPED — drip skipped")
        sys.exit(2)
    generate(a.n)

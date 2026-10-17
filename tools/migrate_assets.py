#!/usr/bin/env python3
"""Prepare a self-hosted copy of Tianjiao bilingual portfolio assets.
Run: python migrate_assets.py
Does not change GitHub or the source site.
"""
import base64
import pathlib
import re
import urllib.request
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "output_site"
OLD = "https://tl3505-stack.github.io/Portfolio/"
NEW = "https://tl3505-stack.github.io/Tianjiao-Portfolio/index.html"
PATTERN = re.compile(r"(?:https://tl3505-stack\.github\.io/Portfolio/)?(?:terrabench|lumina|moonlight|plant-control|portfolio)/[\w-]+\.(?:webp|png|jpe?g)", re.I)
EMBED = re.compile(r"(?P<lang>en|zh):(?P<quote>['\"])(?P<data>[A-Za-z0-9+/=]{30000,})(?P=quote)")

def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()

def main():
    source = ROOT / "index.html"
    if source.exists():
        html = source.read_text(encoding="utf-8")
    else:
        print("Downloading the published bilingual index.html...")
        html = download(NEW).decode("utf-8")
    assets = set()
    def replace(match):
        decoded = base64.b64decode(match["data"]).decode("utf-8")
        assets.update(s.removeprefix(OLD) for s in PATTERN.findall(decoded))
        if OLD + "hero-silk.webp" in decoded:
            assets.add("hero-silk.webp")
        decoded = decoded.replace(OLD, "./")
        encoded = base64.b64encode(decoded.encode("utf-8")).decode("ascii")
        return f'{match["lang"]}:{match["quote"]}{encoded}{match["quote"]}'
    updated, count = EMBED.subn(replace, html)
    if count != 2:
        sys.exit(f"Expected 2 embedded language pages, found {count}. No changes made.")
    print(f"Found {len(assets)} unique assets.")
    errors = []
    OUT.mkdir(exist_ok=True)
    for i, path in enumerate(sorted(assets), 1):
        if ".." in pathlib.PurePosixPath(path).parts:
            sys.exit("Unsafe path")
        target = OUT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            image = download(OLD + path)
            if len(image) < 100 or image[:50].lstrip().lower().startswith(b"<!doctype"):
                raise ValueError("Not a valid image response")
            target.write_bytes(image)
            print(f"[{i}/{len(assets)}] OK {path}")
        except Exception as error:
            errors.append(f"{path}: {error}")
            print(f"[{i}/{len(assets)}] FAILED {path}: {error}")
    if errors:
        (OUT / "MISSING_ASSETS.txt").write_text("\n".join(errors), encoding="utf-8")
        sys.exit("Migration incomplete: see output_site/MISSING_ASSETS.txt; do not publish.")
    (OUT / "index.html").write_text(updated, encoding="utf-8")
    print("SUCCESS! Upload all files INSIDE output_site/ to the new repository root.")

if __name__ == "__main__":
    main()

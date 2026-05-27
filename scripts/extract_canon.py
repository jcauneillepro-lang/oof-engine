"""
extract_canon.py — derive the engine's component knowledge from the canonical
Design_System/index.html. Run this whenever the canon changes; it overwrites
canon_components.json which is loaded by claude_engine.py at startup.

Usage:
  python scripts/extract_canon.py /path/to/Design_System/index.html

The output canon_components.json lists every numbered component (h4 starting
with NN ·), with its live demo HTML chunk — the engine's source of truth.

Why this exists:
  Hand-writing the component vocabulary into the system prompt leads to drift.
  The engine should always know exactly what the canon says — no more, no
  less. If the canon changes, re-run this script.
"""
import json
import re
import sys
from pathlib import Path


def extract(index_html_path: str) -> dict:
    src = Path(index_html_path).read_text()

    pat = re.compile(r'<(h\d)[^>]*>\s*(\d{1,2})\s*[·•.]\s*([^<]+?)</\1>', re.S)
    matches = list(pat.finditer(src))

    components = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 10000, len(src))
        chunk = src[start:end].strip()
        # Strip pre code blocks (we want the live HTML demo)
        chunk = re.sub(r'<pre[^>]*>.*?</pre>', '', chunk, flags=re.S)
        chunk = chunk.strip()
        components.append({
            'n': int(m.group(2)),
            'name': m.group(3).strip(),
            'demo_html': chunk[:1500],
        })

    # Sort by number to be safe
    components.sort(key=lambda c: c['n'])

    return {
        'source': str(Path(index_html_path).resolve()),
        'total_components': len(components),
        'components': components,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Default location relative to this script
        default = Path(__file__).parent.parent.parent / 'OOF_Library' / 'Design_System' / 'index.html'
        if default.exists():
            index_path = str(default)
        else:
            print('Usage: python extract_canon.py /path/to/Design_System/index.html')
            sys.exit(1)
    else:
        index_path = sys.argv[1]

    data = extract(index_path)
    out = Path(__file__).parent.parent / 'canon_components.json'
    out.write_text(json.dumps(data, indent=2))
    print(f'Extracted {data["total_components"]} components → {out}')

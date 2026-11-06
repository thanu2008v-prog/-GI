"""Merge all JSONL into a single bundle.json for the app."""
import json, glob
from pathlib import Path
from collections import defaultdict
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build/bundle.json"
def main():
    files = sorted(glob.glob(str(ROOT / "data/sutras/**/*.jsonl"), recursive=True))
    sutras = []
    for p in files:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    sutras.append(json.loads(line))
    sutras.sort(key=lambda r: (["ezhuthu","sol","porul"].index(r["adhikaram"]),
                               r["othu"], r["sutra"]))
    by_othu, by_kind, by_kuri, by_letter = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for r in sutras:
        by_othu[f'{r["adhikaram"]}.{r["othu"]}'].append(r["id"])
        by_kind[r["computer"]["kind"]].append(r["id"])
        by_kuri[r["kuri"]].append(r["id"])
        first = r["verse"][0]
        by_letter[first].append(r["id"])
    bundle = {
        "meta": {"title": "செந்தமிழ் மரபு",
                 "total_sutras": len(sutras),
                 "schema": "1.4"},
        "counts": {
            "by_adhikaram": {a: sum(1 for r in sutras if r["adhikaram"]==a)
                             for a in ["ezhuthu","sol","porul"]},
            "by_kind": {k: len(v) for k, v in by_kind.items()},
            "by_kuri": {k: len(v) for k, v in by_kuri.items()},
        },
        "sutras": sutras,
        "index": {"by_othu": dict(by_othu), "by_kind": dict(by_kind),
                  "by_kuri": dict(by_kuri), "by_letter": dict(by_letter)},
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(sutras)} sutras, {OUT.stat().st_size//1024} KB)")
if __name__ == "__main__":
    main()

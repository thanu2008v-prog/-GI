"""Export flat CSV for spreadsheet editors (Tamil scholars)."""
import json, glob, csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build/sutras.csv"
FIELDS = ["id","adhikaram","othu","sutra","verse","kaandigai",
          "nul_kurum_function","nul_kurum_text","viparam",
          "kuri","kind","computer"]
def main():
    files = sorted(glob.glob(str(ROOT / "data/sutras/**/*.jsonl"), recursive=True))
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for p in files:
            for line in open(p, encoding="utf-8"):
                if not line.strip():
                    continue
                r = json.loads(line)
                nk = r.get("nul_kurum", {})
                w.writerow({
                    "id": r["id"], "adhikaram": r["adhikaram"],
                    "othu": r["othu"], "sutra": r["sutra"],
                    "verse": r["verse"], "kaandigai": r["kaandigai"],
                    "nul_kurum_function": nk.get("function",""),
                    "nul_kurum_text": nk.get("text",""),
                    "viparam": r.get("viparam",""),
                    "kuri": r["kuri"], "kind": r["computer"]["kind"],
                    "computer": json.dumps(r["computer"], ensure_ascii=False),
                })
    print(f"Wrote {OUT}")
if __name__ == "__main__":
    main()

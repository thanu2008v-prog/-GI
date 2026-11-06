"""export/yaml (தமிழறிஞர் திருத்தியது) → data_v2 — ஒரே மூலத்துக்குத் திரும்புதல்.

காப்பு: 'moolam' (சூத்திரம்) மாறியிருந்தால் ஏற்காது — "சிதைவு இல் என்ப முதல்வன் கண்ணே"
(பொருள். 652). பின் scripts/check_nool.py ஓட்ட வேண்டும்.
python3 scripts/import_yaml.py [export/yaml/ezhuthu/othu-03.yaml ...]
"""
import json, sys, re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
N = lambda s: re.sub(r"[\s/]+", "", s or "")


def main(paths):
    moolam = json.loads((ROOT / "sources/moolam.json").read_text("utf-8"))
    paths = paths or sorted(str(p) for p in (ROOT / "export/yaml").glob("*/*.yaml"))
    changed = 0
    for p in paths:
        docs = yaml.safe_load(Path(p).read_text("utf-8"))
        bad = [d["id"] for d in docs if N(d["moolam"]) != N(moolam[d["id"]])]
        if bad:
            raise SystemExit(f"{p}: மூலம் மாறியுள்ளது — ஏற்கப்படவில்லை (பொருள். 652): {bad}")
        a, o = Path(p).parent.name, Path(p).stem
        out = ROOT / "data_v2" / a / f"{o}.jsonl"
        old = out.read_text("utf-8")
        new = "".join(json.dumps({**d, "moolam": moolam[d["id"]]}, ensure_ascii=False,
                                 separators=(",", ":")) + "\n" for d in docs)
        if new != old:
            out.write_text(new, encoding="utf-8"); changed += 1
    print(f"data_v2-க்குத் திரும்பியவை: {changed} கோப்பு. இனி: python3 scripts/check_nool.py")


if __name__ == "__main__":
    main(sys.argv[1:])

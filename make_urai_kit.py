"""வேறு தளத்தில் உரை எழுதுவதற்கான கட்டளைத் தொகுப்பு → build/urai_kit/ (+ .zip).

எல்லாம் data_v2-இலிருந்து உருவாகும் (ஒரே மூலம்). திரும்பும் உரை: sources/urai_othuNN.json → make check.
"""
import json, glob, shutil, zipfile, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "urai_kit"
KIT = ROOT / "urai_kit"
PAD = {"ezhuthu": ("ezhu", "எழு."), "sol": ("sol", "சொல்."), "porul": ("porul", "பொருள்.")}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    names = json.loads((ROOT / "sources/othu_names.json").read_text("utf-8"))
    moolam = json.loads((ROOT / "sources/moolam.json").read_text("utf-8"))
    recs = []
    for a in ("ezhuthu", "sol", "porul"):
        for p in sorted(glob.glob(str(ROOT / "data_v2" / a / "othu-*.jsonl"))):
            recs += [json.loads(l) for l in open(p, encoding="utf-8")]
    # 1. மூலம்
    shutil.copy(ROOT / "sources/moolam.json", OUT / "moolam.json")
    (OUT / "othu_of.json").write_text(json.dumps({r["id"]: r["othu"] for r in recs}, ensure_ascii=False), "utf-8")
    with open(OUT / "nool_1602.txt", "w", encoding="utf-8") as f:
        f.write("செந்தமிழ் மரபு — 1602 நூற்பா (மூலம்; மாற்றக் கூடாது — பொருள். 652)\n\n")
        cur = None
        for r in recs:
            key = (r["padalam"], r["othu"])
            if key != cur:
                cur = key
                f.write(f"\n=== {names[r['padalam']]['_']} · ஓத்து {r['othu']} {names[r['padalam']][str(r['othu'])]} ===\n\n")
            f.write(f"[{r['id']}] {PAD[r['padalam']][1]} {r['sutra']}\n{r['moolam']}\n\n")
    # 2. இன்றைய நிலை (முடிந்த உரைகள் உட்பட)
    with open(OUT / "sutras_v2.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    # 3. ஓத்து நிலைப் பட்டியல்
    rows = ["| அதிகாரம் | ஓத்து | பெயர் | நூற்பா | உரை உள்ளவை | --othu |", "|---|---|---|---|---|---|"]
    groups = {}
    for r in recs:
        groups.setdefault((r["padalam"], r["othu"]), []).append(r)
    for (a, o), rs in groups.items():
        done = sum(1 for r in rs if (r.get("urai") or {}).get("text"))
        rng = f"{PAD[a][1]} {rs[0]['sutra']}–{rs[-1]['sutra']}"
        rows.append(f"| {names[a]['_']} | {o} | {names[a][str(o)]} | {rng} | {done} / {len(rs)} | `{a}:{o}` |")
    (OUT / "OTHU_NILAI.md").write_text("# ஓத்து நிலை\n\n" + "\n".join(rows) + "\n", "utf-8")
    # 4. மாதிரி: ஓத்து 4 உரை, திரும்ப வேண்டிய வடிவிலேயே
    spec = importlib.util.spec_from_file_location("u4", ROOT / "sources/urai_othu04.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    by = {r["id"]: r for r in recs}
    ex = []
    for i in m.U:
        r = by[i]; u = r.get("urai") or {}
        if not u.get("text") or "ethu" not in m.U[i]:
            continue
        e = {"id": i, "ethu": r["kaandigai"].get("ethu", "")}
        if r["kaandigai"].get("eduthukkaattu"):
            e["eduthukkaattu"] = r["kaandigai"]["eduthukkaattu"]
        e["urai"] = {k: u[k] for k in ("iyaipu", "vagai", "vilakkukkuriyathu", "maruthalai", "thunivu", "text") if k in u}
        ex.append(e)
    (OUT / "maathiri_othu04.json").write_text(json.dumps(ex, ensure_ascii=False, indent=1), "utf-8")
    # 5. கட்டளை, சோதனை நிரல், வடிவம்
    rule = {k: moolam[k] for k in ("porul.645", "porul.647", "porul.648", "porul.649", "porul.650", "porul.652", "porul.654")}
    t = (KIT / "KATTALAI.md").read_text("utf-8")
    for k, v in rule.items():
        t = t.replace("{{" + k + "}}", "> " + v.replace("\n", "  \n> ") + f"  \n> — பொருள். {k.split('.')[1]}")
    (OUT / "KATTALAI.md").write_text(t, "utf-8")
    for fn in ("check_urai.py", "urai_output.schema.json", "THIRUTHAM_othu05_07.md"):
        shutil.copy(KIT / fn, OUT / fn)
    z = ROOT / "build" / "urai_kit.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.iterdir()):
            zf.write(p, f"urai_kit/{p.name}")
    print(f"Wrote {z} ({len(list(OUT.iterdir()))} கோப்பு; மாதிரி {len(ex)} பதிவு)")


if __name__ == "__main__":
    main()

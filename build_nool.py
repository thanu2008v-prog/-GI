"""v2 தரவு → வாசிக்கும் நூல் (build/senthamil_marabu.md).

கணினி வடிவமே மூலம்; இந்த ஆவணம் அதிலிருந்து உருவாகிறது. அமைப்பு பொருள். 470:
படலம் → ஓத்து → சூத்திரம். ஒவ்வொரு சூத்திரத்தின் கீழும் காண்டிகை (பொருள், ஏது,
எடுத்துக்காட்டு — 647, 648), உரை (இயைபு, விதி/விலக்கு, மறுதலைக் கடாஅ, துணிவு — 645, 649, 650).
இறுதியில் round-trip: உருவான கோப்பிலிருந்து 1602 மூலத்தையும் மீண்டும் படித்து ஆவணப் பாடத்தோடு ஒப்பிடும்.
python3 scripts/build_nool.py
"""
import json, glob, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build/senthamil_marabu.md"
TA = {"ezhuthu": "எழு", "sol": "சொல்", "porul": "பொருள்"}
PAD_NO = {"ezhuthu": 1, "sol": 2, "porul": 3}
N = lambda s: re.sub(r"[\s/]+", "", s or "")


def ref_ta(x):
    a, n = x.split(".")
    return f"{ {'ezhu': 'எழு', 'sol': 'சொல்', 'porul': 'பொருள்'}[a] }. {n}"


def main():
    names = json.loads((ROOT / "sources/othu_names.json").read_text("utf-8"))
    recs = [json.loads(l) for p in sorted(glob.glob(str(ROOT / "data_v2/*/*.jsonl")))
            for l in open(p, encoding="utf-8")]
    recs.sort(key=lambda r: (PAD_NO[r["padalam"]], r["sutra"]))
    out = ["# செந்தமிழ் மரபு", "",
           "1602 நூற்பா · வழிநூல்: தனுசாந்தன் வர்ணகுலசிங்கம் · தொழில்நுட்ப உதவி: Claude",
           "", "_இக்கோப்பு data_v2 கணினி வடிவத்திலிருந்து scripts/build_nool.py உருவாக்கியது._", ""]
    cur_p = cur_o = None
    for r in recs:
        p, o = r["padalam"], r["othu"]
        if p != cur_p:
            out += [f"## படலம் {PAD_NO[p]}: {names[p]['_']}", ""]
            cur_p, cur_o = p, None
        if o != cur_o:
            grp = [x["sutra"] for x in recs if x["padalam"] == p and x["othu"] == o]
            out += [f"### ஓத்து {o}: {names[p][str(o)]}", "",
                    f"{len(grp)} சூத்திரங்கள் · {TA[p]}. {min(grp)}–{max(grp)}", ""]
            cur_o, k_in = o, 0
        k_in += 1
        lines = r["moolam"].split("\n")
        out.append(f"**{k_in}** · {TA[p]}. {r['sutra']}\\")
        out += [ln + "\\" for ln in lines[:-1]] + [lines[-1], ""]
        k = r["kaandigai"]
        kt = k["porul"]
        if k.get("ethu"):
            kt += f" ஏது, எடுத்துக்காட்டு (648): {k['ethu']}"
        out += [f"**காண்டிகை.** {kt}", ""]
        u = r.get("urai")
        if u:
            head = []
            if u.get("vagai"):
                vl = u.get("vilakkukkuriyathu") or []
                vs = ""
                if vl and u["vagai"] != "விதி":
                    g = {}
                    for x in vl:
                        a, n = x.split(".")
                        g.setdefault(a, []).append(n)
                    vs = " (" + "; ".join(f"{ {'ezhu': 'எழு', 'sol': 'சொல்', 'porul': 'பொருள்'}[a] }. {', '.join(ns)}" for a, ns in g.items()) + "-க்கு)"
                head.append(f"வகை (645): {u['vagai']}{vs}")
            out += [f"**உரை.** {' · '.join(head + [u.get('text', '')])}", ""]
        out += [f"_நிலை: {r['nilai']}_", ""]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")

    # round-trip — உருவான நூலிலிருந்தே மூலத்தை மீண்டும் படித்தல்
    moolam = json.loads((ROOT / "sources/moolam.json").read_text("utf-8"))
    L = OUT.read_text("utf-8").split("\n")
    hdr = re.compile(r"^\*\*(\d+)\*\* · (எழு|சொல்|பொருள்)\. (\d+)\\$")
    back = {}
    i = 0
    while i < len(L):
        m = hdr.match(L[i])
        if m:
            vid = f"{ {'எழு': 'ezhu', 'சொல்': 'sol', 'பொருள்': 'porul'}[m[2]] }.{m[3]}"
            v = []; i += 1
            while i < len(L) and L[i].strip():
                v.append(L[i].rstrip("\\")); i += 1
            back[vid] = "\n".join(v)
        i += 1
    bad = [k for k in moolam if N(back.get(k)) != N(moolam[k])]
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB); "
          f"round-trip: {len(back)} சூத்திரம், ஆவணப் பாடத்தோடு வேறுபாடு {len(bad)}")
    if bad:
        raise SystemExit(f"round-trip வேறுபாடு: {bad[:10]}")


if __name__ == "__main__":
    main()

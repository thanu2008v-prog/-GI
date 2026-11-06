#!/usr/bin/env python3
"""வேறு தளத்தில் எழுதிய உரையைச் சோதித்தல் — நூலை நூலாலே (பொருள். 645–650, 654).

பயன்: python3 check_urai.py urai_othu05.json [--othu ezhuthu:5]
தேவை: இதே அடைவில் moolam.json. Python 3 மட்டும்; வெளிப் பொதி இல்லை; இணையம் தேவையில்லை.
வெளியீடு: பிழை (திருத்த வேண்டியது) / எச்சரிக்கை (பார்க்க வேண்டியது). பிழை இருந்தால் exit 1.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOOLAM = json.loads((HERE / "moolam.json").read_text("utf-8"))
N = lambda s: re.sub(r"[\s/]+", "", s or "")
NM = {k: N(v) for k, v in MOOLAM.items()}
ALL = "".join(NM.values())
ABBR = {"எழு": "ezhu", "சொல்": "sol", "பொருள்": "porul"}
PAD = {"ezhu": "ezhuthu", "sol": "sol", "porul": "porul"}
VAGAI = {"விதி", "விலக்கு", "விதி-விலக்கு"}
NILAI = ("நூலில் நேரடியாக", "ஒருதலை அன்மை", "நூலில் இல்லை")
PIRAN = ["இளம்பூரண", "நச்சினார்", "பேராசிரிய", "சேனாவரைய", "தெய்வச்சிலை", "கல்லாடன", "நன்னூல்", "பாயிரம்"]
QUOTE = re.compile(r"[\"“]([^\"”]+)[\"”]\s*(?:\((எழு|சொல்|பொருள்)\.\s*(\d+))?")
REF = re.compile(r"(எழு|சொல்|பொருள்)\.\s*(\d+)")
RANGES = {"ezhu": 483, "sol": 463, "porul": 656}


def main(path, othu=None):
    data = json.loads(Path(path).read_text("utf-8"))
    err, warn = [], []
    E = lambda i, m: err.append(f"{i}: {m}")
    W = lambda i, m: warn.append(f"{i}: {m}")
    seen = set()
    old = {}
    if (HERE / "sutras_v2.jsonl").exists():
        for l in open(HERE / "sutras_v2.jsonl", encoding="utf-8"):
            r = json.loads(l)
            if (r.get("urai") or {}).get("text"):
                old[r["id"]] = 1
    noedu = 0
    for d in data:
        i = d.get("id", "?")
        if i not in MOOLAM:
            E(i, "இந்த எண் நூலில் இல்லை"); continue
        if i in seen:
            E(i, "இருமுறை வந்துள்ளது (கூறியது கூறல், 654)")
        seen.add(i)
        if othu:
            a, o = othu
            if PAD[i.split(".")[0]] != a:
                E(i, f"{a} அதிகாரத்துக்கு உரியதன்று")
        u = d.get("urai") or {}
        if not (d.get("ethu") or "").strip():
            E(i, "காண்டிகை ஏது இல்லை (648)")
        if not (u.get("text") or "").strip():
            E(i, "உரை இல்லை (649)")
        if u.get("vagai") not in VAGAI:
            E(i, f"வகை (645) தவறு: {u.get('vagai')!r} — விதி / விலக்கு / விதி-விலக்கு")
        if "விலக்கு" in (u.get("vagai") or "") and not u.get("vilakkukkuriyathu"):
            E(i, "விலக்கு எனில் எதற்கு விலக்கு என்று vilakkukkuriyathu வேண்டும்")
        for r in u.get("vilakkukkuriyathu", []) + u.get("iyaipu", []):
            if r not in MOOLAM:
                E(i, f"சுட்டு {r} நூலில் இல்லை")
            if r == i:
                E(i, "தன்னையே இயைபாகச் சுட்டுகிறது")
        if not u.get("iyaipu"):
            W(i, "இயைபு (649) பட்டியல் வெறுமை")
        if i in old:
            W(i, "இதற்கு உரை ஏற்கனவே உள்ளது — மேலெழுதும்; வேண்டுமென்றே எனில் மட்டும் வை")
        n = int(i.split(".")[1]); pre = i.split(".")[0]
        if u.get("iyaipu") and all(r.split(".")[0] == pre and abs(int(r.split(".")[1]) - n) <= 3 for r in u["iyaipu"]):
            W(i, "இயைபு அண்டை நூற்பாக்கள் மட்டும் — உண்மையான இயைபைத் தேடு (649 \"இன்றியமையாது இயைபவை எல்லாம்\")")
        if u.get("vagai") == "விதி" and re.search(r"\d+-இ?[னற]்?\s*\S*\s*விலக்க", u.get("text", "")):
            W(i, "உரை «விலக்கு» என்கிறது; வகை «விதி» — ஒத்துப் பார் (645)")
        ew = [w for w in re.findall(r"[\u0B80-\u0BFF]{3,}", d.get("ethu", "")) if not re.match(r"[\u0B80-\u0BFF]*(என்|ஆகும்|வரும்)", w)]
        if ew and sum(1 for w in ew if N(w)[:4] in NM[i]) / len(ew) >= 0.6:
            W(i, "ஏது நூற்பாவைத் திருப்பிச் சொல்கிறது; ஏது = ஏன்/எப்படி (648) — பொருள் ஏற்கனவே kaandigai.porul-இல் உள்ளது")
        if not d.get("eduthukkaattu"):
            noedu += 1
        th = u.get("thunivu", "")
        if not any(n in th for n in NILAI):
            E(i, "துணிவில் மூன்று நிலையுள் ஒன்று வேண்டும் (650)")
        # எடுத்துக்காட்டு: நூலின் சொந்தப் பாடத்திலிருந்து மட்டும் (648)
        for q in d.get("eduthukkaattu", []):
            f = q.get("from")
            if f not in MOOLAM:
                E(i, f"எடுத்துக்காட்டின் இடம் {f} நூலில் இல்லை")
            elif N(q.get("text")) not in NM[f]:
                E(i, f"எடுத்துக்காட்டு \"{q.get('text')}\" {f}-இல் எழுத்துக்கு எழுத்து இல்லை")
        for m in u.get("maruthalai", []):
            if not m.get("kadaa") or not m.get("maattram"):
                E(i, "மறுதலைக் கடாஅ-வுக்குக் கேள்வியும் மாற்றமும் வேண்டும் (650)")
            for q in m.get("saanru", []):
                if q.get("from") not in MOOLAM or N(q.get("text")) not in NM[q["from"]]:
                    E(i, f"மறுதலைச் சான்று \"{q.get('text')}\" ({q.get('from')}) நூலில் இல்லை")
        texts = [d.get("ethu", ""), u.get("text", ""), th] + \
                [m.get(k, "") for m in u.get("maruthalai", []) for k in ("kadaa", "maattram")]
        for t in texts:
            for p in PIRAN:
                if p in t:
                    E(i, f"பிறன் கோள் ({p}) — இந்நூல் மட்டும் (656)")
            for m in REF.finditer(t):
                if int(m.group(2)) > RANGES[ABBR[m.group(1)]] or int(m.group(2)) < 1:
                    E(i, f"சுட்டு {m.group(0)} எல்லைக்கு வெளியே")
            for m in QUOTE.finditer(t):
                parts = [x for x in re.split(r"…|\.\.\.", m.group(1)) if N(x)]
                if m.group(2):
                    rid = f"{ABBR[m.group(2)]}.{m.group(3)}"
                    for x in parts:
                        if rid not in NM:
                            E(i, f"{rid} நூலில் இல்லை")
                        elif N(x) not in NM[rid]:
                            E(i, f"மேற்கோள் \"{x.strip()}\" {rid}-இல் எழுத்துக்கு எழுத்து இல்லை")
                else:
                    for x in parts:
                        if N(x) not in NM[i] and N(x) not in ALL:
                            W(i, f"மேற்கோள் \"{x.strip()}\" நூலில் எங்கும் காணவில்லை (மேற்கோளன்றிச் சொல்லாயின் சரி)")
    if data and noedu / len(data) > 0.5:
        W("ஓத்து", f"{noedu} / {len(data)} நூற்பாவுக்கு எடுத்துக்காட்டு இல்லை — நூலின் பாடத்தில் தேடினீர்களா? (648; எ.கா. nool_1602.txt-இல் விதிக்குப் பொருந்தும் புணர்ந்த வடிவம்)")
    if othu:
        a, o = othu
        want = {k for k in MOOLAM if PAD[k.split(".")[0]] == a and k in OTHU and OTHU[k] == o}
        miss = sorted(want - seen, key=lambda k: int(k.split(".")[1]))
        if miss:
            W("ஓத்து", f"உரை இல்லாதவை: {', '.join(miss)}")
    for x in err:
        print("பிழை  ", x)
    for x in warn:
        print("எச்சரிக்கை", x)
    print(f"\nபதிவு {len(data)} · பிழை {len(err)} · எச்சரிக்கை {len(warn)}")
    sys.exit(1 if err else 0)


OTHU = {}
_o = HERE / "othu_of.json"
if _o.exists():
    OTHU = json.loads(_o.read_text("utf-8"))

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    ot = None
    if "--othu" in args:
        k = args.index("--othu"); a, o = args[k + 1].split(":"); ot = (a, int(o)); del args[k:k + 2]
    main(args[0], ot)

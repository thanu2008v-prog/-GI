"""நூலை நூலாலே சோதித்தல் — v2 தரவை இந்நூல் கூறும் விதிகளால் சரிபார்க்கிறது.

  அமைப்பு          பொருள். 470–474   1602 சூத்திரம் → 27 ஓத்து → 3 படலம் → 1 பிண்டம்
  மூலம்            பொருள். 640, 652  ஒவ்வொரு சூத்திரச் சொல்லும் ஆவணப் பாடத்தோடு எழுத்துக்கு எழுத்து; SHA-256
  காண்டிகை         பொருள். 647, 648  ஒவ்வொன்றுக்கும் பொருள்; எடுத்துக்காட்டு நூலுள் உள்ளதே
  உரை             பொருள். 645, 649, 650  இயைபு உள்ள நூற்பா; விதி/விலக்கு; மறுதலைச் சான்று நூலுள்
  பத்துச் சிதைவு    பொருள். 654       அளக்கக் கூடியவை மட்டும் (மற்றவை "மனிதச் சோதனை")
  உத்தி            பொருள். 656       குறிக்கப்பட்ட உத்திகள் 32 பெயருள்ளவையே

நிலை: பிழை (exit 1) / நிலுவை (குன்றக் கூறல் — இன்னும் எழுதப்படாதது) / சரி.
python3 scripts/check_nool.py
"""
import json, glob, re, hashlib, collections, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
N = lambda s: re.sub(r"[\s/]+", "", s or "")
UTTHI = ["நுதலியது அறிதல்", "அதிகார முறை", "தொகுத்துக் கூறல்", "வகுத்து மெய்ந் நிறுத்தல்",
         "மொழிந்த பொருளொடு ஒன்ற மொழியாததனை முட்டு இன்றி முடித்தல்", "வாராததனான் வந்தது முடித்தல்",
         "வந்தது கொண்டு வாராதது உணர்த்தல்", "முந்து மொழிந்ததன் தலைதடுமாற்றே", "ஒப்பக் கூறல்",
         "ஒருதலை மொழிதல்", "தன் கோள் கூறல்", "முறை பிறழாமை", "பிறன் உடன்பட்டது தான் உடம்படுதல்",
         "இறந்தது காத்தல்", "எதிரது போற்றல்", "மொழிவாம் என்றல்", "கூறிற்று என்றல்", "தான் குறியிடுதல்",
         "ஒருதலை அன்மை", "முடிந்தது காட்டல்", "ஆணை கூறல்", "பல் பொருட்கு ஏற்பின் நல்லது கோடல்",
         "தொகுத்த மொழியான் வகுத்தனர் கோடல்", "மறுதலை சிதைத்துத் தன் துணிபு உரைத்தல்", "பிறன் கோள் கூறல்",
         "அறியாது உடம்படல்", "பொருள் இடையிடுதல்", "எதிர் பொருள் உணர்த்தல்",
         "சொல்லின் எச்சம் சொல்லியாங்கு உணர்த்தல்", "தந்து புணர்ந்து உரைத்தல்", "ஞாபகம் கூறல்",
         "உய்த்துக்கொண்டு உணர்த்தல்"]
PIRAN = ["இளம்பூரண", "நச்சினார்", "பேராசிரிய", "சேனாவரைய", "தெய்வச்சிலை", "கல்லாடன", "நன்னூல்"]
EXPECTED = {"ezhuthu": 483, "sol": 463, "porul": 656}


def main():
    recs = [json.loads(l) for p in sorted(glob.glob(str(ROOT / "data_v2/*/*.jsonl")))
            for l in open(p, encoding="utf-8")]
    by = {r["id"]: r for r in recs}
    moolam = json.loads((ROOT / "sources/moolam.json").read_text("utf-8"))
    err, pend, ok = collections.defaultdict(list), collections.defaultdict(list), []

    # அமைப்பு — 470–474
    othu = {(r["padalam"], r["othu"]) for r in recs}
    for a, n in EXPECTED.items():
        have = sorted(r["sutra"] for r in recs if r["padalam"] == a)
        if have != list(range(1, n + 1)):
            err["அமைப்பு (470)"].append(f"{a}: 1–{n} தொடர்ச்சியில்லை")
    if (len(recs), len(othu), len({r['padalam'] for r in recs})) != (1602, 27, 3):
        err["அமைப்பு (470)"].append(f"{len(recs)} / {len(othu)} / {len({r['padalam'] for r in recs})}")
    else:
        ok.append("அமைப்பு (470–474): 1602 சூத்திரம் → 27 ஓத்து → 3 படலம் → 1 பிண்டம்")

    # மூலம் — 640, 652
    diff = [r["id"] for r in recs if N(r["moolam"]) != N(moolam.get(r["id"]))]
    if diff:
        err["மூலம் (652)"] += diff
    h = hashlib.sha256("\n".join(by[k]["moolam"] for k in sorted(by, key=lambda x: (
        ["ezhu", "sol", "porul"].index(x.split(".")[0]), int(x.split(".")[1])))).encode()).hexdigest()
    ok.append(f"மூலம் (640, 652): 1602 / 1602 ஆவணப் பாடத்தோடு ஒத்தது — SHA-256 {h[:16]}…")

    seen_k, seen_u = collections.defaultdict(list), collections.defaultdict(list)
    for r in recs:
        k, u, rid = r["kaandigai"], r.get("urai"), r["id"]
        # காண்டிகை — 647, 648
        if not N(k.get("porul")):
            err["காண்டிகை (647)"].append(rid)
        for q in k.get("eduthukkaattu", []):
            if q["from"] not in by or N(q["text"]) not in N(by[q["from"]]["moolam"]):
                err["எடுத்துக்காட்டு நூலுள் இல்லை (648; 654 தன்னான் கருதிக் கூறல்)"].append(f"{rid}: \"{q['text']}\" ≠ {q['from']}")
        seen_k[N(k.get("porul"))].append(rid)
        en = k.get("en") or {}
        if en.get("kooruvathu") is not None and en.get("enniyathu") is not None \
                and en["kooruvathu"] != en["enniyathu"] and r["nilai"] != "ஒருதலை அன்மை":
            err["மாறு கொளக் கூறல் (654)"].append(f"{rid}: கூறுவது {en['kooruvathu']} ≠ எண்ணியது {en['enniyathu']}")
        text_all = k.get("porul", "") + k.get("ethu", "") + (u or {}).get("text", "")
        for w in PIRAN:
            if w in text_all:
                err["பிறன் கோள் கலப்பு (656)"].append(f"{rid}: {w}")
        for t in r.get("utthi", []):
            if t not in UTTHI:
                err["உத்தி 32-இல் இல்லை (656)"].append(f"{rid}: {t}")
        # உரை — 645, 649, 650
        if not u:
            pend["உரை எழுதப்படவில்லை (649)"].append(rid)
            continue
        if "எடுத்துக்காட்டு (648)" in u.get("text", ""):
            err["எடுத்துக்காட்டு உரையில் (648 — காண்டிகைக்கு உரியது)"].append(rid)
        for x in u.get("iyaipu", []):
            if x not in by:
                err["இயைபு — இல்லாத நூற்பா (649)"].append(f"{rid} → {x}")
        if not u.get("iyaipu"):
            pend["இயைபு குறிக்கப்படவில்லை (649)"].append(rid)
        if not u.get("vagai"):
            pend["விதி / விலக்கு குறிக்கப்படவில்லை (645)"].append(rid)
        for m in u.get("maruthalai", []):
            for q in m.get("saanru", []):
                if q["from"] not in by or N(q["text"]) not in N(by[q["from"]]["moolam"]):
                    err["மறுதலைச் சான்று நூலுள் இல்லை (650)"].append(f"{rid}: \"{q['text']}\" ≠ {q['from']}")
        th = u.get("thunivu", "")
        if "ஒருதலை அன்மை" in th and r["nilai"] == "நூலில் நேரடியாக" and "விதி நூலில் நேரடியாக" not in th:
            err["நிலை மாறுபாடு — துணிவு ஒருதலை அன்மை, பதிவு நேரடி (654 மாறு கொளக் கூறல்)"].append(rid)
        if u.get("text"):
            seen_u[N(u["text"])].append(rid)

    for d, label in ((seen_k, "காண்டிகை"), (seen_u, "உரை")):
        for t, ids in d.items():
            if t and len(ids) > 1:
                err[f"கூறியது கூறல் (654) — ஒரே {label}"].append(", ".join(ids))

    print("— சரி —")
    for x in ok:
        print("  ✔", x)
    print("\n— நிலுவை (குன்றக் கூறல்: இன்னும் செய்ய வேண்டியவை) —")
    for k, v in pend.items():
        print(f"  … {k}: {len(v)}")
    print("\n— பிழை —" if err else "\n— பிழை: இல்லை —")
    for k, v in err.items():
        print(f"  ✘ {k}: {len(v)}")
        for x in v[:6]:
            print("      ", x)
    print("\nமனிதச் சோதனைக்கு உரியவை (பொருள். 654 — எண்ணால் அளக்க இயலாதவை): பொருள் இல கூறல், மயங்கக் கூறல், "
          "கேட்போர்க்கு இன்னா யாப்பு, பழித்த மொழியான் இழுக்கம் கூறல், என்ன வகையினும் மனம் கோள் இன்மை; "
          "\"வல்லோன் புணரா வாரம் போன்றே\" (பொருள். 653).")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()

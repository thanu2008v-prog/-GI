"""நூலை நூலாலே சோதித்தல்: மொழிமரபு விதிகளை 1602 நூற்பாவின் பாடத்தின் மேல் இயக்கி,
நூலே விதிக்கு மாறாகத் தோன்றும் இடங்களைப் பட்டியலிடுகிறது (பொருள். 650 — தன் நூலான் ஐயம்).
எழுத்ததிகாரப் பாடம் பழைய சொற்பிரிப்பில் இருப்பதால் (எ.கா. "யுரையசைக்") சொல், பொருள் பாடமே
முதன்மை அளவு; எழுத்ததிகாரம் தனியே காட்டப்படுகிறது.
python3 -m tests.test_mozhimarabu
"""
import json, glob, collections, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rules.mozhimarabu import check_word, check_text   # noqa: E402

# அடிப்படை அலகுச் சோதனைகள் — நூற்பாச் சொல்லிலிருந்தே
CASES = [
    ("யாது", "முதல்", "ஒத்தது"), ("யுரை", "முதல்", "மாறு"),        # எழு. 65
    ("ஞாயிறு", "முதல்", "ஒத்தது"), ("ஞகாரத்", "முதல்", "விலக்கு"),  # எழு. 64, 66
    ("சல்லல்", "முதல்", "மாறு"),                                      # எழு. 62 — நூலே ஆள்கிறது
    ("எழுத்து", "இறுதி", "ஒத்தது"), ("அளவு", "இறுதி", "ஒருதலை அன்மை"),  # எழு. 69, 74
    ("மகரம்", "இறுதி", "ஒத்தது"),                                     # எழு. 78
]


def main():
    bad = 0
    for w, kind, want in CASES:
        got = [f["status"] for f in check_word(w) if f["kind"] == kind]
        ok = got and got[0] == want
        bad += not ok
        print(("✔" if ok else "✘"), w, kind, got, "எதிர்பார்ப்பு:", want)
    stat = collections.Counter(); found = collections.defaultdict(list)
    for p in sorted(glob.glob(str(ROOT / "data/sutras/*/*.jsonl"))):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            part = "எழுத்து" if r["adhikaram"] == "ezhuthu" else "சொல்-பொருள்"
            for w, fs in check_text(r["verse"].replace("\n", " ")):
                for f in fs:
                    stat[(part, f["kind"], f["status"])] += 1
                    if f["status"] in ("மாறு", "ஒருதலை அன்மை") and part == "சொல்-பொருள்":
                        found[(f["sutra"], f["status"])].append(f"{r['id']}:{w}")
    print("\nதொகை (பாடம், வகை, நிலை):")
    for k, v in sorted(stat.items()):
        print("  ", k, v)
    print("\nசொல்-பொருள் பாடத்தில் நூலே விதிக்கு மாறாகத் தோன்றும் இடங்கள் (ஐயம்):")
    for (s, st), ws in sorted(found.items()):
        print(f"  {s} [{st}] {len(ws)}: {', '.join(ws[:8])}{' …' if len(ws) > 8 else ''}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

"""செந்தமிழ் மரபுக் குறியாக்கம் (மரபுக் குறி) — நூலின் எழுத்து விதிகளையே பிட் அமைப்பாகக் கொண்ட தமிழ்க் குறியாக்கம்.

ஓர் எழுத்து = ஒரு 16-பிட் அலகு. அலகின் பிட்கள் நூல் வகுத்த கூறுகளையே குறிக்கின்றன:

  பிட் 15      1 = மரபு எழுத்து; 0 = பிற குறி (இடைவெளி, வரி முறிவு — அதன் யூனிகோடு மதிப்பே, 0x0000–0x7FFF)
  பிட் 14–12   சார்புநிலை: 0 இயல்பு, 1 குற்றியலுகரம் (எழு. 36), 2 குற்றியலிகரம் (எழு. 34),
               3 ஐகாரக் குறுக்கம் (எழு. 57), 4 மகரக் குறுக்கம் (எழு. 13) — 3, 4 ஒதுக்கியவை
  பிட் 11–10   மெய்யின் இனம்: 0 இல்லை, 1 வல்லினம் (எழு. 19), 2 மெல்லினம் (எழு. 20), 3 இடையினம் (எழு. 21)
  பிட் 9–7     இனத்துள் இடம் 0–5 — நூற்பாவின் வரிசைப்படி. வல்லினமும் மெல்லினமும் ஒரே இடத்தில் ஒரே பிறப்பிடம்:
               க/ங முதல்நா அண்ணம் (எழு. 89), ச/ஞ இடைநா (90), ட/ண நுனிநா (91), த/ந (93), ப/ம இதழ் (97), ற/ன (94);
               ஆகவே இன மெல்லெழுத்து (எழு. 143) = இனப் பிட்டை மட்டும் மாற்றுதல்.
  பிட் 6       ஒதுக்கியது (0)
  பிட் 5–3     உயிர்: 0 இல்லை (புள்ளி — எழு. 15), 1 அ, 2 இ, 3 உ, 4 எ, 5 ஒ (குறில் ஐந்து, எழு. 3), 6 ஐ, 7 ஔ
  பிட் 2       அளவு: 0 குறில் (ஓரளபு, எழு. 3), 1 நெடில் (ஈரளபு, எழு. 4)
  பிட் 1–0     ஒதுக்கியவை (0)

  ஆய்தம் (எழு. 2, 38): இனம் 0, உயிர் 0 — மெய்யும் அல்லாத உயிரும் அல்லாத «முப்பாற் புள்ளி».
  உயிர்மெய் = மெய் + உயிர் ஒரே அலகில் (எழு. 18 «மெய்யின் வழிய துயிர்தோன்று நிலையே»).
  ஐ = அ + இ (எழு. 54), ஔ = அ + உ (எழு. 55) — குறில் இணை இல்லாத நெடில்கள்; பண்பு 6, 7, அளவு எப்போதும் 1.

வட எழுத்து (ஜ, ஷ, ஸ, ஹ முதலியன) நூலின் எழுத்து அல்ல — «வட எழுத்து ஒரீஇ» (சொல். 401); அவை பிற குறியாகவே
நிற்க வேண்டும், ஆனால் 0x8000-க்கு மேற்பட்ட யூனிகோடு மதிப்பு அல்லாததால் இவ்வமைப்பில் நேரடியாக அடங்கும் (பிட் 15 = 0).
"""
from fractions import Fraction
import unicodedata

UYIR = ["அ", "இ", "உ", "எ", "ஒ", "ஐ", "ஔ"]                      # பண்பு 1–7
NEDIL = {"அ": "ஆ", "இ": "ஈ", "உ": "ஊ", "எ": "ஏ", "ஒ": "ஓ"}        # எழு. 3, 4
SIGN = {("அ", 0): "", ("அ", 1): "ா", ("இ", 0): "ி", ("இ", 1): "ீ", ("உ", 0): "ு", ("உ", 1): "ூ",
        ("எ", 0): "ெ", ("எ", 1): "ே", ("ஐ", 1): "ை", ("ஒ", 0): "ொ", ("ஒ", 1): "ோ", ("ஔ", 1): "ௌ"}
INAM = {1: "கசடதபற", 2: "ஙஞணநமன", 3: "யரலவழள"}                  # எழு. 19, 20, 21 — நூற்பா வரிசை
PULLI, AAYTHAM = "்", "ஃ"
SAARBU = {0: "இயல்பு", 1: "குற்றியலுகரம்", 2: "குற்றியலிகரம்", 3: "ஐகாரக் குறுக்கம்", 4: "மகரக் குறுக்கம்"}

MEY_OF = {ch: (i, j) for i, s in INAM.items() for j, ch in enumerate(s)}
SIGN_OF = {v: k for k, v in SIGN.items() if v}
UYIR_OF = {}
for q, u in enumerate(UYIR, 1):
    if u in NEDIL:
        UYIR_OF[u] = (q, 0); UYIR_OF[NEDIL[u]] = (q, 1)
    else:
        UYIR_OF[u] = (q, 1)                                          # ஐ, ஔ — நெடில் (எழு. 4)


def make(inam=0, idam=0, uyir=0, alavu=0, saarbu=0):
    return 0x8000 | (saarbu << 12) | (inam << 10) | (idam << 7) | (uyir << 3) | (alavu << 2)


def fields(c):
    return {"saarbu": (c >> 12) & 7, "inam": (c >> 10) & 3, "idam": (c >> 7) & 7,
            "uyir": (c >> 3) & 7, "alavu": (c >> 2) & 1}


def is_ezhuthu(c):
    return bool(c & 0x8000)


def encode(text):
    """யூனிகோடு தமிழ் → மரபுக் குறி அலகுகள் (ஓர் எழுத்துக்கு ஒன்று)."""
    text = unicodedata.normalize("NFC", text)
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in MEY_OF:
            inam, idam = MEY_OF[ch]
            nx = text[i + 1] if i + 1 < n else ""
            if nx == PULLI:
                out.append(make(inam, idam)); i += 2
            elif nx in SIGN_OF:
                (u, a) = SIGN_OF[nx]; q = UYIR.index(u) + 1
                out.append(make(inam, idam, q, a)); i += 2
            else:                                                     # புள்ளியில்லா மெய் அகரத்தோடு (எழு. 17)
                out.append(make(inam, idam, 1, 0)); i += 1
        elif ch in UYIR_OF:
            q, a = UYIR_OF[ch]; out.append(make(0, 0, q, a)); i += 1
        elif ch == AAYTHAM:
            out.append(make()); i += 1
        else:
            cp = ord(ch)
            if cp >= 0x8000:
                raise ValueError(f"இவ்வமைப்பில் அடங்காத குறி: {ch!r} (U+{cp:04X})")
            out.append(cp); i += 1
    return out


def decode(codes):
    """மரபுக் குறி → யூனிகோடு. சார்புநிலைப் பிட்கள் வடிவத்தை மாற்றுவதில்லை (எழு. 2 «எழுத்தோ ரன்ன»)."""
    s = []
    for c in codes:
        if not is_ezhuthu(c):
            s.append(chr(c)); continue
        f = fields(c)
        if f["inam"] == 0:
            if f["uyir"] == 0:
                s.append(AAYTHAM)
            else:
                u = UYIR[f["uyir"] - 1]
                s.append(NEDIL[u] if (f["alavu"] and u in NEDIL) else u)
        else:
            m = INAM[f["inam"]][f["idam"]]
            s.append(m + (PULLI if f["uyir"] == 0 else SIGN[(UYIR[f["uyir"] - 1], f["alavu"])]))
    return "".join(s)


def maathirai(c):
    """நூல் கூறும் அளவு. மகரக் குறுக்கத்துக்கு எண் நூலில் இல்லை (எழு. 13 «அரையளவு குறுகல்») — None."""
    f = fields(c)
    if f["saarbu"] in (1, 2):
        return Fraction(1, 2)                                         # எழு. 12
    if f["saarbu"] == 3:
        return Fraction(1)                                            # எழு. 57 «ஓரள பாகும்»
    if f["saarbu"] == 4:
        return None
    if f["uyir"] == 0:
        return Fraction(1, 2)                                         # மெய் (எழு. 11), ஆய்தம் (எழு. 12)
    return Fraction(2 if f["alavu"] else 1)                           # எழு. 3, 4, 10


def ina_mellezhuthu(c):
    """எழு. 143: வல்லெழுத்தின் இன மெல்லெழுத்து — இனப் பிட் 1 → 2, இடம் மாறாது."""
    f = fields(c)
    if f["inam"] != 1:
        raise ValueError("வல்லினம் அன்று")
    return (c & ~(3 << 10)) | (2 << 10)


def name(c):
    if not is_ezhuthu(c):
        return f"பிற குறி U+{c:04X}"
    f = fields(c)
    if f["inam"] == 0 and f["uyir"] == 0:
        kind = "ஆய்தம்"
    elif f["inam"] == 0:
        kind = "உயிர் " + ("நெடில்" if f["alavu"] else "குறில்")
    elif f["uyir"] == 0:
        kind = "மெய் (" + {1: "வல்லினம்", 2: "மெல்லினம்", 3: "இடையினம்"}[f["inam"]] + ")"
    else:
        kind = "உயிர்மெய் " + ("நெடில்" if f["alavu"] else "குறில்")
    sb = f" · {SAARBU[f['saarbu']]}" if f["saarbu"] else ""
    return f"{decode([c & ~(7 << 12)])} — {kind}{sb}"


def saarbu_kuri(codes):
    """சார்பெழுத்தைக் குறித்தல் — நூல் விதிப்படி (சொல் எல்லை = இடைவெளி / வரி முறிவு):
    குற்றியலுகரம் — "நெட்டெழுத் திம்பருந் தொடர்மொழி யீற்றுங் / குற்றிய லுகரம் வல்லா றூர்ந்தே" (எழு. 36):
      சொல்லிறுதி வல்லின உகரக் குறில்; சொல் இரண்டு எழுத்துக்கு மேல் (தொடர்மொழி, எழு. 45), அல்லது
      இரண்டெழுத்தாய் முதல் எழுத்து நெடில் (நெட்டெழுத்து இம்பர்).
    குற்றியலிகரம் — "யாவென் சினைமிசை யுரையசைக் கிளவிக் / காவயின் வரூஉம் மகரம் ஊர்ந்தே" (எழு. 34): மியா-வின் இ.
    சொல் எல்லை பாடத்தின் சொற்பிரிப்பைச் சார்ந்தது; எழுத்ததிகாரப் பாடம் பழைய அச்சுப் பிரிப்பு — ஒருதலை அன்மை."""
    out = list(codes)
    words, cur = [], []
    for i, c in enumerate(out):
        if is_ezhuthu(c):
            cur.append(i)
        else:
            if cur: words.append(cur)
            cur = []
    if cur: words.append(cur)
    for w in words:
        last = fields(out[w[-1]])
        if last["inam"] == 1 and last["uyir"] == 3 and last["alavu"] == 0:
            first = fields(out[w[0]])
            if len(w) > 2 or (len(w) == 2 and first["alavu"] == 1 and first["uyir"] != 0):
                out[w[-1]] |= (1 << 12)
        for a, b in zip(w, w[1:]):
            fa, fb = fields(out[a]), fields(out[b])
            if (fa["inam"], fa["idam"], fa["uyir"], fa["alavu"]) == (2, 4, 2, 0) and \
               (fb["inam"], fb["idam"], fb["uyir"], fb["alavu"]) == (3, 0, 1, 1):
                out[a] |= (2 << 12)                                   # மி + யா
    return out

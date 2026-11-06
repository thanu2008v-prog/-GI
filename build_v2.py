"""data_v2 (மூலம்) → build/ (SQLite + FTS5, bundle.json, CSV) + export/yaml (ஓத்து வாரியாக).

மூலம் data_v2 ஒன்றே. இங்கு உருவாகும் எதையும் கைமுறையாகத் திருத்தக் கூடாது (பொருள். 468 —
"மாறுகோள் இன்றி"). YAML தமிழறிஞர் வாசித்துத் திருத்துவதற்கு; திருத்தியதை
scripts/import_yaml.py மீண்டும் data_v2-க்குக் கொண்டுவரும் (ஒரே மூலம்).
python3 scripts/build_v2.py
"""
import json, glob, csv, sqlite3, datetime, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from normalize import nfc, norm_search, sort_key  # noqa: E402

PAD = ["ezhuthu", "sol", "porul"]
B = ROOT / "build"


def load():
    recs = [json.loads(l) for p in sorted(glob.glob(str(ROOT / "data_v2/*/*.jsonl")))
            for l in open(p, encoding="utf-8")]
    recs.sort(key=lambda r: (PAD.index(r["padalam"]), r["sutra"]))   # அதிகார முறை (பொருள். 656)
    return recs


def build_db(recs):
    db = B / "senthamil_v2.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE sutra (id TEXT PRIMARY KEY, padalam TEXT, othu INTEGER, sutra INTEGER,
      moolam TEXT NOT NULL, moolam_norm TEXT, kaandigai_porul TEXT, kaandigai_ethu TEXT,
      urai_text TEXT, urai_vagai TEXT, thunivu TEXT, nilai TEXT, kind TEXT, record TEXT,
      UNIQUE(padalam, sutra));
    CREATE TABLE edu (sutra_id TEXT, text TEXT, from_id TEXT);          -- எடுத்துக்காட்டு (648)
    CREATE TABLE link (from_id TEXT, to_id TEXT, kind TEXT,             -- iyaipu (649) | links | vilakku (645)
      PRIMARY KEY(from_id, to_id, kind));
    CREATE TABLE maruthalai (sutra_id TEXT, kadaa TEXT, maattram TEXT);  -- 650
    CREATE INDEX i_othu ON sutra(padalam, othu); CREATE INDEX i_nilai ON sutra(nilai);
    CREATE INDEX i_link_to ON link(to_id);
    CREATE VIRTUAL TABLE sutra_fts USING fts5(id UNINDEXED, moolam, kaandigai, urai, tokenize='trigram');
    """)
    for r in recs:
        k, u = r["kaandigai"], r.get("urai") or {}
        con.execute("INSERT INTO sutra VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["id"], r["padalam"], r["othu"], r["sutra"], nfc(r["moolam"]), norm_search(r["moolam"]),
                     k["porul"], k.get("ethu"), u.get("text"), u.get("vagai"), u.get("thunivu"),
                     r["nilai"], r["kanini"]["kind"], json.dumps(r, ensure_ascii=False)))
        for q in k.get("eduthukkaattu", []):
            con.execute("INSERT INTO edu VALUES (?,?,?)", (r["id"], q["text"], q["from"]))
        for kind, ts in (("iyaipu", u.get("iyaipu", [])), ("links", r.get("links", [])),
                         ("vilakku", u.get("vilakkukkuriyathu", []))):
            for t in ts:
                con.execute("INSERT OR IGNORE INTO link VALUES (?,?,?)", (r["id"], t, kind))
        for m in u.get("maruthalai", []):
            con.execute("INSERT INTO maruthalai VALUES (?,?,?)", (r["id"], m["kadaa"], m["maattram"]))
        con.execute("INSERT INTO sutra_fts VALUES (?,?,?,?)",
                    (r["id"], norm_search(r["moolam"]), norm_search(k["porul"] + (k.get("ethu") or "")),
                     norm_search(u.get("text", ""))))
    con.commit(); con.execute("VACUUM"); con.close()
    return db


def build_bundle(recs):
    by_othu, by_letter, by_nilai = {}, {}, {}
    for r in recs:
        by_othu.setdefault(f"{r['padalam']}.{r['othu']}", []).append(r["id"])
        by_letter.setdefault(nfc(r["moolam"])[0], []).append(r["id"])
        by_nilai.setdefault(r["nilai"], []).append(r["id"])
    letters = sorted(by_letter, key=sort_key)                      # நூல் கூறும் எழுத்து வரிசை
    bundle = {"meta": {"title": "செந்தமிழ் மரபு", "total_sutras": len(recs), "schema": "2.0",
                       "built": datetime.date.today().isoformat()},
              "counts": {"by_padalam": {p: sum(r["padalam"] == p for r in recs) for p in PAD},
                         "by_nilai": {k: len(v) for k, v in by_nilai.items()},
                         "urai": sum(1 for r in recs if r.get("urai"))},
              "sutras": recs,
              "index": {"by_othu": by_othu, "by_letter": {c: by_letter[c] for c in letters},
                        "by_nilai": by_nilai}}
    out = B / "bundle_v2.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    return out


def build_csv(recs):
    out = B / "sutras_v2.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "padalam", "othu", "sutra", "moolam", "kaandigai_porul", "kaandigai_ethu",
                    "urai", "vagai", "thunivu", "nilai"])
        for r in recs:
            k, u = r["kaandigai"], r.get("urai") or {}
            w.writerow([r["id"], r["padalam"], r["othu"], r["sutra"], r["moolam"], k["porul"],
                        k.get("ethu", ""), u.get("text", ""), u.get("vagai", ""), u.get("thunivu", ""), r["nilai"]])
    return out


class _Lit(str):
    pass


yaml.add_representer(_Lit, lambda d, s: d.represent_scalar("tag:yaml.org,2002:str", s, style="|"))


def export_yaml(recs):
    base = ROOT / "export/yaml"
    n = 0
    for p in PAD:
        for o in sorted({r["othu"] for r in recs if r["padalam"] == p}):
            grp = [r for r in recs if r["padalam"] == p and r["othu"] == o]
            docs = []
            for r in grp:
                d = dict(r)
                d["moolam"] = _Lit(r["moolam"])
                docs.append(d)
            path = base / p / f"othu-{o:02d}.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# இக்கோப்பு data_v2-இலிருந்து உருவானது. 'moolam' (சூத்திரம்) திருத்தக் கூடாது (பொருள். 652).\n"
                            + yaml.dump(docs, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
            n += 1
    return n


def main():
    B.mkdir(exist_ok=True)
    recs = load()
    db, bun, cs = build_db(recs), build_bundle(recs), build_csv(recs)
    n = export_yaml(recs)
    print(f"Built {db.name}, {bun.name} ({bun.stat().st_size // 1024} KB), {cs.name}; YAML: {n} ஓத்து கோப்பு")


if __name__ == "__main__":
    main()

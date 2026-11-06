"""Build build/senthamil.db (SQLite) from all JSONL sutra records.

Tables
  sutra    one row per nūṟpā; full record also kept as JSON in `record`
  link     from_id → to_id, kind ∈ {link, ref, criterion_for}
  sutra_fts  FTS5 (trigram tokenizer → substring search works for Tamil);
             columns are whitespace-stripped so 'அகரமுதல்' finds 'அகர முதல'
"""
import json, glob, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from normalize import nfc, norm_search  # noqa: E402

OUT = ROOT / "build/senthamil.db"
ORDER = ["ezhuthu", "sol", "porul"]

DDL = """
CREATE TABLE sutra (
  id TEXT PRIMARY KEY,
  adhikaram TEXT NOT NULL,
  othu INTEGER NOT NULL,
  sutra INTEGER NOT NULL,
  verse TEXT NOT NULL,
  kaandigai TEXT NOT NULL,
  nul_kurum_text TEXT,
  nul_kurum_function TEXT,
  nul_kurum_kuri TEXT,
  viparam TEXT,
  kuri TEXT NOT NULL,
  kind TEXT NOT NULL,
  computer TEXT NOT NULL,
  v_stated REAL, v_computed REAL, v_match INTEGER,
  record TEXT NOT NULL,
  UNIQUE (adhikaram, sutra)
);
CREATE INDEX sutra_othu ON sutra(adhikaram, othu);
CREATE INDEX sutra_kind ON sutra(kind);
CREATE INDEX sutra_kuri ON sutra(kuri);
CREATE TABLE link (
  from_id TEXT NOT NULL REFERENCES sutra(id),
  to_id   TEXT NOT NULL REFERENCES sutra(id),
  kind    TEXT NOT NULL,
  PRIMARY KEY (from_id, to_id, kind)
);
CREATE INDEX link_to ON link(to_id);
"""


def records():
    for p in sorted(glob.glob(str(ROOT / "data/sutras/**/*.jsonl"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def main():
    OUT.parent.mkdir(exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    con = sqlite3.connect(OUT)
    con.executescript(DDL)
    fts = True
    try:
        con.execute("CREATE VIRTUAL TABLE sutra_fts USING fts5("
                    "id UNINDEXED, verse, kaandigai, nul_kurum, viparam, tokenize='trigram')")
    except sqlite3.OperationalError:
        fts = False

    rows = sorted(records(), key=lambda r: (ORDER.index(r["adhikaram"]), r["sutra"]))
    for r in rows:
        nk = r.get("nul_kurum", {})
        v = r.get("verification") or {}
        con.execute(
            "INSERT INTO sutra VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r["id"], r["adhikaram"], r["othu"], r["sutra"], nfc(r["verse"]),
             nfc(r["kaandigai"]), nk.get("text"), nk.get("function"), nk.get("kuri"),
             r.get("viparam", ""), r["kuri"], r["computer"]["kind"],
             json.dumps(r["computer"], ensure_ascii=False),
             v.get("stated"), v.get("computed"),
             None if v.get("match") is None else int(v["match"]),
             json.dumps(r, ensure_ascii=False)))
        for kind, targets in (("link", r.get("links", [])),
                              ("ref", nk.get("refs", [])),
                              ("criterion_for", nk.get("criterion_for", []))):
            for t in targets:
                con.execute("INSERT OR IGNORE INTO link VALUES (?,?,?)", (r["id"], t, kind))
        if fts:
            con.execute("INSERT INTO sutra_fts VALUES (?,?,?,?,?)",
                        (r["id"], norm_search(r["verse"]), norm_search(r["kaandigai"]),
                         norm_search(nk.get("text", "")), norm_search(r.get("viparam", ""))))
    con.commit()
    con.execute("VACUUM")
    con.close()
    print(f"Built {OUT.relative_to(ROOT)} with {len(rows)} sutras; FTS5={'on' if fts else 'off'}")


if __name__ == "__main__":
    main()

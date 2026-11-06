"""Validate all JSONL sutra records against schema + integrity checks.

Errors (exit 1): bad JSON, schema violations, duplicate ids, id/field
mismatch, unresolved links, verification mismatch on a non-AMBIGUOUS record.
Warnings (exit 0): verification mismatch already marked AMBIGUOUS,
sutra numbers missing from the expected range.
"""
import json, glob, sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
PREFIX = {"ezhuthu": "ezhu", "sol": "sol", "porul": "porul"}
EXPECTED = {"ezhuthu": 483, "sol": 463, "porul": 656}


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except json.JSONDecodeError as e:
                yield i, {"__json_error__": f"line {i}: {e}"}


def main(pattern="data/sutras/**/*.jsonl"):
    schema = json.loads((ROOT / "schema/sutra.schema.json").read_text("utf-8"))
    validator = Draft202012Validator(schema)
    files = sorted(glob.glob(str(ROOT / pattern), recursive=True))
    if not files:
        print("No JSONL files found under", pattern); sys.exit(1)

    seen_ids, all_records = {}, []
    errors, warnings = [], []
    for path in files:
        for line_no, rec in load_jsonl(path):
            tag = f"{Path(path).parent.name}/{Path(path).name}:{line_no}"
            if "__json_error__" in rec:
                errors.append(f"{tag} JSON: {rec['__json_error__']}")
                continue
            for err in validator.iter_errors(rec):
                errors.append(f"{tag} schema: {err.message} at {list(err.path)}")
            rid = rec.get("id")
            if rid in seen_ids:
                errors.append(f"{tag} duplicate id {rid} (also {seen_ids[rid]})")
            seen_ids[rid] = tag
            # id must agree with adhikaram + sutra
            a, n = rec.get("adhikaram"), rec.get("sutra")
            if a in PREFIX and rid != f"{PREFIX[a]}.{n}":
                errors.append(f"{tag} id {rid} ≠ adhikaram/sutra {a}/{n}")
            # file must agree with adhikaram + othu
            exp_file = f"{a}/othu-{rec.get('othu', 0):02d}.jsonl"
            if not str(path).endswith(exp_file):
                errors.append(f"{tag} {rid} belongs in {exp_file}")
            v = rec.get("verification", {})
            if v.get("stated") is not None and v.get("computed") is not None \
                    and v["stated"] != v["computed"]:
                msg = f"{rid} verification mismatch (stated {v['stated']} ≠ computed {v['computed']})"
                if rec.get("kuri") == "AMBIGUOUS":
                    warnings.append(msg + " — AMBIGUOUS")
                else:
                    errors.append(f"{tag} {msg}")
            all_records.append(rec)

    ids = set(seen_ids)
    for rec in all_records:
        nk = rec.get("nul_kurum", {})
        for l in rec.get("links", []) + nk.get("refs", []) + nk.get("criterion_for", []):
            if l not in ids:
                errors.append(f"{rec['id']} links unknown id: {l}")

    for a, total in EXPECTED.items():
        have = {r["sutra"] for r in all_records if r.get("adhikaram") == a}
        if not have:
            continue
        missing = [n for n in range(1, total + 1) if n not in have]
        if missing:
            warnings.append(f"{a}: {len(missing)} sutra(s) missing: "
                            + ", ".join(f"{PREFIX[a]}.{n}" for n in missing[:20]))

    print(f"Files: {len(files)}  Records: {len(all_records)}  Unique ids: {len(ids)}")
    for w in warnings:
        print(" ! warning:", w)
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors[:50]:
            print(" -", e)
        if len(errors) > 50:
            print(f" ... {len(errors)-50} more")
        sys.exit(1)
    print("OK — all records valid.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sutras/**/*.jsonl")

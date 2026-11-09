"""scripts/export_bundle.py — data_v2 (மூலம்) → build/bundle_v2.json (செயலிக்கு).

முன்பு இது பழைய v1 தரவிலிருந்து (data/sutras) build/bundle.json உருவாக்கியது; அதில் உரை
இல்லை, செயலியும் இப்போது அதைப் படிப்பதில்லை. மூலம் data_v2 ஒன்றே (PLAN.md), ஆகவே இது
build_v2.py-இன் அதே தொகுப்பு முறையைப் பயன்படுத்துகிறது — இரண்டு வடிவம் இருந்தால் மாறுகோள் எழும்
(பொருள். 468 "மாறுகோள் இன்றி").
python3 scripts/export_bundle.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_v2 import B, load, build_bundle  # noqa: E402


def main():
    B.mkdir(exist_ok=True)
    recs = load()
    out = build_bundle(recs)
    n_urai = sum(1 for r in recs if (r.get("urai") or {}).get("text", "").strip())
    print(f"Wrote {out.relative_to(ROOT)} ({len(recs)} சூத்திரம், உரை {n_urai}, {out.stat().st_size // 1024} KB)")
    if len(recs) != 1602:
        sys.exit(f"சூத்திர எண்ணிக்கை 1602 அல்ல: {len(recs)}")


if __name__ == "__main__":
    main()

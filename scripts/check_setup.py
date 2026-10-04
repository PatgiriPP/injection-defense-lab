"""Step 2 check: is everything wired? Run:  python scripts/check_setup.py"""

from __future__ import annotations

import os
import sys

from injlab import data, defenses, detector, literature, settings, target

ok = True
print(f"Results folder : {settings.RESULTS}")
print(f"Target model   : {target.model_id()}")

key_var = settings.PROVIDER_KEYS.get(settings.TARGET_PROVIDER)
if settings.TARGET_PROVIDER != "mock":
    if not os.environ.get(key_var or ""):
        print(f"[FAIL] {key_var} is not set"); ok = False
    else:
        try:
            msgs = defenses.build_messages((), data.build_document("e01", "A0_none"))
            out = target.complete(msgs)
            print(f"[ OK ] target model replied: {out[:100]!r}")
        except Exception as e:
            print(f"[FAIL] target model call: {e}"); ok = False

name = detector.detector_name()
flag_attack = detector.flags(data.build_document("e01", "A1_plain"))
flag_clean = detector.flags(data.build_document("e01", "A0_none"))
print(f"[ OK ] detector = {name}; flags plain attack: {flag_attack}; flags clean email: {flag_clean}")
if name.startswith("heuristic"):
    print("       (install the real detector with:  pip install -e '.[detector]')")

try:
    hits = literature.search("prompt injection defense LLM", 2)
    print(f"[ OK ] OpenAlex literature search: {hits[0]['title'][:80]!r}")
except Exception as e:
    print(f"[WARN] literature search failed: {e}")

print("\nAll good. Next: python scripts/run_grid.py" if ok else "\nFix the FAIL lines above first.")
sys.exit(0 if ok else 1)

"""Precompute D3 detector scores for every email x approved attack. Run in a normal terminal."""
import json
from injlab import data, detector, settings
cache, new = detector._disk_cache(), 0
for attack in data.approved_attacks():
    for e in data.EMAILS:
        doc = data.build_document(e["id"], attack)
        k = detector._key(doc)
        if k not in cache:
            cache[k] = round(detector.model_score(doc), 6); new += 1
detector.CACHE.write_text(json.dumps(cache))
print(f"Detector cache: {len(cache)} documents ({new} new). Model: {settings.DETECTOR_MODEL}")

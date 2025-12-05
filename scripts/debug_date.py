from fhirclient.models.fhirdatetime import FHIRDateTime
from datetime import datetime

formats = [
    datetime.utcnow().isoformat(),
    datetime.utcnow().replace(microsecond=0).isoformat(),
    datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "2025-12-05T12:00:00+00:00"
]

for f in formats:
    try:
        dt = FHIRDateTime(f)
        print(f"SUCCESS: {f} -> {dt.date}")
    except Exception as e:
        print(f"FAIL: {f} -> {e}")

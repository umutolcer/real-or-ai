"""
Makes a shareable copy of the raw export: ids become P01, P02, ...,
names and the database row id are dropped, everything else stays as is.

    python anonymize_responses.py responses_rows.csv data/responses_anonymized.csv
"""
import sys
from pathlib import Path
import pandas as pd

src = sys.argv[1] if len(sys.argv) > 1 else "responses_rows.csv"
dst = Path(sys.argv[2] if len(sys.argv) > 2 else "data/responses_anonymized.csv")

df = pd.read_csv(src)
first = df.groupby("participant_id").timestamp.min().sort_values()
mapping = {pid: f"P{i + 1:02d}" for i, pid in enumerate(first.index)}
df["participant_id"] = df.participant_id.map(mapping)
df = df.drop(columns=[c for c in ("participant_name", "id") if c in df.columns])
df = df.sort_values(["participant_id", "timestamp"])
dst.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(dst, index=False)
print(f"wrote {dst} ({len(df)} rows, {df.participant_id.nunique()} participants)")

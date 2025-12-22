#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from core.extract import extract_merged_experiment_table


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract a merged per-track table from web/userdata.")
    ap.add_argument("--userdata", required=True, help="Path to web/userdata")
    ap.add_argument("--framework", default=None, help="Optional path to web/data/framework.json")
    ap.add_argument("--dir_disc", default=None, help="Optional path to sinossi/out_sinossi_injected/")
    ap.add_argument("--out", required=True, help="Output CSV path")

    args = ap.parse_args()

    df = extract_merged_experiment_table(args.userdata, args.framework, args.dir_disc)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

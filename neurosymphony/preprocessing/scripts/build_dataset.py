#!/usr/bin/env python3
"""Build dataset*.csv from final.csv.

Usage: python -m scripts.build_dataset --in final.csv --mode {positive,all,raw,both}
  positive -> dataset_categoricalonly.csv
  all      -> final_aggr_allmovements_qc.csv
  raw      -> dataset.csv (no filtering; continuous-valence model's input)
Default mode is both (positive + all). See --help for gate-threshold flags.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CONDITION_MAPS = {
    "aggregated_condition_affective": {1: "Aff Coher", 2: "Aff Opp", 3: "Aff Coher", 4: "Aff Opp"},
    "aggregated_condition_injected": {1: "Ref", 2: "Ref", 3: "Inj", 4: "Inj"},
    "aggregated_condition_affective_only_true": {1: "Group A", 2: "Group B", 3: "Group C", 4: "Group C"},
    "aggregated_condition_affective_only_inj": {1: "Group C", 2: "Group C", 3: "Group A", 4: "Group B"},
}


def _track_condition(df: pd.DataFrame) -> pd.Series:
    col = "track_condition" if "track_condition" in df.columns else "cond_track"
    return df[col].astype(int)


def add_condition_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    track_condition = _track_condition(df)
    for col, mapping in CONDITION_MAPS.items():
        df[col] = track_condition.map(mapping)
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["description_coher_score"] = df[["track_q3_1", "track_q3_2"]].mean(axis=1, skipna=False)

    nr = len(df)
    order = np.argsort(df["goldsmi_gf_score"].to_numpy(), kind="stable")
    lo, hi = nr // 3, (2 * nr) // 3
    groups_gf = np.ones(nr, dtype=int)
    groups_gf[order[lo:hi]] = 2
    groups_gf[order[hi:]] = 3
    df["groups_gf"] = groups_gf

    slope = df["description_valence_trend_slope"]
    groups_vl_slope = np.ones(nr, dtype=int)
    groups_vl_slope[(slope.abs() < 0.5).to_numpy()] = 2
    groups_vl_slope[(slope > 0.5).to_numpy()] = 3
    df["groups_vl_slope"] = groups_vl_slope

    mean_valence = df["description_score_mvt_valence"]
    groups_vl_mean = np.ones(nr, dtype=int)
    groups_vl_mean[((mean_valence - 5).abs() < 2).to_numpy()] = 2
    groups_vl_mean[((mean_valence - 5) > 2).to_numpy()] = 3
    df["groups_vl_mean"] = groups_vl_mean

    return df


def add_track_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["track_id"] = df["expid"].astype(str) + "_" + df["track_number"].astype(int).astype(str)
    return df


def derive_gate_thresholds(df: pd.DataFrame, k: float = 1) -> tuple[float, float]:
    """coherent_min = mean - k*SD, opposite_max = mean + k*SD, over the
    movements' own reference-note valence."""
    movement_stats = df.groupby(["expid", "track_number"]).agg(
        ref_valence=("description_score_mvt_valence_reference", "first"),
        ref_opp_valence=("description_score_mvt_valence_reference_opp", "first"),
    )
    coherent_min = movement_stats["ref_valence"].mean() - k * movement_stats["ref_valence"].std()
    opposite_max = movement_stats["ref_opp_valence"].mean() + k * movement_stats["ref_opp_valence"].std()
    return float(coherent_min), float(opposite_max)


def movement_level_gate(df: pd.DataFrame, coherent_min: float, opposite_max: float) -> pd.DataFrame:
    """Keep only movements where the pooled Coherent trials read positive
    and the pooled Opposite trials read negative."""
    coher_mean = (
        df.loc[df["aggregated_condition_affective"] == "Aff Coher"]
        .groupby(["expid", "track_number"])["description_score_mvt_valence"].mean()
    )
    opp_mean = (
        df.loc[df["aggregated_condition_affective"] == "Aff Opp"]
        .groupby(["expid", "track_number"])["description_score_mvt_valence"].mean()
    )
    movement_stats = pd.DataFrame({"live_coher": coher_mean, "live_opp": opp_mean})

    ok_movements = movement_stats[
        (movement_stats["live_coher"] >= coherent_min) & (movement_stats["live_opp"] <= opposite_max)
    ].index

    excluded = movement_stats.index.difference(ok_movements)
    print(f"Step 1 (movement-level gate, live pooled Coherent/Opposite mean): {len(ok_movements)}/{len(movement_stats)} movements survive.")
    for expid, track_number in excluded:
        row = movement_stats.loc[(expid, track_number)]
        print(
            f"  excluded {expid}/track{track_number}: "
            f"live_coher={row['live_coher']:.2f}, live_opp={row['live_opp']:.2f}"
        )

    keep_mask = df.set_index(["expid", "track_number"]).index.isin(ok_movements)
    return df.loc[keep_mask].reset_index(drop=True)


def static_reference_row_trim(df: pd.DataFrame, coherent_min: float, opposite_max: float) -> pd.DataFrame:
    """Drop rows whose own Reference note falls on the wrong side of
    coherent_min/opposite_max."""
    before = len(df)
    drop_cond1 = (df["track_condition"] == 1) & (df["description_score_mvt_valence"] < coherent_min)
    drop_cond2 = (df["track_condition"] == 2) & (df["description_score_mvt_valence"] > opposite_max)
    out = df.loc[~(drop_cond1 | drop_cond2)].reset_index(drop=True)
    print(f"Step 2 (static per-row Reference check): removed {before - len(out)} rows.")
    return out


def pooled_consistency_trim(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Within each movement, drop trials that pull their group's mean
    toward the other group."""
    df = df.copy()
    removed_total = 0
    for expid in sorted(df["expid"].unique()):
        for track_n in range(1, 5):
            mvt = (df["expid"] == expid) & (df["track_number"] == track_n)
            if mvt.sum() == 0:
                continue
            coher = mvt & (df["aggregated_condition_affective"] == "Aff Coher")
            opp = mvt & (df["aggregated_condition_affective"] == "Aff Opp")
            if coher.sum() == 0 or opp.sum() == 0:
                continue

            mean_coher = df.loc[coher, "description_score_mvt_valence"].mean()
            mean_opp = df.loc[opp, "description_score_mvt_valence"].mean()
            if mean_coher > mean_opp:
                bad_coher = coher & (df["description_score_mvt_valence"] < mean_coher - threshold)
                bad_opp = opp & (df["description_score_mvt_valence"] > mean_opp + threshold)
            else:
                bad_coher = coher & (df["description_score_mvt_valence"] > mean_coher + threshold)
                bad_opp = opp & (df["description_score_mvt_valence"] < mean_opp - threshold)

            n_removed = int((bad_coher | bad_opp).sum())
            if n_removed:
                print(f"  removed {n_removed} rows from {expid} track{track_n}")
                removed_total += n_removed
            df = df.loc[~(mvt & (bad_coher | bad_opp))]

    print(f"Step 3 (pooled per-movement consistency trim): removed {removed_total} rows total.")
    return df.reset_index(drop=True)


def build_dataset(
    df: pd.DataFrame,
    apply_movement_gate: bool,
    apply_qc: bool = True,
    gate_coherent_min: float | None = None,
    gate_opposite_max: float | None = None,
    gate_k: float = 1,
    row_coherent_min: float = 7,
    row_opposite_max: float = 4,
    outlier_threshold: float = 2,
) -> pd.DataFrame:
    """apply_movement_gate=True builds the 'positive' dataset,
    False builds the 'all' dataset."""
    df = add_condition_columns(df)

    if apply_movement_gate:
        if gate_coherent_min is None or gate_opposite_max is None:
            derived_min, derived_max = derive_gate_thresholds(df, k=gate_k)
            if gate_coherent_min is None:
                gate_coherent_min = derived_min
            if gate_opposite_max is None:
                gate_opposite_max = derived_max
            print(
                f"Step 1 gate thresholds derived from data (k={gate_k}): "
                f"coherent_min={gate_coherent_min:.3f}, opposite_max={gate_opposite_max:.3f}"
            )
        df = movement_level_gate(df, gate_coherent_min, gate_opposite_max)
    else:
        n_movements = df.groupby(["expid", "track_number"]).ngroups
        print(f"Step 1 (movement-level gate): skipped -- all {n_movements} movements retained.")

    if apply_qc:
        df = static_reference_row_trim(df, row_coherent_min, row_opposite_max)
        df = pooled_consistency_trim(df, outlier_threshold)
    else:
        print("Steps 2-3 (row QC): skipped -- every row kept as-is (raw mode).")

    df = add_derived_columns(df)
    df = add_track_id(df)
    return df


def _run_and_write(df_in: pd.DataFrame, apply_movement_gate: bool, out_path: str, apply_qc: bool = True, **kwargs) -> None:
    out = build_dataset(df_in, apply_movement_gate, apply_qc=apply_qc, **kwargs)
    print(f"\nFinal: {len(out):,} rows across {out.groupby(['expid','track_number']).ngroups} movements "
          f"(input was {len(df_in):,} rows across {df_in.groupby(['expid','track_number']).ngroups} movements).")
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", default="final.csv")
    ap.add_argument(
        "--mode", choices=["positive", "all", "raw", "both"], default="both",
        help="positive: movement gate + row QC. all: row QC only. raw: no "
             "filtering (continuous-valence model). both (default): positive + all.",
    )
    ap.add_argument("--out-positive", default="dataset_categoricalonly.csv")
    ap.add_argument("--out-all", default="final_aggr_allmovements_qc.csv")
    ap.add_argument("--out-raw", default="dataset.csv")
    ap.add_argument(
        "--gate-coherent-min", type=float, default=None,
        help="Step 1 lower bound. Default: derived as mean - gate-k*SD of "
             "the movements' reference-note valence.",
    )
    ap.add_argument(
        "--gate-opposite-max", type=float, default=None,
        help="Step 1 upper bound. Default: derived, mean + gate-k*SD.",
    )
    ap.add_argument(
        "--gate-k", type=float, default=1,
        help="SD multiplier for deriving the gate bounds. Default 1.0.",
    )
    ap.add_argument(
        "--row-coherent-min", type=float, default=7,
        help="Step 2 (live per-row Reference check) lower bound.",
    )
    ap.add_argument(
        "--row-opposite-max", type=float, default=4,
        help="Step 2 upper bound.",
    )
    ap.add_argument("--outlier-threshold", type=float, default=2)
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    kwargs = dict(
        gate_coherent_min=args.gate_coherent_min,
        gate_opposite_max=args.gate_opposite_max,
        gate_k=args.gate_k,
        row_coherent_min=args.row_coherent_min,
        row_opposite_max=args.row_opposite_max,
        outlier_threshold=args.outlier_threshold,
    )

    if args.mode in ("positive", "both"):
        print("=" * 70)
        print("MODE: positive (movement-level gate + row QC)")
        print("=" * 70)
        _run_and_write(df, True, args.out_positive, **kwargs)

    if args.mode in ("all", "both"):
        print("=" * 70)
        print("MODE: all (row QC only, no movement-level gate)")
        print("=" * 70)
        _run_and_write(df, False, args.out_all, **kwargs)

    if args.mode == "raw":
        print("=" * 70)
        print("MODE: raw (no gate, no row QC -- passthrough)")
        print("=" * 70)
        _run_and_write(df, False, args.out_raw, apply_qc=False, **kwargs)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Regressions of feedback valence against program-note valence and
against perceived emotion, from participants' textual feedback.

Run after preprocessing/ has produced final.csv, feedbacks_metrics.csv
(process_feedback_openai) and dataset_categoricalonly.csv (build_dataset).

Set REPO below to that preprocessing output directory (currently
hardcoded to a different repo's path), then run
`python feedback_valence_check.py`. Writes
analysis/figures/feedback_valence_regressions_eligible_retained.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent.parent.parent

FIG_DIR = REPO / "analysis" / "figures"

AFF_COND = {1: "Aff Coher", 2: "Aff Opp", 3: "Aff Coher", 4: "Aff Opp"}

Q_LABELS = {
    "track_q2_1": "Perceived Positive",
    "track_q2_2": "Perceived Negative",
}


def load_eligible_retained_notes():
    fdf = pd.read_csv(REPO / "feedbacks_metrics.csv")[
        ["userid", "expid", "track_number", "rating_feedback_valence"]
    ]
    main = pd.read_csv(REPO / "final.csv")[
        [
            "userid", "expid", "track_number", "track_condition",
            "description_score_mvt_valence",
            "track_q2_1", "track_q2_2", "track_q2_3", "track_q2_4",
        ]
    ].drop_duplicates(subset=["userid", "expid", "track_number"])

    df = fdf.merge(main, on=["userid", "expid", "track_number"], how="inner")
    df["aff_cond"] = df["track_condition"].map(AFF_COND)

    truepos = pd.read_csv(REPO / "dataset_categoricalonly.csv")[["expid", "track_number"]].drop_duplicates()
    truepos_keys = set(map(tuple, truepos.values))
    df["is_truepos_mvt"] = [
        (r.expid, r.track_number) in truepos_keys for r in df.itertuples()
    ]
    return df


def regress(name, sub, dv, iv):
    sub = sub.dropna(subset=[dv, iv])
    n = len(sub)
    df_resid = n - 2
    if df_resid < 1:
        print(f"{name:55s} n={n:3d}  -- too few points, skipped")
        return None
    res = linregress(sub[iv], sub[dv])
    r2 = res.rvalue ** 2
    t = res.slope / res.stderr
    row = {
        "name": name, "n": n, "df": df_resid,
        "slope": res.slope, "se": res.stderr, "t": t,
        "p": res.pvalue, "r2": r2,
    }
    print(
        f"{name:55s} n={n:3d}  b={res.slope:+.4f}  se={res.stderr:.4f}  "
        f"t({df_resid})={t:+.3f}  p={res.pvalue:.4f}  R2={r2:.4f}"
    )
    return row


def main():
    df = load_eligible_retained_notes()
    assert len(df) == 143, f"expected 143 eligible retained-participant notes, got {len(df)}"

    predictor = "description_score_mvt_valence"

    rows = []
    print(f"=== Feedback valence ~ program-note valence ({predictor}), by subset ===")
    rows.append(regress("All samples", df,
                         "rating_feedback_valence", predictor))
    rows.append(regress("Coherent-only", df[df.aff_cond == "Aff Coher"],
                         "rating_feedback_valence", predictor))
    rows.append(regress("Opposite-only", df[df.aff_cond == "Aff Opp"],
                         "rating_feedback_valence", predictor))

    truepos_df = df[df.is_truepos_mvt]
    rows.append(regress("Truepos movements (H1 categorical gate)",
                         truepos_df, "rating_feedback_valence", predictor))

    print("\n=== Feedback valence ~ perceived (felt) emotion, by condition ===")
    for cond_label, cond_val in [("Coherent Valence", "Aff Coher"), ("Opposite Valence", "Aff Opp")]:
        sub_cond = df[df.aff_cond == cond_val]
        for col, label in Q_LABELS.items():
            rows.append(regress(f"{cond_label} / {label}", sub_cond,
                                 "rating_feedback_valence", col))

    out = pd.DataFrame([r for r in rows if r is not None])
    out_path = FIG_DIR / "feedback_valence_regressions_eligible_retained.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}  (n_notes={len(df)})")


if __name__ == "__main__":
    main()

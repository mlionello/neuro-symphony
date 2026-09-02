"""
H1 continuous button-press check (Joy/Happiness, Sadness) on the
truepos-gated exp1/exp2 movements: paired sign/Wilcoxon test (Part A)
plus directional test (Part B).

Run after preprocessing/ has produced dataset_categoricalonly.csv
(build_dataset --mode positive). No CLI args; paths self-locate from the
script's own directory. Writes four files to analysis/figures/:
h1_button_press_movement_summary_exp1exp2_truepos.csv,
h1_button_press_permutation_validity_exp1exp2_truepos.csv,
h1_button_press_slopeplot_exp1exp2_truepos.png (Part A), and
h1_button_press_clusterperm_exp1exp2_truepos.csv (Part B).
"""
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, binomtest, ttest_ind
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent.parent

DATA_DIR = REPO / "preprocessing" if (REPO / "preprocessing" / "dataset_categoricalonly.csv").exists() else REPO
sys.path.insert(0, str(DATA_DIR))
os.chdir(DATA_DIR) 
from core.metrics import load_pressing_csv

FIG_DIR = REPO / "analysis" / "figures"

CH_IDX = {"Joy/Happiness": 1, "Sadness": 2}
LOW_N_THRESHOLD = 3
COND_COLORS = {"Aff Coher": "#2b6cb0", "Aff Opp": "#dd6b20"}
COND_LABELS = {"Aff Coher": "Coherent", "Aff Opp": "Opposite"}
CHANNEL_COLORS = {"Joy/Happiness": "#2b6cb0", "Sadness": "#c53030"}
SYMPH_SHORT = {"exp1": "Brahms 3", "exp2": "Dvořák 8"}
RESPONSES = {"Joy/Happiness": ("Joyful", "greater"), "Sadness": ("Sad", "less")}


# =====================================================================
# Part A -- whole-movement mean per participant, paired across movements
# =====================================================================
def participant_scalar(pressing_csv_path, ch_idx):
    """Plain mean of the raw button state across the whole trace -- see
    module docstring for why this replaced an earlier binned version."""
    if not isinstance(pressing_csv_path, str) or not Path(pressing_csv_path).exists():
        return None
    m = load_pressing_csv(pressing_csv_path)
    m = m[1:]
    if m.shape[0] < 5:
        return None
    state = m[:, 1 + ch_idx]
    return float(state.mean())


df = pd.read_csv(DATA_DIR / "dataset_categoricalonly.csv")
df = df.drop_duplicates(["userid", "expid", "track_number"])
df = df[df["expid"].isin(["exp1", "exp2"])] 
print(f"loaded {len(df)} rows (exp1/exp2, truepos-gated); condition counts:")
print(df["aggregated_condition_affective"].value_counts())

movements = df[["expid", "track_number"]].drop_duplicates().sort_values(["expid", "track_number"])
print(f"\n{len(movements)} movements")


def build_res():
    rows = []
    for _, mv in movements.iterrows():
        expid, track_number = mv["expid"], mv["track_number"]
        mrows = df[(df["expid"] == expid) & (df["track_number"] == track_number)]
        for channel, ch_idx in CH_IDX.items():
            cond_vals = {}
            for cond in ["Aff Coher", "Aff Opp"]:
                crows = mrows[mrows["aggregated_condition_affective"] == cond]
                vals = [participant_scalar(p, ch_idx) for p in crows["pressing_csv"]]
                vals = [v for v in vals if v is not None]
                cond_vals[cond] = vals
            n_c, n_o = len(cond_vals["Aff Coher"]), len(cond_vals["Aff Opp"])
            if n_c == 0 or n_o == 0:
                continue
            coherent_mean = float(np.mean(cond_vals["Aff Coher"]))
            opposite_mean = float(np.mean(cond_vals["Aff Opp"]))
            rows.append({
                "expid": expid, "track_number": track_number, "channel": channel,
                "coherent_mean": coherent_mean, "opposite_mean": opposite_mean,
                "diff": coherent_mean - opposite_mean,
                "n_coherent": n_c, "n_opposite": n_o,
                "low_n": min(n_c, n_o) < LOW_N_THRESHOLD,
            })
    return pd.DataFrame(rows)


res = build_res()
out_csv = FIG_DIR / "h1_button_press_movement_summary_exp1exp2_truepos.csv"
res.to_csv(out_csv, index=False)
print(f"\nwrote {out_csv} ({len(res)} rows)")


def run_tests(sub, channel, direction, verbose=True):
    x = sub["coherent_mean"].values
    y = sub["opposite_mean"].values
    k = len(x)
    if direction == "greater":
        n_favorable = int(np.sum(x > y))
        sign_p = binomtest(n_favorable, k, p=0.5, alternative="greater").pvalue
    else:
        n_favorable = int(np.sum(y > x))
        sign_p = binomtest(n_favorable, k, p=0.5, alternative="greater").pvalue
    if not np.allclose(x, y):
        w_stat, w_p = wilcoxon(x, y, alternative=direction)
    else:
        w_stat, w_p = np.nan, np.nan
    if verbose:
        print(f"  {channel} [{direction}], k={k}: sign test {n_favorable}/{k} favorable, p={sign_p:.4f}; "
              f"Wilcoxon W={w_stat}, p={w_p:.4f}" if not np.isnan(w_p) else
              f"  {channel} [{direction}], k={k}: sign test {n_favorable}/{k} favorable, p={sign_p:.4f}; Wilcoxon: n/a")
    return n_favorable, k, sign_p, w_stat, w_p


results_summary = {}
for channel, direction in [("Joy/Happiness", "greater"), ("Sadness", "less")]:
    print(f"\n=== {channel} (H: Coherent {'>' if direction=='greater' else '<'} Opposite) ===")
    sub_all = res[res["channel"] == channel]
    sub_hi = sub_all[~sub_all["low_n"]]
    print(" all movements:")
    r_all = run_tests(sub_all, channel, direction)
    print(" excluding low_n:")
    r_hi = run_tests(sub_hi, channel, direction)
    results_summary[channel] = {"all": r_all, "hi": r_hi}

# --- permutation-based validity check
N_PERM = 10000
_rng = np.random.default_rng(12345)

precomp = {}
for _, mv in movements.iterrows():
    expid, tn = mv["expid"], mv["track_number"]
    mrows = df[(df["expid"] == expid) & (df["track_number"] == tn)]
    for channel, ch_idx in CH_IDX.items():
        scalars, is_coh = [], []
        for _, r in mrows.iterrows():
            v = participant_scalar(r["pressing_csv"], ch_idx)
            if v is not None:
                scalars.append(v)
                is_coh.append(r["aggregated_condition_affective"] == "Aff Coher")
        precomp[(expid, tn, channel)] = (np.array(scalars), int(sum(is_coh)))


def real_movement_diffs(channel, ch_idx):
    xs, ys = [], []
    for _, mv in movements.iterrows():
        expid, tn = mv["expid"], mv["track_number"]
        mrows = df[(df["expid"] == expid) & (df["track_number"] == tn)]
        coh_vals, opp_vals = [], []
        for _, r in mrows.iterrows():
            v = participant_scalar(r["pressing_csv"], ch_idx)
            if v is None:
                continue
            (coh_vals if r["aggregated_condition_affective"] == "Aff Coher" else opp_vals).append(v)
        if not coh_vals or not opp_vals:
            continue
        xs.append(np.mean(coh_vals)); ys.append(np.mean(opp_vals))
    return np.array(xs), np.array(ys)


def signed_rank_favorable(diff, favorable_sign):
    ranks = pd.Series(np.abs(diff)).rank().values
    return ranks[np.sign(diff) == favorable_sign].sum()


fpr_rows = []
for channel, ch_idx in CH_IDX.items():
    direction = RESPONSES[channel][1]
    favorable_sign = 1 if direction == "greater" else -1

    x, y = real_movement_diffs(channel, ch_idx)
    real_diff = x - y
    real_w_plus = signed_rank_favorable(real_diff, favorable_sign)
    real_n_fav = int(np.sum(np.sign(real_diff) == favorable_sign))

    perm_w_plus, perm_n_fav, n_sig_sign, n_sig_wilcoxon = [], [], 0, 0
    for _ in range(N_PERM):
        xs, ys = [], []
        for _, mv in movements.iterrows():
            expid, tn = mv["expid"], mv["track_number"]
            scalars, n_c = precomp[(expid, tn, channel)]
            if n_c == 0 or n_c == len(scalars):
                continue
            perm = _rng.permutation(len(scalars))
            xs.append(scalars[perm[:n_c]].mean()); ys.append(scalars[perm[n_c:]].mean())
        diff = np.array(xs) - np.array(ys)
        n_fav = int(np.sum(np.sign(diff) == favorable_sign))
        w_plus = signed_rank_favorable(diff, favorable_sign)
        perm_n_fav.append(n_fav); perm_w_plus.append(w_plus)
        k = len(diff)
        sign_p = binomtest(n_fav, k, p=0.5, alternative="greater").pvalue
        if sign_p < 0.05:
            n_sig_sign += 1
        if not np.allclose(np.array(xs), np.array(ys)):
            _, w_p = wilcoxon(xs, ys, alternative=direction)
            if w_p < 0.05:
                n_sig_wilcoxon += 1

    perm_n_fav, perm_w_plus = np.array(perm_n_fav), np.array(perm_w_plus)
    p_perm_sign = (np.sum(perm_n_fav >= real_n_fav) + 1) / (N_PERM + 1)
    p_perm_wilcoxon = (np.sum(perm_w_plus >= real_w_plus) + 1) / (N_PERM + 1)
    fpr_rows.append({
        "channel": channel, "real_n_favorable": real_n_fav, "real_w_plus": real_w_plus,
        "permutation_p_sign": p_perm_sign, "permutation_p_wilcoxon": p_perm_wilcoxon,
        "fpr_sign_at_.05": n_sig_sign / N_PERM, "fpr_wilcoxon_at_.05": n_sig_wilcoxon / N_PERM,
    })

fpr_df = pd.DataFrame(fpr_rows)
print(f"\n=== permutation validity check ({N_PERM} permutations, label-reshuffled within movement) ===")
print(fpr_df.to_string(index=False))
out_csv_fpr = FIG_DIR / "h1_button_press_permutation_validity_exp1exp2_truepos.csv"
fpr_df.to_csv(out_csv_fpr, index=False)
print(f"\nwrote {out_csv_fpr}")

# --- slope plot:
# across-movement average line ---
fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
for ax, channel in zip(axes, ["Joy/Happiness", "Sadness"]):
    sub = res[res["channel"] == channel]
    for _, r in sub.iterrows():
        alpha = 0.35 if r["low_n"] else 0.9
        color = COND_COLORS["Aff Coher"] if r["diff"] > 0 else COND_COLORS["Aff Opp"]
        ax.plot([0, 1], [r["coherent_mean"], r["opposite_mean"]], color=color, alpha=alpha,
                 linewidth=1.5, marker="o", markersize=3)

    placed_y = None
    min_gap = 0.028
    for _, r in sub.sort_values("opposite_mean").iterrows():
        alpha = 0.35 if r["low_n"] else 0.9
        color = COND_COLORS["Aff Coher"] if r["diff"] > 0 else COND_COLORS["Aff Opp"]
        y = r["opposite_mean"] if placed_y is None else max(r["opposite_mean"], placed_y + min_gap)
        placed_y = y
        label = f"{SYMPH_SHORT[r['expid']]} mvt {r['track_number']}"
        ax.text(1.04, y, label, color=color, alpha=alpha, fontsize=7, va="center")

    avg_coherent = sub["coherent_mean"].mean()
    avg_opposite = sub["opposite_mean"].mean()
    ax.plot([0, 1], [avg_coherent, avg_opposite], color="black", alpha=1.0,
             linewidth=3.5, marker="o", markersize=8, label="movement average")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Coherent", "Opposite"])
    ax.set_xlim(-0.3, 1.9)
    ax.set_ylim(0, 0.6)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.set_title(channel, fontsize=11)
axes[0].set_ylabel("Whole-movement mean proportion pressed")
plt.tight_layout()
out_png = FIG_DIR / "h1_button_press_slopeplot_exp1exp2_truepos.png"
plt.savefig(out_png, dpi=180)
print(f"\nwrote {out_png}")


# =====================================================================
# Part B -- directional test's
# =====================================================================
def load_group_traces(pressing_csvs, ch_idx):
    traces = []
    for p in pressing_csvs:
        if not isinstance(p, str) or not Path(p).exists():
            continue
        m = load_pressing_csv(p)
        m = m[1:]
        traces.append(m[:, 1 + ch_idx])
    return traces


def directional_test_row(expid, tracknumber, channel, ch_idx):
    resp_label, tail = RESPONSES[channel]
    mrows = df[(df["expid"] == expid) & (df["track_number"] == tracknumber)]
    opp_traces = load_group_traces(mrows[mrows["aggregated_condition_affective"] == "Aff Opp"]["pressing_csv"], ch_idx)
    coh_traces = load_group_traces(mrows[mrows["aggregated_condition_affective"] == "Aff Coher"]["pressing_csv"], ch_idx)
    M_opp, M_coher = len(opp_traces), len(coh_traces)
    if M_opp < 2 or M_coher < 2:
        return {"expid": expid, "movement": tracknumber, "response": resp_label,
                "n_sig_timepoints": 0, "M_coher": M_coher, "M_opp": M_opp,
                "mean_coher": np.nan, "mean_opp": np.nan, "mean_diff_coher_minus_opp": np.nan,
                "tstat_welch": np.nan, "p_one_sided": np.nan, "hedges_g": np.nan,
                "meets_direction": False, "prop_timepoints_aligned": np.nan}

    common_len = min(min(len(t) for t in opp_traces), min(len(t) for t in coh_traces))
    X_opp = np.stack([t[:common_len] for t in opp_traces], axis=1)
    X_coher = np.stack([t[:common_len] for t in coh_traces], axis=1) 

    valid = ~((np.var(X_opp, axis=1, ddof=1) == 0) | (np.var(X_coher, axis=1, ddof=1) == 0))

    _, p_dir = ttest_ind(X_opp[valid], X_coher[valid], axis=1, equal_var=False)
    sig_param_unc = np.zeros(X_opp.shape[0], dtype=bool)
    sig_param_unc[valid] = p_dir < 0.05
    mask = sig_param_unc

    avg_opp = np.nanmean(X_opp, axis=1)
    avg_coher = np.nanmean(X_coher, axis=1)

    if not mask.any():
        return {"expid": expid, "movement": tracknumber, "response": resp_label,
                "n_sig_timepoints": 0, "M_coher": M_coher, "M_opp": M_opp,
                "mean_coher": np.nan, "mean_opp": np.nan, "mean_diff_coher_minus_opp": np.nan,
                "tstat_welch": np.nan, "p_one_sided": np.nan, "hedges_g": np.nan,
                "meets_direction": False, "prop_timepoints_aligned": np.nan}

    subj_opp = np.nanmean(X_opp[mask, :], axis=0)
    subj_coh = np.nanmean(X_coher[mask, :], axis=0)

    tstat, p_one_sided = ttest_ind(subj_coh, subj_opp, equal_var=False, alternative=tail)

    m_coh, m_opp = np.mean(subj_coh), np.mean(subj_opp)
    diff_mean = m_coh - m_opp
    n1, n2 = len(subj_coh), len(subj_opp)
    s1, s2 = np.std(subj_coh, ddof=1), np.std(subj_opp, ddof=1)
    d = (m_coh - m_opp) / np.sqrt((s1 ** 2 + s2 ** 2) / 2)
    J = 1 - 3 / (4 * (n1 + n2) - 9)
    g = d * J

    expect_sign = 1 if resp_label == "Joyful" else -1
    meets_direction = bool(np.sign(diff_mean) == expect_sign)

    avg_diff_trace = avg_coher - avg_opp
    if expect_sign == 1:
        aligned = avg_diff_trace[mask] > 0
    else:
        aligned = avg_diff_trace[mask] < 0
    prop_aligned = float(np.mean(aligned))

    return {"expid": expid, "movement": tracknumber, "response": resp_label,
            "n_sig_timepoints": int(mask.sum()), "M_coher": M_coher, "M_opp": M_opp,
            "mean_coher": m_coh, "mean_opp": m_opp, "mean_diff_coher_minus_opp": diff_mean,
            "tstat_welch": tstat, "p_one_sided": p_one_sided, "hedges_g": g,
            "meets_direction": meets_direction, "prop_timepoints_aligned": prop_aligned}


python_rows = []
for _, mv in movements.iterrows():
    for channel, ch_idx in CH_IDX.items():
        r = directional_test_row(mv["expid"], mv["track_number"], channel, ch_idx)
        if r is not None:
            python_rows.append(r)

directional_test_df = pd.DataFrame(python_rows).sort_values(["expid", "movement", "response"]).reset_index(drop=True)
print("\n=== Part B: directional test, on dataset_categoricalonly.csv data ===")
print(directional_test_df.to_string(index=False))

out_csv_b = FIG_DIR / "h1_button_press_clusterperm_exp1exp2_truepos.csv"
directional_test_df.to_csv(out_csv_b, index=False)
print(f"\nwrote {out_csv_b}")

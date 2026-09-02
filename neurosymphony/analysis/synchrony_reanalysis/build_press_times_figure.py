#!/usr/bin/env python3
"""Plot per-participant Joy/Happiness button-press states over the first
two minutes of a movement (default: exp1 track 1, Brahms No. 3, mvt I),
split by Affective Coherence condition. Writes
analysis/figures/press_times_example.png.

--expid/--mvt pick a different movement. --full renders the whole
movement instead (press_times_example_full.png, 30 s bins; override with
--win).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent.parent
DATA_DIR = REPO / "preprocessing" if (REPO / "preprocessing" / "dataset.csv").exists() else REPO
sys.path.insert(0, str(DATA_DIR))
os.chdir(DATA_DIR)
from core.metrics import load_pressing_csv

OUT_DIR = REPO / "analysis" / "figures" / "press_times_by_movement"

BUTTON_LABELS = ["Power/Energy", "Joy/Happiness", "Sadness", "Wonder/Surprise", "Tension", "Calm/Tranquillity"]
CHANNEL = "Joy/Happiness"
CHANNEL_SLUG = {"Joy/Happiness": "joy", "Sadness": "sadness"}

COND_COLORS = {"Aff Coher": "#2b6cb0", "Aff Opp": "#dd6b20"}
COND_LABELS = {"Aff Coher": "Coherent", "Aff Opp": "Opposite"}

ROMAN_MVT = {1: "I", 2: "II", 3: "III", 4: "IV"}


def piece_label(expid, track_number):
    """e.g. exp1, track 1 -> 'Brahms Symphony No. 3, movement I' (from framework.json)."""
    framework = json.loads((REPO / "web" / "data" / "framework.json").read_text())
    title = framework[expid]["title"]
    m = re.match(r"([\w-]+), (\d+)\w* symphony", title)
    composer, num = m.group(1), m.group(2)
    mvt_label = ROMAN_MVT.get(track_number, str(track_number))
    return f"{composer} Symphony No. {num}, movement {mvt_label}"


def render_figure(expid, track_number, channel, full, bin_width, out_path):
    ch_idx = BUTTON_LABELS.index(channel)

    df = pd.read_csv(DATA_DIR / "dataset.csv")
    assert df["userid"].nunique() == 36, (
        f"expected dataset.csv to contain exactly the 36 retained participants, "
        f"found {df['userid'].nunique()}; check the data source before regenerating this figure"
    )
    sub = df[(df["expid"] == expid) & (df["track_number"] == track_number) & df["pressing_csv"].notna()]
    sub = sub.drop_duplicates("userid")
    cond_by_user = dict(zip(sub["userid"], sub["aggregated_condition_affective"]))

    raw = {}
    max_t = 0.0
    for _, row in sub.iterrows():
        m = load_pressing_csv(row["pressing_csv"])
        m = m[1:]
        t_sec = m[:, 0] / 1000.0
        state = m[:, 1 + ch_idx]
        raw[row["userid"]] = (t_sec, state)
        max_t = max(max_t, t_sec.max())

    WINDOW_S = int(np.ceil(max_t)) if full else 180

    records = []
    for userid, (t_sec, state) in raw.items():
        mask = t_sec <= WINDOW_S
        for t, s in zip(t_sec[mask], state[mask]):
            records.append((userid, t, s))

    long_df = pd.DataFrame(records, columns=["userid", "t", "state"])
    userids = sorted(long_df["userid"].unique(), key=lambda u: (cond_by_user[u], u))
    n = len(userids)
    n_coher = sum(cond_by_user[u] == "Aff Coher" for u in userids)
    print(f"n participants: {n} (Coherent={n_coher}, Opposite={n - n_coher})")

    bins = np.arange(0, WINDOW_S + 1, 1)

    def per_second_proportion(user_subset):
        vals_per_bin = []
        for b in bins:
            vals = []
            for u in user_subset:
                d = long_df[long_df["userid"] == u]
                d = d[d["t"] <= b]
                if len(d):
                    vals.append(d["state"].iloc[-1])
            vals_per_bin.append(np.mean(vals) if vals else np.nan)
        return np.array(vals_per_bin)

    def coarse_bin(prop_raw, bin_width=bin_width):
        edges = np.arange(0, WINDOW_S + bin_width, bin_width)
        means, sds, centers = [], [], []
        for i in range(len(edges) - 1):
            lo, hi = edges[i], edges[i + 1]
            m = (bins >= lo) & (bins < hi)
            means.append(np.nanmean(prop_raw[m]))
            sds.append(np.nanstd(prop_raw[m]))
            centers.append((lo + hi) / 2)
        return np.array(centers), np.array(means), np.array(sds)

    fig_width = 10 if full else 7
    fig, axes = plt.subplots(2, 1, figsize=(fig_width, 5.4), sharex=True,
                              gridspec_kw={"height_ratios": [3, 1.4]})

    ax = axes[0]
    for i, u in enumerate(userids):
        d = long_df[long_df["userid"] == u].sort_values("t")
        t = d["t"].values
        s = d["state"].values
        on = s == 1
        color = COND_COLORS[cond_by_user[u]]
        if on.any():
            change = np.diff(np.concatenate([[0], on.astype(int), [0]]))
            starts = np.where(change == 1)[0]
            ends = np.where(change == -1)[0]
            for st, en in zip(starts, ends):
                t0 = t[st]
                t1 = t[en] if en < len(t) else WINDOW_S
                ax.plot([t0, t1], [i, i], color=color, linewidth=2, solid_capstyle="butt")
    ax.axhline(n_coher - 0.5, color="black", linewidth=0.6, linestyle=":")
    ax.set_ylim(-1, n)
    ax.set_ylabel(f"Participant (n={n})")
    ax.set_yticks([])
    span_label = f"full {WINDOW_S // 60}:{WINDOW_S % 60:02d} min" if full else f"first {WINDOW_S // 60} min"
    ax.set_title(f"'{channel}' button state -- {piece_label(expid, track_number)} ({span_label})", fontsize=9)
    handles = [plt.Line2D([0], [0], color=COND_COLORS[c], lw=2, label=COND_LABELS[c]) for c in COND_COLORS]
    ax.legend(handles=handles, fontsize=7, loc="upper right", frameon=False)

    ax2 = axes[1]
    for cond in ["Aff Coher", "Aff Opp"]:
        users_c = [u for u in userids if cond_by_user[u] == cond]
        prop_raw_c = per_second_proportion(users_c)
        centers, means, sds = coarse_bin(prop_raw_c)
        color = COND_COLORS[cond]
        ax2.fill_between(centers, means - sds, means + sds, color=color, alpha=0.15, linewidth=0)
        ax2.plot(centers, means, color=color, linewidth=1,
                  label=f"{COND_LABELS[cond]} (n={len(users_c)})")
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Proportion 'on'")
    ax2.legend(fontsize=7, loc="upper right", frameon=False, title=f"{bin_width} s bin average ± SD", title_fontsize=6)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print("wrote", out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--win", default=None, type=int,
                         help="coarse bin width in seconds for the summary panel "
                              "(default: 10, or 30 with --full)")
    parser.add_argument("--expid", default=0, type=int, help="experiment number (default: 1)")
    parser.add_argument("--mvt", default=0, type=int, help="track/movement number (default: 1)")
    parser.add_argument("--full", action="store_true",
                         help="render the whole movement instead of just the first 2 minutes")
    parser.add_argument("--all", action="store_true",
                         help="ignore --mvt/--full/--win: render the full-length trajectory, "
                              "10 s bins, for Joy/Happiness and Sadness, for every movement of --expid "
                              "(press_times_<expid>_mvt<N>_<joy|sadness>_full.png)")
    parser.add_argument("--all-symphonies", action="store_true",
                         help="with --all, iterate over every symphony (exp1..expN) instead of just --expid")
    args = parser.parse_args()
    expid = "exp" + str(args.expid) if args.expid > 0 else "exp1"

    if args.all:
        OUT_DIR.mkdir(exist_ok=True)
        framework = json.loads((REPO / "web" / "data" / "framework.json").read_text())
        expids = [f"exp{i}" for i in range(1, framework["nb"]["experiments"] + 1)] if args.all_symphonies else [expid]
        for e in expids:
            number_mvt = framework[e]["number_mvt"]
            for mvt in range(1, number_mvt + 1):
                for channel in ["Joy/Happiness", "Sadness"]:
                    out = OUT_DIR / f"press_times_{e}_mvt{mvt}_{CHANNEL_SLUG[channel]}_full.png"
                    render_figure(e, mvt, channel, full=True, bin_width=10, out_path=out)
        return

    track_number = args.mvt if args.mvt > 0 else 1
    bin_width = args.win if args.win is not None else (30 if args.full else 10)
    if args.full:
        OUT_DIR.mkdir(exist_ok=True)
        out = OUT_DIR / "press_times_example_full.png"
    else:
        out = REPO / "analysis" / "figures" / "press_times_example.png"
    render_figure(expid, track_number, CHANNEL, args.full, bin_width, out)


if __name__ == "__main__":
    main()

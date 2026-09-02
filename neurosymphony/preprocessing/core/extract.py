from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .goldmsi import compute_goldmsi_scores


COND_MAP = {1: 'TT', 2: 'TF', 3: 'FT', 4: 'FF'}
Q_LABELS = {"track_q2_1": 'perceivedpos', "track_q2_2": 'perceivedneg', "track_q2_3": 'recognpos', "track_q2_4": 'recognneg'}
TRACK_QUESTION_COUNTS = {1: 3, 2: 4, 3: 2}  # q1_1..q1_3, q2_1..q2_4, q3_1..q3_2


def _safe_int(x: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(float(x))
    except Exception:
        return default


def calculate_big_five_scores(ratings: List[float]) -> Dict[str, float]:
    if len(ratings) != 10:
        raise ValueError("BFI-10 expects 10 ratings")

    reverse_items = {1, 3, 4, 5, 7}
    scores = [
        (6 - ratings[i - 1]) if i in reverse_items else ratings[i - 1]
        for i in range(1, 11)
    ]

    return {
        "Extraversion": float(scores[0] + scores[4]),
        "Agreeableness": float(scores[1] + scores[6]),
        "Conscientiousness": float(scores[2] + scores[7]),
        "Neuroticism": float(scores[3] + scores[8]),
        "Openness_to_Experience": float(scores[4] + scores[9]),
    }


def _iter_user_json_files(userdata_dir: Path) -> Iterable[Path]:
    for p in userdata_dir.glob("user_*/**/*.json"):
        if p.is_file():
            yield p


def _extract_user_level(user_json: Dict[str, Any], userid: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"userid": userid}

    q = user_json.get("demographics_and_GMSI")
    if not isinstance(q, dict):
        return out

    demographics = q.get("demographics", {}) or {}
    out.update(
        {
            "demographics_age": demographics.get("age"),
            "demographics_gender": demographics.get("gender"),
            "demographics_highest_education": demographics.get("highest_education"),
            "demographics_occupation": demographics.get("occupation"),
            "demographics_childhood_country": demographics.get("childhood_country"),
            "demographics_mother_tongue": demographics.get("mother_tongue"),
            "demographics_psychiatric_treatment": demographics.get("psychiatric_treatment"),
            "demographics_psychiatric_diagnosis": demographics.get("psychiatric_diagnosis"),
        }
    )

    # BFI-10
    bigfive = q.get("bigfive", {}) or {}
    ratings = []
    for i in range(1, 11):
        ratings.append(float(bigfive.get(f"q{i}", "nan")))
    if all(pd.notna(r) for r in ratings):
        bf = calculate_big_five_scores(ratings)
        for k, v in bf.items():
            out[f"bigfive_scores_{k}"] = v

    # Gold-MSI
    g1 = q.get("goldsmi1", {}) or {}
    g2 = q.get("goldsmi2", {}) or {}
    gold_vals: List[str] = []
    for i in range(1, 40):
        key = f"q{i}"
        if i <= 16:
            gold_vals.append(g1.get(key))
        else:
            gold_vals.append(g2.get(key))

    if all(v is not None for v in gold_vals[:38]):
        scores = compute_goldmsi_scores(gold_vals)
        out.update({f"goldsmi_{k}": v for k, v in scores.items()})

    return out


def _list_experiment_ids(user_json: Dict[str, Any]) -> List[str]:
    exp_ids = [k for k in user_json.keys() if re.match(r"^exp\d+$", k)]
    exp_ids.sort(key=lambda s: int(s[3:]))
    return exp_ids


def _who5_sum(exp: Dict[str, Any]) -> Optional[int]:
    who5 = exp.get("who5")
    if not isinstance(who5, dict):
        return None
    vals = []
    for i in range(5):
        v = _safe_int(who5.get(f"q{i}"))
        if v is None:
            return None
        vals.append(v)
    return int(sum(vals))


def _norm_list(x, n=4, fill=None):
    """Pad/truncate x to length n."""
    if not isinstance(x, list):
        x = []
    x = list(x)[:n]
    if len(x) < n:
        x.extend([fill] * (n - len(x)))
    return x


def _is_complete_session(cond_per_session, desc_indices, descriptions):
    if any(v is None for v in cond_per_session):
        return False
    if any(v is None for v in desc_indices):
        return False
    if any((d is None) or (isinstance(d, dict) and not d.get("description")) or (isinstance(d, str) and not d.strip())
           for d in descriptions):
        return False
    return True


def _load_ratings(rating_folder: Path, framework: Dict[str, Any], expid: str, cache: Dict[str, "pd.DataFrame"]):
    if expid not in cache:
        desc_path = Path(framework[expid]['description_path']).stem.split('_')[0]
        cache[expid] = pd.read_csv(rating_folder / ("sorted_" + desc_path + "_rating.csv"))
    return cache[expid]


def extract_merged_experiment_table(
    userdata_dir: str | Path,
    framework_path: Optional[str | Path] = None,
    rating_folder: Optional[str | Path] = None,
) -> pd.DataFrame:
    userdata_dir = Path(userdata_dir)
    rating_folder = Path(rating_folder)
    if not userdata_dir.exists():
        raise FileNotFoundError(userdata_dir)

    framework = None
    if framework_path is not None:
        fp = Path(framework_path)
        if fp.exists():
            framework = json.loads(fp.read_text(encoding="utf-8"))

    rows: List[Dict[str, Any]] = []
    ratings_cache: Dict[str, Any] = {}

    for json_path in _iter_user_json_files(userdata_dir):
        userid = json_path.stem
        try:
            user_json = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if 'demographics_and_GMSI' not in user_json:
            continue

        questionnaire = user_json['demographics_and_GMSI']

        if not all(key in questionnaire for key in ['demographics', 'bigfive', 'goldsmi1', 'goldsmi2']):
            continue

        if len(questionnaire['demographics']) < 8 or len(questionnaire['bigfive']) < 10 or len(questionnaire['goldsmi1']) < 16 or len(questionnaire['goldsmi2']) < 23:
            continue

        user_level = _extract_user_level(user_json, userid)
        exp_ids = _list_experiment_ids(user_json)

        for expid in exp_ids:
            exp = user_json.get(expid)
            if not isinstance(exp, dict):
                continue
            if not all(key in exp for key in
                       ['track_1', 'track_2', 'track_3', 'track_4', 'post_experiment', 'who5']):
                continue

            who5 = _who5_sum(exp)

            session = exp.get("session_data", {}) or {}

            cond_per_session = _norm_list(session.get("cond_per_session"), n=4, fill=None)
            desc_indices = _norm_list(session.get("description_indices"), n=4, fill=None)
            descriptions = _norm_list(session.get("descriptions"), n=4, fill=None)

            if not _is_complete_session(cond_per_session, desc_indices, descriptions) or any([int(a)<0 for a in desc_indices]):
                continue

            post = exp.get("post_experiment", {}) or {}
            ratings = _load_ratings(rating_folder, framework, expid, ratings_cache)

            exp_level: Dict[str, Any] = {
                "post_experiment_q1_1": post.get("q1_1"),
                "post_experiment_q1_2": post.get("q1_2"),
                "post_experiment_q1_3": post.get("q1_3"),
                "post_experiment_q1_4": post.get("q1_4"),
                "post_experiment_q1_5": post.get("q1_5"),
                "post_experiment_q1_6": post.get("q1_6"),
                "post_experiment_recon_auth": post.get("recon_auth"),
                "post_experiment_recon_work": post.get("recon_work"),
            }
            if framework and expid in framework:
                for meta_key in ["title", "composer", "name"]:
                    if meta_key in framework[expid]:
                        exp_level[f"framework_{meta_key}"] = framework[expid][meta_key]

            for track_n in range(1, 5):
                track = exp.get(f"track_{track_n}", {}) or {}
                track_condition = np.where(np.array(cond_per_session) == track_n)[0][0] + 1

                r: Dict[str, Any] = {}
                r.update(user_level)
                r.update(exp_level)
                r.update(
                    {
                        "expid": expid,
                        "track_number": track_n,
                        "who5_sum": who5,
                        "description_line": (desc_indices[track_n - 1] if len(desc_indices) >= track_n else None),
                        "description_text": (
                            (descriptions[track_n - 1] or {}).get("description")
                            if isinstance(descriptions[track_n - 1], dict)
                            else None
                        ),
                        "track_condition": track_condition,
                        "condition": COND_MAP.get(track_condition, 'NA'),
                        "reading_dur": track.get("reading_duration"),
                        "starting_dur": track.get("starting_duration"),
                        "questionnaire_dur": track.get("questionnaire_duration"),
                        "listening_dur": track.get("listening_duration"),
                        "track_reading_duration": track.get("reading_duration"),
                        "track_starting_duration": track.get("starting_duration"),
                        "track_questionnaire_duration": track.get("questionnaire_duration"),
                        "track_listening_duration": track.get("listening_duration"),
                        "feedback": post.get("comments"),
                        "track_feedback": track.get("feedback"),
                    }
                )

                for q, n_items in TRACK_QUESTION_COUNTS.items():
                    for i in range(1, n_items + 1):
                        key = f"q{q}_{i}"
                        if key in track:
                            r[f"track_q{q}_{i}"] = track[key]

                for init_q_label, verbose_label in Q_LABELS.items():
                    if init_q_label in r:
                        r[verbose_label] = r[init_q_label]

                pressing_name = f"{expid}_traccia{track_n}.csv"
                pressing_path = json_path.parent / pressing_name
                if pressing_path.exists():
                    r[f"track_pressing_csv"] = str(pressing_path)

                    r["pressing_csv"] = str(pressing_path)
                    r["pressing_track"] = track_n

                target_line = r["description_line"]
                r.update({
                    'description_valence_mean': ratings.iloc[target_line]['valence_mean'],
                    'description_valence_trend_slope': ratings.iloc[target_line]['valence_trend_slope'],
                    'description_score_mvt_valence': ratings.iloc[target_line]['score_mvt_valence'],
                    'description_arousal_mean': ratings.iloc[target_line]['arousal_mean'],
                    'description_arousal_trend_slope': ratings.iloc[target_line]['arousal_trend_slope'],
                    'description_score_mvt_arousal': ratings.iloc[target_line]['score_mvt_arousal'],
                    'description_score_mvt_valence_reference': ratings.iloc[int(target_line / 18) * 18][
                        'score_mvt_valence'],
                    'description_score_mvt_valence_reference_opp': ratings.iloc[int(target_line / 18) * 18 + 1][
                        'score_mvt_valence']})

                rows.append(r)

    df = pd.DataFrame(rows)
    return df

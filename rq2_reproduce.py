"""Reproduce RQ2 statistics from pseudonymized numeric metrics and coding labels.

No learner text, original identifier, name or demographic variable is required.
Computations implement the F5–F10 procedures documented in this package.
The common statistical helper provides Holm adjustment.

The finite BCa bootstrap is run in public participant-ID order. Its resampling
seed and 20,000 samples match the original procedure, but a different row order
can change Monte Carlo confidence limits. Original confidence limits remain in
the reference tables and are compared separately, not silently overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common_statistics import holm_adjust, save_csv

GENRES = ["자기소개서", "중고거래 글", "SNS 글"]
SOURCES = ["A 대응", "B 대응", "A·B 공통", "A·B 통합", "C 의미 신규"]
F9_CODES = ["정보 유지", "정보 추가", "정보 삭제", "정보 대체", "정보 구체화", "정보 일반화"]
F_METRICS = {
    "retention_ra": "F5 형태 유지율 R_A",
    "borrowing_rb": "F6 형태 차용률 R_B",
    "novelty_nc": "F7 형태 신규율 N_C",
    "proximity_p": "F8 근접도 P",
}
BCa_COLUMNS = ["학습자평균_BCa95_low", "학습자평균_BCa95_high"]
OUTPUT_FILES = [
    "RQ2_23_F5_F8_학습자단위_BCa95.csv",
    "RQ2_25_F5_F8_유형효과_Friedman.csv",
    "RQ2_26_F5_F8_유형사후_Wilcoxon.csv",
    "RQ2_F9_F10_분포.csv",
    "RQ2_F9_F10_출처별_F9.csv",
    "RQ2_F9_F10_유형효과_Friedman.csv",
    "RQ2_F9_F10_유형사후_Wilcoxon.csv",
]


def summary(values: pd.Series, prefix: str) -> dict:
    """Same descriptive statistics as the original RQ2 numeric script."""
    x = pd.to_numeric(values, errors="coerce").dropna()
    return {
        f"{prefix}_n": len(x), f"{prefix}_mean": x.mean(),
        f"{prefix}_sd": x.std(ddof=1), f"{prefix}_median": x.median(),
        f"{prefix}_q1": x.quantile(.25), f"{prefix}_q3": x.quantile(.75),
        f"{prefix}_min": x.min(), f"{prefix}_max": x.max(),
    }


def rank_biserial(diff: pd.Series) -> float:
    d = pd.to_numeric(diff, errors="coerce").dropna()
    d = d[d != 0]
    if d.empty:
        return 0.0
    values = d.to_numpy(float)
    ranks = stats.rankdata(np.abs(values))
    return float((ranks[values > 0].sum() - ranks[values < 0].sum()) / ranks.sum())


def split_codes(value: str) -> list[str]:
    return list(dict.fromkeys(x.strip() for x in str(value).split("|") if x.strip()))


def numeric_rq2(source: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """F5–F8 summaries, BCa intervals, genre Friedman and pairwise Wilcoxon."""
    source = source.sort_values(["participant_id", "genre"], kind="stable").copy()
    learner = source.groupby("participant_id", observed=True)[list(F_METRICS)].mean()
    bca_rows, omnibus, posthoc = [], [], []
    for metric, label in F_METRICS.items():
        ci = stats.bootstrap(
            (learner[metric].to_numpy(float),), np.mean,
            confidence_level=.95, method="BCa", n_resamples=20000,
            random_state=np.random.default_rng(20260820),
        )
        bca_rows.append({
            "지표": label, **summary(source[metric], "과제"),
            **summary(learner[metric], "학습자"),
            BCa_COLUMNS[0]: ci.confidence_interval.low,
            BCa_COLUMNS[1]: ci.confidence_interval.high,
        })
        wide = source.pivot_table(
            index="participant_id", columns="genre", values=metric, aggfunc="first"
        ).reindex(columns=GENRES).dropna()
        chi, raw_p = stats.friedmanchisquare(*(wide[g] for g in GENRES))
        row = {"지표": label, "chi2": chi, "df": 2, "p_raw": raw_p,
               "kendall_W": chi / (len(wide) * 2)}
        for genre in GENRES:
            row.update(summary(wide[genre], genre))
            for suffix in ["n", "min", "max"]:
                row.pop(f"{genre}_{suffix}")
        omnibus.append(row)
        pairs = []
        for before, after in combinations(GENRES, 2):
            delta = wide[after] - wide[before]
            w, p = stats.wilcoxon(
                wide[after], wide[before], zero_method="wilcox", alternative="two-sided"
            )
            pairs.append({
                "지표": label, "비교": f"{after} - {before}",
                "앞_중앙값": wide[before].median(), "뒤_중앙값": wide[after].median(),
                "중앙값차_뒤-앞": delta.median(), "Wilcoxon_W": w, "p_raw": p,
                "rank_biserial": rank_biserial(delta),
            })
        for pair, adjusted in zip(pairs, holm_adjust([x["p_raw"] for x in pairs])):
            pair["p_holm_within_metric"] = adjusted
            posthoc.append(pair)
    omnibus = pd.DataFrame(omnibus)
    omnibus["p_holm_family"] = holm_adjust(omnibus["p_raw"])
    return {
        OUTPUT_FILES[0]: pd.DataFrame(bca_rows),
        OUTPUT_FILES[1]: omnibus,
        OUTPUT_FILES[2]: pd.DataFrame(posthoc),
    }


def coding_rq2(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Code-only counterpart of the original F9/F10 aggregation procedure."""
    frame = frame.copy()
    frame["meaning_source"] = frame["meaning_source"].str.strip().replace({"A⋅B 통합": "A·B 통합"})
    assert len(frame) == 802
    assert frame["unit_id"].nunique() == 802
    assert frame["task_id"].nunique() == 84
    assert frame["participant_id"].nunique() == 28
    assert set(frame["meaning_source"]) <= set(SOURCES)
    assert set(frame["f9"]) <= set(F9_CODES)
    assert frame[["task_id", "participant_id", "genre", "meaning_source", "f9", "f10_codes"]].ne("").all().all()
    dimensions = [
        ("의미 출처", "meaning_source", False),
        ("F9 정보 조정", "f9", False),
        ("F10 표현 조정", "f10_codes", True),
    ]
    code_sets = {
        dim: sorted({code for value in frame[field]
                     for code in (split_codes(value) if multi else [value])})
        for dim, field, multi in dimensions
    }
    distribution = []
    for scope in ["전체", *GENRES]:
        subset = frame if scope == "전체" else frame[frame["genre"] == scope]
        for dim, field, multi in dimensions:
            counts = Counter(code for value in subset[field]
                             for code in (split_codes(value) if multi else [value]))
            for code in code_sets[dim]:
                distribution.append({
                    "분석범위": scope, "평가차원": dim, "코드": code,
                    "단위출현수": counts[code], "분모_C의미단위": len(subset),
                    "단위출현비율": counts[code] / len(subset),
                })
    tasks = []
    for task_id, group in frame.groupby("task_id", sort=False):
        row = {"task_id": task_id, "participant_id": group.iloc[0]["participant_id"],
               "genre": group.iloc[0]["genre"], "C의미단위수": len(group)}
        for dim, field, multi in dimensions:
            counts = Counter(code for value in group[field]
                             for code in (split_codes(value) if multi else [value]))
            for code in code_sets[dim]:
                row[f"{dim}|{code}|수"] = counts[code]
                row[f"{dim}|{code}|비율"] = counts[code] / len(group)
        tasks.append(row)
    task_frame = pd.DataFrame(tasks)
    assert task_frame.groupby("participant_id")["genre"].nunique().eq(3).all()
    omnibus, posthoc = [], []
    for dim, field, multi in dimensions:
        family = []
        for code in code_sets[dim]:
            wide = task_frame.pivot(
                index="participant_id", columns="genre", values=f"{dim}|{code}|비율"
            ).reindex(columns=GENRES)
            assert wide.shape == (28, 3) and wide.notna().all().all()
            if np.all(wide.max(axis=1).to_numpy() == wide.min(axis=1).to_numpy()):
                chi, p = 0., 1.
            else:
                chi, p = stats.friedmanchisquare(*(wide[g] for g in GENRES))
            row = {
                "평가차원": dim, "코드": code, "n": 28,
                "자기소개서_M": wide[GENRES[0]].mean(), "중고거래_M": wide[GENRES[1]].mean(),
                "SNS_M": wide[GENRES[2]].mean(), "Friedman_chi2": chi,
                "df": 2, "p": p, "Kendall_W": chi / 56,
            }
            pairs = []
            for before, after in combinations(GENRES, 2):
                delta = wide[after] - wide[before]
                nonzero = delta.to_numpy()[delta.to_numpy() != 0]
                if len(nonzero):
                    w, pv = stats.wilcoxon(
                        wide[after], wide[before], zero_method="wilcox", alternative="two-sided"
                    )
                    ranks = stats.rankdata(np.abs(nonzero))
                    r = (ranks[nonzero > 0].sum() - ranks[nonzero < 0].sum()) / ranks.sum()
                else:
                    w, pv, r = 0., 1., 0.
                pairs.append({
                    "평가차원": dim, "코드": code, "비교": f"{after} - {before}", "n": 28,
                    "앞_M": wide[before].mean(), "뒤_M": wide[after].mean(),
                    "뒤-앞": delta.mean(), "Wilcoxon_W": w, "p": pv, "순위양류상관": r,
                })
            for pair, adjusted in zip(pairs, holm_adjust([x["p"] for x in pairs])):
                pair["Holm_p_지표내"] = adjusted
                pair["판정"] = "유의" if adjusted < .05 else "비유의"
            family.append((row, pairs))
        for (row, pairs), adjusted in zip(family, holm_adjust([x[0]["p"] for x in family])):
            row["Holm_p"] = adjusted
            row["판정"] = "유의" if adjusted < .05 else "비유의"
            for pair in pairs:
                pair["전체검정판정"] = row["판정"]
            omnibus.append(row)
            posthoc.extend(pairs)
    cross = []
    for source in SOURCES:
        subset = frame[frame["meaning_source"] == source]
        counts = Counter(subset["f9"])
        for code in F9_CODES:
            cross.append({
                "의미 출처": source, "F9 정보 조정": code, "빈도": counts[code],
                "출처별_단위수": len(subset), "출처내_비율": counts[code] / len(subset),
            })
    return {
        OUTPUT_FILES[3]: pd.DataFrame(distribution),
        OUTPUT_FILES[4]: pd.DataFrame(cross),
        OUTPUT_FILES[5]: pd.DataFrame(omnibus),
        OUTPUT_FILES[6]: pd.DataFrame(posthoc),
    }


def reproduce_rq2(data_dir: Path, output_dir: Path) -> dict:
    source = pd.read_csv(data_dir / "source_metrics.csv", encoding="utf-8-sig")
    codes = pd.read_csv(data_dir / "meaning_codes.csv", encoding="utf-8-sig", keep_default_na=False)
    assert len(source) == 84 and source["participant_id"].nunique() == 28
    assert source["task_id"].nunique() == 84
    assert source.groupby("participant_id")["genre"].nunique().eq(3).all()
    outputs = {**numeric_rq2(source), **coding_rq2(codes)}
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        save_csv(frame, output_dir / name)
    return {
        "tables": [{"file": name, "rows": len(frame), "columns": len(frame.columns)}
                   for name, frame in outputs.items()],
        "bootstrap": {
            "method": "BCa", "confidence_level": .95, "n_resamples": 20000,
            "seed": 20260820, "learner_order": "public participant_id ascending",
            "original_limits_may_differ_due_to_finite_resampling_order": True,
            "original_confidence_limits_are_not_modified": True,
        },
    }


def compare_rq2(output_dir: Path, reference_dir: Path) -> dict:
    """Validate deterministic cells; report BCa CI differences explicitly."""
    reports, drift = [], []
    all_passed = True
    for name in OUTPUT_FILES:
        got = pd.read_csv(output_dir / name, encoding="utf-8-sig")
        ref = pd.read_csv(reference_dir / name, encoding="utf-8-sig")
        shape_ok = got.shape == ref.shape and list(got.columns) == list(ref.columns)
        passed = shape_ok
        bad_columns = []
        if shape_ok:
            for column in got.columns:
                if name == OUTPUT_FILES[0] and column in BCa_COLUMNS:
                    for label, new, original in zip(got["지표"], got[column], ref[column]):
                        if not np.isclose(new, original, rtol=1e-8, atol=1e-9, equal_nan=True):
                            drift.append({"metric": label, "column": column,
                                          "public_replay": float(new), "original_reference": float(original),
                                          "absolute_difference": float(abs(new-original))})
                    continue
                if pd.api.types.is_numeric_dtype(got[column]) and pd.api.types.is_numeric_dtype(ref[column]):
                    same = np.allclose(got[column], ref[column], rtol=1e-8, atol=1e-9, equal_nan=True)
                else:
                    same = got[column].fillna("").astype(str).equals(ref[column].fillna("").astype(str))
                if not same:
                    passed = False
                    bad_columns.append(column)
        all_passed &= passed
        reports.append({"file": name, "shape_match": shape_ok,
                        "deterministic_cells_passed": bool(passed), "mismatch_columns": bad_columns})
    return {
        "deterministic_statistics_passed": bool(all_passed),
        "comparison_tolerance": {"relative": 1e-8, "absolute": 1e-9},
        "tables": reports,
        "bca_confidence_limit_comparison": {
            "different_cells": len(drift),
            "max_absolute_difference": max((r["absolute_difference"] for r in drift), default=0.),
            "details": drift,
            "explanation": "Public participant-ID ordering changes finite Monte Carlo resamples; original limits are retained in references.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent / "data")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new directory")
    report = reproduce_rq2(args.data, args.output)
    if args.reference:
        report["validation"] = compare_rq2(args.output, args.reference)
    (args.output / "rq2_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.reference and not report["validation"]["deterministic_statistics_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

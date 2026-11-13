"""반복측정 자료에 공통으로 사용하는 통계 함수.

연구 설계의 핵심
------------------
28명의 학습자가 자기소개서·중고거래 글·SNS 글을 모두 작성했으므로 세 관측은
서로 독립적이지 않다. 따라서 독립집단 일원 ANOVA가 아니라 같은 학습자를 행으로
맞춘 반복측정 검정을 사용한다. 이 모듈은 RQ1과 RQ2가 같은 계산 규칙을 공유하도록
만든 단일 출처(single source of truth)이다.

주의
----
함수는 결측이 있는 학습자를 해당 검정에서만 제외한다. 입력 DataFrame의 행은
학습자, 열은 반복 조건(A/B/C 또는 세 글쓰기 유형)이어야 한다.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg, stats


def save_csv(frame: pd.DataFrame, path: Path) -> None:
    """Excel에서 한글이 깨지지 않도록 UTF-8 BOM CSV로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def holm_adjust(p_values) -> np.ndarray:
    """여러 검정을 동시에 수행할 때 가족오류율을 제어하는 Holm 보정.

    가장 작은 p부터 엄격한 기준을 적용하되 Bonferroni보다 검정력이 높은 순차
    보정이다. NaN은 유지하며, 입력 순서와 같은 순서로 보정 p를 반환한다.
    """
    p = np.asarray(p_values, dtype=float)
    result = np.full_like(p, np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    if len(valid) == 0:
        return result
    order = valid[np.argsort(p[valid])]
    m = len(order)
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * p[idx])
        running = max(running, candidate)
        result[idx] = running
    return result


def rm_anova(wide: pd.DataFrame) -> dict:
    """일원 반복측정 ANOVA와 구형성 진단·GG 보정을 계산한다.

    반환값의 `판정_p`는 Mauchly p<.05이면 Greenhouse–Geisser 보정 p,
    그렇지 않으면 일반 p이다. `부분_eta2`는 조건 효과의 크기이다.
    """
    clean = wide.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    x = clean.to_numpy(dtype=float)
    n, k = x.shape if x.ndim == 2 else (0, 0)
    base = {
        "n": n, "조건수": k, "F": np.nan, "df1": np.nan, "df2": np.nan,
        "일반_p": np.nan, "Mauchly_W": np.nan, "Mauchly_p": np.nan,
        "GG_epsilon": np.nan, "GG_df1": np.nan, "GG_df2": np.nan,
        "GG_p": np.nan, "판정_p": np.nan, "부분_eta2": np.nan,
    }
    if n < 3 or k < 2:
        return base

    grand = x.mean()
    subject_means = x.mean(axis=1, keepdims=True)
    condition_means = x.mean(axis=0, keepdims=True)
    ss_total = ((x - grand) ** 2).sum()
    ss_subject = k * ((subject_means - grand) ** 2).sum()
    ss_condition = n * ((condition_means - grand) ** 2).sum()
    ss_error = max(0.0, ss_total - ss_subject - ss_condition)
    df1 = k - 1
    df2 = (n - 1) * (k - 1)
    ms_condition = ss_condition / df1
    ms_error = ss_error / df2 if df2 else np.nan
    f_value = ms_condition / ms_error if ms_error and ms_error > 0 else np.nan
    p_value = stats.f.sf(f_value, df1, df2) if np.isfinite(f_value) else np.nan
    eta = ss_condition / (ss_condition + ss_error) if (ss_condition + ss_error) > 0 else np.nan

    mauchly_w = mauchly_p = gg_eps = np.nan
    if k >= 3:
        covariance = np.cov(x, rowvar=False, ddof=1)
        contrast = linalg.helmert(k, full=False)
        projected = contrast @ covariance @ contrast.T
        eigenvalues = np.linalg.eigvalsh(projected)
        eigenvalues = eigenvalues[eigenvalues > 1e-12]
        p_dim = k - 1
        if len(eigenvalues) == p_dim:
            mean_eigen = eigenvalues.mean()
            mauchly_w = float(np.prod(eigenvalues) / (mean_eigen ** p_dim))
            mauchly_w = min(1.0, max(mauchly_w, 1e-15))
            correction = (2 * p_dim**2 + p_dim + 2) / (6 * p_dim * (n - 1))
            chi2 = -(n - 1) * (1 - correction) * np.log(mauchly_w)
            df_m = p_dim * (p_dim + 1) / 2 - 1
            mauchly_p = float(stats.chi2.sf(chi2, df_m))
        trace = np.trace(projected)
        denom = p_dim * np.trace(projected @ projected)
        gg_eps = float((trace**2) / denom) if denom > 0 else np.nan
        if np.isfinite(gg_eps):
            gg_eps = min(1.0, max(1 / p_dim, gg_eps))
    else:
        gg_eps = 1.0

    gg_df1 = df1 * gg_eps if np.isfinite(gg_eps) else np.nan
    gg_df2 = df2 * gg_eps if np.isfinite(gg_eps) else np.nan
    gg_p = stats.f.sf(f_value, gg_df1, gg_df2) if np.isfinite(f_value) and np.isfinite(gg_eps) else np.nan
    decision_p = gg_p if np.isfinite(mauchly_p) and mauchly_p < 0.05 else p_value
    base.update({
        "F": f_value, "df1": df1, "df2": df2, "일반_p": p_value,
        "Mauchly_W": mauchly_w, "Mauchly_p": mauchly_p,
        "GG_epsilon": gg_eps, "GG_df1": gg_df1, "GG_df2": gg_df2,
        "GG_p": gg_p, "판정_p": decision_p, "부분_eta2": eta,
    })
    return base


def friedman_test(wide: pd.DataFrame) -> dict:
    """비모수 반복측정 검정과 Kendall W를 계산한다."""
    clean = wide.apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    n, k = clean.shape
    if n < 3 or k < 3:
        return {"n": n, "chi2": np.nan, "df": k - 1, "p": np.nan, "Kendall_W": np.nan}
    chi2, p_value = stats.friedmanchisquare(*(clean[c].to_numpy() for c in clean.columns))
    w = chi2 / (n * (k - 1))
    return {"n": n, "chi2": chi2, "df": k - 1, "p": p_value, "Kendall_W": w}


def paired_tests(wide: pd.DataFrame, condition_order: list[str]) -> pd.DataFrame:
    """모든 조건쌍의 대응 t·Wilcoxon·효과크기·95% CI를 계산한다."""
    clean = wide[condition_order].apply(pd.to_numeric, errors="coerce")
    rows = []
    for before, after in combinations(condition_order, 2):
        pair = clean[[before, after]].dropna()
        x = pair[before].to_numpy(float)
        y = pair[after].to_numpy(float)
        diff = y - x
        n = len(diff)
        if n < 2:
            continue
        t_value, t_p = stats.ttest_rel(y, x, nan_policy="omit")
        sd_diff = diff.std(ddof=1)
        dz = diff.mean() / sd_diff if sd_diff > 0 else np.nan
        se = sd_diff / np.sqrt(n) if sd_diff > 0 else 0.0
        critical = stats.t.ppf(0.975, n - 1)
        ci_low = diff.mean() - critical * se
        ci_high = diff.mean() + critical * se
        nonzero = diff[diff != 0]
        if len(nonzero):
            wilcoxon_w, wilcoxon_p = stats.wilcoxon(nonzero, zero_method="wilcox", alternative="two-sided")
            ranks = stats.rankdata(np.abs(nonzero))
            positive = ranks[nonzero > 0].sum()
            negative = ranks[nonzero < 0].sum()
            r_rb = (positive - negative) / (positive + negative) if positive + negative else np.nan
        else:
            wilcoxon_w, wilcoxon_p, r_rb = 0.0, 1.0, 0.0
        rows.append({
            "비교": f"{after} - {before}", "앞조건": before, "뒤조건": after,
            "n": n, "앞평균": x.mean(), "뒤평균": y.mean(), "평균차": diff.mean(),
            "95CI_하한": ci_low, "95CI_상한": ci_high, "t": t_value,
            "t_df": n - 1, "t_p": t_p, "Cohen_dz": dz,
            "Wilcoxon_W": wilcoxon_w, "Wilcoxon_p": wilcoxon_p, "순위양분상관": r_rb,
        })
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["t_Holm_p"] = holm_adjust(frame["t_p"])
        frame["Wilcoxon_Holm_p"] = holm_adjust(frame["Wilcoxon_p"])
    return frame


def one_sample_summary(values, null_value: float = 0.0) -> dict:
    """학습자 단위 평균의 M·SD·95% CI와 0(또는 지정값) 기준 t검정."""
    arr = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(float)
    n = len(arr)
    if n < 2:
        return {"n": n, "평균": np.nan, "표준편차": np.nan, "95CI_하한": np.nan,
                "95CI_상한": np.nan, "t": np.nan, "df": np.nan, "p": np.nan, "Cohen_dz": np.nan}
    mean = arr.mean()
    sd = arr.std(ddof=1)
    se = sd / np.sqrt(n)
    critical = stats.t.ppf(.975, n - 1)
    t_value, p_value = stats.ttest_1samp(arr, popmean=null_value)
    return {
        "n": n, "평균": mean, "표준편차": sd,
        "95CI_하한": mean - critical * se, "95CI_상한": mean + critical * se,
        "t": t_value, "df": n - 1, "p": p_value,
        "Cohen_dz": (mean - null_value) / sd if sd > 0 else np.nan,
    }


def significance_label(p_value) -> str:
    if not np.isfinite(p_value):
        return "계산 불가"
    if p_value < 0.001:
        return "p<.001"
    if p_value < 0.01:
        return "p<.01"
    if p_value < 0.05:
        return "p<.05"
    return "비유의"


def set_korean_font() -> None:
    """macOS·Windows·Linux에서 찾을 수 있는 첫 한글 글꼴을 사용한다."""
    import matplotlib
    from matplotlib import font_manager

    candidates = ["Apple SD Gothic Neo", "AppleGothic", "Malgun Gothic", "NanumGothic", "Noto Sans CJK KR"]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    for font in candidates:
        if font in installed:
            matplotlib.rcParams["font.family"] = font
            break
    matplotlib.rcParams["axes.unicode_minus"] = False

"""Replay the manuscript's six F1-F3 measures and manually coded F4.

Each text is measured before release. This module averages the three task
measurements within each participant and version, then calculates omnibus
statistics and the three within-measure pairwise tests. Stored omnibus
multiplicity-adjusted p-values are reference-only and are not recalculated
or inserted into these computed tables.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common_statistics import friedman_test, holm_adjust, paired_tests, rm_anova, save_csv

VERSIONS = ['A', 'B', 'C']
GENRES = ['자기소개서', '중고거래 글', 'SNS 글']
METRICS = {
    'characters': '문자수',
    'eojeols': '어절수',
    'sentences': '문장수',
    'mattr20': 'MATTR20',
    'mean_sentence_length': '평균문장길이',
    'predicates_per_sentence': '문장당서술어수',
}
F4 = 'manual_errors_per_100_eojeols'
F4_LABEL = '문법오류율_1차'
OUTPUT_FILES = [
    'RQ1_ABC_six_measures.csv',
    'RQ1_ABC_pairwise.csv',
    'RQ1_F4_ABC.csv',
    'RQ1_F4_pairwise.csv',
    'RQ1_topic_seven_measures.csv',
    'RQ1_topic_pairwise.csv',
]
REF_ABC = 'RQ1_13_제4장_A_B_C_통합통계표.csv'
REF_F4 = 'RQ1_20_F4_ABC_Friedman.csv'
REF_F4_PAIR = 'RQ1_21_F4_ABC_Wilcoxon.csv'
REF_TOPIC = 'RQ1_23_확정주검정_유형효과.csv'


def validate_input(frame):
    required = {'participant_id', 'task_id', 'genre', 'version', *METRICS, F4}
    optional = {'manual_error_count', 'mattr_short_ttr'}
    if required - set(frame.columns):
        raise ValueError('Required manuscript-scope numeric columns are missing')
    if set(frame.columns) - required - optional:
        raise ValueError('Unexpected input columns outside the public manuscript scope')
    if len(frame) != 252 or frame.participant_id.nunique() != 28 or frame.task_id.nunique() != 84:
        raise ValueError('Expected 252 texts, 28 participants and 84 tasks')
    if set(frame.version) != set(VERSIONS) or set(frame.genre) != set(GENRES):
        raise ValueError('Unexpected version or genre labels')
    if frame.duplicated(['task_id', 'version']).any():
        raise ValueError('Duplicate task-version rows')
    if not frame.groupby(['participant_id', 'genre']).size().eq(3).all():
        raise ValueError('Expected all three versions for each participant and genre')
    values = frame[[*METRICS, F4]].apply(pd.to_numeric, errors='coerce')
    if values.isna().any().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError('Manuscript measures must contain finite numeric values')


def task_values(frame, metric):
    return frame.pivot(index=['participant_id', 'task_id', 'genre'],
                       columns='version', values=metric).reindex(columns=VERSIONS).dropna()


def descriptive(wide, columns):
    result = {'n': len(wide)}
    for column in columns:
        result[column + '_M'] = wide[column].mean()
        result[column + '_SD'] = wide[column].std(ddof=1)
    return result


def anova_summary(wide):
    result = rm_anova(wide)
    gg = bool(np.isfinite(result['Mauchly_p']) and result['Mauchly_p'] < .05)
    return {'test': 'repeated-measures ANOVA', 'statistic': result['F'],
            'df1': result['GG_df1'] if gg else result['df1'],
            'df2': result['GG_df2'] if gg else result['df2'],
            'p_uncorrected': result['판정_p'],
            'effect_size': result['부분_eta2'], 'effect_size_type': 'partial eta squared',
            'mauchly_p': result['Mauchly_p'], 'gg_epsilon': result['GG_epsilon'],
            'gg_applied': gg}


def friedman_summary(wide):
    result = friedman_test(wide)
    return {'test': 'Friedman', 'statistic': result['chi2'], 'df1': result['df'],
            'df2': np.nan, 'p_uncorrected': result['p'], 'effect_size': result['Kendall_W'],
            'effect_size_type': 'Kendall W', 'mauchly_p': np.nan,
            'gg_epsilon': np.nan, 'gg_applied': False}


def t_pairs(wide, conditions, metric):
    pairs = paired_tests(wide, conditions)
    rows = []
    for _, row in pairs.iterrows():
        rows.append({'metric': metric, 'before': row['앞조건'], 'after': row['뒤조건'],
                     'n': row['n'], 'before_M': row['앞평균'], 'after_M': row['뒤평균'],
                     'mean_difference_after_minus_before': row['평균차'],
                     'ci95_low': row['95CI_하한'], 'ci95_high': row['95CI_상한'],
                     'test': 'paired t', 'statistic': row['t'], 'df': row['t_df'],
                     'p_raw': row['t_p'], 'p_holm_within_measure': row['t_Holm_p'],
                     'effect_size': row['Cohen_dz'], 'effect_size_type': 'Cohen dz'})
    return rows


def wilcoxon_pairs(wide, conditions, metric, remove_zero_before_test=False):
    rows = []
    for before, after in combinations(conditions, 2):
        difference = wide[after] - wide[before]
        nonzero = difference[difference != 0]
        if remove_zero_before_test:
            test = stats.wilcoxon(nonzero, zero_method='wilcox', alternative='two-sided')
        else:
            test = stats.wilcoxon(wide[after], wide[before], zero_method='wilcox')
        ranks = stats.rankdata(abs(nonzero))
        positive = ranks[nonzero.to_numpy() > 0].sum()
        negative = ranks[nonzero.to_numpy() < 0].sum()
        effect = float((positive - negative) / (positive + negative)) if positive + negative else 0.0
        rows.append({'metric': metric, 'before': before, 'after': after, 'n': len(wide),
                     'before_M': wide[before].mean(), 'after_M': wide[after].mean(),
                     'mean_difference_after_minus_before': difference.mean(),
                     'median_difference_after_minus_before': difference.median(),
                     'test': 'Wilcoxon', 'statistic': float(test.statistic),
                     'p_raw': float(test.pvalue), 'effect_size': effect,
                     'effect_size_type': 'rank-biserial correlation'})
    for row, adjusted in zip(rows, holm_adjust([row['p_raw'] for row in rows])):
        row['p_holm_within_measure'] = adjusted
    return rows


def reproduce_rq1(data_dir: Path, output_dir: Path) -> dict:
    frame = pd.read_csv(Path(data_dir) / 'text_metrics.csv', encoding='utf-8-sig')
    validate_input(frame)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    abc_rows, abc_pairs, topic_rows, topic_pairs = [], [], [], []
    for metric in METRICS:
        task = task_values(frame, metric)
        learner = task.groupby(level='participant_id')[VERSIONS].mean()
        abc_rows.append({'metric': metric, **descriptive(learner, VERSIONS), **anova_summary(learner)})
        abc_pairs.extend(t_pairs(learner, VERSIONS, metric))
        delta = (task.C - task.A).reset_index(name='delta').pivot(
            index='participant_id', columns='genre', values='delta').reindex(columns=GENRES)
        topic_rows.append({'metric': metric, **descriptive(delta, GENRES), **anova_summary(delta)})
        topic_pairs.extend(t_pairs(delta, GENRES, metric))
    task = task_values(frame, F4)
    learner = task.groupby(level='participant_id')[VERSIONS].mean()
    f4_rows = [{'metric': F4, **descriptive(learner, VERSIONS), **friedman_summary(learner)}]
    f4_pairs = wilcoxon_pairs(learner, VERSIONS, F4)
    delta = (task.C - task.A).reset_index(name='delta').pivot(
        index='participant_id', columns='genre', values='delta').reindex(columns=GENRES)
    topic_rows.append({'metric': F4, **descriptive(delta, GENRES), **friedman_summary(delta)})
    topic_pairs.extend(wilcoxon_pairs(delta, GENRES, F4, remove_zero_before_test=True))
    tables = [abc_rows, abc_pairs, f4_rows, f4_pairs, topic_rows, topic_pairs]
    for filename, rows in zip(OUTPUT_FILES, tables):
        save_csv(pd.DataFrame(rows), output_dir / filename)
    return {'mode': 'manuscript_scope_numeric_replay', 'participants': 28, 'tasks': 84,
            'texts': 252, 'automated_manuscript_measures': 6, 'manual_accuracy_measures': 1,
            'outputs': OUTPUT_FILES, 'nlp_recomputed': False, 'manual_coding_changed': False,
            'omnibus_adjusted_p_recalculated': False,
            'omnibus_adjusted_p_policy': 'Stored manuscript values are reference-only. Computed tables contain unadjusted omnibus p-values and within-measure pairwise Holm values.'}


def compare_rq1(output_dir: Path, reference_dir: Path) -> dict:
    output_dir, reference_dir = Path(output_dir), Path(reference_dir)
    abc = pd.read_csv(output_dir / OUTPUT_FILES[0]).set_index('metric')
    abc_pairs = pd.read_csv(output_dir / OUTPUT_FILES[1])
    f4 = pd.read_csv(output_dir / OUTPUT_FILES[2]).iloc[0]
    f4_pairs = pd.read_csv(output_dir / OUTPUT_FILES[3])
    topic = pd.read_csv(output_dir / OUTPUT_FILES[4]).set_index('metric')
    topic_pairs = pd.read_csv(output_dir / OUTPUT_FILES[5])
    ref_abc = pd.read_csv(reference_dir / REF_ABC, encoding='utf-8-sig').set_index('지표')
    ref_f4 = pd.read_csv(reference_dir / REF_F4, encoding='utf-8-sig').iloc[0]
    ref_f4_pairs = pd.read_csv(reference_dir / REF_F4_PAIR, encoding='utf-8-sig')
    ref_topic = pd.read_csv(reference_dir / REF_TOPIC, encoding='utf-8-sig').set_index('지표')
    if set(ref_abc.index) != set(METRICS.values()) or set(ref_topic.index) != {*METRICS.values(), F4_LABEL}:
        raise ValueError('Reference tables must contain only manuscript measures')
    comparisons = []
    def check(label, got, expected):
        comparisons.append({'check': label, 'passed': bool(np.isclose(got, expected, rtol=1e-8, atol=1e-9, equal_nan=True))})
    for metric, label in METRICS.items():
        got, ref = abc.loc[metric], ref_abc.loc[label]
        check(metric + ': ABC n', got['n'], ref['n'])
        for version in VERSIONS:
            for stat in ['M', 'SD']:
                column = version + '_' + stat
                check(metric + ': ABC ' + column, got[column], ref[column])
        for actual, stored in [('statistic', 'F'), ('df1', 'df1'), ('df2', 'df2'), ('effect_size', '부분_eta2')]:
            check(metric + ': ABC ' + actual, got[actual], ref[stored])
        # The reference reports F and its reported degrees of freedom; its
        # corresponding p is independently reconstructed without multiplicity.
        check(metric + ': ABC omnibus unadjusted p', got['p_uncorrected'], stats.f.sf(ref['F'], ref['df1'], ref['df2']))
        for _, pair in abc_pairs[abc_pairs.metric == metric].iterrows():
            column = pair['before'] + '-' + pair['after'] + '_Holm_p'
            check(metric + ': ABC pair ' + pair['before'] + pair['after'], pair['p_holm_within_measure'], ref[column])
    check('F4: ABC n', f4['n'], ref_f4['n'])
    for version in VERSIONS:
        for stat in ['M', 'SD']:
            column = version + '_' + stat
            check('F4: ABC ' + column, f4[column], ref_f4[column])
    for actual, stored in [('statistic', 'chi2'), ('df1', 'df'), ('p_uncorrected', 'p'), ('effect_size', 'Kendall_W')]:
        check('F4: ABC ' + actual, f4[actual], ref_f4[stored])
    for _, pair in f4_pairs.iterrows():
        ref = ref_f4_pairs.loc[ref_f4_pairs['비교'] == pair['before'] + '–' + pair['after']].iloc[0]
        for actual, stored in [('statistic', 'Wilcoxon_W'), ('p_raw', 'p_raw'), ('p_holm_within_measure', 'p_holm'), ('effect_size', 'rank_biserial')]:
            check('F4: ABC pair ' + pair['before'] + pair['after'] + ' ' + actual, pair[actual], ref[stored])
    names = {**METRICS, F4: F4_LABEL}
    prefixes = {'자기소개서': '자기소개서', '중고거래 글': '중고거래', 'SNS 글': 'SNS'}
    for metric, label in names.items():
        got, ref = topic.loc[metric], ref_topic.loc[label]
        check(metric + ': topic n', got['n'], ref['n'])
        for genre, prefix in prefixes.items():
            for stat in ['M', 'SD']:
                check(metric + ': topic ' + genre + '_' + stat, got[genre + '_' + stat], ref[prefix + '_' + stat])
        for actual, stored in [('statistic', '통계량'), ('df1', 'df1'), ('df2', 'df2'), ('p_uncorrected', '원p'), ('effect_size', '효과크기')]:
            check(metric + ': topic ' + actual, got[actual], ref[stored])
        for _, pair in topic_pairs[topic_pairs.metric == metric].iterrows():
            column = pair['after'] + ' - ' + pair['before'] + ' | Holm p'
            check(metric + ': topic pair ' + pair['before'] + pair['after'], pair['p_holm_within_measure'], ref[column])
    failures = [comparison['check'] for comparison in comparisons if not comparison['passed']]
    return {'passed': not failures, 'checked_numeric_cells': len(comparisons),
            'tolerance': {'relative': 1e-8, 'absolute': 1e-9}, 'failed_checks': failures,
            'omnibus_adjusted_p_recalculated': False,
            'reference_only_fields': {'ABC': ['Holm_p'], 'topic': ['전체_Holm_p', '판정']},
            'scope': 'Descriptive statistics, omnibus statistics/df/unadjusted p/effect sizes, and within-measure pairwise Holm results. Reference-only omnibus adjusted p-values are not claimed as recalculated.'}

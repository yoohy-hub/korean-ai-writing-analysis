"""Synthetic regression checks and the public data-scope contract."""
from pathlib import Path
import math
import sys
import unittest
import unicodedata
import numpy as np
import pandas as pd
from scipy import stats

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from paper_metrics import normalize_text,eojeol_count,mattr20,form_source_metrics
from common_statistics import holm_adjust,rm_anova,paired_tests
from rq2_reproduce import split_codes,rank_biserial

class Integrity(unittest.TestCase):
    def test_unicode_and_line_endings(self):
        self.assertEqual(normalize_text(unicodedata.normalize('NFD','가나다')+'\r\n'),'가나다')
    def test_symbol_only_segments(self):
        self.assertEqual(eojeol_count('안녕 # !!! AI 23'),3)
    def test_empty_text_measurements(self):
        self.assertEqual(eojeol_count(''),0);self.assertIsNone(mattr20([]))
    def test_short_mattr(self):
        self.assertAlmostEqual(mattr20(['가/NNG','가/NNG','나/NNG']),2/3)
    def test_mattr_window_boundary(self):
        self.assertEqual(mattr20([str(i) for i in range(20)]),1)
    def test_mattr_repetition(self):
        self.assertAlmostEqual(mattr20(['가/NNG']*25),.05)
    def test_mattr_pos_identity(self):
        self.assertEqual(mattr20(['가/VV','가/JKS']),1)
    def test_form_source_denominators(self):
        a={'a','b'};b={'b','c'};c={'a','b','c','d'}
        r=form_source_metrics(a,b,c)
        self.assertEqual(r['retention_ra'],1);self.assertEqual(r['borrowing_rb'],1)
        self.assertEqual(r['novelty_nc'],.25);self.assertEqual(r['proximity_p'],0)
    def test_form_source_empty_and_zero(self):
        self.assertIsNone(form_source_metrics(set(),set(),set())['proximity_p'])
        self.assertEqual(form_source_metrics({'a'},{'b'},{'c'})['proximity_p'],0)
    def test_holm_known_values(self):
        np.testing.assert_allclose(holm_adjust([.01,.04,.03]),[.03,.06,.06])
    def test_holm_missing(self):
        x=holm_adjust([np.nan,.01,.03]);self.assertTrue(math.isnan(x[0]));np.testing.assert_allclose(x[1:],[.02,.03])
    def test_paired_alignment(self):
        df=pd.DataFrame({'A':[1,3,2,8,9],'B':[3,4,6,8,12]});r=paired_tests(df,['A','B']).iloc[0]
        self.assertAlmostEqual(r['t_p'],stats.ttest_1samp(df.B-df.A,0).pvalue);self.assertEqual(r['평균차'],2)
    def test_anova_independent_sum_of_squares(self):
        x=np.array([[1,4,3],[2,5,6],[4,3,8],[5,7,6],[7,8,9]],float)
        centered=x-x.mean(axis=1,keepdims=True);effect=centered.mean(axis=0);residual=centered-effect
        expected=(len(x)*np.sum(effect**2)/2)/(np.sum(residual**2)/8)
        r=rm_anova(pd.DataFrame(x));self.assertAlmostEqual(r['F'],expected)
        self.assertGreaterEqual(r['GG_epsilon'],.5);self.assertLessEqual(r['GG_epsilon'],1)
    def test_multi_code_uniqueness(self):
        self.assertEqual(split_codes('어미 조정|어미 조정|내용어 조정'),['어미 조정','내용어 조정'])
    def test_rank_biserial_zeros(self):
        self.assertEqual(rank_biserial(pd.Series([0,0,0])),0)
        self.assertEqual(rank_biserial(pd.Series([1,2,3])),1)
    def test_paper_data_contract(self):
        f=pd.read_csv(ROOT/'data/text_metrics.csv')
        allowed={'participant_id','task_id','genre','version','characters','eojeols','sentences',
            'mean_sentence_length','mattr20','predicates_per_sentence','manual_errors_per_100_eojeols',
            'manual_error_count','mattr_short_ttr'}
        self.assertEqual(set(f),allowed);self.assertEqual(len(f),252)
        self.assertEqual(f.participant_id.nunique(),28);self.assertEqual(f.task_id.nunique(),84)
        self.assertFalse(f.duplicated(['task_id','version']).any())
if __name__=='__main__':unittest.main(verbosity=2)

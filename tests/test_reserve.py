"""Synthetic checks for the reserve walk; no Lending Club data required."""
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

notebook = json.loads((Path(__file__).resolve().parents[1] / 'python/04_reserve.ipynb').read_text(encoding='utf8'))
source = ''.join(notebook['cells'][7]['source']).split('\ncphd, cphp = fit_hazards(df)')[0]
namespace = {'np': np, 'pd': pd}
exec(source, namespace)

class Model:
    def __init__(self, survival):
        self.baseline_survival_ = pd.DataFrame({'baseline survival': survival}, index=[0, 36, 60, 72])
    def predict_partial_hazard(self, x):
        return pd.Series(np.ones(len(x)), index=x.index)

class ReserveTests(unittest.TestCase):
    def test_last_month_and_overdue(self):
        book = pd.DataFrame({ 'int_rate':[0.,0.,0.], 'dti':[10.]*3, 'fico':[700.]*3,
            'annual_inc':[50000.]*3, 'grade_num':[2]*3, 'term':[36]*3,
            'loan_amnt':[3600.]*3, 'out_prncp':[100.,200.,0.], 'age':[35.,37.,37.],
            'delq90':[0]*3, 'loan_status':['Current']*3 })
        default = Model([1., .5, .4, .3]); prepay = Model([1., 1., 1., 1.])
        result = namespace['ecl'](book, default, {36:prepay, 60:prepay}, .9)
        self.assertGreater(result.iloc[0].ecl, 0)
        self.assertAlmostEqual(result.iloc[1].ecl, 180.)
        self.assertEqual(result.iloc[2].ecl, 0.)
        self.assertTrue(result.rem_pd.between(0,1).all())
        self.assertTrue((result.ecl <= .9 * book.out_prncp + 1e-8).all())

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from survival_data import add_survival_events

class EventTests(unittest.TestCase):
    def test_censoring_and_early_payoff(self):
        df = pd.DataFrame({
            'loan_status': ['Current', 'Charged Off', 'Fully Paid', 'Fully Paid', 'Charged Off'],
            'issue_d': pd.to_datetime(['2016-01-01'] * 5),
            'last_pymnt_d': pd.to_datetime(['2017-01-01', '2017-02-01', '2017-01-01', '2018-12-01', None]),
            'term': [36] * 5,
        })
        missing = add_survival_events(df, pd.Timestamp('2019-03-01'))
        self.assertEqual(missing, 1)
        self.assertEqual(df.prepaid.tolist(), [0, 0, 1, 0, 0])
        self.assertEqual(df.default_event.tolist(), [0, 1, 0, 0, 1])
        self.assertAlmostEqual(df.months_obs.iloc[0], round((pd.Timestamp('2019-03-01')-pd.Timestamp('2016-01-01')).days/30, 1))
        self.assertTrue(pd.isna(df.months_obs.iloc[-1]))

if __name__ == '__main__': unittest.main()

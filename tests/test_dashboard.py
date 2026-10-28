"""Check dashboard and Python reserve calculations against the exported model."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from test_reserve import namespace

ROOT = Path(__file__).resolve().parents[1]

class PayloadModel:
    def __init__(self, payload):
        self.p = payload
        self.baseline_survival_ = pd.DataFrame({'baseline survival': [v for _, v in payload['base']]}, index=[t for t, _ in payload['base']])
    def predict_partial_hazard(self, frame):
        return np.exp(sum(self.p['coef'][key] * (frame[key] - self.p['means'][key]) for key in self.p['coef']))

class DashboardParity(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js is needed for dashboard parity')
    def test_calculator_matches_python(self):
        payload = json.loads((ROOT / 'output/dashboard_model.json').read_text(encoding='utf8'))
        models = payload['models']
        default = PayloadModel(models['default'])
        prepay = {36: PayloadModel(models['prepayment_36']), 60: PayloadModel(models['prepayment_60'])}
        html = (ROOT / 'index.html').read_text(encoding='utf8')
        embedded = html.split('<script id="dashboard-model" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(embedded), payload)
        js_functions = html[html.index('function s0('):html.index('function colorFor(')]
        for term, age, balance in [(36, 0, 15000), (36, 35, 500), (36, 36, 500), (60, 24, 8000)]:
            state = {'grade_num': 3, 'int_rate': 14, 'age': age, 'fico': 690, 'annual_inc': 65000, 'loan_amnt': 15000, 'balance': balance, 'dti': 18, 'term': term}
            js = 'const COXD=' + json.dumps(models['default']) + ';const COXP=' + json.dumps({36: models['prepayment_36'], 60: models['prepayment_60']}) + ';const LGD_CONST=' + str(payload['lgd']) + ';' + js_functions + ';state=' + json.dumps(state) + ';console.log(JSON.stringify(compute()));'
            result = json.loads(subprocess.check_output(['node', '-e', js], text=True))
            row = {**state, 'int_rate': .14, 'out_prncp': balance, 'delq90': 0, 'loan_status': 'Current'}
            py = namespace['ecl'](pd.DataFrame([row]), default, prepay, payload['lgd'], use_status=False).iloc[0]
            self.assertAlmostEqual(py.ecl, result['el'], places=6)
            self.assertAlmostEqual(py.rem_pd, result['pd'], places=9)

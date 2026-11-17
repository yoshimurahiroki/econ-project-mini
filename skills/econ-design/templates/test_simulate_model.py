import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('simulate_model', Path(__file__).with_name('simulate_model.py'))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class ModelDecisionTests(unittest.TestCase):
    def parameters(self, **changes):
        return {**{k: values[0] for k, values in model.RANGES.items()}, **changes}

    def test_flat_pay_implements_zero_effort_and_avoids_measurement_cost(self):
        p = self.parameters(K=10.)
        b, q = model.rung_multitask(p)
        result = model.decide(p, b, q)
        self.assertEqual(result['action'], 'flat pay')
        self.assertEqual(result['b'], 0.)
        self.assertEqual(result['actor_response']['effort'], [0., 0.])
        self.assertEqual(result['objective'], 0.)
        self.assertEqual(result['objective_loss'], 0.)

    def test_scaled_technology_and_payroll_match_the_same_optimum(self):
        p = self.parameters(f1=3., g1=2., K=0.)
        b, q = model.rung_single_task(p)
        self.assertAlmostEqual(b, 6. / 4.05)
        self.assertTrue(model.optimum_verified(p, b, q))
        result = model.decide(p, b, q)
        response = result['actor_response']
        self.assertAlmostEqual(response['effort'][0], b * 2.)
        self.assertAlmostEqual(response['fixed_pay'] + b * response['expected_kpi'], response['expected_pay'])
        self.assertAlmostEqual(response['agent_certainty_equivalent'], 0.)
        self.assertAlmostEqual(result['objective'], response['principal_payoff'])
        self.assertGreater(result['objective'], model.surplus(q, b * .5))

    def test_rate_changes_and_reproducible_decisions_survive_the_saved_report(self):
        p = self.parameters(r=1., sigma2=.5, g2=.5, cap=.3, K=0.)
        with tempfile.TemporaryDirectory() as folder, patch.dict(model.RANGES, {k: [v] for k, v in p.items()}, clear=True):
            path = Path(folder) / 'result.json'
            with contextlib.redirect_stdout(io.StringIO()):
                model.main(path)
            result = json.loads(path.read_text())
        self.assertEqual(result['ladder'][1]['decisions_changed_vs_previous'], 1.)
        self.assertEqual(result['ladder'][2]['decisions_changed_vs_previous'], 1.)
        for rung in result['ladder']:
            row = rung['cases'][0]
            self.assertEqual(row['action'], 'KPI bonus')
            self.assertEqual(row['parameters']['K'], 0.)
            self.assertEqual(row['actor_response'], model.outcomes(row['parameters'], row['b']))
            self.assertEqual(row['objective_loss'], 0.)


if __name__ == '__main__':
    unittest.main()

"""Exercise the research CLI using a small calculation and its consumers."""
import json
import importlib.metadata
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).with_name('research.py').resolve()


class ResearchPipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'data.txt').write_text('4')
        (self.root / 'spec.txt').write_text('3')
        (self.root / 'labels.txt').write_text('Result: {{stat:estimate}} units\n')
        (self.root / 'estimate.py').write_text("""import json, pathlib, sys
x = int(pathlib.Path(sys.argv[1]).read_text())
y = int(pathlib.Path(sys.argv[2]).read_text())
pathlib.Path(sys.argv[3]).write_text(json.dumps({'estimate': {'value': x * y, 'unit': 'units'}}))
""")
        self.spec = {'pipeline': 'demo', 'stages': [
            {'id': 'estimate', 'inputs': ['data.txt', 'spec.txt', 'estimate.py'], 'depends': {},
             'outputs': {'result': 'result.json'}, 'argv': [sys.executable, '{root}/estimate.py', '{root}/data.txt', '{root}/spec.txt', '{out:result}']},
            {'id': 'paper', 'inputs': ['labels.txt'], 'depends': {'estimate': ['result']}, 'outputs': {'text': 'paper.txt'},
             'render': {'template': 'labels.txt', 'output': 'text', 'statistics': {'estimate': {'stage': 'estimate', 'output': 'result', 'key': ['estimate'], 'unit': 'units', 'format': '.2f'}}}},
            {'id': 'independent', 'inputs': ['data.txt'], 'depends': {}, 'outputs': {'copy': 'copy.txt'},
             'argv': [sys.executable, '-c', 'import pathlib,sys; pathlib.Path(sys.argv[2]).write_text(pathlib.Path(sys.argv[1]).read_text())', '{root}/data.txt', '{out:copy}']},
        ]}
        self.write_spec()

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self):
        (self.root / 'manifest.json').write_text(json.dumps(self.spec))

    def cli(self, code=0, profile=None):
        args = [sys.executable, str(RUNNER), '--root', str(self.root)]
        if profile is not None:
            args += ['--profile', profile]
        p = subprocess.run(args + ['manifest.json'], text=True, capture_output=True)
        self.assertEqual(p.returncode, code, p.stderr + p.stdout)
        return json.loads(p.stdout) if p.stdout else p.stderr


    def test_failed_replacement_preserves_previous_and_blocks_descendant(self):
        first = self.cli()
        prior = self.root / first['estimate']['outputs']['result']
        old = prior.read_bytes()
        (self.root / 'estimate.py').write_text('raise SystemExit(7)\n')
        failed = self.cli(1)
        self.assertEqual(failed['estimate']['status'], 'failed')
        self.assertEqual(failed['paper']['status'], 'blocked')
        self.assertEqual(failed['independent']['status'], 'reused')
        self.assertEqual(prior.read_bytes(), old)
        tasks = json.loads((self.root / '.agents/state/team.json').read_text())['tasks']
        self.assertEqual(tasks[failed['estimate']['task']]['status'], 'failed')
        self.assertEqual(tasks[failed['estimate']['task']]['outputs']['research:execution']['value']['returncode'], 7)

    def test_saved_definitions_and_numbers_reach_section_consumers(self):
        saved = {'statistics': {'effect': {'value': 2.5, 'unit': 'hours_per_week'}},
                 'metadata': {'comparison': 'offer versus no offer', 'period': 'one year',
                              'equilibrium': r'q_i = (a-c)/(3b)',
                              'notation': 'Literal marker: {{stat:effect}}'}}
        source = self.root / 'saved.json'
        source.write_text(json.dumps(saved))
        source_bytes = source.read_bytes()
        self.spec['stages'][0] = {
            'id': 'saved', 'inputs': ['saved.json'], 'depends': {},
            'outputs': {'result': 'result.json'},
            'argv': [sys.executable, '-c', 'import shutil,sys; shutil.copyfile(sys.argv[1],sys.argv[2])',
                     '{root}/saved.json', '{out:result}']}
        template = ('{{definition:comparison}}: {{stat:effect}} hours/week over {{definition:period}}.\n'
                    '{{definition:equilibrium}}\n{{definition:notation}}\n')
        (self.root / 'labels.txt').write_text(template)
        paper = self.spec['stages'][1]
        paper['depends'] = {'saved': ['result']}
        paper['render']['statistics'] = {'effect': {'stage': 'saved', 'output': 'result',
                                                   'key': ['statistics', 'effect'],
                                                   'unit': 'hours_per_week', 'format': '.1f'}}
        paper['render']['definitions'] = {
            key: {'stage': 'saved', 'output': 'result', 'key': ['metadata', key]}
            for key in saved['metadata']}
        self.write_spec()
        first = self.cli()
        output = self.root / first['paper']['outputs']['text']
        self.assertEqual(output.read_text(),
                         'offer versus no offer: 2.5 hours/week over one year.\n'
                         'q_i = (a-c)/(3b)\nLiteral marker: {{stat:effect}}\n')
        (self.root / 'labels.txt').write_text('# Results\n' + template)
        updated = self.cli()
        self.assertEqual(updated['saved']['status'], 'reused')
        self.assertEqual(updated['independent']['status'], 'reused')
        self.assertEqual(updated['paper']['status'], 'executed')
        self.assertEqual(source.read_bytes(), source_bytes)
        self.assertEqual(output.read_text().splitlines()[0], 'offer versus no offer: 2.5 hours/week over one year.')
        paper['render']['definitions']['comparison']['key'] = ['statistics', 'effect']
        self.write_spec()
        failed = self.cli(1)
        self.assertEqual(failed['paper']['status'], 'failed')
        self.assertIn('saved nonempty text', failed['paper']['error'])

    def test_requirement_pins_class_api_and_changed_environment(self):
        version = importlib.metadata.version('packaging')
        (self.root / 'requirements.txt').write_text('packaging==' + version + '\n')
        stage = self.spec['stages'][0]
        stage['inputs'].append('requirements.txt')
        stage['runtime'] = {'language': 'python', 'probe_argv': [sys.executable],
                            'requirements': ['requirements.txt'],
                            'apis': [{'package': 'packaging',
                                      'symbol': 'packaging.specifiers.SpecifierSet.contains',
                                      'positional': 2, 'keywords': ['prereleases']}]}
        self.write_spec()
        first = self.cli()
        self.assertEqual(first['estimate']['status'], 'executed')
        saved = json.loads((self.root / '.agents/state/team.json').read_text())['tasks'][first['estimate']['task']]
        runtime = saved['outputs']['research:execution']['value']['runtime']
        self.assertEqual(runtime['observed']['packages']['packaging']['version'], version)
        self.assertIn('prereleases', runtime['observed']['apis'][0]['signature'])
        self.assertIn('requirements.txt', runtime['files'])
        self.assertEqual(self.cli()['estimate']['status'], 'reused')
        (self.root / 'requirements.txt').write_text('packaging==0.0.0\n')
        blocked = self.cli(1)
        self.assertEqual(blocked['estimate']['status'], 'blocked')
        self.assertIn('version mismatch', blocked['estimate']['reason'])
        self.assertEqual(blocked['paper']['status'], 'blocked')
        self.assertEqual(blocked['independent']['status'], 'reused')
        stage['runtime']['packages'] = {'packaging': version}
        self.write_spec()
        self.assertIn('Conflicting runtime versions', self.cli(2))

    def test_numerical_contracts_select_and_execute(self):
        project = RUNNER.parent.parent
        selector = project / 'skills/econ-data/scripts/research_causal.py'
        cases = [
            ('MC-finite-correlated-equilibrium', 'correlated_equilibrium', 'equilibrium',
             {'payoffs': [[[1, -1], [-1, 1]], [[-1, 1], [1, -1]]]}),
            ('MC-finite-tu-shapley-core', 'tu_shapley_core', 'allocation',
             {'values': [0, 1, 2, 5, 0, 3, 4, 8]}),
            ('MC-interbank-clearing', 'interbank_clearing', 'equilibrium',
             {'liabilities': [[0, 6], [3, 0]], 'outside_liabilities': [4, 3], 'external_assets': [1, 2]}),
            ('MC-multitask-incentives', 'multitask_incentives', 'policy_value',
             {'b': 1, 'm': 2, 'rho': .25, 'a': .5, 'vq': 2, 'vqly': 3}),
        ]
        results = {}
        for contract, model, target, inputs in cases:
            with self.subTest(model=model):
                request = {'question': 'Calculate the supplied finite model.',
                    'estimand': 'The equation-defined allocation and payoffs.',
                    'identification': 'Hold the supplied primitives fixed.',
                    'design': 'structural', 'outcome_scale': 'payoff', 'data_structure': 'finite_model',
                    'treatment_pattern': 'none', 'dependence': 'deterministic',
                    'model_contract_id': contract, 'target': {'kind': target},
                    'adopted_specification': {'model': model, 'inputs': inputs, 'unit': 'payoff units'}}
                request_path = self.root / (model+'-selection.json')
                selected_path = self.root / (model+'-selected.json')
                request_path.write_text(json.dumps(request))
                selected_run = subprocess.run([sys.executable, str(selector), 'select', str(request_path),
                    '--output', str(selected_path)], cwd=project, text=True, capture_output=True)
                self.assertEqual(selected_run.returncode, 0, selected_run.stderr)
                selected = json.loads(selected_path.read_text())
                self.assertEqual(selected['status'], 'selected')
                self.assertFalse(selected['executed'])
                self.assertEqual(selected['method'], model)
                implementation = selected['method_selection']['official_implementation']
                execution = implementation['execution_specification']
                self.assertEqual(execution['status'], 'specified')
                self.assertEqual(execution['specification'], request['adopted_specification'])
                self.assertFalse(execution['adoption_required'])
                spec_path = self.root / (model+'-spec.json')
                result_path = self.root / (model+'-result.json')
                spec_path.write_text(json.dumps(execution['specification']))
                argv = [sys.executable if i == 0 else str(spec_path) if arg == 'SPEC.json'
                        else str(result_path) if arg == 'RESULT.json' else arg
                        for i, arg in enumerate(execution['command'])]
                completed = subprocess.run(argv, cwd=project, text=True, capture_output=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                saved = json.loads(result_path.read_text())
                self.assertEqual(saved['model_contract'], contract)
                self.assertEqual(saved['specification'], execution['specification'])
                self.assertEqual(saved['unit'], 'payoff units')
                results[model] = saved['fullresults']

        # Matching pennies has four equally likely recommendations and zero gains from deviation.
        ce = results['correlated_equilibrium']
        for row in ce['probabilities']:
            for probability in row:
                self.assertAlmostEqual(probability, .25, places=10)
        self.assertEqual(ce['payoffs'], [0., 0.])
        self.assertLessEqual(ce['mass_error'], 1e-10)
        self.assertTrue(all(abs(row['slack']) <= 1e-10 for row in ce['obedience']))
        # The six player orders yield these marginal-contribution averages.
        shapley = results['tu_shapley_core']
        self.assertEqual(shapley['allocation'], ['8/3', '11/3', '5/3'])
        self.assertEqual(shapley['efficiency_residual'], '0')
        self.assertTrue(shapley['in_core'])
        # p1=1+p2/2 and p2=2+3*p1/5; both payments are below nominal debt.
        clearing = results['interbank_clearing']
        for actual, expected in zip(clearing['payments'], (20/7, 26/7)):
            self.assertAlmostEqual(actual, expected, places=9)
        self.assertLessEqual(clearing['fixed_point_residual'], 1e-11)
        self.assertAlmostEqual(sum(clearing['outside_payments'])+sum(clearing['equity']), 3, places=9)
        # x+y/4=1 and y+x/4=2 define the interior effort choice.
        effort = results['multitask_incentives']
        for name, expected in [('x', 8/15), ('y', 28/15), ('principal_payoff', 169/30), ('agent_payoff', 79/30)]:
            self.assertAlmostEqual(effort[name], expected, places=10)
        self.assertLessEqual(effort['kkt_residual'], 1e-10)

        # A partial adopted input remains a specification request and executes no model.
        del request['adopted_specification']['inputs']['m']
        request_path.write_text(json.dumps(request))
        partial = subprocess.run([sys.executable, str(selector), 'select', str(request_path),
            '--output', str(selected_path)], cwd=project, text=True, capture_output=True)
        self.assertEqual(partial.returncode, 0, partial.stderr)
        execution = json.loads(selected_path.read_text())['method_selection']['official_implementation']['execution_specification']
        self.assertEqual(execution['status'], 'inputs_required')
        self.assertEqual(execution['missing_fields'], ['inputs.m'])


if __name__ == '__main__':
    unittest.main()

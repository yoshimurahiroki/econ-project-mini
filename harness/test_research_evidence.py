import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paragraph
import research_evidence as evidence
import research_artifacts as artifacts
import research_meetings as meetings


def selection(text, quote):
    start = text.index(quote)
    return {'start': start, 'end': start + len(quote), 'quote': quote}


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paper = 'In 1990 the estimate was 1.25 hours. Euler: c = beta * future.'
        self.source = 'The 1990 sample covers households.'
        self.code = 'residual = c - beta * future\n'
        self.write('spec.json', json.dumps({'beta': 0.96}))
        spec_hash = self.ref('spec.json')['sha256']
        self.result = {'sample': 'households', 'scenario': 'baseline', 'model': 'Euler', 'specification': spec_hash,
                       'stats': {'estimate': {'value': 1.249, 'unit': 'hours'},
                                 'beta': {'value': 0.96, 'unit': 'dimensionless'}}, 'residual': 1e-10}
        self.write('paper.txt', self.paper)
        self.write('source.txt', self.source)
        self.write('code.py', self.code)
        self.write('result.json', json.dumps(self.result))
        self.identities = {'sample': 'households', 'scenario': 'baseline', 'model': 'Euler', 'specification': spec_hash}
        keys = {name: [name] for name in self.identities}
        judgment = {'reviewer': 'native-owner', 'decision': 'supported', 'rationale': 'Compared the exact passages.'}
        self.contract = {
            'manuscript': self.ref('paper.txt'), 'adopted': self.identities,
            'sources': {'original': {**self.ref('source.txt'), 'metadata': {'identities': {'sample': 'households'}}}},
            'claims': [{'id': 'sample', 'target': selection(self.paper, 'In 1990'),
                        'sources': [{'id': 'original', 'span': selection(self.source, '1990 sample covers households')}],
                        'judgment': judgment}],
            'numbers': [{'id': 'estimate', 'target': selection(self.paper, '1.25'),
                         'unit_target': selection(self.paper, 'hours'), 'unit_display': 'hours',
                         'result': {**self.ref('result.json'), 'key': ['stats', 'estimate'],
                                    'unit': 'hours', 'format': '.2f', 'identity_keys': keys}}],
            'models': [{'id': 'euler', 'equation': selection(self.paper, 'c = beta * future'),
                        'code': {**self.ref('code.py'), 'span': selection(self.code, self.code.strip())},
                        'result': {**self.ref('result.json'), 'residual_key': ['residual'],
                                   'tolerance': 1e-8, 'identity_keys': keys}, 'judgment': judgment}],
            'coverage': {'spans': [selection(self.paper, self.paper)],
                         'accounted': [{'target': selection(self.paper, '1990'), 'claim': 'sample', 'kind': 'source'}]}}

    def write(self, name, data):
        (self.root / name).write_text(data, encoding='utf-8')

    def ref(self, name):
        return {'path': name, 'sha256': paragraph.sha((self.root / name).read_bytes())}

    def result_change(self, mutate):
        result = copy.deepcopy(self.result)
        mutate(result)
        self.write('result.json', json.dumps(result))
        for key in ('numbers', 'models'):
            self.contract[key][0]['result'].update(self.ref('result.json'))


    def test_changed_number_sample_scenario_and_unit(self):
        for field, value, message in [('value', 1.4, 'formatted statistic'), ('unit', 'days', 'unit differs')]:
            with self.subTest(field=field):
                self.result_change(lambda r: r['stats']['estimate'].__setitem__(field, value))
                with self.assertRaisesRegex(ValueError, message):
                    evidence.bind(self.contract, self.root)
        for field in ('sample', 'scenario', 'model', 'specification'):
            with self.subTest(field=field):
                self.result_change(lambda r: r.__setitem__(field, 'different'))
                with self.assertRaisesRegex(ValueError, 'identity differs'):
                    evidence.bind(self.contract, self.root)
        self.result_change(lambda r: r['stats']['estimate'].__setitem__('value', float('nan')))
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            evidence.bind(self.contract, self.root)
        self.result_change(lambda r: r['stats'].pop('estimate'))
        with self.assertRaisesRegex(ValueError, 'missing JSON key'):
            evidence.bind(self.contract, self.root)

    def test_registration_preserves_saved_inference_without_derivation(self):
        saved = {'method': 'official-example', 'coefficients': {'effect': 0.0, 'omitted': None},
                 'standard_errors': {'effect': 0.25, 'omitted': None},
                 'covariance': [[0.0625, None], [None, None]],
                 'inference': {'reference_distribution': 'normal'}}
        self.write('saved.json', json.dumps(saved))
        spec = {'sources': [{'id': 'fit', 'result': 'saved.json', 'code': 'code.py',
                             'expected_hashes': {'code': self.ref('code.py')['sha256']},
                             'coefficient_units': {'effect': 'hours'}}], 'bindings': {}}
        registry = artifacts.normalize(self.root, spec)
        self.assertEqual(set(registry['statistics']), {'fit.coefficient.effect', 'fit.standard_error.effect'})
        self.assertEqual(registry['records']['fit']['source_result'], saved)
        saved['inference'].update(confidence_level=0.90, confidence_intervals={'effect': [-0.41, 0.41]},
                                  p_values={'effect': 1.0, 'omitted': None})
        self.write('saved.json', json.dumps(saved))
        registry = artifacts.normalize(self.root, spec)
        self.assertEqual(registry['statistics']['fit.confidence_lower.effect']['value'], -0.41)
        self.assertNotIn('fit.confidence_95_lower.effect', registry['statistics'])
        self.assertEqual(registry['items']['fit-coefficients']['metadata']['confidence_level'], 0.90)

    def test_comparison_retains_definitions_within_one_display(self):
        definitions = {'estimand': 'ATT(g,t)', 'population': 'eligible people', 'sample': 'sample-v1',
                       'period': [2020, 2022], 'weights': None, 'base_period': 'universal'}
        registry = {'schema': 'research-artifact-registry-v1', 'statistics': {}, 'records': {
            'a': {'source_result': dict(definitions, cohort=2021)},
            'b': {'source_result': dict(definitions, cohort=2022)}}}
        registry['items'] = artifacts.prepare_gallery_items(registry, [{
            'id': 'effects', 'title': 'Saved effects', 'kind': 'coefficient', 'result_ids': ['a', 'b'],
            'columns': [{'key': 'estimate', 'label': 'Effect', 'unit': 'hours'}],
            'rows': [{'result_id': 'a', 'estimate': 1.0}, {'result_id': 'b', 'estimate': 2.0}],
            'display': {'plot_type': 'table'}}])
        self.write('gallery.json', json.dumps(registry))
        compared = artifacts.gallery_compare(self.root, 'gallery.json', ['effects'])
        self.assertEqual(compared['result_definition_differences']['cohort'], {'effects/a': 2021, 'effects/b': 2022})
        self.assertEqual(compared['comparison_contract']['status'], 'different_definitions')
        self.assertEqual(compared['comparison_contract']['unrecorded_fields'], {})
        self.assertFalse(compared['comparison_contract']['analysis_executed'])
        self.assertEqual(compared['items'][0]['source_reference']['keys'], ['items', 'effects'])

    def test_result_materials_place_saved_exhibits_and_keep_summary(self):
        root = Path(__file__).resolve().parent.parent
        entries = [{'id': key, 'title': key, 'kind': kind, 'result_ids': [key], 'files': [],
                    'metadata': {}, 'rows': [], 'columns': [], 'interpretation': 'Saved interpretation'}
                   for key, kind in [('main', 'coefficient'), ('sample', 'descriptive'), ('event', 'event_study')]]
        entries[0]['findings'] = 'Saved finding'
        output = self.root / 'materials'
        meetings.create_bundle(root, output, entries, title='Results', kind='results',
                               project_view={'research_question': 'Effect on hours?', 'results_summary': 'Saved main result'})
        meeting, bodies, _ = meetings.load_meeting(output)
        ids = [row['id'] for row in meeting['sections']]
        self.assertLess(ids.index('result-2'), ids.index('results'))
        self.assertLess(ids.index('results'), ids.index('result-1'))
        self.assertLess(ids.index('result-1'), ids.index('result-3'))
        self.assertEqual(bodies['results'], 'Saved main result')
        self.assertEqual(bodies['findings'], 'main: Saved finding')
        self.assertEqual(meeting['artifacts']['main']['rows'], entries[0]['rows'])

    def test_saved_regression_presentation_survives_edit_and_native_export(self):
        definitions = {'estimand': 'linear projection', 'population': 'synthetic example',
                       'sample': 'saved-sample', 'period': '2024', 'weights': None, 'n': 40}
        registry = {'schema': 'research-artifact-registry-v1', 'statistics': {}, 'records': {
            'fit': {'source_result': definitions, 'references': {'data': {'path': 'unavailable-raw.csv'}}}}}
        rows = [{'result_id': 'fit', 'outcome': outcome, 'term': 'treatment', 'estimate': estimate,
                 'se': 0.25, 'ci_low': estimate - 0.4, 'ci_high': estimate + 0.4, 'p_value': p}
                for outcome, estimate, p in [('hours', 0.0, 1.0), ('earnings', 2.0, 0.003)]]
        registry['items'] = artifacts.prepare_gallery_items(registry, [{
            'id': 'regression', 'title': 'Saved models', 'kind': 'table', 'result_ids': ['fit'],
            'columns': [{'key': key, 'label': key, 'unit': ''} for key in rows[0] if key != 'result_id'],
            'rows': rows, 'metadata': {'table_type': 'regression'},
            'display': {'plot_type': 'table', 'outcome_column': 'outcome', 'show_ci': True,
                        'term_labels': {'treatment': 'Treatment'}, 'statistic_rows': [{'field': 'n', 'label': 'N'}]}}])
        self.write('gallery.json', json.dumps(registry))
        revision = artifacts.state.content_hash(registry['items']['regression'])
        artifacts.edit_gallery_item(self.root, 'gallery.json', 'regression',
                                    {'display': {'title': 'Main results'}}, expected_revision=revision)
        saved = json.loads((self.root / 'gallery.json').read_text())
        self.assertEqual(saved['items']['regression']['rows'], rows)
        entries = artifacts.gallery_items(self.root, 'gallery.json')
        self.assertEqual(entries[0]['presentation']['body'][0]['cells'], ['0.000', '2.000'])
        self.assertEqual(entries[0]['presentation']['body'][1]['cells'], ['(0.250)', '(0.250)'])
        template_root = Path(__file__).resolve().parent.parent / 'tex' / 'slides'
        target = self.root / 'tex' / 'slides'
        target.mkdir(parents=True)
        (target / 'meeting_templates.json').write_bytes((template_root / 'meeting_templates.json').read_bytes())
        bundle = self.root / 'meeting'
        meetings.create_bundle(self.root, bundle, entries, title='Results', kind='results')
        native = meetings.native_slides_requests(bundle)
        cells = [request['insertText']['text'] for request in native['requests']
                 if 'insertText' in request and 'cellLocation' in request['insertText']]
        self.assertIn('0.000', cells)
        self.assertIn('(0.250)', cells)
        self.assertIn('[1.600, 2.400]', cells)
        self.assertEqual(native['images'], [])
        self.assertTrue(native['new_independent_edition'])


if __name__ == '__main__':
    unittest.main()

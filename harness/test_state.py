"""Bounded, offline state-contract regressions using disposable local fixtures."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('team_state', Path(__file__).with_name('state.py'))
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)

class TeamStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ['input', 'artifact']:
            (self.root / name).write_text(name)
        self.cli('init')

    def cli(self, *args):
        with patch('sys.argv', ['team_state', '--root', str(self.root), *args]), contextlib.redirect_stdout(io.StringIO()) as out:
            h.main()
        return json.loads(out.getvalue())

    def state(self):
        return json.loads((self.root / '.agents/state/team.json').read_text())


    def release(self, task, *args):
        """Supply explicit synthetic user evidence in this offline fixture."""
        hold = args[args.index('--hold-id') + 1]
        evidence = self.root / ('release-' + hold.replace(':', '-') + '.json')
        evidence.write_text(json.dumps({
            'source': 'user', 'message_id': 'fixture-release-' + hold,
            'text': 'Release the named hold for this test fixture.',
            'source_task_id': task, 'hold_id': hold,
        }))
        return self.cli('release-hold', task, *args, '--user-release', evidence.name)

    def task(self, key='T'):
        return self.state()['tasks'][key]

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value, ensure_ascii=False))
        return name

    def project_fixture(self, repository='acme/research', numbers=(11, 12), project_id=None, decisions=None):
        """Synthetic scientific inputs, independent of any real research result."""
        self.write_json('context.json', {'request_refs': [], 'active_instruction_refs': [],
            'goal_and_constraints': 'Exercise project integration with synthetic source text.',
            'adopted_decisions': decisions if decisions is not None else [
                {'decision_id': 'D1', 'version': 1, 'choice': 'Keep saved results',
                 'reason': 'The display operation uses their existing values.', 'switch_condition': 'A changed adopted input'}]})
        self.add(name='CASE', kind='answer', *['--task-context', 'context.json'])
        for key in ('T', 'U'):
            self.add('--parent', 'CASE', '--required-output', json.dumps({'role': 'result', 'kind': 'object', 'target': key + '-result'}),
                     name=key, kind='answer')
        module = h._project_argument()
        sources = {'S': {'text': 'Synthetic fixture: source A and source B are independent inputs.'}}
        source_hash = module.sha256(sources['S']['text'])
        reference = {'source_id': 'S', 'start': 0, 'end': len(sources['S']['text']),
                     'quote': sources['S']['text'], 'source_sha256': source_hash}
        nodes = []
        for index, key in enumerate(('C', 'A', 'B')):
            nodes.append({'node_id': key, 'parent_id': None if key == 'C' else 'C',
                'child_ids': ['A', 'B'] if key == 'C' else [], 'claim': 'Synthetic claim ' + key,
                'question': 'What does the synthetic source establish for ' + key + '?',
                'next_questions': [{'question': 'Which input supports the claim?', 'answered_by': ['A', 'B']}] if key == 'C' else [],
                'logical_role': 'evidence', 'inference_form': 'inductive' if key == 'C' else 'atomic',
                'abstraction_level': 0 if key == 'C' else 1, 'scope': {}, 'source_refs': [] if key == 'C' else [reference],
                'section_id': 'fixture', 'paragraph_ids': [], 'reasoning': 'Combine the two fixture inputs.',
                'order': {'basis': 'structure', 'position': index, 'rationale': 'Fixture hierarchy'}})
        nodes[0]['integration'] = {'member_ids': ['A', 'B'], 'conclusion': nodes[0]['claim'],
                                  'common_property': 'Synthetic source inputs', 'meaning': 'Both inputs belong to the fixture.'}
        graph = {'schema_version': 1, 'version': '1', 'central_question': nodes[0]['question'], 'central_answer': nodes[0]['claim'],
            'root_ids': ['C'], 'nodes': nodes, 'dependencies': [], 'source_ids': ['S'], 'source_manifest': {'S': source_hash},
            'groups': [{'group_id': 'G', 'parent_id': 'C', 'member_ids': ['A', 'B'], 'classification_basis': 'Fixture input',
                        'logical_role': 'evidence', 'inference_form': 'inductive',
                        'order': {'basis': 'structure', 'ordered_ids': ['A', 'B'], 'rationale': 'Input order'}}]}
        self.write_json('argument-v1.json', graph)
        self.write_json('sources.json', sources)
        definition = {'schema_version': 1, 'argument': {'path': 'argument-v1.json', 'sources_path': 'sources.json'},
            'resources': {}, 'work': [{'task_id': key, 'node_ids': [node], 'duration_hours': 1, 'resources': {},
                                     'issue_number': number, 'custom_work_field': 'retained'}
                                    for key, node, number in zip(('T', 'U'), ('A', 'B'), numbers)],
            'data_date_hour': 0, 'time_unit': 'hours', 'origin': 'relative:synthetic-demo',
            'target_finish_hour': 10, 'approved_finish_hour': 12, 'decision_rights': {},
            'github': {'repository': repository, 'issue_template': 'research-task.yml'}, 'custom_project_field': {'keep': True},
            'synthetic_fixture': True}
        definition['work'][0]['artifact_ids'] = {'results': ['R1'], 'figures': ['F1'], 'documents': ['DOC1']}
        if project_id:
            definition['github']['project_id'] = project_id
        self.write_json('plan-v1.json', definition)
        self.cli('project-bind', 'CASE', '--definition', 'plan-v1.json')
        return definition, graph

    def github_snapshot(self):
        issues = [{'number': number, 'title': title, 'html_url': f'https://github.com/acme/research/issues/{number}',
                   'state': state, 'assignees': [{'login': 'scientist'}], 'blocked_by': [], 'blocking': [],
                   'body': '### Priority\n\nP2\n\n### Due date\n\n2026-11-10\n\n### Classification\n\nanalysis\n\n### Progress\n\nIn progress',
                   'updated_at': '2026-11-05T12:00:00Z', 'closed_at': '2026-11-05T12:00:00Z' if state == 'closed' else None}
                  for number, title, state in ((11, 'Inspect saved result', 'closed'), (12, 'Explain result', 'open'))]
        return {'schema_version': 1, 'repository': 'acme/research', 'source': 'synthetic connector fixture',
                'fetched_at': '2026-11-05T12:01:00Z', 'issues': issues, 'project': None}

    def test_github_summary_is_derived_and_keeps_execution_receipts_separate(self):
        self.project_fixture()
        data = self.github_snapshot()
        self.write_json('github.json', data)
        store = self.root / '.agents/state/team.json'
        original = store.read_bytes()
        summary = self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary', '--owner', 'scientist',
                           '--github', 'github.json', '--save', 'summary.json')
        self.assertEqual(original, store.read_bytes())
        self.assertEqual(summary, json.loads((self.root / 'summary.json').read_text()))
        self.assertEqual([11], [row['number'] for row in summary['completed']])
        self.assertEqual([12], [row['number'] for row in summary['active']])
        self.assertEqual(('Inspect saved result', ['scientist'], '2026-11-10', 'P2', 'analysis'),
                         tuple(summary['completed'][0][key] for key in ('title', 'assignees', 'due_date', 'priority', 'classification')))
        self.assertFalse(summary['work'][0]['current_completion'])
        self.assertEqual('queued', summary['work'][0]['execution']['status'])
        self.assertEqual(['F1'], summary['completed'][0]['links']['artifact_ids']['figures'])
        self.assertEqual({'keep': True}, summary['plan']['custom_project_field'])
        self.assertIn('template=research-task.yml', summary['github']['management']['new_issue_url'])
        data['issues'][0].update(state='open', closed_at=None, body='### Progress\n\nNot started')
        data['issues'][1]['blocked_by'] = [data['issues'][0].copy()]
        self.write_json('github.json', data)
        updated = self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary', '--github', 'github.json')
        self.assertEqual([11], [row['number'] for row in updated['next']])
        self.assertEqual([12], [row['number'] for row in updated['blocked']])
        self.assertEqual(original, store.read_bytes())

    def test_project_revisions_and_impact_preserve_unaffected_results(self):
        definition, graph = self.project_fixture()
        for key in ('T', 'U'):
            self.cli('start', key)
            self.cli('output', key, key + '-result', '--kind', 'object', '--value', '{"value":7}')
            self.completed(key)
        definition['work'][0]['duration_hours'] = 2
        self.write_json('plan-timing.json', definition)
        timing = self.cli('project-impact', 'CASE', '--definition', 'plan-timing.json')['impact']
        self.assertEqual([], timing['affected_outputs'])
        self.assertEqual(['T'], timing['schedule_task_ids'])
        self.assertEqual(['T-result', 'U-result'], [row['output_id'] for row in timing['reusable_outputs']])
        graph['nodes'][1]['claim'] = 'A revised synthetic premise'
        graph['version'] = '2'
        self.write_json('argument-v2.json', graph)
        definition['argument']['path'] = 'argument-v2.json'
        self.write_json('plan-v2.json', definition)
        delta = self.cli('project-diff', 'CASE', '--definition', 'plan-v2.json')
        self.assertTrue(delta['proposed'])
        self.assertEqual(['T'], delta['impact']['affected_task_ids'])
        self.assertEqual(['T-result'], [row['output_id'] for row in delta['impact']['affected_outputs']])
        self.assertEqual(['U-result'], [row['output_id'] for row in delta['impact']['reusable_outputs']])
        self.assertEqual('https://github.com/acme/research/issues/11', delta['impact']['affected_issues'][0]['url'])
        with self.assertRaisesRegex(ValueError, 'user-change'):
            self.cli('project-bind', 'CASE', '--definition', 'plan-v2.json')
        self.write_json('change.json', {'source': 'user', 'message_id': 'synthetic-fixture-amendment', 'text': 'Adopt the synthetic second plan.',
            'previous_project_sha256': h.content_hash(delta['from_binding']), 'replacement_project_sha256': h.content_hash(delta['to_binding'])})
        self.cli('project-bind', 'CASE', '--definition', 'plan-v2.json', '--user-change', 'change.json')
        history = self.cli('project-history', 'CASE')['revisions']
        self.assertEqual([1, 2], [row['revision'] for row in history])
        self.assertEqual('plan-v1.json', history[0]['binding']['definition']['path'])
        saved = self.cli('project-diff', 'CASE', '--from-revision', '1', '--to-revision', '2')
        self.assertEqual(delta['changes'], saved['changes'])
        self.assertEqual('retained', json.loads((self.root / 'plan-v2.json').read_text())['work'][0]['custom_work_field'])

    def test_project_observations_use_existing_output_and_context_owners(self):
        _, graph = self.project_fixture()
        roles = ('project_finding', 'project_interpretation', 'project_open_decision')
        requirements = [value for role in roles for value in ('--required-output', json.dumps({'role': role, 'kind': 'object', 'target': role}))]
        self.add('--parent', 'CASE', *requirements, name='NOTES', kind='answer')
        self.cli('start', 'NOTES')
        for role, status in zip(roles, ('observed', 'recorded', 'open')):
            value = {'actor': 'scientist', 'date': '2026-11-05', 'status': status, 'text': role + ' text', 'decision_id': 'D2',
                     'evidence': [{'path': 'input', 'sha256': h.digest(self.root / 'input')}],
                     'target': {'node_id': 'A', 'argument_sha256': h._project_argument().argument_sha256(graph)}}
            self.cli('output', 'NOTES', role, '--kind', 'object', '--value', json.dumps(value))
        self.write_json('github.json', self.github_snapshot())
        summary = self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary', '--github', 'github.json')
        self.assertEqual('project_finding text', summary['findings'][0]['value']['text'])
        self.assertEqual('project_interpretation text', summary['interpretations'][0]['value']['text'])
        self.assertEqual('D2', summary['open_decisions'][0]['value']['decision_id'])
        self.assertEqual('D1', summary['adopted_decisions'][0]['decision_id'])
        value = summary['interpretations'][0]['value']
        value['text'] = 'Edited interpretation of the same saved result'
        self.cli('output', 'NOTES', 'project_interpretation', '--kind', 'object', '--value', json.dumps(value))
        edited = self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary', '--github', 'github.json')
        self.assertEqual(value['text'], edited['interpretations'][0]['value']['text'])
        self.assertNotEqual(summary['interpretations'][0]['version'], edited['interpretations'][0]['version'])

    def test_native_github_read_paginates_project_and_dependency_connections(self):
        self.project_fixture(project_id='PVT_fixture')
        issues = self.github_snapshot()['issues']
        project = {'id': 'PVT_fixture', 'title': 'Research', 'url': 'https://github.com/orgs/acme/projects/1'}
        def run(command, **kwargs):
            endpoint = command[4]
            if endpoint == 'graphql':
                query = next(value[6:] for value in command if value.startswith('query='))
                self.assertTrue(query.startswith('query('))
                self.assertIn('--paginate', command)
                self.assertIn('--slurp', command)
                connection = 'fields' if 'fields(first:' in query else 'items'
                page_rows = ([
                    [{'id': 'status', 'name': 'Status'}],
                    [{'id': 'priority', 'name': 'Priority', 'options': [{'id': 'p1', 'name': 'P1'}, {'id': 'p2', 'name': 'P2'}]}]]
                    if connection == 'fields' else [
                    [{'id': 'item11', 'isArchived': False, 'content': {'number': 11, 'repository': {'nameWithOwner': 'acme/research'}},
                      'priority': {'name': 'P1'}, 'status': {'name': 'Done'}}],
                    [{'id': 'item12', 'isArchived': False, 'content': {'number': 12, 'repository': {'nameWithOwner': 'acme/research'}},
                      'priority': {'name': 'P2'}, 'status': {'name': 'In Progress'}, 'due_date': {'date': '2026-11-09'}}]])
                pages = []
                for index, rows in enumerate(page_rows):
                    node = {**project, connection: {'nodes': rows, 'pageInfo': {'hasNextPage': index == 0,
                                                                                 'endCursor': 'cursor' if index == 0 else None}}}
                    pages.append({'data': {'node': node}})
                return SimpleNamespace(returncode=0, stdout=json.dumps(pages), stderr='')
            self.assertEqual('GET', command[command.index('--method') + 1])
            result = [[], []] if '/dependencies/' in endpoint else issues[int(endpoint.rsplit('/', 1)[1]) - 11]
            return SimpleNamespace(returncode=0, stdout=json.dumps(result), stderr='')
        with patch.object(h.subprocess, 'run', side_effect=run):
            summary = self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary')
        self.assertEqual('P1', summary['completed'][0]['priority'])
        self.assertEqual('P2', summary['active'][0]['priority'])
        self.assertEqual('2026-11-09', summary['active'][0]['due_date'])
        self.assertEqual('gh api', summary['github']['source'])
        with patch.object(h.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='', stderr='authentication required')):
            with self.assertRaisesRegex(ValueError, 'authentication required'):
                self.cli('project-view', 'CASE', '--role', 'manage', '--view', 'summary')

    def add(self, *args, name='T', kind='create'):
        if '--required-output' not in args and '--required-action' not in args:
            target = 'message:1' if kind == 'answer' else ('input' if kind == 'modify' else 'artifact')
            requirement = {'role': 'final', 'kind': 'message' if kind == 'answer' else 'file', 'target': target}
            args = (*args, '--required-output', json.dumps(requirement))
        self.cli('add', name, '--owner', 'writer', '--operation-kind', kind, '--next', 'Produce result', *args)


    def prepared(self, *args, name='T'):
        self.add('--scope', 'artifact', '--input', 'input',
                 '--required-check', json.dumps({'id': 'check', 'targets': ['artifact']}), name=name)
        self.cli('start', name)
        self.cli('output', name, 'artifact')

    def verify(self, *args, name='T', check='check'):
        self.cli('verify', name, '--check', check, '--result', 'passed', '--reviewer', 'reviewer', *args)

    def completed(self, name='T'):
        self.cli('transition', name, 'completed')


    def rejects_completion(self, name='T'):
        with self.assertRaises(ValueError):
            self.completed(name)


    def test_external_input_change_rejects_pass_and_completion(self):
        self.prepared()
        self.verify()
        (self.root / 'input').write_text('changed')
        self.rejects_completion()
        with self.assertRaises(ValueError):
            self.verify()
        self.assertEqual(['T'], self.cli('inspect')['affected_tasks'])


    def test_permission_hold_needs_recorded_release(self):
        self.add(kind='answer'); self.cli('start', 'T')
        self.cli('transition', 'T', 'blocked', '--reason', 'permission', '--hold-id', 'approval', '--next', 'Await approval')
        with self.assertRaises(ValueError): self.cli('resume', 'T')
        with self.assertRaises(ValueError): self.cli('requeue', 'T')
        with self.assertRaisesRegex(ValueError, 'requires --user-release'):
            self.cli('release-hold', 'T', '--hold-id', 'approval',
                     '--authority', 'user-message:approved', '--next', 'Continue')
        self.release( 'T', '--hold-id', 'approval', '--authority', 'user-message:approved', '--next', 'Continue approved work')
        self.cli('resume', 'T')
        self.assertEqual('user-message:approved', self.task()['hold_releases'][-1]['authority'])
        self.assertEqual('fixture-release-approval', self.task()['hold_releases'][-1]['message']['message_id'])



class HookCallbacksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plugin = Path(__file__).resolve().parent.parent
        spec = importlib.util.spec_from_file_location('tested_hooks', self.plugin / 'harness/codex_hooks.py')
        self.hooks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.hooks)
        self.directory = self.root / 'hook'
        self.directory.mkdir()
        request = 'Produce the requested output and final response.'
        request_sha = self.hooks.gate.sha(request.encode())
        self.context = {'schema_version': 2, 'task_id': 'task', 'turn_id': 'turn', 'session_id': 'session',
            'cwd': str(self.root), 'plugin_root': str(self.plugin), 'plugin_data': str(self.root / 'data'),
            'prompt_sha256': request_sha, 'operation_binding': {'conditions': ['data_code_change']},
            'completion_contract': {'request_sha256': request_sha, 'operation_kind': 'create',
                'authority': 'fixture request', 'external_targets': [],
                'required_outputs': [{'role': 'artifact', 'kind': 'file', 'target': 'output.txt'},
                                     {'role': 'response', 'kind': 'message', 'target': 'response'}],
                'required_actions': [{'operation': 'write', 'target_kind': 'file', 'target_id': 'output.txt'}]}}
        self.hooks.save_record(self.directory / 'context.json', self.context)
        self.hooks.save_record(self.directory / 'original-prompt.json', {'text': request, 'sha256': request_sha})

    def event(self, hook, tool='write_file', *, target='output.txt', identity='write-1', response=None):
        return {'hook_event_name': hook, 'session_id': 'session', 'turn_id': 'turn', 'cwd': str(self.root),
                'tool_name': tool, 'tool_use_id': identity, 'tool_input': {'path': str(self.root / target)},
                'tool_response': {'success': True} if response is None else response}

    def dispatch(self, event):
        with patch.dict(os.environ, {'PLUGIN_ROOT': str(self.plugin), 'PLUGIN_DATA': str(self.root / 'data')}), \
             patch.object(self.hooks, '_active_directory', return_value=self.directory):
            return self.hooks.dispatch(event, event['hook_event_name'])

    def test_actual_callbacks_and_stop_reuse_execution_records(self):
        hooks = self.hooks
        read = self.event('PreToolUse', 'read_file')
        with patch.object(hooks, '_policy_snapshot', side_effect=AssertionError('policy scan')), \
             patch.object(hooks, '_bound_state', side_effect=AssertionError('state scan')), \
             patch.object(hooks, '_completion_task', side_effect=AssertionError('contract scan')):
            self.assertEqual({}, self.dispatch(read))
        write = self.event('PreToolUse')
        with patch.object(hooks, '_completion_task', return_value=None):
            with self.assertRaisesRegex(ValueError, 'authority'):
                self.dispatch(write)
        with patch.object(hooks, '_policy_snapshot', side_effect=AssertionError('policy scan')):
            self.assertEqual({}, self.dispatch(write))
        (self.root / 'output.txt').write_text('actual output\n')
        callback = self.event('PostToolUse')
        with patch.object(hooks, '_pre_tool', side_effect=AssertionError('repeated preflight')), \
             patch.object(hooks, '_policy_snapshot', side_effect=AssertionError('policy scan')), \
             patch.object(hooks, '_bound_state', side_effect=AssertionError('state scan')):
            self.assertEqual({}, self.dispatch(callback))
            self.assertEqual({}, self.dispatch(callback))
        context = hooks._read(self.directory / 'context.json')
        self.assertEqual(1, len(context['unbound_operations']))
        observed = hooks._completion_observations(self.directory, context)
        self.assertEqual({'output.txt': hooks.gate.sha(b'actual output\n')}, observed[0]['output_versions'])
        stop = {'last_assistant_message': 'The requested output is complete.'}
        with patch.object(hooks.gate, 'file_snapshot', side_effect=AssertionError('Stop file scan')), \
             patch.object(hooks, '_operation_manifest', side_effect=AssertionError('Stop policy scan')):
            self.assertEqual('completed', hooks._verify_ordinary_stop(stop, self.plugin, self.directory))
        failed = self.event('PostToolUse', identity='write-failed', response={'error': 'write failed'})
        self.dispatch(failed)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            hooks._verify_ordinary_stop(stop, self.plugin, self.directory)
        self.assertFalse((self.directory / 'attempts.json').exists())

    def test_changed_rules_and_compaction_preserve_restoration(self):
        hooks = self.hooks
        source = self.root / 'AGENTS.md'
        source.write_text('Original project rule.\n')
        context = self.context
        context['completion_contract']['required_outputs'][0]['target'] = 'AGENTS.md'
        context['completion_contract']['required_actions'][0]['target_id'] = 'AGENTS.md'
        hooks.save_record(self.directory / 'context.json', context)
        hooks.save_record(self.directory / 'reinjection.json', {'instruction_policy_sha256': 'fixture',
            'instruction_sources': {str(source): hooks.gate.sha(source.read_bytes())}})
        read = self.event('PostToolUse', 'read_file', target='AGENTS.md', response=source.read_text())
        self.assertIn('Original project rule.', hooks._scoped_instructions(read, self.directory, context))
        self.assertEqual({}, self.dispatch(self.event('PreToolUse', target='AGENTS.md')))
        source.write_text('Updated project rule.\n')
        response = self.dispatch(self.event('PostToolUse', target='AGENTS.md'))
        self.assertIn('Updated project rule.', response['hookSpecificOutput']['additionalContext'])
        with self.assertRaisesRegex(ValueError, 'governing source changed'):
            self.dispatch(self.event('PreToolUse', target='AGENTS.md'))
        self.assertEqual({}, self.dispatch(self.event('PreToolUse', 'read_file', target='AGENTS.md')))
        compact = {**self.event('PostCompact'), 'trigger': 'auto'}
        with patch.object(hooks, '_policy_snapshot', side_effect=AssertionError('compaction preflight')), \
             patch.object(hooks, '_bound_state', side_effect=AssertionError('compaction state scan')):
            self.assertEqual({}, self.dispatch(compact))
        original = hooks._read(self.directory / 'original-prompt.json')['text']
        with patch.object(hooks, '_restoration', return_value=original + '\nComplete governing rules.') as restore:
            result = self.dispatch(self.event('PreToolUse', 'read_file', target='AGENTS.md'))
            restore.assert_called_once()
        self.assertEqual('deny', result['hookSpecificOutput']['permissionDecision'])
        restored = result['hookSpecificOutput']['additionalContext']
        self.assertIn(original, restored)
        self.assertIn('Complete governing rules.', restored)
        self.assertIn('Updated project rule.', restored)
        registration = json.loads((self.plugin / 'hooks/hooks.json').read_text())
        self.assertNotIn('PreCompact', registration['hooks'])

    def test_changed_checks_execute_the_selected_paths(self):
        checks = self.hooks.gate
        source = self.root / 'changed.py'
        source.write_text('answer = 42\n')
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = checks.main(['check-changed', '--root', str(self.root), '--path', source.name, '--check', 'syntax'])
        self.assertEqual(0, result)
        self.assertTrue(list(self.root.glob('__pycache__/changed.*.pyc')))
        self.assertEqual(['syntax'], json.loads(out.getvalue().splitlines()[-1])['checks'])
        self.assertEqual([], checks.changed_checks(self.root, ['notes.md'], ['tests', 'registry', 'distribution']))
        commands = checks.changed_checks(self.plugin, ['harness/codex_hooks.py'], ['tests'])
        self.assertEqual(['tests'], [name for name, _ in commands])
        selected = commands[0][1]
        self.assertIn('harness/test_state.py::HookCallbacksTests::test_actual_callbacks_and_stop_reuse_execution_records', selected)
        self.assertNotIn('harness/test_state.py::TeamStateTests::test_permission_hold_needs_recorded_release', selected)


if __name__ == '__main__':
    unittest.main()

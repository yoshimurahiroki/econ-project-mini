"""Public hook behavior: short answers, shared writing signals and bounded stops."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from harness.local_checks import scan

spec = importlib.util.spec_from_file_location('economics_check', Path(__file__).with_name('check.py'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


DICTIONARY = json.loads((Path(__file__).resolve().parents[1] / 'quality/prose_rules.json').read_text())


class HookTests(unittest.TestCase):
    def writing_signals(self, text):
        return scan({'answer.txt': text.encode('utf-8')}, DICTIONARY)

    def test_coordinator_bypasses_worksheets_and_research_keeps_them(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'PLUGIN_DATA': folder, 'ERS_HARNESS_ROLE': ''}):
            (Path(folder) / '.codex').mkdir()
            (Path(folder) / '.codex/harness-role').write_text('coordinator\n')
            def event(name, **extra):
                payload = {'session_id': 'coordinator', 'cwd': folder, **extra}
                with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))):
                    return check.main(name)
            context = event('UserPromptSubmit')['hookSpecificOutput']['additionalContext']
            self.assertIn('coordinator role', context)
            self.assertNotIn('Copy runtime/WORKSHEET.md', context)
            edit = {'tool_name': 'Edit', 'tool_input': {'file_path': str(Path(folder) / 'model.py')}}
            self.assertEqual(event('PreToolUse', **edit), {})
            self.assertEqual(event('Stop'), {})
            with patch.dict(os.environ, {'ERS_HARNESS_ROLE': 'research'}):
                event('UserPromptSubmit')
                self.assertEqual(event('PreToolUse', **edit)['hookSpecificOutput']['permissionDecision'], 'deny')
                self.assertEqual(event('Stop')['decision'], 'block')

    def test_answer_writer_enforces_committed_decision_order(self):
        with tempfile.TemporaryDirectory() as folder:
            worksheet = Path(folder) / 'task.md'
            original = ('## 3. Model\nKey condition: model A\n'
                        '## 5. Execution\nCommands run and saved result files: result.json\n'
                        '## 6. Interpretation and decision\nDecision: adopt A [user]\n'
                        'Switches when: profit difference > 0\nSpecification changes: none\n')
            worksheet.write_text(original)
            answer, _ = check.answer_paths(worksheet)
            with self.assertRaises(ValueError):
                check.answer_command('write-answer', worksheet, 'A')
            self.assertFalse(answer.exists())
            answer.write_text('draft before final decision')
            with self.assertRaises(ValueError):
                check.answer_command('commit-decision', worksheet)
            answer.unlink()
            committed = check.answer_command('commit-decision', worksheet)
            check.answer_command('write-answer', worksheet, 'adopt A')
            self.assertEqual(check.answer_order_problems(worksheet), [])
            worksheet.write_text(original.replace('model A', 'model B'))
            self.assertTrue(check.answer_order_problems(worksheet))
            worksheet.write_text(original)
            worksheet.write_text(original.replace('adopt A', 'adopt B'))
            with self.assertRaises(ValueError):
                check.answer_command('write-answer', worksheet, 'adopt B')
            self.assertTrue(check.answer_order_problems(worksheet))
            check.answer_command('commit-decision', worksheet)
            check.answer_command('write-answer', worksheet, 'adopt B')
            self.assertEqual(check.answer_order_problems(worksheet), [])
            answer.write_text('edited outside the writer')
            self.assertTrue(check.answer_order_problems(worksheet))

    def test_answer_writer_saves_affirmative_body_and_preserves_previous_answer(self):
        with tempfile.TemporaryDirectory() as folder:
            worksheet = Path(folder) / 'task.md'
            worksheet.write_text('## 6. Interpretation and decision\n'
                                 'Decision: Aを採用する [user]\nSpecification changes: none\n')
            check.answer_command('commit-decision', worksheet)
            answer, receipt = check.answer_paths(worksheet)
            for body in ('この案は不十分です。', 'この計算はできません。', 'This result is not identified.'):
                with self.subTest(body=body), self.assertRaises(ValueError):
                    check.answer_command('write-answer', worksheet, body)
            self.assertFalse(answer.exists())
            self.assertEqual(json.loads(receipt.read_text())['stage'], 'committed')
            body = 'Aを採用します。効果は−2人です。'
            check.answer_command('write-answer', worksheet, body)
            with self.assertRaises(ValueError):
                check.answer_command('write-answer', worksheet, 'この案は不可能です。')
            self.assertEqual(answer.read_text(), body)
            self.assertEqual(check.answer_order_problems(worksheet), [])

    def test_writer_catches_deferrals_and_preserves_actual_results(self):
        rejected = (
            '因果解釈を左右する。', '結果を左右します。', '成否の鍵を握ります。',
            '結論は追加資料に依存します。', '仮定を追加する。', '前提を追加します。',
            '追加の制約を導入します。', '識別には条件が必要です。', 'この前提が不可欠です。',
            '追加情報が必須です。', '対応を要します。', '情報が求められます。',
            '信頼区間を報告します。', '標準誤差と区間を併記します。',
            'This interpretation requires additional assumptions.',
            'The conclusion depends on the premise.', 'We will report confidence intervals.')
        for text in rejected:
            with self.subTest(text=text):
                self.assertTrue(check.affirmative_rewrites(text))
        accepted = (
            '推定値は2.4人、95%信頼区間は[1.8, 3.0]です。',
            '| 係数 | 標準誤差 | 95%信頼区間 |\n| 2.4 | 0.3 | [1.8, 3.0] |',
            '公開情報の市場では方式Aを採用します。私的情報の市場では方式Bを採用します。本件はBを採用します。')
        for text in accepted:
            with self.subTest(text=text):
                self.assertEqual(check.affirmative_rewrites(text), [])

    def test_retreat_signals_preserve_direct_numbers_and_thresholds(self):
        for text in ('未推定です。', '確認していません。', '効果を意味しません。', '示唆しません。',
                     '答えを左右します。', '重要です。', '大事です。', '二つに分けて考えます。',
                     'This is not the effect.', '価格の幅は需要の形で変わります。',
                     '提案するには、追加の根拠が必要です。', '暫定案です。', '設計の出発点です。'):
            with self.subTest(text=text):
                self.assertTrue(self.writing_signals(text))
        self.assertEqual(self.writing_signals('価格を704円にする。切替点は乗客18人。18人未満で毎時1便へ戻す。'), [])

    def test_hypothetical_framing_is_caught_in_both_languages(self):
        for text in ('仮に需要が増える。', '価格を1000円とする。', '費用が下がるとすれば増便する。',
                     'もし需要が増えたら値上げする。', '弾力性を2と仮定する。',
                     '需要増を想定すると増便になる。', 'If demand rises, raise the price.',
                     'if costs fall, expand.', 'Assuming demand rises, expand.',
                     'Suppose the cost is 400 yen.', 'Let us assume a fixed cost.'):
            with self.subTest(text=text):
                self.assertTrue(self.writing_signals(text))
        self.assertEqual(self.writing_signals('最適価格は704円。目的関数は677万円。切替弾力性は1.94。'), [])

    def test_short_answer_is_saved_and_worksheet_blocks_are_bounded(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'PLUGIN_DATA': folder}):
            def event(name, **extra):
                payload = {'session_id': 'short-answer', 'cwd': folder, **extra}
                with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))):
                    return check.main(name)
            event('UserPromptSubmit')
            outputs = [event('Stop', last_assistant_message='未推定です。')
                       for _ in range(check.MAX_STOP_BLOCKS + 1)]
            self.assertIn('未推定です。', check.load_state('short-answer')['answer'])
            self.assertEqual(sum(x.get('decision') == 'block' for x in outputs), check.MAX_STOP_BLOCKS)
            self.assertIn('systemMessage', outputs[-1])

    def test_newer_handoff_preserves_worksheet_and_finishes_immediately(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'PLUGIN_DATA': folder}):
            def event(name):
                payload = {'session_id': 'model-inputs', 'cwd': folder,
                           'last_assistant_message': '未推定です。'}
                with patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))):
                    return check.main(name)
            context = event('UserPromptSubmit')['hookSpecificOutput']['additionalContext']
            self.assertIn(check.writing_instruction(), context)
            work = Path(folder) / 'work'
            work.mkdir()
            lines = ['# Task', 'Status: closed', 'Current step: 7', 'Next action: complete']
            for name in check.SECTIONS:
                lines += ['## ' + name, 'Completed economic calculation CONTRACT-07 [user]']
                if name.startswith('4.'):
                    lines += ['Without data: actor costs and effort responses unspecified [assumption]']
                if name.startswith('6.'):
                    lines += ['Decision: choose the maximizing action [user]',
                              'Switches when: cost exceeds 10 units [assumption]',
                              'Specification changes: 0']
            (work / 'task.md').write_text('\n'.join(lines))
            handoff = work / 'handoff.md'
            handoff.write_text('# Handoff\nSaved results and the next action.\n')
            newer = (work / 'task.md').stat().st_mtime + 2
            os.utime(handoff, (newer, newer))
            check.answer_command('commit-decision', work / 'task.md')
            check.answer_command('write-answer', work / 'task.md', 'Choose the maximizing action.')
            first, second, third = event('Stop'), event('Stop'), event('Stop')
            self.assertEqual([first, second, third], [{}, {}, {}])


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Economics task hooks for Codex and Claude Code.

SessionStart / UserPromptSubmit: state the procedure and record the start of the turn.
Claude PreToolUse: Write/Edit operations wait for worksheet sections 1-3.
Research agents commit the decision before saving an official answer through the guarded writer.
Stop: check the adopted decision, specification record and official answer order; reuse compact records.
Economic review follows the requested claim through econ-review; WRITING owns the final expression pass.
SubagentStop: a worker rereads its return against the procedure once.
"""
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

COORDINATOR = ('Harness evaluation coordinator role. Handle harness changes, sequential child evaluations, '
               'result comparisons and user conversation directly. The seven-step economist procedure and '
               'worksheets apply to evaluated research agents. Launch each evaluated agent in research mode '
               'in its own working directory. Use concise direct answers and reuse existing results. '
               'Run only the evaluations the user authorized. Follow AGENTS.md role scope.')

POINTER = ("Research role: follow AGENTS.md and runtime/ECONOMIST.md through the seven stages. "
           "Use the task skill and reuse settled work. Record compact results in work/<topic>.md from "
           "runtime/WORKSHEET.md, with sources and knowledge IDs. Apply runtime/WRITING.md from the first "
           "visible message; retrieve exemplars at stage 7. Save adopted sections 1–6 through "
           "hooks/check.py commit-decision, then write-answer. Complete the header before returning the complete saved body.")
WORKER_REVIEW = ('Before returning, check the return against runtime/ECONOMIST.md: it states the economic object it '
                 'serves, the model or method used with knowledge unit IDs, the actual commands run and saved files, '
                 'and the result the parent needs. Add what is missing; otherwise return without comment.')
SECTIONS = ['1. Situation and stakes', '2. Question', '3. Model', '4. Estimand and identification',
            '5. Execution', '6. Interpretation and decision', '7. Expression']
SOURCE_TAG = re.compile(r'\[(?:user|context|knowledge|literature|data|assumption)\b')
KNOWLEDGE_ID = re.compile(r'\b(?:MC-[A-Za-z0-9-]+|[A-Z]{2,}(?:-[A-Z]+)?-\d{2})\b')
EDIT_TOOLS = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}
MAX_STOP_BLOCKS = 3
MIN_FILLED = 15


def state_path(session):
    base = Path(os.environ.get('PLUGIN_DATA') or os.environ.get('CLAUDE_PLUGIN_DATA')
                or Path.home() / '.local' / 'state' / 'econ-harness')
    return base / (hashlib.sha256(str(session).encode('utf-8')).hexdigest()[:32] + '.json')


def load_state(session):
    try:
        return json.loads(state_path(session).read_text(encoding='utf-8'))
    except Exception:
        return {'start': 0.0, 'blocks': 0}


def save_state(session, state):
    try:
        path = state_path(session)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding='utf-8')
    except Exception:
        pass


def template_lines():
    try:
        text = (Path(__file__).resolve().parent.parent / 'runtime' / 'WORKSHEET.md').read_text(encoding='utf-8')
    except Exception:
        return set()
    return {line.strip() for line in text.splitlines() if line.strip()}


def sections(text):
    found, current = {}, None
    for line in text.splitlines():
        match = re.match(r'^##\s+(\d)\.', line)
        if match:
            index = int(match.group(1)) - 1
            current = SECTIONS[index] if 0 <= index < len(SECTIONS) else None
            if current:
                found[current] = []
            continue
        if line.startswith('#'):
            current = None
        elif current:
            found[current].append(line)
    return found


def filled(lines, template):
    """Characters written beyond the template text and empty labels."""
    total = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in template:
            continue
        label = re.match(r'^[^:：]{1,60}[:：]\s*(.*)$', stripped)
        value = label.group(1) if label else stripped
        total += len(re.sub(r'\(IDs from knowledge\.py[^)]*\)', '', value).strip(' -–'))
    return total


def label_text(lines, label, template):
    """Text written under a label: its own line (template guidance excluded) and the lines that follow it up
    to the next label or heading."""
    out, inside = [], False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\s*' + re.escape(label) + r'\s*[:：]', line):
            inside = True
            if stripped not in template:
                out.append(re.sub(r'^[^:：]*[:：]\s*', '', stripped))
            continue
        if inside:
            if stripped.startswith('#') or re.match(r'^[A-Z][^:：]{1,60}[:：]', stripped):
                break
            out.append(stripped)
    return ' '.join(s for s in out if s).strip()


def label_value(lines, label):
    for line in lines:
        match = re.match(r'^\s*' + re.escape(label) + r'\s*[:：]\s*(.*)$', line)
        if match:
            return match.group(1).strip()
    return ''


def worksheet_problems(cwd, start, upto):
    """Problems with the most recently written worksheet of this turn, checked through section `upto`."""
    work = Path(cwd) / 'work'
    candidates = sorted((p for p in work.glob('*.md') if p.stat().st_mtime >= start - 1 and
                         re.search(r'(?m)^\s*Status\s*[:：]', p.read_text(encoding='utf-8', errors='replace')
                                   .split('\n## 1.')[0])),
                        key=lambda p: p.stat().st_mtime, reverse=True) if work.is_dir() else []
    if not candidates:
        return None, ['no worksheet in work/ was written in this turn: copy runtime/WORKSHEET.md to '
                      'work/<topic>.md (or update the existing one for this topic) and fill it']
    path = candidates[0]
    found, problems = sections(path.read_text(encoding='utf-8', errors='replace')), []
    if upto >= 6 and '6. Interpretation and decision' in found:
        for label in ('Decision', 'Specification changes'):
            if not label_value(found['6. Interpretation and decision'], label) or \
                    label_value(found['6. Interpretation and decision'], label).startswith('(number after'):
                problems.append(f'section 6 has no "{label}:" entry')
    if upto >= 7:
        header = path.read_text(encoding='utf-8', errors='replace').split('\n## 1.')[0].splitlines()
        status = label_value(header, 'Status').lower()
        if status not in ('open', 'closed'):
            problems.append('the header has no "Status: open" or "Status: closed" line')
        elif status == 'open' and not label_value(header, 'Next action'):
            problems.append('the worksheet is open and its header has no "Next action:"')
    return path, problems


def open_worksheets(cwd):
    """Open worksheets and their next actions, read at session start so work resumes where it stopped."""
    work = Path(cwd) / 'work'
    out = []
    for path in sorted(work.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)[:5] if work.is_dir() else []:
        header = path.read_text(encoding='utf-8', errors='replace').split('\n## 1.')[0].splitlines()
        if label_value(header, 'Status').lower() == 'open':
            out.append(f'{path.name}: step {label_value(header, "Current step") or "?"}; next: '
                       f'{label_value(header, "Next action") or "(not set)"}')
    return out


def edit_targets(payload):
    tool_input = payload.get('tool_input') or {}
    paths = [tool_input.get(key) for key in ('file_path', 'path', 'notebook_path') if tool_input.get(key)]
    patch = tool_input.get('patch') or tool_input.get('input') or tool_input.get('command') or ''
    if isinstance(patch, str):
        paths += [p.strip() for p in re.findall(r'^\*\*\* (?:Add|Update|Delete) File:\s*(.+)$', patch, re.M)]
    return [p for p in paths if isinstance(p, str)]


def gated(path, cwd):
    """Edits inside the project and outside work/ are gated; scratch and temporary files are not."""
    root = Path(cwd).resolve()
    target = (Path(path) if Path(path).is_absolute() else root / path).resolve()
    return root in target.parents and (root / 'work') not in target.parents


def writing_instruction():
    script_dir = Path(__file__).resolve().parent
    for path in (script_dir.parent / 'runtime/WRITING.md', script_dir / 'ECON_WRITING.md'):
        if path.is_file():
            record = re.search(r'^\*\*All-stage record\.\*\* (.+)$', path.read_text(encoding='utf-8'), re.M)
            if record:
                return record.group(1)
    return ''


def affirmative_rewrites(body):
    """Locate affirmative rewrites with the existing scanner and dictionary."""
    directory = Path(__file__).resolve().parent
    root = directory.parent
    scanner = root / 'harness/local_checks.py'
    dictionary = root / 'quality/prose_rules.json'
    if not scanner.is_file():
        scanner, dictionary = directory / 'LOCAL_CHECKS.py', directory / 'PROSE_CHECK_RULES.json'
    spec = importlib.util.spec_from_file_location('ers_answer_scanner', scanner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rules = module.parse_json(dictionary.read_bytes())
    rules['rules'] = [rule for rule in rules['rules'] if rule['action'] == 'block']
    hits = module.scan({'answer.md': body.encode('utf-8')}, rules)
    return list(dict.fromkeys(sentence.group().strip()
        for sentence in re.finditer(r'.+?(?:[。．!?！？]|\.(?=\s|$)|\n|$)', body, re.S)
        if any(sentence.start() <= hit['start'] < sentence.end() for hit in hits)))


def affirmative_instruction(passages):
    return ('Give the substantive judgment, decisive economic reason and consequence in affirmative clauses. '
            'Delete sentences whose only content is a standard definition, routine identifying condition, '
            'implementation detail or reporting announcement. Select other sentences by the economic judgment they change. '
            'Use the source-backed result and actual quantities without altering their scientific meaning. '
            'Before rewriting, retrieve original wording with exemplars.py borrow --level phrase; '
            'include new compound nouns and predicates; use economic actor/action query terms and batch lookups with repeated --query. '
            'First state the actual actors, both sides of the comparison, the outcome and one economic reason '
            'in the names used by the question. Replace compressed comparison nouns with complete clauses. '
            'For a changed subject-action-object relation use --level sentence and read its context. '
            'Edit the working draft with the returned source predicates, noun-verb phrases, particles and syntax, '
            'using the adopted economic result and actual quantities. Read the whole sentence as a plain actor/action/object assertion, '
            'and delete empty scope or interpretation announcements and warnings about claims absent from the request. '
            'Remove redundant technical topics instead of moving them into added paragraphs. Return the complete body: '
            + json.dumps(passages, ensure_ascii=False))


def answer_paths(worksheet):
    return (worksheet.with_name(worksheet.stem + '-answer.md'),
            worksheet.with_name(worksheet.stem + '-answer-state.json'))


def decision_hash(worksheet):
    found = sections(worksheet.read_text(encoding='utf-8'))
    for label in ('Decision', 'Specification changes'):
        value = label_value(found.get(SECTIONS[5], []), label)
        if not value or value.startswith('('):
            raise ValueError('Fill section 6 ' + label + ' before committing the decision.')
    body = '\n'.join(line for section in SECTIONS[:6] for line in found.get(section, []))
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


def answer_state(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def answer_command(command, worksheet, body=None):
    worksheet = Path(worksheet).resolve()
    answer, receipt = answer_paths(worksheet)
    digest = decision_hash(worksheet)
    state = answer_state(receipt)
    if command == 'commit-decision':
        found = sections(worksheet.read_text(encoding='utf-8'))
        if answer.exists() and (state.get('stage') != 'drafted' or
                state.get('answer_sha256') != hashlib.sha256(answer.read_bytes()).hexdigest()):
            raise ValueError('Remove the uncommitted draft, then commit the saved decision before writing it.')
        receipt.write_text(json.dumps({'stage': 'committed', 'decision_sha256': digest}) + '\n', encoding='utf-8')
        return {'status': 'committed', 'worksheet': str(worksheet), 'answer_path': str(answer),
                'writing_instruction': writing_instruction(),
                'adopted_content': {label: value
                    for section, labels in ((SECTIONS[5], ('Result against the predictions', 'Magnitude', 'Decision')), )
                    for label in labels
                    if (value := label_value(found.get(section, []), label)) and not value.startswith('(')},
                'next': 'Save the answer through write-answer with its body on stdin.'}
    if state.get('stage') not in ('committed', 'drafted') or state.get('decision_sha256') != digest:
        raise ValueError('Commit the final decision before write-answer. Decision changes require a new commit.')
    if not body or not body.strip():
        raise ValueError('Supply the complete answer body on stdin.')
    passages = affirmative_rewrites(body)
    if passages:
        raise ValueError(affirmative_instruction(passages))
    answer.write_text(body, encoding='utf-8')
    receipt.write_text(json.dumps({'stage': 'drafted', 'decision_sha256': digest,
                                  'answer_sha256': hashlib.sha256(answer.read_bytes()).hexdigest()}) + '\n',
                       encoding='utf-8')
    return {'status': 'drafted', 'answer_path': str(answer),
            'writing_instruction': writing_instruction(),
            'next': 'Read the saved affirmative body for meaning and economic consequence, then return that complete body.'}


def answer_order_problems(worksheet):
    answer, receipt = answer_paths(worksheet)
    try:
        state = answer_state(receipt)
        if state.get('stage') != 'drafted':
            return ['commit the final decision, then save the answer through write-answer']
        if state.get('decision_sha256') != decision_hash(worksheet):
            return ['the saved decision changed after committing; commit it again and regenerate the answer']
        if not answer.is_file() or state.get('answer_sha256') != hashlib.sha256(answer.read_bytes()).hexdigest():
            return ['save the current answer through write-answer']
    except (OSError, ValueError, TypeError):
        return ['commit the final decision, then save the answer through write-answer']
    return []


def main(event):
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    session = payload.get('session_id') or 'default'
    cwd = payload.get('cwd') or os.getcwd()
    role = os.environ.get('ERS_HARNESS_ROLE')
    if not role:
        try:
            role = (Path(cwd) / '.codex/harness-role').read_text(encoding='utf-8').strip()
        except OSError:
            role = 'research'
    if role == 'coordinator' and event != 'SubagentStop':
        if event in ('SessionStart', 'UserPromptSubmit'):
            return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext': COORDINATOR}}
        return {}
    if event in ('SessionStart', 'UserPromptSubmit'):
        if event == 'UserPromptSubmit':
            save_state(session, {'start': time.time(), 'blocks': 0})
            return {}
        context = writing_instruction() + '\n' + POINTER
        if event == 'SessionStart':
            pending = open_worksheets(cwd)
            if pending:
                context += ' Open worksheets (resume from their next action): ' + ' | '.join(pending)
        return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext': context}}
    state = load_state(session)
    if event == 'PreToolUse':
        if str(payload.get('tool_name', '')).rsplit('__', 1)[-1] not in EDIT_TOOLS:
            return {}
        targets = [p for p in edit_targets(payload) if gated(p, cwd)]
        if not targets:
            return {}
        _, problems = worksheet_problems(cwd, state.get('start', 0.0), 3)
        if not problems:
            return {}
        return {'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                       'permissionDecisionReason': 'Create this turn\'s worksheet '
                                       'before editing ' + ', '.join(targets[:3]) + ': ' + '; '.join(problems) + '.'}}
    if event == 'SubagentStop':
        return {} if payload.get('stop_hook_active') else {'decision': 'block', 'reason': WORKER_REVIEW}
    if event == 'Stop':
        message = str(payload.get('last_assistant_message') or '')
        if message.strip() and message not in state.get('answer', ''):
            state['answer'] = (state.get('answer', '') + '\n' + message)[-20000:]
            save_state(session, state)
        passages = affirmative_rewrites(message) if message.strip() else []
        if passages:
            return {'decision': 'block', 'reason': affirmative_instruction(passages)}
        path, problems = worksheet_problems(cwd, state.get('start', 0.0), 7)
        if path and not problems:
            order_problems = answer_order_problems(path)
            if order_problems:
                return {'decision': 'block', 'reason': 'Official answer order: ' + '; '.join(order_problems) +
                        '. Use python3 hooks/check.py commit-decision ' + str(path) +
                        ' followed by python3 hooks/check.py write-answer ' + str(path) + ' with the body on stdin.'}
        if problems and state.get('blocks', 0) < MAX_STOP_BLOCKS:
            state['blocks'] = state.get('blocks', 0) + 1
            save_state(session, state)
            where = f' ({path.name})' if path else ''
            return {'decision': 'block', 'reason': 'Complete the worksheet' + where + ' before finishing: '
                    + '; '.join(problems) + '. Then align the answer with it.'}
        if problems:
            return {'systemMessage': 'Economics worksheet incomplete after ' + str(MAX_STOP_BLOCKS)
                    + ' requests: ' + '; '.join(problems)}
        return {}
    return {}


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'Stop'
    try:
        if command in ('commit-decision', 'write-answer'):
            result = answer_command(command, sys.argv[2], sys.stdin.read() if command == 'write-answer' else None)
        else:
            result = main(command)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, TypeError, IndexError) as exc:
        print(json.dumps({'status': 'blocked', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

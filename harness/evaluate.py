"""Sequential, resumable ERS comparisons. Each CLI session consumes the approved sequential evaluation budget."""
import argparse
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import tarfile
import time

ROOT = None
REPO = Path(__file__).resolve().parents[1]
CODEX = Path(os.environ.get('CODEX_BIN') or shutil.which('codex') or 'codex')
SESSION_HOME = None
MODEL = 'gpt-6.1-sol'
CAP = 0


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2))


def read_events(path):
    messages, commands, usage = [], [], {}
    for line in path.read_text(errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get('item') or {}
        if event.get('type') == 'item.completed':
            if item.get('type') == 'agent_message' and item.get('text', '').strip():
                messages.append(item['text'].strip())
            if item.get('type') == 'command_execution':
                commands.append({'command': item.get('command'), 'exit': item.get('exit_code'),
                                 'output': str(item.get('aggregated_output', ''))[:500]})
        if event.get('type') == 'turn.completed':
            for key, value in (event.get('usage') or {}).items():
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
    return {'messages': messages, 'final': messages[-1] if messages else '',
            'commands': commands, 'usage': usage}


def prepare_home(work):
    SESSION_HOME.mkdir(exist_ok=True)
    auth = SESSION_HOME / 'auth.json'
    if not auth.exists():
        auth.symlink_to(Path.home() / '.codex/auth.json')
    (SESSION_HOME / 'config.toml').write_text(
        f'[projects.{json.dumps(str(work))}]\ntrust_level = "trusted"\n')


def call(out, work, prompt, kind, schema=None):
    if (out / 'meta.json').exists():
        return json.loads((out / 'meta.json').read_text())
    ledger_path = ROOT / 'calls.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    if len(ledger) >= CAP:
        raise RuntimeError('Approved evaluation budget exhausted')
    if out.exists():
        raise RuntimeError(f'Incomplete call requires inspection: {out}')
    out.mkdir(parents=True)
    prepare_home(work)
    record = {'number': len(ledger) + 1, 'id': out.name, 'kind': kind, 'model': MODEL,
              'effort': 'low', 'started': time.time()}
    ledger.append(record)
    save(ledger_path, ledger)
    args = [str(CODEX), 'exec', '-m', MODEL, '-c', 'model_reasoning_effort="low"',
            '--disable', 'multi_agent', '--disable', 'apps', '-C', str(work),
            '--skip-git-repo-check', '--dangerously-bypass-approvals-and-sandbox',
            '--dangerously-bypass-hook-trust', '--json', '--color', 'never',
            '-o', str(out / 'last.md')]
    if schema:
        args += ['--output-schema', str(schema)]
    args += ['-']
    print(json.dumps({'call': record['number'], 'id': out.name, 'kind': kind}), flush=True)
    start = time.monotonic()
    with (out / 'events.jsonl').open('w') as events, (out / 'stderr.txt').open('w') as errors:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=errors,
                                env=dict(os.environ, CODEX_HOME=str(SESSION_HOME), ERS_HARNESS_ROLE="research"))
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
        selector = selectors.DefaultSelector()
        selector.register(proc.stdout, selectors.EVENT_READ)
        recent = []
        pending = b''
        stop_reason = None
        while selector.get_map():
            if time.monotonic() - start > 2400:
                stop_reason = 'timeout'
                proc.kill()
            ready = selector.select(timeout=30)
            if not ready:
                print(json.dumps({'id': out.name, 'elapsed': round(time.monotonic()-start)}), flush=True)
            for key, _ in ready:
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                pending += chunk
                lines = pending.split(b'\n')
                pending = lines.pop()
                for raw in lines:
                    line = raw.decode(errors='replace') + '\n'
                    events.write(line)
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    item = event.get('item') or {}
                    if event.get('type') == 'item.completed' and item.get('type') == 'command_execution':
                        signature = (item.get('command'), item.get('aggregated_output'))
                        recent = (recent + [signature])[-3:]
                        if len(recent) == 3 and recent[0] == recent[1] == recent[2]:
                            stop_reason = 'three identical consecutive operations and outputs'
                            proc.kill()
                events.flush()
        code = proc.wait()
    parsed = read_events(out / 'events.jsonl')
    meta = {**record, 'exit': code, 'stop_reason': stop_reason,
            'seconds': round(time.monotonic()-start), 'usage': parsed['usage']}
    save(out / 'meta.json', meta)
    ledger[-1] = meta
    save(ledger_path, ledger)
    print(json.dumps({'done': out.name, 'exit': code, 'seconds': meta['seconds'],
                      'usage': meta['usage']}, ensure_ascii=False), flush=True)
    return meta


def tree(revision):
    revision = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', revision], text=True).strip()
    dst = ROOT / 'trees' / revision
    if not dst.exists():
        dst.mkdir(parents=True)
        archive = subprocess.check_output(['git', '-C', str(REPO), 'archive', revision])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(dst, filter='data')
    return revision, dst


def evaluate(label, revision, tasks, task_root):
    revision, src = tree(revision)
    index_path = ROOT / 'private-key.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    for task in tasks:
        source = task_root / task
        digest = hashlib.sha256()
        for path in sorted(source.rglob('*')):
            if path.is_file():
                digest.update(str(path.relative_to(source)).encode())
                digest.update(path.read_bytes())
        run_id = hashlib.sha256(f'{revision}:{task}:{digest.hexdigest()}:{MODEL}:low:serial-v1'.encode()).hexdigest()[:12]
        out = ROOT / 'runs' / run_id
        work = ROOT / 'copies' / run_id
        if not work.exists():
            shutil.copytree(src, work, symlinks=True)
            (work / 'work').mkdir(exist_ok=True)
            inputs = source / 'inputs'
            if inputs.exists():
                shutil.copytree(inputs, work / 'inputs', dirs_exist_ok=True)
            hook_path = work / '.codex/hooks.json'
            hook_path.parent.mkdir(exist_ok=True)
            hook_path.write_text((work / 'hooks/hooks.json').read_text().replace('$PLUGIN_ROOT', str(work)))
        index[run_id] = {'revision': revision, 'task': task, 'task_root': str(task_root), 'label': label}
        save(index_path, index)
        prompt = source.joinpath('prompt.txt').read_text() + '\n\nすべて逐次実行。同時実行数1。子エージェントの起動は禁止。'
        meta = call(out, work, prompt, 'evaluation')
        if meta['exit'] != 0:
            raise RuntimeError(f'Failed run {run_id}; inspect before continuing')


def main():
    global ROOT, SESSION_HOME, CAP
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--task-root', type=Path, required=True)
    parser.add_argument('--tasks', required=True)
    args = parser.parse_args()
    ROOT = args.output.resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    SESSION_HOME = ROOT / 'session-home'
    tasks = args.tasks.split(',')
    CAP = len(tasks)
    with (ROOT / 'execution.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        evaluate('evaluation', args.revision, tasks, args.task_root)


if __name__ == '__main__':
    main()

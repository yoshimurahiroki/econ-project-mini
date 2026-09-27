"""Apply the authorized one-time cleanup in the isolated task branch."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

root = Path.cwd()
shared = os.environ.get('SHARED_COMMIT')
if shared:
    paths = ['.cursorrules', '.agents/skills/econ-assertive/SKILL.md', '.agents/skills/econ-data/SKILL.md', '.agents/skills/econ-data/references/reproducible-workflow.md', '.agents/skills/econ-data/references/implementation.md', 'docs/ai/project_instructions.txt', 'docs/ai/project_bridge.txt', 'docs/ai/repo_context.md', 'docs/ai/integration.md', 'scripts/export_project.py', '.pre-commit-config.yaml']
    for path in paths:
        data = subprocess.run(['git','show',f'{shared}:{path}'],check=True,capture_output=True).stdout
        target = root/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
for path in ['.github/workflows/research-config.yml','tests/test_research_config.py','scripts/ai.mk','scripts/ai_tools.py','scripts/style_guard.py','scripts/sync_rules.py','scripts/sync_rules.sh','scripts/setup_ai_skills.sh','docs/ai/skills.json','docs/ai/ai_research_assistant_guidelines.md','docs/ai/cloud_llm_guidelines.md','docs/ai/econ_writing_reference.md','.textlintrc.json']:
    (root/path).unlink(missing_ok=True)

for p in (root/'.agents/skills').glob('*/SKILL.md'):
    if p.parent.name == 'econ-assertive':
        continue
    s=p.read_text().replace('Use `econ-assertive` by default for generated prose: direct drafting, then mandatory post-draft detection, necessity assessment and revision.', 'Use `econ-assertive` for prose. Apply the repository simplicity and minimum-verification rules to every generated artifact.')
    s=s.replace('Carry paths and hashes rather than whole private records.', 'Carry relevant paths and source IDs rather than whole private records.')
    s=s.replace('Resume completed stages from their source and output fingerprints.', 'Resume completed stages from existing sources and results.')
    s=s.replace('Keep one canonical task record.', 'Reuse an existing task record when continuation requires it.')
    s=s.replace('Use scripts for counts, joins, arithmetic and checks. Run cheap deterministic tests before expensive execution. Reuse verified outputs while data, code, parameters and environment stay fixed. Invalidate dependent outputs after a change. A release runs the complete requested pipeline.', 'Use direct computation for the requested result. Default to no separate mechanical check; use one targeted execution only for a concrete unresolved risk. Reuse unchanged outputs and rerun affected steps. Full clean execution follows an actual reproduction or release need.')
    if p.parent.name=='econ-writing':
        s=s.replace('Select content before layout.', 'Use the smallest structure that carries the requested argument. Remove decorative layouts, repeated summaries, filler sections and unrequested deliverables. Select content before layout.')
        s=s.replace('Compile the delivered source, check references and mathematics, and inspect rendered pages after layout changes. Execute the full post-draft prose audit, revise only affected passages and recheck claim/exhibit alignment before delivery.', 'Produce the requested artifact using its existing build command. Inspect changed content and layout through the actual output. Avoid separate font/metadata scans and reports. Review wording once within drafting, then recheck edited passages. A discussion needs no build command.')
    if p.parent.name=='econ-review':
        s+='\nUse source inspection and existing results first. Execute a new check only to settle a specific consequential issue in the requested review. Omit checklist-driven tests and reports of passing checks.\n'
    p.write_text(s)
p=root/'.agents/skills/econ-assertive/references/patterns.md'
s=p.read_text().replace('The examples are authored fixtures, not empirical findings.', 'The examples illustrate editing decisions.')
a=s.index('## Internal decision record'); b=s.index('## Efficiency',a)
p.write_text(s[:a]+s[b:])
p=root/'docs/ai/sources.md'
s=p.read_text()
s=s.replace("The new two-stage gate is an implementation of the current user's instructions. The detector supplies candidates. Necessity judgment uses the current claim and source evidence. Post-draft review is mandatory even after a phrase-clean scan. The audit record is internal by default.", 'Direct drafting is followed by one meaning-based necessity review using the current claim and source evidence.')
a=s.index('## Product and performance evidence'); b=s.index('## Second review:',a)
s=s[:a]+s[b:]
s=s.replace('The adopted procedures are locally implemented and tested; external runtimes are not installed.', 'These sources supply workflow choices for the actual research task.')
s=s.replace('Keep task routing and cheap fixtures; cross-language replication follows a specific need.', 'Keep task routing; additional execution follows a concrete research need.')
s=s.replace('Preserve the existing runner and use input-dependent reruns; keep full release reproduction.', 'Preserve the runner and rerun affected outputs; reproduce fully when requested.')
s=s.split('This revision also tests')[0].rstrip()+'\n'
p.write_text(s)
index=['# Research task index','','Read one matching skill and econ-assertive for prose. Apply repository simplicity and minimum-verification rules to their outputs.','']
for p in sorted((root/'.agents/skills').glob('*/SKILL.md')):
    desc=next(line[13:] for line in p.read_text().splitlines() if line.startswith('description: '))
    index.append(f'- `{p.parent.name}`: {desc}')
index+=['','[Integration](integration.md) supplies Project exports. [Sources](sources.md) records methodological references.']
(root/'docs/ai/compiled_ai_skills.md').write_text('\n'.join(index)+'\n')
for path,title in [('docs/issue/task_template.md','Task'),('docs/issue/issue_template.md','Issue')]:
    (root/path).write_text(f'# {title}\n\n## Requested result\nState the output and its purpose.\n\n## Scope\nName the relevant inputs, files and authorized changes.\n\n## Completion\nUse inspection and existing evidence first. Specify a command only for a concrete consequential risk; choose the smallest operation. No default test suite or verification report.\n')

# Keep dependency and document recipes; remove automatic verification chains.
p=root/'Makefile'
s=p.read_text()
s=re.sub(r'^\.PHONY:(?:[^\n]*\\\n)*[^\n]*\n','',s,count=1,flags=re.M)
s=s.replace('R_MAKEVARS_USER ?= $(CURDIR)/scripts/r-makevars\n','R_MAKEVARS_USER ?= $(CURDIR)/scripts/r-makevars\nFILE ?=\nTEST ?=\n')
def recipe(text,name,replacement=''):
    pattern=rf'^{re.escape(name)}:[^\n]*\n(?:(?:\t[^\n]*|[ \t]*)\n)*'
    return re.sub(pattern,replacement,text,flags=re.M)
for name in ['check','check-code','check-ai','check-mcp','check-r','check-qmd','check-pdf','ai-references']:
    s=recipe(s,name)
s=recipe(s,'test','test:\n\t@test -n "$(TEST)" || { echo "Specify a test path or node with TEST=..." >&2; exit 2; }\n\t$(THREAD_ENV) $(PIXI_RUN) pytest -q -p no:cacheprovider -- "$(TEST)"\n\n')
s=recipe(s,'format','format:\n\t@test -n "$(FILE)" || { echo "Specify a file with FILE=..." >&2; exit 2; }\n\t$(PIXI_RUN) ruff format -- "$(FILE)"\n\nlint:\n\t@test -n "$(FILE)" || { echo "Specify a file with FILE=..." >&2; exit 2; }\n\t$(PIXI_RUN) ruff check -- "$(FILE)"\n\n')
s=recipe(s,'help','help:\n\t@echo "sync / r-install / r-plan: project dependencies"\n\t@echo "build-paper / build-slides / quarto-*: requested documents"\n\t@echo "test TEST=path::node: one selected test"\n\t@echo "lint FILE=path / format FILE=path: explicit file operations"\n\t@echo "Project export: python scripts/export_project.py --output /tmp/econ-project"\n\t@echo "clean: remove generated caches and build files"\n\n')
s=s.replace('RFILE ?=\n','').replace('PDF ?=\n','')
targets=re.findall(r'^([a-z][a-z-]*):',s,re.M)
s=s.replace('\n\n\n','\n\n').rstrip()+'\n'
s='# Project commands; checks require an explicit target.\n.PHONY: '+' '.join(dict.fromkeys(targets))+'\n'+s[s.index('\n')+1:]
p.write_text(s)

p=root/'.devcontainer/setup-environment.sh'
s=p.read_text()
s=re.sub(r'^.*(?:setup_ai_skills|sync_rules).*\n','',s,flags=re.M)
s=re.sub(r'^run_logged\(\) \{\n.*?^\}\n\n','',s,flags=re.M|re.S)
s=re.sub(r'^run_logged /tmp/setup_ide_mcp.log .*$','bash scripts/setup_ide_mcp.sh',s,flags=re.M)
s=s.replace('bash scripts/setup_ide_mcp.sh > /tmp/setup_ide_mcp.log 2>&1 || true','bash scripts/setup_ide_mcp.sh')
p.write_text(s)
p=root/'.devcontainer/Dockerfile'
p.write_text(p.read_text().replace('# setup_ai_skills.sh can fetch optional reference repositories after creation.','# Optional reference files are read only for a specific task.'))

# One editor-settings source, with automatic analysis and tests turned off.
p=root/'.devcontainer/devcontainer.json'
dev=json.loads(p.read_text())
settings_path=root/'.vscode/settings.json'
settings=dev.get('customizations',{}).get('vscode',{}).get('settings',{}).copy()
settings.update(json.loads(settings_path.read_text()))
settings.update({'editor.formatOnSave':False,'notebook.formatOnSave.enabled':False,'editor.codeActionsOnSave':{'source.fixAll':'never','source.organizeImports':'never'},'python.testing.pytestEnabled':False,'python.testing.unittestEnabled':False,'python.testing.autoTestDiscoverOnSaveEnabled':False,'python.testing.promptToConfigure':False,'python.analysis.typeCheckingMode':'off','python.analysis.diagnosticMode':'openFilesOnly','ruff.lint.enable':False,'mypy-type-checker.enabled':False,'pylint.enabled':False,'flake8.enabled':False,'ltex.enabled':False,'markdownlint.enable':False,'cSpell.enabled':False,'r.lsp.diagnostics':False,'latex-workshop.latex.autoBuild.run':'never','latex-workshop.linting.chktex.enabled':False,'latex-workshop.linting.lacheck.enabled':False})
settings_path.write_text(json.dumps(settings,indent=2)+'\n')
extensions=['ms-python.python','ms-python.vscode-pylance','ms-toolsai.jupyter','REditorSupport.r','quarto.quarto','James-Yu.latex-workshop','charliermarsh.ruff']
for host in dev.get('customizations',{}).values():
    host['extensions']=extensions
    host.pop('settings',None)
dev.pop('updateContentCommand',None)
for name in ['ECC_UPDATE_SKILLS','ECC_FETCH_AI_REFERENCES']:
    dev.get('remoteEnv',{}).pop(name,None)
p.write_text(json.dumps(dev,indent=2)+'\n')
(root/'.vscode/extensions.json').write_text(json.dumps({'recommendations':extensions},indent=2)+'\n')
p=root/'.vscode/tasks.json'
doc=json.loads(p.read_text())
doc['tasks']=[t for t in doc.get('tasks',[]) if not re.search(r'\b(?:check|test)\b',t.get('command',''),re.I)]
if not doc['tasks']:
    doc['tasks']=[{'label':'Build paper','type':'shell','command':'make build-paper','group':'build','problemMatcher':[]},{'label':'Build slides','type':'shell','command':'make build-slides','problemMatcher':[]}]
p.write_text(json.dumps(doc,indent=2)+'\n')

# Keep package declarations intact; remove repository-wide Pixi test chains.
p=root/'pyproject.toml'
s=p.read_text()
s=re.sub(r'(?ms)^\[tool\.mypy\].*?(?=^\[build-system\])','',s)
s=re.sub(r'(?m)^\[tool\.pytest\.ini_options\]\n(?:[^\[\n][^\n]*\n|\n)*','',s)
start=s.index('[tool.pixi.tasks]')
end=s.find('\n[',start+1)
end=len(s) if end<0 else end
block=s[start:end]
block=re.sub(r'(?m)^(?:test|check|format|lint|pre-commit) = .*\n','',block)
if os.environ['GITHUB_REPOSITORY'].endswith('/econ-project'):
    block=block.replace('[tool.pixi.tasks]\n','[tool.pixi.tasks]\ntest = "make test"\nlint = "make lint"\nformat = "make format"\n')
s=s[:start]+block+s[end:]
p.write_text(s)

name=os.environ['GITHUB_REPOSITORY'].split('/')[-1]
(root/'README.md').write_text(f'''# {name}

General economics research with Python, R, Quarto and LaTeX. Open the repository in the Dev Container. Full and mini retain their separate package environments.

## Working rules

`.cursorrules` owns common policy. [Research skills](docs/ai/compiled_ai_skills.md) supply task methods. Use direct code, concise prose and plain templates. Reuse existing results and add only what the current task needs.

Mechanical checks are off by default. A concrete risk in a changed result justifies the smallest relevant execution. Writing includes one meaning-based post-draft review. Routine scanners, configuration suites and passing-check reports are removed.

## Dependencies

```sh
make sync
make r-install
pixi add PACKAGE
rv add PACKAGE
```

Run research code with the existing Pixi/R environment. Full keeps its broad research stack; mini adds analysis packages as needed.

## Documents and explicit operations

```sh
make build-paper
make build-slides
make test TEST=tests/example.py::test_result
make lint FILE=scripts/example.py
make format FILE=scripts/example.py
```

Tests, lint and formatting run only for the explicitly named target. Commit hooks retain only private-key detection. Editor test discovery, routine lint and automatic formatting are disabled.

## Chat and Work

[Project integration](docs/ai/integration.md) describes the existing-Project bridge and standalone export.

```sh
python scripts/export_project.py --profile bridge --output /tmp/econ-bridge
```

Code and templates stay in Git. Raw data, papers and credentials retain their existing storage and access rules. Source assets and unrelated work are preserved.
''')

# Exercise the changed exporter directly, without introducing a test suite.
with tempfile.TemporaryDirectory() as tmp:
    for profile in ['bridge','standalone']:
        subprocess.run(['python3','scripts/export_project.py','--profile',profile,'--output',str(Path(tmp)/profile)],check=True)

# Delete only the obsolete configuration-check runs requested by the user.
api=f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}"
headers={'Authorization':f"Bearer {os.environ['GH_TOKEN']}",'Accept':'application/vnd.github+json'}
def request(path,method='GET'):
    with urlopen(Request(api+path,headers=headers,method=method),timeout=30) as response:
        data=response.read()
        return json.loads(data) if data else None
runs=[]
page=1
while True:
    batch=request(f'/actions/runs?per_page=100&page={page}')['workflow_runs']
    runs += [r['id'] for r in batch if r.get('path')=='.github/workflows/research-config.yml' and r['status']=='completed']
    if len(batch)<100:
        break
    page+=1
for run in runs:
    request(f'/actions/runs/{run}','DELETE')
print(f'Deleted obsolete configuration runs: {len(runs)}')

# Remove the one-time maintenance mechanism from the finished branch.
(root/'scripts/_simplify_once.py').unlink(missing_ok=True)
(root/'.github/workflows/simplify-once.yml').unlink()
paths=subprocess.run(['git','diff','--name-only','-z'],check=True,capture_output=True).stdout.decode().strip('\0').split('\0')
paths=sorted(set(paths+['scripts/export_project.py']))
subprocess.run(['git','config','user.name','github-actions[bot]'],check=True)
subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],check=True)
subprocess.run(['git','add','--',*paths],check=True)
subprocess.run(['git','commit','-m','Remove automatic checks and simplify project commands and editor setup'],check=True)
subprocess.run(['git','push','origin',f"HEAD:{os.environ['GITHUB_REF_NAME']}"],check=True)

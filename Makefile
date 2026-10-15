# Explicit project operations.
.PHONY: help prepare-pixi sync install setup-dev setup-quality setup-extensions register-kernels setup-r-kernel quality quality-staged quality-changed typecheck format-check format lint test r-parse clean r-install r-plan build-paper build-slides quarto-html qmd-pdf slides-pdf quarto-pdf quarto-reveal

PIXI ?= pixi
PIXI_RUN = $(PIXI) run
QUALITY_RUN = $(PIXI) run -e quality
THREAD_ENV = OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
R_MAKEVARS_USER ?= $(CURDIR)/scripts/r-makevars
FILE ?=
BASE ?=
TEST ?=
QMD ?=
PAPER ?= tex/paper/ecta_template.tex
SLIDES ?= tex/slides/main.tex

help:
	@echo "sync / r-install / r-plan: dependencies"
	@echo "build-paper PAPER=path / build-slides SLIDES=path / quarto-* QMD=path: documents"
	@echo "test TEST=path::node / lint FILE=path / format FILE=path: explicit targets"
	@echo "quality FILE=path / quality-staged / quality-changed BASE=ref: changed code checks"
	@echo "setup-quality / typecheck FILE=path / format-check FILE=path / r-parse FILE=path"
	@echo "Project export: python scripts/export_project.py --profile standalone --task econ-paper --references .agents/skills/econ-workflow/references/descriptive-model.md --output /tmp/econ-paper-new; profiles and all-method export: docs/ai/integration.md"

prepare-pixi:
	sudo mkdir -p .pixi /home/vscode/.cache /home/vscode/.cache/R /home/vscode/.cache/rattler /home/vscode/.cache/rv
	sudo chown vscode:vscode /home/vscode/.cache
	sudo chown vscode:vscode .pixi /home/vscode/.cache/R /home/vscode/.cache/rattler /home/vscode/.cache/rv
	sudo chmod u+rwx /home/vscode/.cache
	sudo chmod u+rwX .pixi /home/vscode/.cache/R /home/vscode/.cache/rattler /home/vscode/.cache/rv

sync: prepare-pixi
	$(PIXI) install
install: sync
setup-dev: sync
	$(PIXI_RUN) pre-commit install
setup-quality:
	$(PIXI) install -e quality
	$(QUALITY_RUN) pre-commit install
setup-extensions:
	bash scripts/setup_extensions.sh
register-kernels:
	bash .devcontainer/register-kernels.sh
setup-r-kernel: register-kernels

quality:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(QUALITY_RUN) pre-commit run --files "$(FILE)"
quality-staged:
	$(QUALITY_RUN) pre-commit run
quality-changed:
	@test -n "$(BASE)" || { echo "Specify BASE=ref (committed changes only)" >&2; exit 2; }
	$(QUALITY_RUN) pre-commit run --from-ref "$(BASE)" --to-ref HEAD
typecheck:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(QUALITY_RUN) mypy -- "$(FILE)"
format-check:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(QUALITY_RUN) ruff format --check -- "$(FILE)"
r-parse:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(PIXI_RUN) Rscript --vanilla -e 'invisible(parse(file = commandArgs(TRUE)[1]))' "$(FILE)"

format:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(PIXI_RUN) ruff format -- "$(FILE)"
lint:
	@test -n "$(FILE)" || { echo "Specify FILE=path" >&2; exit 2; }
	$(PIXI_RUN) ruff check -- "$(FILE)"
test:
	@test -n "$(TEST)" || { echo "Specify TEST=path::node" >&2; exit 2; }
	$(THREAD_ENV) $(PIXI_RUN) pytest -q -p no:cacheprovider -- "$(TEST)"

r-install: RV_ACTION = sync
r-plan: RV_ACTION = plan
r-install: prepare-pixi
r-install r-plan:
	$(PIXI_RUN) bash -lc ' \
		set -euo pipefail; \
		export PKG_CONFIG="$$CONDA_PREFIX/bin/pkg-config"; \
		export PKG_CONFIG_PATH="$$CONDA_PREFIX/lib/pkgconfig:$$CONDA_PREFIX/share/pkgconfig:$${PKG_CONFIG_PATH:-}"; \
		export LIBRARY_PATH="$$CONDA_PREFIX/lib:$${LIBRARY_PATH:-}"; \
		export LD_LIBRARY_PATH="$$CONDA_PREFIX/lib:$${LD_LIBRARY_PATH:-}"; \
		export R_MAKEVARS_USER="$(R_MAKEVARS_USER)"; \
		export XML_CONFIG="$$CONDA_PREFIX/bin/xml2-config"; \
		export NANONEXT_LIBS=1; \
		unset NANONEXT_TLS CMAKE_PREFIX_PATH JAVA_HOME; \
		if [ "$(RV_ACTION)" = sync ]; then \
			if pgrep -u "$$(id -u)" -x rv >/dev/null; then \
				echo "Another rv process is running." >&2; exit 1; \
			fi; \
			ln -sf libxml2.so.16 "$$CONDA_PREFIX/lib/libxml2.so" 2>/dev/null || true; \
		fi; \
		rv $(RV_ACTION) \
	'

build-paper:
	python3 scripts/build_latex.py -- '$(subst ','"'"',$(PAPER))'
build-slides:
	python3 scripts/build_latex.py -- '$(subst ','"'"',$(SLIDES))'
quarto-html:
	$(PIXI_RUN) quarto render "$(if $(strip $(QMD)),$(QMD),.)" --to html
qmd-pdf:
	@test -n "$(QMD)" || { echo "Specify QMD=path" >&2; exit 2; }
	TEXINPUTS="$(CURDIR)/tex/paper:$${TEXINPUTS:-}" \
	BSTINPUTS="$(CURDIR)/tex/paper:$${BSTINPUTS:-}" \
	$(PIXI_RUN) quarto render "$(QMD)" --to pdf
slides-pdf:
	@test -n "$(QMD)" || { echo "Specify QMD=path" >&2; exit 2; }
	$(PIXI_RUN) quarto render "$(QMD)" --to beamer
quarto-pdf: qmd-pdf
quarto-reveal:
	$(PIXI_RUN) quarto render "$(if $(strip $(QMD)),$(QMD),.)" --to revealjs

clean:
	rm -rf -- .coverage .mypy_cache .pytest_cache .ruff_cache _site _book .quarto
	find tex -type f \( -name '*.aux' -o -name '*.blg' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.synctex.gz' -o -name '*.run.xml' -o -name '*.fdb_latexmk' -o -name '*.fls' \) -delete

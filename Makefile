# Explicit project operations.
.PHONY: help prepare-pixi sync setup-extensions register-kernels format clean r-install r-plan build-paper build-slides quarto-html qmd-pdf slides-pdf quarto-pdf quarto-reveal

PIXI ?= pixi
PIXI_RUN = $(PIXI) run
export R_BUILD_MAKEVARS := $(if $(filter undefined,$(origin R_MAKEVARS_USER)),$(CURDIR)/scripts/r-makevars,$(value R_MAKEVARS_USER))
unexport R_MAKEVARS_USER
FILE ?=
# Keep user paths out of recipe text and prevent Make from expanding them again
# while exporting its original command-line variables to child processes.
export FORMAT_FILE := $(value FILE)
unexport FILE
FORMAT_FILE_INPUT = test -f "$$FORMAT_FILE" || { printf '%s\n' 'Specify FILE=path to an existing file' >&2; exit 2; }; case "$$FORMAT_FILE" in /*) ;; *) FORMAT_FILE="./$$FORMAT_FILE" ;; esac
QMD ?=
export QUARTO_DOCUMENT := $(value QMD)
unexport QMD
QUARTO_INPUT = case "$$QUARTO_DOCUMENT" in /*|./*|../*) ;; *) QUARTO_DOCUMENT="./$$QUARTO_DOCUMENT" ;; esac
PAPER ?= tex/paper/ecta_template.tex
SLIDES ?= tex/slides/main.tex
export LATEX_PAPER := $(value PAPER)
export LATEX_SLIDES := $(value SLIDES)
unexport PAPER SLIDES
export TEXINPUTS := $(CURDIR)/tex/paper:$(TEXINPUTS)
export BSTINPUTS := $(CURDIR)/tex/paper:$(BSTINPUTS)

help:
	@echo "sync / r-install / r-plan: dependencies"
	@echo "build-paper PAPER=path / build-slides SLIDES=path / quarto-* QMD=path: documents"
	@echo "format FILE=path: format the named source file"
	@echo "Project export: python scripts/export_project.py --task econ-writing --mode compose --output /tmp/econ-writing-new; selection and export: docs/ai/integration.md"

prepare-pixi:
	mkdir -p .pixi

sync: prepare-pixi
	$(PIXI) install
setup-extensions:
	bash scripts/setup_extensions.sh --sync
register-kernels:
	bash .devcontainer/register-kernels.sh

format:
	@$(FORMAT_FILE_INPUT); $(PIXI_RUN) ruff format -- "$$FORMAT_FILE"
r-install: RV_ACTION = sync
r-plan: RV_ACTION = plan
r-install: prepare-pixi
r-install r-plan:
	$(PIXI_RUN) bash -c ' \
		set -euo pipefail; \
		export PKG_CONFIG="$$CONDA_PREFIX/bin/pkg-config"; \
		export PKG_CONFIG_PATH="$$CONDA_PREFIX/lib/pkgconfig:$$CONDA_PREFIX/share/pkgconfig:$${PKG_CONFIG_PATH:-}"; \
		export LIBRARY_PATH="$$CONDA_PREFIX/lib:$${LIBRARY_PATH:-}"; \
		export LD_LIBRARY_PATH="$$CONDA_PREFIX/lib:$${LD_LIBRARY_PATH:-}"; \
		export R_MAKEVARS_USER="$$R_BUILD_MAKEVARS"; \
		export XML_CONFIG="$$CONDA_PREFIX/bin/xml2-config"; \
		export NANONEXT_LIBS=1; \
		unset NANONEXT_TLS CMAKE_PREFIX_PATH JAVA_HOME; \
		if [ "$(RV_ACTION)" = sync ]; then \
			if pgrep -u "$$(id -u)" -x rv >/dev/null; then \
				echo "Another rv process is running." >&2; exit 1; \
			fi; \
		fi; \
		rv $(RV_ACTION) \
	'

build-paper:
	python3 scripts/build_latex.py -- "$$LATEX_PAPER"
build-slides:
	python3 scripts/build_latex.py -- "$$LATEX_SLIDES"
quarto-html:
	@QUARTO_DOCUMENT="$${QUARTO_DOCUMENT:-.}"; $(QUARTO_INPUT); $(PIXI_RUN) quarto render "$$QUARTO_DOCUMENT" --to html
qmd-pdf:
	@test -n "$$QUARTO_DOCUMENT" || { echo "Specify QMD=path" >&2; exit 2; }; $(QUARTO_INPUT); $(PIXI_RUN) quarto render "$$QUARTO_DOCUMENT" --to pdf
slides-pdf:
	@test -n "$$QUARTO_DOCUMENT" || { echo "Specify QMD=path" >&2; exit 2; }; $(QUARTO_INPUT); $(PIXI_RUN) quarto render "$$QUARTO_DOCUMENT" --to beamer
quarto-pdf: qmd-pdf
quarto-reveal:
	@QUARTO_DOCUMENT="$${QUARTO_DOCUMENT:-.}"; $(QUARTO_INPUT); $(PIXI_RUN) quarto render "$$QUARTO_DOCUMENT" --to revealjs

clean:
	rm -rf -- .ruff_cache _site _book .quarto
	find tex -type f \( -name '*.aux' -o -name '*.blg' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.synctex.gz' -o -name '*.run.xml' -o -name '*.fdb_latexmk' -o -name '*.fls' \) -delete

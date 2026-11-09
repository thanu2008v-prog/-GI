.PHONY: all help install build v2 export bundle nool check clean serve

PYTHON ?= python3

help:
	@echo "Targets:"
	@echo "  make all      - run the standard project build/check flow"
	@echo "  make v2       - generate the v2 data bundle and exports"
	@echo "  make nool     - build the readable book and validate the round-trip"
	@echo "  make check    - run the validation pipeline"
	@echo "  make serve    - serve the project locally for the browser UI"
	@echo "  make clean    - remove generated build artifacts"

all: check

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install "PyYAML>=6.0"

v2:
	$(PYTHON) build_v2.py
	$(PYTHON) export_bundle.py
	$(PYTHON) export_csv.py

nool:
	$(PYTHON) build_nool.py
	$(PYTHON) check_nool.py

check: v2 nool

clean:
	rm -rf build
	find . -type d -name "__pycache__" -exec rm -rf {} +

serve:
	$(PYTHON) -m http.server 8000

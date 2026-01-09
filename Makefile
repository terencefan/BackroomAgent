.PHONY: install server graph frontend-install frontend-dev frontend-build clean format

PYTHON = .venv/bin/python
PIP = .venv/bin/pip

# backend
install:
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

graph:
	PYTHONPATH=. $(PYTHON) scripts/generate_level_graph.py
	PYTHONPATH=. $(PYTHON) scripts/generate_item_graph.py
	PYTHONPATH=. $(PYTHON) scripts/generate_entity_graph.py
	PYTHONPATH=. $(PYTHON) scripts/generate_agent_graphs.py

scripts-fetch:
	PYTHONPATH=. $(PYTHON) scripts/batch_fetch_levels.py

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ --cov=backroom_agent --cov-report=term-missing

format:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .
	cd frontend && npm run lint -- --fix

# frontend
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +

# data management
BACKEND ?= pickle

clean-orphans:
	PYTHONPATH=. $(PYTHON) scripts/clean_orphans.py

clean-stores:
	PYTHONPATH=. $(PYTHON) scripts/clean_old_stores.py --backend=$(BACKEND)

rebuild-indices:
	PYTHONPATH=. $(PYTHON) scripts/rebuild_indices.py --backend=$(BACKEND)

rebuild-all: rebuild-indices

.PHONY: install server graph frontend-install frontend-dev frontend-build clean

PYTHON = .venv/bin/python
PIP = .venv/bin/pip

# backend
install:
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

server:
	$(PYTHON) backend/main.py

graph:
	PYTHONPATH=. $(PYTHON) backroom_agent/utils/map_generator.py

scripts-fetch:
	PYTHONPATH=. $(PYTHON) scripts/batch_fetch_levels.py

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ --cov=backroom_agent --cov-report=term-missing

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
	PYTHONPATH=. $(PYTHON) scripts/clean_and_rebuild.py

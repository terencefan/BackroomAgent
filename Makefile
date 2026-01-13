.PHONY: install server client graph frontend-install frontend-dev frontend-build clean format install-hooks

PYTHON = .venv/bin/python
PIP = .venv/bin/pip

# backend
server:
	PYTHONPATH=. $(PYTHON) -m backroom_agent.server

client:
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && cd frontend && npm run dev

install:
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

graph:
	PYTHONPATH=. $(PYTHON) scripts/generate_level_graph.py & \
	PYTHONPATH=. $(PYTHON) scripts/generate_item_graph.py & \
	PYTHONPATH=. $(PYTHON) scripts/generate_entity_graph.py & \
	PYTHONPATH=. $(PYTHON) scripts/generate_agent_graphs.py & \
	wait

scripts-fetch:
	PYTHONPATH=. $(PYTHON) scripts/batch_fetch_levels.py

test:
	PYTHONPATH=. $(PYTHON) -m pytest tests/ --cov=backroom_agent --cov-report=term-missing

format:
	$(PYTHON) -m black .
	$(PYTHON) -m isort .
	.venv/bin/pyright
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && cd frontend && npm run lint -- --fix

# git hooks
install-hooks:
	@echo "📦 安装 Git hooks..."
	@if [ -d .githooks ]; then \
		for hook in .githooks/*; do \
			if [ -f $$hook ] && [ "$${hook##*.}" != "py" ]; then \
				hook_name=$$(basename $$hook); \
				cp $$hook .git/hooks/$$hook_name; \
				chmod +x .git/hooks/$$hook_name; \
				echo "✅ 已安装: $$hook_name"; \
			fi; \
		done; \
		echo "🎉 Git hooks 安装完成！"; \
	else \
		echo "❌ .githooks 目录不存在"; \
	fi

# frontend
frontend-install:
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && cd frontend && npm install

frontend-dev:
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && cd frontend && npm run dev

frontend-build:
	export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && cd frontend && npm run build

# cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	$(MAKE) clean-redis

# data management
BACKEND ?= pickle

clean-orphans:
	PYTHONPATH=. $(PYTHON) scripts/clean_orphans.py

clean-stores:
	PYTHONPATH=. $(PYTHON) scripts/clean_old_stores.py --backend=$(BACKEND)

rebuild-indices:
	PYTHONPATH=. $(PYTHON) scripts/rebuild_indices.py --backend=$(BACKEND)

rebuild-all: rebuild-indices

clean-redis:
	PYTHONPATH=. $(PYTHON) scripts/clear_redis.py

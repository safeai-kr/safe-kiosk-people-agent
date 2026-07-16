LOCK_VENV := /tmp/safe-kiosk-people-agent-lock-venv
PIP_TOOLS_VERSION := 7.5.2

.PHONY: lock
lock:
	python3.11 -m venv --clear $(LOCK_VENV)
	$(LOCK_VENV)/bin/pip install --disable-pip-version-check pip-tools==$(PIP_TOOLS_VERSION)
	CUSTOM_COMPILE_COMMAND='make lock' $(LOCK_VENV)/bin/pip-compile --resolver=backtracking --strip-extras --generate-hashes --allow-unsafe --output-file=requirements.lock pyproject.toml
	CUSTOM_COMPILE_COMMAND='make lock' $(LOCK_VENV)/bin/pip-compile --resolver=backtracking --strip-extras --generate-hashes --allow-unsafe --extra=dev --output-file=requirements-dev.lock pyproject.toml
LOCK_VENV := /tmp/safe-kiosk-people-agent-lock-venv
PIP_TOOLS_VERSION := 7.5.2

.PHONY: lock
lock:
	python3.11 -m venv --clear $(LOCK_VENV)
	$(LOCK_VENV)/bin/pip install --disable-pip-version-check pip-tools==$(PIP_TOOLS_VERSION)
	CUSTOM_COMPILE_COMMAND='make lock' $(LOCK_VENV)/bin/pip-compile --resolver=backtracking --strip-extras --generate-hashes --allow-unsafe --output-file=requirements.lock pyproject.toml
	CUSTOM_COMPILE_COMMAND='make lock' $(LOCK_VENV)/bin/pip-compile --resolver=backtracking --strip-extras --generate-hashes --allow-unsafe --extra=dev --output-file=requirements-dev.lock pyproject.toml

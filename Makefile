.PHONY: lint test run

lint:
	.venv/bin/ruff check awg_gui tests
	.venv/bin/ruff format --check awg_gui tests

test:
	.venv/bin/pytest

run:
	.venv/bin/awg-gui

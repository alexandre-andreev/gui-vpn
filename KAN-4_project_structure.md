# KAN-4: Скелет проекта (pyproject.toml, структура, ruff, pytest)

> **Jira:** KAN-4 · Проект: Разработка приложения для управления впн · Статус: К выполнению

---

Подготовить базу проекта `awg-gui`.

## Что нужно

- Создать `pyproject.toml` (Python 3.11+, имя пакета `awg-gui`, точка входа `awg-gui = awg_gui.__main__:main`).
- Создать структуру каталогов: `awg_gui/`, `tests/`, `docs/`, `policy/`.
- Настроить venv-инструкцию в README.
- Подключить `ruff` (lint + format) и `pytest` + `pytest-cov`.
- Базовый `awg_gui/__main__.py` с `print("ok")` для smoke-теста.
- `Makefile` с целями `lint`, `test`, `run`.

## Acceptance

- `python -m venv .venv && .venv/bin/pip install -e .[dev]` отрабатывает без ошибок.
- `make lint` и `make test` зелёные.
- `awg-gui` запускается из консоли после установки.

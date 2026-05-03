# awg-gui

GUI-утилита для управления VPN-подключением AmneziaWG на Debian 12.

## Требования

- Python 3.11+
- `python3-tk` (`sudo apt install python3-tk`)

## Установка

```bash
python3 -m venv .venv
.venv/bin/pip install -e .[dev]
```

## Использование

```bash
awg-gui          # запуск через консоль (после установки)
make run         # запуск через make
```

## Разработка

```bash
make lint        # ruff check + format check
make test        # pytest с покрытием
```

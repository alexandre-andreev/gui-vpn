# awg-gui

Графический интерфейс для управления VPN-подключением [AmneziaWG](https://github.com/amnezia-vpn/amneziawg-linux-kernel-module) на Debian 12.

Позволяет переключаться между VPN-конфигурациями, видеть статус соединения и управлять автозапуском — без работы в терминале.

## Возможности

- Список серверов из каталога `.conf`-файлов, сгруппированный по странам
- Подключение / отключение / переключение туннеля одним кликом
- Индикатор состояния (серый / оранжевый / зелёный / красный)
- Проверка доступности интернета в фоне
- Автозапуск VPN при загрузке системы
- Автозапуск приложения при входе в систему
- Атомарная замена `wg0.conf` с резервной копией `.original`

## Требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.11+ |
| python3-tk | любая (из репозитория Debian) |
| AmneziaWG | установлен, сервис `awg-quick@wg0` доступен |
| PolicyKit (`polkit`) | для привилегированных операций |

```bash
sudo apt install python3-tk
```

## Установка

### 1. Клонировать репозиторий

```bash
git clone <repo-url> awg-gui
cd awg-gui
```

### 2. Создать виртуальное окружение и установить пакет

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 3. Установить PolicyKit-политику и helper-скрипт

```bash
sudo bash install.sh
```

Скрипт копирует:
- `policy/awg-gui-helper` → `/usr/local/lib/awg-gui/awg-gui-helper` (права 0755, root)
- `policy/org.awg-gui.policy` → `/usr/share/polkit-1/actions/` (права 0644, root)

Подробнее: [docs/install.md](docs/install.md)

## Быстрый старт

```bash
.venv/bin/awg-gui
# или
make run
```

При первом запуске укажите каталог с `.conf`-файлами в **Настройки → Каталог конфигураций**.

Файлы должны иметь имена вида `CountryCityS1.conf` (например, `GermanyBerlinS7.conf`).

## Разработка

```bash
make lint        # ruff check + format check
make test        # pytest + coverage
```

Тесты не требуют root и не обращаются к реальному `systemctl` — подробности в [docs/install.md](docs/install.md).

## Структура проекта

```
awg_gui/          # Python-пакет
  config_manager.py   — парсинг .conf-файлов
  vpn_service.py      — обёртка над helper-скриптом
  network_checker.py  — фоновая проверка интернета
  controller.py       — логика подключения (очередь + потоки)
  ui.py               — Tkinter-интерфейс
  autostart.py        — управление .desktop-файлом
  settings.py         — хранение настроек (JSON)
  logger.py           — логирование в файл
policy/           # PolicyKit: helper-скрипт и .policy-файл
tests/            # pytest (unit + bash integration)
install.sh        # установка helper + policy (root)
```

## Лицензия

MIT

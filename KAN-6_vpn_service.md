# KAN-6: vpn_service — pkexec + атомарная подмена wg0.conf + бэкап

> **Jira:** KAN-6 · Проект: Разработка приложения для управления впн · Статус: К выполнению

---

Реализовать модуль `awg_gui/vpn_service.py` — обёртка над AmneziaWG/systemctl.

## Что нужно

- Методы: `start()`, `stop()`, `is_active()`, `enable_autostart()`, `disable_autostart()`, `is_autostart_enabled()`, `apply_config(config_path)`, `restore_original()`, `get_active_config_hash()`.
- Все привилегированные команды через `pkexec systemctl …` и `pkexec cp/mv` (или вспомогательный helper-скрипт, вызываемый через одну `pkexec`-сессию).
- **Атомарная подмена** `/etc/amnezia/amneziawg/wg0.conf`:
  1. Скопировать новый конфиг во временный файл рядом с целевым (`/etc/amnezia/amneziawg/wg0.conf.tmp.<pid>`).
  2. `os.replace(tmp, target)` — атомарная операция на одном FS.
- **Бэкап** при первом запуске: если `wg0.conf.original` не существует, создать его копией текущего `wg0.conf`.
- `restore_original()` — возврат `wg0.conf` из бэкапа.

## Совместимость с bash-скриптами (FR-10, NFR-7)

- После любой операции `wg0.conf` всегда валидный AmneziaWG-конфиг.
- Аварийный exit / kill не оставляет полузаписанный файл.

## Тесты

- Юнит-тесты с моками `subprocess.run` для всех команд.
- Тест атомарной подмены на временной директории.
- Тест бэкапа: первый запуск создаёт `original`, повторные — нет.

## Acceptance

- `apply_config()` + `start()` поднимают туннель (smoke-тест на dev-машине).
- После `kill -9` во время `apply_config()` `wg0.conf` остаётся валидным.

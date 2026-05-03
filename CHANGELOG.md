# Changelog

## [0.1.0] — 2026-05-03

Первый рабочий релиз.

### Добавлено

- **Структура проекта** (KAN-4): `pyproject.toml`, `Makefile`, пакет `awg_gui`, конфигурация ruff и pytest.
- **Менеджер конфигураций** (KAN-5): парсинг `.conf`-файлов с разбором имён вида `CountryCityS1.conf`; поддержка многословных стран (Czech Republic, Hong Kong, United Kingdom); нормализация пробелов в именах файлов.
- **VPN-сервис** (KAN-6→KAN-9): управление туннелем через `systemctl` и `awg-gui-helper`; атомарная замена `wg0.conf` (rename(2)); резервная копия `.original` при первом применении.
- **Проверка сети** (KAN-7): фоновый `NetworkChecker` с дебаунсингом (2 последовательных одинаковых результата); HTTP-зонд + TCP-фолбек.
- **Tkinter UI + Controller** (KAN-8): список серверов, сгруппированный по странам; индикатор состояния; диалог настроек; потокобезопасная очередь событий.
- **PolicyKit + helper** (KAN-9): `policy/awg-gui-helper` (bash, test mode через `AWG_TEST_MODE=1`); `policy/org.awg-gui.policy` (`auth_admin_keep`); `install.sh`.
- **Документация** (KAN-10): README, runbook, инструкция по откату, руководство по установке, CHANGELOG.

# KAN-9: PolicyKit-политика и инструкция по установке

> **Jira:** KAN-9 · Проект: Разработка приложения для управления впн · Статус: К выполнению

---

Подготовить PolicyKit-политику для эскалации привилегий через `pkexec`.

## Что нужно

- Файл `policy/org.awg-gui.policy` (XML, формат PolicyKit).
- Действия:
  - `org.awg-gui.start` — `systemctl start awg-quick@wg0.service`
  - `org.awg-gui.stop` — `systemctl stop awg-quick@wg0.service`
  - `org.awg-gui.enable` — `systemctl enable awg-quick@wg0.service`
  - `org.awg-gui.disable` — `systemctl disable awg-quick@wg0.service`
  - `org.awg-gui.apply-config` — копирование `wg0.conf` в `/etc/amnezia/amneziawg/`
- `auth_admin_keep` — кэш авторизации на 5 минут, чтобы не запрашивать пароль каждый раз.
- Helper-скрипт `awg-gui-helper` в `/usr/local/lib/awg-gui/`, вызываемый через `pkexec`, для безопасного выполнения операций (без передачи произвольных аргументов).
- Установщик: `bash install.sh` копирует политику в `/usr/share/polkit-1/actions/` и helper в `/usr/local/lib/awg-gui/`.

## Acceptance

- На свежей Debian 12 после `sudo bash install.sh` приложение работает с одним запросом пароля на сеанс операций.
- `pkexec --version` присутствует в зависимостях установки (PolicyKit входит в Debian по умолчанию).

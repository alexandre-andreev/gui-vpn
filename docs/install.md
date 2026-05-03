# Установка awg-gui

## Предварительные условия

- Debian 12 (или совместимый дистрибутив)
- Python 3.11+
- AmneziaWG установлен и настроен (`/etc/amnezia/amneziawg/wg0.conf` существует)
- `polkit` установлен (`sudo apt install policykit-1`)
- `python3-tk` установлен (`sudo apt install python3-tk`)

---

## Шаг 1. Получить исходный код

```bash
git clone <repo-url> awg-gui
cd awg-gui
```

---

## Шаг 2. Создать виртуальное окружение

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

Для разработки (тесты, линтер):

```bash
.venv/bin/pip install -e ".[dev]"
```

---

## Шаг 3. Установить PolicyKit-политику и helper-скрипт

```bash
sudo bash install.sh
```

Что происходит:

| Действие | Результат |
|----------|-----------|
| `install -m 0755 policy/awg-gui-helper` | `/usr/local/lib/awg-gui/awg-gui-helper` |
| `install -m 0644 policy/org.awg-gui.policy` | `/usr/share/polkit-1/actions/org.awg-gui.policy` |

Helper-скрипт запускается как root через `pkexec`. PolicyKit использует политику `org.awg-gui.manage` с уровнем `auth_admin_keep` — это означает, что диалог ввода пароля появляется один раз и кешируется примерно на 5 минут.

### Проверка установки

```bash
ls -la /usr/local/lib/awg-gui/awg-gui-helper
# -rwxr-xr-x 1 root root ... awg-gui-helper

ls /usr/share/polkit-1/actions/org.awg-gui.policy
# /usr/share/polkit-1/actions/org.awg-gui.policy
```

---

## Шаг 4. Запустить приложение

```bash
.venv/bin/awg-gui
```

При первом запуске откройте **Настройки** и укажите каталог с `.conf`-файлами.

---

## Обновление

```bash
git pull
.venv/bin/pip install -e .
sudo bash install.sh   # если изменился helper или policy
```

---

## Запуск тестов

Тесты не требуют root:

```bash
make test
# или
.venv/bin/pytest
```

- `tests/test_vpn_service.py` — unit-тесты с моком `subprocess.run`
- `tests/test_helper.py` — bash-интеграционные тесты с `AWG_TEST_MODE=1`

---

## Удаление

См. [rollback-to-bash.md](rollback-to-bash.md#удаление-awg-gui).

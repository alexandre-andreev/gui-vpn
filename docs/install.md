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

## Шаг 2. Создать виртуальное окружение и установить пакет

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

Для разработки (тесты, линтер):

```bash
.venv/bin/pip install -e ".[dev]"
```

---

## Шаг 3. Установить PolicyKit-политику, helper-скрипт и системный лаунчер

```bash
sudo bash install.sh
```

Что происходит:

| Действие | Результат |
|----------|-----------|
| `install -m 0755 policy/awg-gui-helper` | `/usr/local/lib/awg-gui/awg-gui-helper` |
| `install -m 0644 policy/org.awg-gui.policy` | `/usr/share/polkit-1/actions/org.awg-gui.policy` |
| создание лаунчера | `/usr/local/bin/awg-gui` |

Скрипт должен найти `.venv/bin/awg-gui` в каталоге репозитория. Если виртуальное окружение
не создано, `install.sh` завершится с ошибкой — нужно сначала выполнить шаг 2.

Helper-скрипт запускается как root через `pkexec`. PolicyKit использует политику
`org.awg-gui.manage` с уровнем `auth_admin_keep` — диалог ввода пароля появляется один раз
и кешируется примерно на 5 минут.

Системный лаунчер `/usr/local/bin/awg-gui` используется автозапуском и горячими клавишами.
При запуске из терминала он автоматически уходит в фон, возвращая управление консоли.

### Проверка установки

```bash
ls -la /usr/local/lib/awg-gui/awg-gui-helper
# -rwxr-xr-x 1 root root ... awg-gui-helper

ls /usr/share/polkit-1/actions/org.awg-gui.policy
# /usr/share/polkit-1/actions/org.awg-gui.policy

which awg-gui
# /usr/local/bin/awg-gui
```

---

## Шаг 4. Запустить приложение

```bash
awg-gui
```

При запуске из терминала консоль сразу освобождается (процесс уходит в фон).
Логи пишутся в `~/.local/share/awg-gui/awg-gui.log`.

При первом запуске откройте **Настройки** и укажите каталог с `.conf`-файлами.

---

## Шаг 5. Настроить горячую клавишу (опционально)

### GNOME (стандартный рабочий стол Debian)

1. Откройте **Параметры → Клавиатура → Просмотр и изменение комбинаций клавиш → Пользовательские комбинации клавиш**
2. Нажмите **+**
3. Заполните поля:
   - **Название**: `awg-gui`
   - **Команда**: `/usr/local/bin/awg-gui`
4. Нажмите **Задать комбинацию** и нажмите нужные клавиши (например, `Ctrl+Alt+V`)

### XFCE

1. Откройте **Настройки → Клавиатура → Комбинации клавиш приложений**
2. Нажмите **Добавить**
3. **Команда**: `/usr/local/bin/awg-gui`
4. Нажмите нужную комбинацию клавиш

### Важно

Используйте полный путь `/usr/local/bin/awg-gui` — именно он гарантирует работу
при любом состоянии окружения (PATH, активированные venv и т. д.).

---

## Автозапуск при входе в систему

Включается и отключается в самом приложении: **Настройки → Запускать awg-gui при входе в систему**.

После включения создаётся файл `~/.config/autostart/awg-gui.desktop` с абсолютным путём
к исполняемому файлу (берётся из `/usr/local/bin/awg-gui`). Это обеспечивает корректный
запуск без зависимости от PATH сессии.

---

## Обновление

```bash
git pull
.venv/bin/pip install -e .
sudo bash install.sh   # если изменился helper, policy или версия Python
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
- `tests/test_autostart.py` — тесты управления `.desktop`-файлом
- `tests/test_helper.py` — bash-интеграционные тесты с `AWG_TEST_MODE=1`

---

## Удаление

```bash
sudo rm /usr/local/bin/awg-gui
sudo rm /usr/local/lib/awg-gui/awg-gui-helper
sudo rmdir /usr/local/lib/awg-gui
sudo rm /usr/share/polkit-1/actions/org.awg-gui.policy
```

Подробнее: [rollback-to-bash.md](rollback-to-bash.md#удаление-awg-gui).
